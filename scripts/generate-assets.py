#!/usr/bin/env python3
"""Generate Favicons, App Icons, and Open Graph (OG) Images for Direct Streams Providers.

Outputs:
  - landing/favicon.svg
  - landing/favicon-16x16.png
  - landing/favicon-32x32.png
  - landing/favicon.ico
  - landing/apple-touch-icon.png (180x180)
  - landing/icon-192.png (192x192)
  - landing/icon-512.png (512x512)
  - landing/og-image.png (1200x630, English)
  - landing/og-image-vi.png (1200x630, Vietnamese)
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parent.parent
LANDING_DIR = ROOT_DIR / "landing"

# Color Palette matching the site's CSS
BG = (10, 10, 9)            # #0a0a09
BG_CARD = (20, 19, 17)      # #141311
LINE = (42, 40, 36)         # #2a2824
INK = (242, 239, 233)       # #f2efe9
MUTED = (156, 150, 138)     # #9c968a
ACCENT = (255, 59, 0)       # #ff3b00
ACCENT_BG = (42, 16, 8)     # #2a1008
ACCENT2 = (255, 184, 0)     # #ffb800
TEAL = (45, 212, 191)       # #2dd4bf

# Font paths
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
if not os.path.exists(FONT_BOLD):
    FONT_BOLD = "/System/Library/Fonts/Helvetica.ttc"
if not os.path.exists(FONT_REGULAR):
    FONT_REGULAR = "/System/Library/Fonts/Helvetica.ttc"


def create_favicon_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#181715" />
      <stop offset="100%" stop-color="#0a0a09" />
    </linearGradient>
    <linearGradient id="playGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ff5500" />
      <stop offset="100%" stop-color="#ff3b00" />
    </linearGradient>
  </defs>
  <!-- Background Container -->
  <rect width="64" height="64" rx="16" fill="url(#bgGrad)" stroke="#2a2824" stroke-width="2" />
  
  <!-- TV / Screen Frame -->
  <rect x="12" y="16" width="40" height="30" rx="6" fill="#141311" stroke="#33302a" stroke-width="2" />
  
  <!-- Antenna -->
  <path d="M37 10 L32 16 L27 10" stroke="#ff3b00" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />
  
  <!-- Play Triangle -->
  <path d="M28 23.5 L40 31 L28 38.5 Z" fill="url(#playGrad)" />
  
  <!-- Live Indicator Dot -->
  <circle cx="47" cy="21" r="2.5" fill="#2dd4bf" />
  
  <!-- Stand -->
  <path d="M25 50 L39 50" stroke="#ffb800" stroke-width="2.5" stroke-linecap="round" />
</svg>
"""


def render_icon_image(size: int) -> Image.Image:
    """Render high-resolution icon using PIL for crisp output at any size."""
    scale = 4  # supersample for antialiasing
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Outer rounded box
    pad = int(s * 0.04)
    corner = int(s * 0.25)
    d.rounded_rectangle(
        [pad, pad, s - pad, s - pad],
        radius=corner,
        fill=BG,
        outline=LINE,
        width=max(2, int(scale * 2)),
    )

    # TV screen inner box
    tv_x1 = int(s * 0.20)
    tv_y1 = int(s * 0.26)
    tv_x2 = int(s * 0.80)
    tv_y2 = int(s * 0.72)
    tv_r = int(s * 0.10)
    d.rounded_rectangle(
        [tv_x1, tv_y1, tv_x2, tv_y2],
        radius=tv_r,
        fill=BG_CARD,
        outline=(50, 48, 42),
        width=max(2, int(scale * 1.8)),
    )

    # Antenna
    ant_w = max(2, int(scale * 2.2))
    ant_top_y = int(s * 0.15)
    ant_mid_y = int(s * 0.26)
    ant_left_x = int(s * 0.41)
    ant_mid_x = int(s * 0.50)
    ant_right_x = int(s * 0.59)
    d.line([(ant_left_x, ant_top_y), (ant_mid_x, ant_mid_y)], fill=ACCENT, width=ant_w)
    d.line([(ant_right_x, ant_top_y), (ant_mid_x, ant_mid_y)], fill=ACCENT, width=ant_w)

    # Play triangle
    p1 = (int(s * 0.44), int(s * 0.38))
    p2 = (int(s * 0.63), int(s * 0.49))
    p3 = (int(s * 0.44), int(s * 0.60))
    d.polygon([p1, p2, p3], fill=ACCENT)

    # Live pulse dot (teal)
    dot_r = max(2, int(s * 0.045))
    dot_cx = int(s * 0.74)
    dot_cy = int(s * 0.34)
    d.ellipse(
        [dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r],
        fill=TEAL,
    )

    # Stand line
    stand_y = int(s * 0.81)
    d.line(
        [(int(s * 0.38), stand_y), (int(s * 0.62), stand_y)],
        fill=ACCENT2,
        width=max(2, int(scale * 2.2)),
    )

    # Downsample with Lanczos for smooth antialiasing
    return img.resize((size, size), Image.Resampling.LANCZOS)


def generate_og_image(lang: str = "en") -> Image.Image:
    """Generate high-impact 1200x630 Open Graph card matching modern dark mode aesthetic."""
    w, h = 1200, 630
    img = Image.new("RGBA", (w, h), BG)
    d = ImageDraw.Draw(img)

    # Outer border
    d.rectangle([0, 0, w - 1, h - 1], outline=LINE, width=2)
    # Subtle inner margin border
    d.rectangle([20, 20, w - 21, h - 21], outline=(25, 24, 22), width=1)

    # Subtle top accent glow bar (orange line at the top)
    d.rectangle([22, 22, w - 23, 26], fill=ACCENT)

    # Fonts
    f_kicker = ImageFont.truetype(FONT_BOLD, 14)
    f_title_big = ImageFont.truetype(FONT_BOLD, 68)
    f_sub = ImageFont.truetype(FONT_REGULAR, 22)
    f_code = ImageFont.truetype(FONT_BOLD, 15)
    f_card_title = ImageFont.truetype(FONT_BOLD, 22)
    f_card_sub = ImageFont.truetype(FONT_BOLD, 14)
    f_meta = ImageFont.truetype(FONT_REGULAR, 13)
    f_domain = ImageFont.truetype(FONT_BOLD, 16)

    # --- Header Row ---
    # Left: Brand pill
    brand_text = "DIRECT—STREAMS."
    brand_w = int(d.textlength(brand_text, font=f_code))
    pill_x, pill_y = 60, 56
    pill_pad_x, pill_pad_y = 18, 10
    d.rounded_rectangle(
        [pill_x, pill_y, pill_x + brand_w + pill_pad_x * 2, pill_y + 36],
        radius=18,
        fill=BG_CARD,
        outline=LINE,
        width=1,
    )
    # Draw brand with orange dot
    d.text((pill_x + pill_pad_x, pill_y + pill_pad_y), "DIRECT—STREAMS", font=f_code, fill=INK)
    dot_offset = int(d.textlength("DIRECT—STREAMS", font=f_code))
    d.text((pill_x + pill_pad_x + dot_offset, pill_y + pill_pad_y), ".", font=f_code, fill=ACCENT)

    # Right: Badges
    badges = ["NUVIO", "WUPLAY", "STREMIO"]
    bx = w - 60
    for b in reversed(badges):
        bw = int(d.textlength(b, font=f_kicker)) + 24
        bx -= bw
        d.rounded_rectangle(
            [bx, pill_y, bx + bw, pill_y + 36],
            radius=18,
            fill=(18, 17, 15),
            outline=LINE,
            width=1,
        )
        d.text((bx + 12, pill_y + 11), b, font=f_kicker, fill=MUTED)
        bx -= 8

    # --- Center Left: Hero Statement ---
    if lang == "vi":
        line1 = "CHỌN PHIM."
        line2_part1 = "TỰ "
        line2_acc = "BẮT"
        line2_part2 = " LINK."
        line3 = "TV CHIẾU NGAY."
        sub_text = (
            "Trình bắt link MP4 & 4K HLS trực tiếp cho Nuvio, WuPlay, Stremio.\n"
            "Không cần tài khoản · Tự đính kèm header vượt lỗi 428 · Sẵn phụ đề."
        )
    else:
        line1 = "YOU PICK."
        line2_part1 = "IT "
        line2_acc = "FINDS"
        line2_part2 = " IT."
        line3 = "TV PLAYS."
        sub_text = (
            "Tiny scrapers turning title taps into direct MP4 / 4K HLS streams.\n"
            "0 provider accounts · okhttp header forwarding · Subtitles included."
        )

    text_x = 60
    text_y = 145

    # Line 1
    d.text((text_x, text_y), line1, font=f_title_big, fill=INK)
    text_y += 76

    # Line 2 with accent highlight
    w_p1 = int(d.textlength(line2_part1, font=f_title_big))
    w_acc = int(d.textlength(line2_acc, font=f_title_big))
    d.text((text_x, text_y), line2_part1, font=f_title_big, fill=INK)
    d.text((text_x + w_p1, text_y), line2_acc, font=f_title_big, fill=ACCENT)
    d.text((text_x + w_p1 + w_acc, text_y), line2_part2, font=f_title_big, fill=INK)
    text_y += 76

    # Line 3
    d.text((text_x, text_y), line3, font=f_title_big, fill=INK)
    text_y += 90

    # Subtitle paragraphs
    d.text((text_x, text_y), sub_text, font=f_sub, fill=MUTED, spacing=8)

    # --- Center Right: Interactive TV Modal Mockup ---
    mock_w, mock_h = 420, 270
    mock_x = w - mock_w - 60
    mock_y = 160

    # Modal container
    d.rounded_rectangle(
        [mock_x, mock_y, mock_x + mock_w, mock_y + mock_h],
        radius=18,
        fill=(8, 8, 7),
        outline=LINE,
        width=1,
    )

    # Modal Header
    d.rectangle([mock_x, mock_y + 44, mock_x + mock_w, mock_y + 45], fill=(30, 28, 25))
    # Teal dot
    d.ellipse([mock_x + 18, mock_y + 19, mock_x + 26, mock_y + 27], fill=TEAL)
    d.text((mock_x + 34, mock_y + 16), "NUVIO TV — NOW RESOLVING", font=f_card_sub, fill=MUTED)
    d.text((mock_x + mock_w - 110, mock_y + 16), "TMDB 872585", font=f_card_sub, fill=INK)

    # Movie Title
    d.text((mock_x + 18, mock_y + 60), "Oppenheimer", font=f_card_title, fill=INK)
    d.text((mock_x + 18 + int(d.textlength("Oppenheimer", font=f_card_title)) + 8, mock_y + 64), "— 4K", font=f_card_sub, fill=ACCENT2)

    # Stream Row 1 (Hot / 4K)
    r1_y = mock_y + 104
    d.rounded_rectangle(
        [mock_x + 18, r1_y, mock_x + mock_w - 18, r1_y + 44],
        radius=10,
        fill=ACCENT_BG,
        outline=ACCENT,
        width=1,
    )
    d.text((mock_x + 30, r1_y + 13), "Movy · 2160p 4K HLS", font=f_card_sub, fill=INK)
    badge1 = "11 PHỤ ĐỀ · XEM ▶" if lang == "vi" else "SUBS 11 · PLAY ▶"
    d.text((mock_x + mock_w - 30 - int(d.textlength(badge1, font=f_card_sub)), r1_y + 13), badge1, font=f_card_sub, fill=ACCENT2)

    # Stream Row 2 (1080p MP4)
    r2_y = mock_y + 158
    d.rounded_rectangle(
        [mock_x + 18, r2_y, mock_x + mock_w - 18, r2_y + 40],
        radius=10,
        fill=(18, 17, 15),
        outline=LINE,
        width=1,
    )
    d.text((mock_x + 30, r2_y + 12), "7Movies · 1080p MP4", font=f_card_sub, fill=MUTED)
    badge2 = "8 PHỤ ĐỀ" if lang == "vi" else "SUBS 8"
    d.text((mock_x + mock_w - 30 - int(d.textlength(badge2, font=f_card_sub)), r2_y + 12), badge2, font=f_card_sub, fill=MUTED)

    # Progress Packet bar
    bar_y = mock_y + 214
    d.rounded_rectangle([mock_x + 18, bar_y, mock_x + mock_w - 18, bar_y + 4], radius=2, fill=(30, 28, 25))
    d.rounded_rectangle([mock_x + 18, bar_y, mock_x + int(mock_w * 0.45), bar_y + 4], radius=2, fill=ACCENT)

    # Status meta
    meta_text = "CDN 206 Partial Content · okhttp/4.12.0 · 0 buffer stalls"
    d.text((mock_x + 18, mock_y + 232), meta_text, font=f_meta, fill=(110, 105, 95))

    # --- Bottom Footer Bar ---
    foot_y = h - 68
    d.line([(50, foot_y - 14), (w - 50, foot_y - 14)], fill=LINE, width=1)

    # Feature tags
    if lang == "vi":
        features = ["4K HLS", "MP4 TRỰC TIẾP", "GIẢI MÃ PHẦN CỨNG", "KHÔNG CẦN SERVER"]
    else:
        features = ["4K HLS", "DIRECT MP4", "HARDWARE DECODE", "ZERO ACCOUNT"]

    tag_x = 60
    for feat in features:
        fw = int(d.textlength(feat, font=f_kicker)) + 22
        d.rounded_rectangle(
            [tag_x, foot_y, tag_x + fw, foot_y + 30],
            radius=6,
            fill=(18, 17, 15),
            outline=LINE,
            width=1,
        )
        d.text((tag_x + 11, foot_y + 8), feat, font=f_kicker, fill=MUTED)
        tag_x += fw + 8

    # Domain
    domain_str = "direct-streams-providers.vercel.app"
    dom_w = int(d.textlength(domain_str, font=f_domain))
    d.text((w - 60 - dom_w, foot_y + 6), domain_str, font=f_domain, fill=INK)

    return img


def main() -> None:
    LANDING_DIR.mkdir(parents=True, exist_ok=True)
    print("🎨 Generating Direct Streams Providers assets into:", LANDING_DIR)

    # 1. Favicon SVG
    svg_path = LANDING_DIR / "favicon.svg"
    svg_content = create_favicon_svg()
    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"  ✓ {svg_path.name}")

    # 2. Raster Icons
    sizes = [
        ("favicon-16x16.png", 16),
        ("favicon-32x32.png", 32),
        ("apple-touch-icon.png", 180),
        ("icon-192.png", 192),
        ("icon-512.png", 512),
    ]
    ico_frames: list[Image.Image] = []

    for name, sz in sizes:
        icon_img = render_icon_image(sz)
        out_file = LANDING_DIR / name
        icon_img.save(out_file, format="PNG", optimize=True)
        print(f"  ✓ {name} ({sz}x{sz})")
        if sz in (16, 32, 48):
            ico_frames.append(icon_img)

    # Favicon ICO
    ico_img_48 = render_icon_image(48)
    ico_frames.append(ico_img_48)
    ico_path = LANDING_DIR / "favicon.ico"
    # PIL can save multi-frame .ico
    render_icon_image(32).save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
    )
    print(f"  ✓ favicon.ico (multi-res 16, 32, 48)")

    # 3. Open Graph Images
    og_en = generate_og_image(lang="en")
    og_en_path = LANDING_DIR / "og-image.png"
    og_en.save(og_en_path, format="PNG", optimize=True)
    print(f"  ✓ {og_en_path.name} (1200x630)")

    og_vi = generate_og_image(lang="vi")
    og_vi_path = LANDING_DIR / "og-image-vi.png"
    og_vi.save(og_vi_path, format="PNG", optimize=True)
    print(f"  ✓ {og_vi_path.name} (1200x630)")

    print("✨ All assets generated successfully!")


if __name__ == "__main__":
    main()
