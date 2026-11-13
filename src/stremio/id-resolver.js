/**
 * ID Resolver for Stremio / WuPlay.
 *
 * Resolves IMDB IDs (tt...) to TMDB IDs using fast caching and dual fallback:
 *   1. Bounded in-memory LRU cache O(1)
 *   2. TMDB /find via the wecollege proxy (db.wecollege.net/3/find), the authority on TMDB ids
 *   3. Cinemeta (v3-cinemeta.strem.io) as fallback: its moviedb_id can be stale
 */

const CINEMETA_URL = "https://v3-cinemeta.strem.io/meta";
const WECOLLEGE_FIND = "https://db.wecollege.net/3/find";

const imdbToTmdbCache = new Map();
const MAX_CACHE_SIZE = 500;
const LOOKUP_TIMEOUT_MS = 2500;

function setCache(imdbId, tmdbId) {
  if (imdbToTmdbCache.size >= MAX_CACHE_SIZE) {
    const oldest = imdbToTmdbCache.keys().next().value;
    imdbToTmdbCache.delete(oldest);
  }
  imdbToTmdbCache.set(imdbId, tmdbId);
}

// GET a JSON body within LOOKUP_TIMEOUT_MS; null on any failure (timeout, non-2xx, bad JSON).
async function fetchJsonOrNull(url) {
  const controller = typeof AbortController === "function" ? new AbortController() : null;
  const timer = controller ? setTimeout(() => controller.abort(), LOOKUP_TIMEOUT_MS) : null;
  try {
    const res = await fetch(url, {
      signal: controller ? controller.signal : undefined,
      headers: { "User-Agent": "Mozilla/5.0" },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    return null;
  } finally {
    if (timer) clearTimeout(timer);
  }
}

// TMDB /find (through the wecollege proxy): the first result of the requested kind, else the other kind.
async function findViaTmdb(imdbId, stremioType) {
  const data = await fetchJsonOrNull(`${WECOLLEGE_FIND}/${imdbId}?external_source=imdb_id`);
  if (!data) return null;
  const movie = data.movie_results && data.movie_results[0];
  const tv = data.tv_results && data.tv_results[0];
  const hit = stremioType === "series" ? tv || movie : movie || tv;
  return hit && hit.id ? String(hit.id) : null;
}

// Cinemeta's meta.moviedb_id (fallback only: it can be stale, see resolveTmdbId).
async function findViaCinemeta(imdbId, stremioType) {
  const data = await fetchJsonOrNull(`${CINEMETA_URL}/${stremioType}/${imdbId}.json`);
  const id = data && data.meta && (data.meta.moviedb_id || data.meta.tmdb_id);
  return id ? String(id) : null;
}

/**
 * Resolves an ID string (e.g., "tt0468569", "tmdb:155", "155") to a numeric TMDB ID.
 * @param {string} rawId - The raw ID from Stremio request
 * @param {string} mediaType - "movie" or "series"
 * @returns {Promise<string|null>} - The resolved TMDB ID string, or null
 */
async function resolveTmdbId(rawId, mediaType) {
  if (!rawId) return null;
  const idStr = String(rawId).trim();

  // 1. Direct TMDB ID
  if (idStr.startsWith("tmdb:")) {
    const clean = idStr.replace(/^tmdb:/, "").split(":")[0];
    return clean || null;
  }
  if (/^\d+$/.test(idStr)) {
    return idStr;
  }

  // 2. IMDB ID (e.g. tt0468569 or tt0903747:1:1)
  const imdbId = idStr.split(":")[0];
  if (!/^tt\d+$/.test(imdbId)) {
    return null;
  }

  // Check cache O(1)
  const cached = imdbToTmdbCache.get(imdbId);
  if (cached) return cached;

  const stremioType = mediaType === "series" || mediaType === "tv" ? "series" : "movie";

  // TMDB's own /find answers first: it is the authority on its ids. Cinemeta's moviedb_id can
  // point at a dead TMDB entry (tt5109280 "Raya and the Last Dragon" -> 508441 instead of
  // 527774), and every provider is keyed by the TMDB id, so a stale one empties them all.
  // Cinemeta stays as the fallback for when the TMDB proxy is down or has no match.
  const tmdbId = (await findViaTmdb(imdbId, stremioType)) || (await findViaCinemeta(imdbId, stremioType));
  if (tmdbId) {
    setCache(imdbId, tmdbId);
    return tmdbId;
  }
  return null;
}

module.exports = { resolveTmdbId };
