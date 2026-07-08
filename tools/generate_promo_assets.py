#!/usr/bin/env python3
"""Generate SVG and PNG promo assets for zuiti-skill."""

from pathlib import Path
import math
import shutil
import subprocess
import tempfile
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT_BOLD = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_REGULAR = "/System/Library/Fonts/STHeiti Light.ttc"
FONT_SONG = "/System/Library/Fonts/Supplemental/Songti.ttc"
FONT_MONO = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
INK = "#1f1c19"
MUTED = "#6f655a"
RED = "#b9472f"
PAPER = "#f8f0e3"
PANEL = "#fff8eb"
LINE = "#d8c8b2"


def tspan_lines(lines, x, y, size, weight=400, fill="#1f1c19", line_height=1.42):
    spans = []
    dy = 0
    for line in lines:
        spans.append(
            f'<tspan x="{x}" dy="{dy}">{escape(line)}</tspan>'
        )
        dy = round(size * line_height, 1)
    return (
        f'<text x="{x}" y="{y}" font-family="Inter, PingFang SC, '
        f'Microsoft YaHei, Arial, sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}">' + "".join(spans) + "</text>"
    )


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def font(size, weight="regular"):
    path = FONT_BOLD if weight == "bold" else FONT_REGULAR
    return ImageFont.truetype(path, size)


def song_font(size, weight="regular"):
    path = FONT_BOLD if weight == "bold" else FONT_SONG
    return ImageFont.truetype(path, size)


def draw_paper(draw, width, height):
    draw.rectangle((0, 0, width, height), fill=PAPER)
    for x in range(-height, width, 34):
        draw.line((x, height, x + height, 0), fill="#eadfce", width=1)


def text_width(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


def wrap(draw, text, fnt, max_width):
    lines = []
    current = ""
    for char in text:
        trial = current + char
        if current and text_width(draw, trial, fnt) > max_width:
            lines.append(current)
            current = char
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def draw_multiline(draw, xy, lines, fnt, fill=INK, line_gap=12):
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def rounded(draw, box, radius=24, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def save_png(path, image):
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def ease(t):
    t = max(0, min(1, t))
    return 1 - (1 - t) ** 3


def lerp(a, b, t):
    return a + (b - a) * ease(t)


def fade_color(hex_color, alpha, bg="#fffaf0"):
    def rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

    fg = rgb(hex_color)
    base = rgb(bg)
    return tuple(int(base[i] * (1 - alpha) + fg[i] * alpha) for i in range(3))


def alpha_paste(base, overlay, xy):
    if overlay.mode != "RGBA":
        overlay = overlay.convert("RGBA")
    base.paste(overlay, xy, overlay)


def draw_card(draw, box, title, lines, accent=RED, fill=PANEL, title_size=22, body_size=28):
    rounded(draw, box, 20, fill=fill, outline="#ddcfba", width=1)
    x1, y1, x2, _ = box
    draw.text((x1 + 28, y1 + 24), title, font=font(title_size, "bold"), fill=accent)
    y = y1 + 66
    for line in lines:
        draw.text((x1 + 28, y), line, font=font(body_size, "bold"), fill=INK)
        y += body_size + 12


def animated_hero():
    width, height = 960, 540
    scale = 2
    fps = 16
    frame_count = 112
    frames = []

    def sc(v):
        return int(round(v * scale))

    def box(values):
        return tuple(sc(v) for v in values)

    def fnt(size, weight="regular"):
        return font(sc(size), weight)

    def mono(size):
        return ImageFont.truetype(FONT_MONO, sc(size))

    def draw_text(layer, xy, text, size, fill=INK, weight="regular", alpha=1, mono_font=False):
        draw = ImageDraw.Draw(layer)
        color = Image.new("RGBA", (1, 1), fill).getpixel((0, 0))
        color = (*color[:3], int(255 * alpha))
        draw.text((sc(xy[0]), sc(xy[1])), text, font=mono(size) if mono_font else fnt(size, weight), fill=color)

    def draw_round(layer, values, radius, fill, outline=None, width_px=1, alpha=1):
        draw = ImageDraw.Draw(layer)
        fill_rgba = None
        outline_rgba = None
        if fill:
            c = Image.new("RGBA", (1, 1), fill).getpixel((0, 0))
            fill_rgba = (*c[:3], int(255 * alpha))
        if outline:
            c = Image.new("RGBA", (1, 1), outline).getpixel((0, 0))
            outline_rgba = (*c[:3], int(255 * alpha))
        draw.rounded_rectangle(box(values), radius=sc(radius), fill=fill_rgba, outline=outline_rgba, width=sc(width_px))

    def draw_line(layer, values, fill, width_px=1, alpha=1):
        draw = ImageDraw.Draw(layer)
        c = Image.new("RGBA", (1, 1), fill).getpixel((0, 0))
        draw.line(box(values), fill=(*c[:3], int(255 * alpha)), width=sc(width_px))

    def draw_corner_marks(layer, alpha):
        marks = [
            ((72, 64, 94, 64), (72, 64, 72, 86)),
            ((866, 64, 888, 64), (888, 64, 888, 86)),
            ((72, 476, 94, 476), (72, 454, 72, 476)),
            ((866, 476, 888, 476), (888, 454, 888, 476)),
        ]
        for a, b in marks:
            draw_line(layer, a, RED, 1.4, alpha)
            draw_line(layer, b, RED, 1.4, alpha)

    def draw_apparatus(layer, cx, top, alpha, frame_index):
        draw = ImageDraw.Draw(layer)
        line = (126, 118, 104, int(210 * alpha))
        red = (185, 71, 47, int(255 * alpha))
        cream = (246, 239, 226, int(210 * alpha))
        w = sc(2.1)
        pts = [(cx - 72, top), (cx + 72, top), (cx + 28, top + 82), (cx - 28, top + 82)]
        pts = [(sc(x), sc(y)) for x, y in pts]
        draw.line(pts + [pts[0]], fill=line, width=w, joint="curve")
        draw.line(box((cx - 28, top + 82, cx - 18, top + 126)), fill=line, width=w)
        draw.line(box((cx + 28, top + 82, cx + 18, top + 126)), fill=line, width=w)
        draw.line(box((cx - 18, top + 126, cx + 18, top + 126)), fill=line, width=w)
        draw.text((sc(cx - 44), sc(top + 58)), "DISTILL", font=mono(14), fill=red)
        draw.text((sc(cx - 18), sc(top + 76)), "翻译", font=fnt(12, "bold"), fill=cream)
        for j, (dy, span) in enumerate([(136, 92), (160, 78), (184, 62)]):
            draw.arc(box((cx - span / 2, top + dy, cx + span / 2, top + dy + 34)), 8, 352, fill=line, width=w)
        draw.ellipse(box((cx - 52, top + 216, cx + 52, top + 320)), outline=line, width=w)
        draw.line(box((cx - 34, top + 268, cx + 34, top + 268)), fill=(214, 108, 86, int(150 * alpha)), width=sc(1.5))
        draw.line(box((cx - 48, top + 336, cx + 48, top + 336)), fill=line, width=w)
        pulse = 4 + 3 * math.sin(frame_index * 0.38)
        draw.ellipse(box((cx - pulse, top + 118 - pulse, cx + pulse, top + 118 + pulse)), fill=red)

    def draw_input(layer, x, y, alpha):
        draw_round(layer, (x, y, x + 336, y + 126), 18, PANEL, "#ddcfba", alpha=alpha)
        draw_text(layer, (x + 24, y + 20), "朋友发来", 15, RED, "bold", alpha)
        draw_text(layer, (x + 24, y + 50), "最近手头是不是宽裕点了？", 18, INK, "bold", alpha)
        draw_text(layer, (x + 24, y + 80), "上次那个事儿……你懂的哈，", 18, INK, "bold", alpha)
        draw_text(layer, (x + 24, y + 108), "不急不急。", 18, INK, "bold", alpha)

    def draw_translation(layer, alpha):
        draw_round(layer, (628, 112, 878, 260), 22, "#17130f", None, alpha=alpha)
        draw_text(layer, (656, 138), "嘴替翻译", 15, "#f05b3c", "bold", alpha)
        draw_text(layer, (656, 174), "他欠你钱，", 24, "#fff6e8", "bold", alpha)
        draw_text(layer, (656, 211), "却把主动权拿走。", 24, "#fff6e8", "bold", alpha)

    def draw_reply(layer, idx, title, body, alpha):
        y = 284 + idx * 58 - (1 - ease(alpha)) * 12
        draw_round(layer, (626, y + 4, 884, y + 50), 14, "#e2d4c0", None, alpha=0.28 * alpha)
        draw_round(layer, (620, y, 878, y + 46), 14, PANEL, "#ddcfba", alpha=alpha)
        draw_text(layer, (638, y + 12), title, 15, RED, "bold", alpha)
        draw_text(layer, (716, y + 12), body, 15, INK, "bold", alpha)

    def draw_droplet(layer, progress, alpha):
        if progress <= 0:
            return
        cx = 482
        if progress < 0.28:
            x = cx
            y = 154 + progress / 0.28 * 88
        elif progress < 0.72:
            p = (progress - 0.28) / 0.44
            x = cx + math.sin(p * math.pi * 5) * (42 * (1 - p * 0.28))
            y = 242 + p * 124
        else:
            p = (progress - 0.72) / 0.28
            x = cx
            y = 366 + p * 42
        draw = ImageDraw.Draw(layer)
        glow = int(80 * alpha)
        draw.ellipse(box((x - 15, y - 15, x + 15, y + 15)), fill=(185, 71, 47, glow))
        draw.ellipse(box((x - 5.5, y - 5.5, x + 5.5, y + 5.5)), fill=(185, 71, 47, int(255 * alpha)))

    for i in range(frame_count):
        t = i / (frame_count - 1)
        base = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
        bd = ImageDraw.Draw(base)
        bd.rectangle((0, 0, width * scale, height * scale), fill=PAPER)
        for x in range(-height * scale, width * scale, sc(26)):
            bd.line((x, height * scale, x + height * scale, 0), fill="#eadfce", width=1)
        bd.rounded_rectangle(box((34, 30, 926, 510)), radius=sc(26), fill="#fffaf0", outline=LINE, width=sc(1))

        static = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw_corner_marks(static, ease(t / 0.12))
        draw_text(static, (66, 58), "ZUITI.SKILL  |  MESSAGE DISTILLER", 12, "#9a8878", "bold", 1)
        draw_line(static, (66, 82, 132, 82), RED, 3, 1)
        draw_text(static, (66, 118), "朋友欠钱不还", 38, INK, "bold")
        draw_text(static, (66, 166), "还反过来试探你", 38, RED, "bold")
        draw_text(static, (66, 222), "别吵，先把账拉回明面上。", 19, MUTED, "regular")
        base.alpha_composite(static)

        apparatus_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw_apparatus(apparatus_layer, 482, 106, 0.26 + 0.74 * ease((t - 0.03) / 0.18), i)
        base.alpha_composite(apparatus_layer)

        input_alpha = ease((t - 0.10) / 0.14)
        input_x = lerp(-330, 66, (t - 0.08) / 0.18)
        input_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw_input(input_layer, input_x, 292, input_alpha)
        base.alpha_composite(input_layer)

        # Process labels around the line-art device.
        labels = [
            (0.30, "欠账反转", 344, 170),
            (0.42, "不急话术", 372, 300),
            (0.54, "定个时间", 510, 360),
        ]
        label_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        for start, text, x, y in labels:
            a = ease((t - start) / 0.12)
            if a > 0:
                draw_text(label_layer, (x, y), text, 14, RED, "bold", a)
        base.alpha_composite(label_layer)

        drop_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw_droplet(drop_layer, ease((t - 0.24) / 0.36), ease((t - 0.20) / 0.12))
        base.alpha_composite(drop_layer)

        trans_alpha = ease((t - 0.42) / 0.14)
        trans_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        if trans_alpha > 0:
            draw_translation(trans_layer, trans_alpha)
        base.alpha_composite(trans_layer)

        replies = [
            ("体面版", "方便时安排一下。"),
            ("绵里藏针", "这个月定个时间？"),
            ("掀桌版", "账还是得算明白。"),
        ]
        reply_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        for idx, (title, body) in enumerate(replies):
            a = ease((t - 0.56 - idx * 0.06) / 0.10)
            if a > 0:
                draw_reply(reply_layer, idx, title, body, a)
        base.alpha_composite(reply_layer)

        end_alpha = ease((t - 0.78) / 0.12)
        footer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw_text(footer, (104, 462), "推荐：绵里藏针版，把钱拉回明面上，也给对方留台阶", 17, MUTED, "bold", end_alpha)
        draw_text(footer, (628, 463), "npx skills add SilentFleetKK/zuiti-skill", 12, INK, "regular", end_alpha, mono_font=True)
        base.alpha_composite(footer)

        low = base.resize((width, height), Image.Resampling.LANCZOS).convert("RGB")
        frames.append(low)

    out = ROOT / "assets" / "hero.gif"
    out.parent.mkdir(parents=True, exist_ok=True)

    if shutil.which("ffmpeg"):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for idx, frame in enumerate(frames):
                frame.save(tmp_path / f"frame-{idx:04d}.png")
            palette = tmp_path / "palette.png"
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-framerate",
                    str(fps),
                    "-i",
                    str(tmp_path / "frame-%04d.png"),
                    "-vf",
                    "palettegen=max_colors=128:stats_mode=diff",
                    str(palette),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-framerate",
                    str(fps),
                    "-i",
                    str(tmp_path / "frame-%04d.png"),
                    "-i",
                    str(palette),
                    "-lavfi",
                    "paletteuse=dither=bayer:bayer_scale=3",
                    "-loop",
                    "0",
                    str(out),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-framerate",
                    str(fps),
                    "-i",
                    str(tmp_path / "frame-%04d.png"),
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    str(ROOT / "assets" / "hero.mp4"),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    else:
        gif_frames = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=128) for f in frames]
        gif_frames[0].save(
            out,
            save_all=True,
            append_images=gif_frames[1:],
            duration=int(1000 / fps),
            loop=0,
            optimize=True,
            disposal=2,
        )


def banner():
    content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1520" height="620" viewBox="0 0 1520 620">
  <defs>
    <pattern id="paper" width="26" height="26" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">
      <line x1="0" y1="0" x2="0" y2="26" stroke="#eadfce" stroke-width="1" opacity="0.45"/>
    </pattern>
    <filter id="softShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="#2b2118" flood-opacity="0.12"/>
    </filter>
  </defs>
  <rect width="1520" height="620" fill="#f6efe2"/>
  <rect width="1520" height="620" fill="url(#paper)" opacity="0.8"/>
  <rect x="70" y="62" width="1380" height="496" rx="34" fill="#fffaf0" stroke="#d9cbb7" filter="url(#softShadow)"/>
  <text x="126" y="128" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="22" font-weight="700" letter-spacing="5" fill="#b9472f">ZUITI.SKILL</text>
  <line x1="126" y1="152" x2="236" y2="152" stroke="#b9472f" stroke-width="6"/>
  <text x="126" y="245" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="72" font-weight="800" fill="#1f1c19">把阴阳怪气翻译成人话</text>
  <text x="126" y="335" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="72" font-weight="800" fill="#1f1c19">把憋屈回复成<tspan fill="#b9472f">体面</tspan></text>
  <text x="130" y="418" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="30" fill="#6f655a">潜台词翻译 + 误读风险 + 三档回复 + 发送建议</text>
  <g transform="translate(980 160)">
    <rect x="0" y="0" width="350" height="235" rx="24" fill="#17130f"/>
    <text x="34" y="58" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="20" fill="#d6c6ad">难回消息</text>
    <text x="34" y="112" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="30" font-weight="700" fill="#fff6e8">“不急不急”</text>
    <text x="34" y="172" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="24" fill="#f05b3c">→ 把欠账定成有期限的事</text>
  </g>
  <text x="126" y="510" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="24" font-weight="700" fill="#1f1c19">npx skills add SilentFleetKK/zuiti-skill</text>
</svg>
'''
    write(ROOT / "assets" / "banner.svg", content)


def banner_png():
    width, height = 1520, 620
    img = Image.new("RGB", (width, height), PAPER)
    d = ImageDraw.Draw(img)
    draw_paper(d, width, height)
    rounded(d, (70, 62, 1450, 558), 34, fill="#fffaf0", outline=LINE, width=2)
    d.text((126, 108), "ZUITI.SKILL", font=font(30, "bold"), fill=RED)
    d.line((126, 164, 236, 164), fill=RED, width=7)
    d.text((126, 230), "把阴阳怪气翻译成人话", font=font(76, "bold"), fill=INK)
    d.text((126, 323), "把憋屈回复成", font=font(76, "bold"), fill=INK)
    d.text((660, 323), "体面", font=font(76, "bold"), fill=RED)
    d.text((130, 430), "潜台词翻译 + 误读风险 + 三档回复 + 发送建议", font=font(32), fill=MUTED)
    rounded(d, (990, 160, 1348, 402), 28, fill="#17130f")
    d.text((1026, 210), "难回消息", font=font(23, "bold"), fill="#d6c6ad")
    d.text((1026, 275), "“不急不急”", font=font(34, "bold"), fill="#fff6e8")
    d.text((1026, 338), "→ 把欠账定成有期限的事", font=font(24, "bold"), fill="#f05b3c")
    d.text((126, 515), "npx skills add SilentFleetKK/zuiti-skill", font=ImageFont.truetype(FONT_MONO, 26), fill=INK)
    save_png(ROOT / "assets" / "banner.png", img)


def hero_poster_png():
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), PAPER)
    d = ImageDraw.Draw(img)
    draw_paper(d, width, height)
    rounded(d, (56, 50, 1544, 850), 36, fill="#fffaf0", outline=LINE, width=2)

    d.text((105, 108), "嘴替.skill", font=font(42, "bold"), fill=INK)
    d.text((105, 168), "朋友欠钱不还", font=font(68, "bold"), fill=INK)
    d.text((105, 254), "还反过来试探你", font=font(68, "bold"), fill=RED)
    d.text((108, 355), "先把“不急不急”翻译清楚。", font=font(36, "bold"), fill=INK)
    d.text((108, 410), "不吵、不翻旧账，把欠账变成有期限的事。", font=font(28), fill=MUTED)

    steps = [
        ("01", "潜台词翻译", "看清对方在施压、试探、甩锅，还是只是焦虑。"),
        ("02", "误读风险", "爽感之外加刹车，避免把普通消息解读成敌意。"),
        ("03", "三档回复", "体面 / 绵里藏针 / 掀桌，每档都能直接复制。"),
        ("04", "发送建议", "告诉你当前更适合发哪档，以及为什么。"),
    ]
    y = 485
    for no, title, desc in steps:
        rounded(d, (105, y, 725, y + 62), 16, fill=PANEL, outline="#e2d4c0", width=1)
        d.text((130, y + 17), no, font=font(22, "bold"), fill=RED)
        d.text((190, y + 14), title, font=font(28, "bold"), fill=INK)
        d.text((365, y + 18), desc, font=font(19), fill=MUTED)
        y += 76

    rounded(d, (835, 125, 1450, 755), 32, fill="#17130f")
    d.text((885, 178), "朋友发来", font=font(25, "bold"), fill="#d6c6ad")
    rounded(d, (885, 220, 1398, 350), 22, fill="#fff8eb")
    d.text((920, 246), "最近手头是不是宽裕点了？", font=font(27, "bold"), fill=INK)
    d.text((920, 288), "上次那个事儿……你懂的哈，", font=font(27, "bold"), fill=INK)
    d.text((920, 326), "不急不急。", font=font(27, "bold"), fill=INK)
    d.text((885, 390), "嘴替翻译", font=font(25, "bold"), fill="#f05b3c")
    d.text((885, 438), "他欠你钱，", font=font(36, "bold"), fill="#fff6e8")
    d.text((885, 486), "却把主动权拿走。", font=font(36, "bold"), fill="#fff6e8")
    rounded(d, (885, 565, 1398, 675), 22, fill="#fff8eb")
    d.text((920, 592), "说到那个事儿，我也一直记着呢。", font=font(26, "bold"), fill=INK)
    d.text((920, 634), "你看这个月方便定个时间不？", font=font(26, "bold"), fill=INK)
    d.text((105, 805), "npx skills add SilentFleetKK/zuiti-skill", font=ImageFont.truetype(FONT_MONO, 28), fill=INK)
    save_png(ROOT / "assets" / "hero-poster.png", img)


CARDS = [
    {
        "slug": "boss-weekend",
        "scene": "老板周末派活",
        "message": ["在吗？PPT 周末帮我优化优化。", "不用太精细，你效率高，半天就搞定。"],
        "translation": ["“半天就搞定”不是体谅，", "是把你的周末先定价成小事。"],
        "reply": ["好的领导。不过“半天搞定”我不敢打包票。", "给大老板看的东西，我不想按“不用太精细”的标准来。", "我周末排一下，时间先记成调休哈。"],
        "tag": "绵里藏针版",
    },
    {
        "slug": "aunt-marriage",
        "scene": "亲戚催婚",
        "message": ["你看你表妹孩子都两个了，", "你到底怎么想的？眼光别太高。"],
        "translation": ["她把你的人生节奏，", "说成了需要向她交代的问题。"],
        "reply": ["谢谢三姨惦记。表妹幸福我也替她高兴。", "我这边也挺好的，眼光不是高，", "是想找个真合适的，这事急不来。"],
        "tag": "绵里藏针版",
    },
    {
        "slug": "client-v1",
        "scene": "甲方改回第一版",
        "message": ["还是觉得第一版顺眼，改回第一版吧。", "尽快哈，上线时间不变。"],
        "translation": ["他们内部反复试错，", "却默认从你的工期里扣成本。"],
        "reply": ["可以改回第一版，但先说清楚两件事：", "五轮修改工时需要重新确认；", "这次锁版后，后续修改按新需求走。"],
        "tag": "掀桌版",
    },
    {
        "slug": "friend-money",
        "scene": "朋友借钱不还",
        "message": ["最近手头是不是宽裕点了？", "上次那个事儿……你懂的哈，不急不急。"],
        "translation": ["他欠你钱，却暗示", "“你宽裕，就别催我”。"],
        "reply": ["我这边紧紧巴巴的哈～那事儿我也记着呢。", "这个月方便不？分次也行，", "咱把它了了，彼此都轻松。"],
        "tag": "绵里藏针版",
    },
    {
        "slug": "ex-midnight",
        "scene": "前任深夜试探",
        "message": ["睡了吗？突然有点想你，", "最近还好吗。"],
        "translation": ["深夜 + 想你，是在试探", "你这里还有没有情绪缺口。"],
        "reply": ["挺好的，谢谢关心。", "夜深了早点休息，你也照顾好自己。"],
        "tag": "体面版",
    },
]


def card_svg(card):
    message = tspan_lines(card["message"], 78, 205, 36, 500, "#6a6158", 1.55)
    translation = tspan_lines(card["translation"], 78, 380, 52, 800, "#1f1c19", 1.34)
    reply = tspan_lines(card["reply"], 104, 655, 34, 500, "#2a2520", 1.5)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">
  <defs>
    <pattern id="paper" width="24" height="24" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">
      <line x1="0" y1="0" x2="0" y2="24" stroke="#eadfce" stroke-width="1" opacity="0.45"/>
    </pattern>
  </defs>
  <rect width="1080" height="1080" fill="#f8f0e3"/>
  <rect width="1080" height="1080" fill="url(#paper)" opacity="0.8"/>
  <rect x="38" y="38" width="1004" height="1004" fill="none" stroke="#d8c8b2" stroke-width="2"/>
  <line x1="86" y1="105" x2="155" y2="105" stroke="#b9472f" stroke-width="6"/>
  <text x="178" y="117" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="26" font-weight="800" letter-spacing="4" fill="#1f1c19">ZUITI · {escape(card["scene"])}</text>
  <text x="78" y="174" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="22" font-weight="700" fill="#b9472f">对方发来</text>
  {message}
  <text x="78" y="340" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="22" font-weight="700" fill="#b9472f">潜台词翻译</text>
  {translation}
  <rect x="78" y="578" width="924" height="262" rx="20" fill="#fff8eb" stroke="#ddcfba"/>
  <text x="104" y="625" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="24" font-weight="800" fill="#b9472f">{escape(card["tag"])}</text>
  {reply}
  <line x1="78" y1="902" x2="1002" y2="902" stroke="#d8c8b2" stroke-width="2"/>
  <text x="78" y="955" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="30" font-weight="800" fill="#1f1c19">嘴替.skill</text>
  <text x="575" y="955" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="24" font-weight="600" fill="#6f655a">npx skills add SilentFleetKK/zuiti-skill</text>
  <text x="78" y="1000" font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" font-size="20" fill="#8b8073">把阴阳怪气翻译成人话，把憋屈回复成体面。</text>
</svg>
'''


def card_png(card):
    width = height = 1080
    img = Image.new("RGB", (width, height), PAPER)
    d = ImageDraw.Draw(img)
    draw_paper(d, width, height)
    d.rectangle((38, 38, 1042, 1042), outline=LINE, width=2)
    d.line((86, 105, 155, 105), fill=RED, width=6)
    d.text((178, 90), f"ZUITI · {card['scene']}", font=font(30, "bold"), fill=INK)

    d.text((78, 164), "对方发来", font=font(24, "bold"), fill=RED)
    y = 198
    for line in card["message"]:
        d.text((78, y), line, font=font(39, "bold"), fill=MUTED)
        y += 58

    d.text((78, 340), "潜台词翻译", font=font(24, "bold"), fill=RED)
    y = 375
    for line in card["translation"]:
        d.text((78, y), line, font=font(55, "bold"), fill=INK)
        y += 76

    rounded(d, (78, 578, 1002, 840), 20, fill=PANEL, outline="#ddcfba", width=1)
    d.text((104, 622), card["tag"], font=font(26, "bold"), fill=RED)
    y = 674
    for line in card["reply"]:
        d.text((104, y), line, font=font(35, "bold"), fill=INK)
        y += 50

    d.line((78, 902, 1002, 902), fill=LINE, width=2)
    d.text((78, 930), "嘴替.skill", font=font(34, "bold"), fill=INK)
    d.text((575, 937), "npx skills add SilentFleetKK/zuiti-skill", font=ImageFont.truetype(FONT_MONO, 23), fill=MUTED)
    d.text((78, 987), "把阴阳怪气翻译成人话，把憋屈回复成体面。", font=font(23), fill="#8b8073")
    save_png(ROOT / "promo" / "cards" / f"{card['slug']}.png", img)


def cards():
    for item in CARDS:
        write(ROOT / "promo" / "cards" / f"{item['slug']}.svg", card_svg(item))
        card_png(item)


def promo_readme():
    rows = "\n".join(
        f"| {card['scene']} | `cards/{card['slug']}.png` / `cards/{card['slug']}.svg` | {card['tag']} |"
        for card in CARDS
    )
    content = f"""# Promo Assets

首批传播素材，围绕最容易被截图转发的五类难回消息。

| 场景 | 文件 | 主推档位 |
|---|---|---|
{rows}

这些卡片的结构固定为：对方发来 -> 潜台词翻译 -> 推荐回复 -> 安装命令。README 默认使用 PNG，保证 GitHub 首页稳定显示；SVG 保留给后续二次编辑。后续新增案例时，优先复用 `tools/generate_promo_assets.py` 生成，保持视觉一致。
"""
    write(ROOT / "promo" / "README.md", content)


def main():
    animated_hero()
    banner()
    banner_png()
    hero_poster_png()
    cards()
    promo_readme()


if __name__ == "__main__":
    main()
