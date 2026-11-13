/**
 * Offline IMDb -> TMDB resolver tests (no network: fetch is stubbed, providers are stubbed).
 *
 * Edge case behind this file: Stremio/WuPlay ask for "Raya and the Last Dragon" as tt5109280.
 * Cinemeta's meta.moviedb_id for it is 508441, a dead TMDB entry; TMDB's own /find says 527774
 * (https://flystream.net/movie/527774). Trusting Cinemeta sent 508441 to every provider, so
 * FlyStream answered HTTP 400 and only Movy showed. The fixtures below are those real answers.
 * Run: node test-id-resolver-offline.js
 */
const assert = require("assert");
const path = require("path");

const RAYA_IMDB = "tt5109280";
const RAYA_TMDB = "527774";
const RAYA_CINEMETA_STALE = 508441;

// Stub network: per-test handlers for the two lookup hosts; anything else is a test failure.
let handlers = {};
const calls = [];
const json = (status, body) => ({ ok: status >= 200 && status < 300, status, json: async () => body });
global.fetch = async (url) => {
  url = String(url);
  calls.push(url);
  if (url.startsWith("https://db.wecollege.net/3/find/")) return handlers.find(url);
  if (url.startsWith("https://v3-cinemeta.strem.io/meta/")) return handlers.cinemeta(url);
  throw new Error("unexpected network call in offline test: " + url);
};
const cinemetaSays = (moviedbId) => async () => json(200, { meta: { imdb_id: RAYA_IMDB, moviedb_id: moviedbId } });
const findSays = (movieIds, tvIds) => async () =>
  json(200, {
    movie_results: (movieIds || []).map((id) => ({ id })),
    tv_results: (tvIds || []).map((id) => ({ id })),
  });

// Fresh resolver module (its LRU cache is module state) for each case.
function freshResolver() {
  const p = require.resolve("./src/stremio/id-resolver");
  delete require.cache[p];
  return require(p).resolveTmdbId;
}

async function run() {
  console.log("\n🧪 Offline IMDb -> TMDB resolver tests\n");

  // 1. The Raya case: TMDB /find wins over Cinemeta's stale moviedb_id
  let resolve = freshResolver();
  handlers = { find: findSays([Number(RAYA_TMDB)]), cinemeta: cinemetaSays(RAYA_CINEMETA_STALE) };
  calls.length = 0;
  assert.strictEqual(await resolve(RAYA_IMDB, "movie"), RAYA_TMDB, "TMDB /find id, not Cinemeta's 508441");
  assert.strictEqual(calls.filter((u) => u.includes("cinemeta")).length, 0, "Cinemeta not asked when TMDB answers");
  console.log("✓ tt5109280 (Raya) -> 527774 from TMDB /find, not Cinemeta's stale 508441");

  // 2. Cached: a repeat lookup makes no call
  calls.length = 0;
  assert.strictEqual(await resolve(RAYA_IMDB, "movie"), RAYA_TMDB);
  assert.strictEqual(calls.length, 0, "repeat lookup served from cache");
  console.log("✓ repeat lookup served from cache");

  // 3. TMDB proxy down (HTTP 500 / network error) -> Cinemeta fallback
  for (const failure of ["http500", "throw"]) {
    resolve = freshResolver();
    handlers = {
      find: async () => {
        if (failure === "throw") throw new Error("ECONNRESET");
        return json(500, {});
      },
      cinemeta: cinemetaSays(155),
    };
    assert.strictEqual(await resolve("tt0468569", "movie"), "155", "falls back to Cinemeta on " + failure);
  }
  console.log("✓ TMDB proxy HTTP 500 / network error -> Cinemeta fallback");

  // 4. TMDB has no match -> Cinemeta fallback
  resolve = freshResolver();
  handlers = { find: findSays([], []), cinemeta: cinemetaSays(155) };
  assert.strictEqual(await resolve("tt0468569", "movie"), "155");
  console.log("✓ empty TMDB /find -> Cinemeta fallback");

  // 5. Both fail -> null, and the miss is not cached (next request asks again)
  resolve = freshResolver();
  handlers = { find: async () => json(503, {}), cinemeta: async () => json(404, {}) };
  assert.strictEqual(await resolve(RAYA_IMDB, "movie"), null);
  handlers = { find: findSays([Number(RAYA_TMDB)]), cinemeta: cinemetaSays(RAYA_CINEMETA_STALE) };
  assert.strictEqual(await resolve(RAYA_IMDB, "movie"), RAYA_TMDB, "a failed lookup is retried, not cached");
  console.log("✓ both lookups failing -> null, not cached");

  // 6. Series prefer tv_results, movies prefer movie_results; episode suffix ignored
  resolve = freshResolver();
  handlers = { find: findSays([111], [1396]), cinemeta: cinemetaSays(999) };
  assert.strictEqual(await resolve("tt0903747:1:1", "series"), "1396");
  resolve = freshResolver();
  assert.strictEqual(await resolve("tt0903747", "movie"), "111");
  console.log("✓ series -> tv_results, movie -> movie_results");

  // 7. Router: /stream/movie/tt5109280.json hands 527774 to every provider
  const got = {};
  const stub = (rel, tag) => {
    const p = require.resolve(path.join(__dirname, rel));
    const getStreams = async (tmdbId) => {
      got[tag] = tmdbId;
      return [{ name: tag, url: "https://" + tag + "/1", quality: "1080p", subtitles: [] }];
    };
    require.cache[p] = { id: p, filename: p, loaded: true, exports: { getStreams, fetchSubtitles: async () => [] } };
  };
  stub("src/movy/index.js", "movy");
  stub("src/7movies/index.js", "seven");
  stub("src/flystream/index.js", "fly");
  freshResolver(); // router requires a fresh, empty-cache resolver
  handlers = { find: findSays([Number(RAYA_TMDB)]), cinemeta: cinemetaSays(RAYA_CINEMETA_STALE) };
  const { route } = require("./src/stremio/router");
  const res = await route(`/stream/movie/${RAYA_IMDB}.json`, {}, "http://h", {});
  const body = typeof res.body === "string" ? JSON.parse(res.body) : res.body;
  assert.deepStrictEqual(got, { movy: RAYA_TMDB, seven: RAYA_TMDB, fly: RAYA_TMDB }, "all providers get 527774");
  assert.strictEqual(body.streams.length, 3, "Movy, 7Movies and FlyStream rows all returned");
  console.log("✓ router: /stream/movie/tt5109280.json -> 527774 for Movy, 7Movies and FlyStream");

  console.log("\n✅ id resolver offline tests passed\n");
}

run().catch((err) => {
  console.error("❌", err);
  process.exit(1);
});
