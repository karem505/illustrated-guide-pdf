#!/usr/bin/env python3
"""Build annotated guide figures from a recording or from loose screenshots.

    python3 shots.py figures.json OUTDIR [--video REC.mp4] [--theme theme.json]

figures.json is {"figures": [ {...}, ... ]}; see references/AUTHORING.md.
Each figure produces OUTDIR/<id>.jpg.

Pipeline per figure, in this order:
  1. source   — a frame pulled from --video at `at` seconds, or an image at `src`
  2. region   — isolate the interesting rectangle (see REGION MODES below)
  3. blur     — soften recording artefacts (screen-share pills, names, emails)
  4. taskbar  — detect and cut an OS taskbar at the bottom
  5. trim     — final manual nudge, fractions of the region
  6. markers  — numbered badges with leader lines

REGION MODES
  "full"            use the frame as-is
  "share"           meeting recording: the shared screen is a block anchored at
                    the left with the participant tiles across a dark gutter
  "window"          crop away uniform (letterbox) borders on all four sides
  [x, y, w, h]      explicit, as fractions of the frame

WHY VARIANCE AND NOT BRIGHTNESS
  Dark application UIs (editors, design tools, most 2020s SaaS) are almost black,
  so a brightness threshold reads real content as letterbox and crops it away.
  Per-column standard deviation does not care how dark the pixels are, only
  whether they differ — the dead gutter is the only place it collapses.
"""
import argparse, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

NUMERALS = {
    "latin": "0123456789",
    "arabic-indic": "٠١٢٣٤٥٦٧٨٩",
    "devanagari": "०१२३४५६७८९",
    "persian": "۰۱۲۳۴۵۶۷۸۹",
}

def numeral(n, system):
    digits = NUMERALS.get(system, NUMERALS["latin"])
    return "".join(digits[int(c)] for c in str(n))

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

# ---------------------------------------------------------------- region modes
def region_share(a, thr=8.0, min_run=10, search_from=0.4):
    """Shared screen anchored left, participants right across a dark gutter."""
    sd = a.std(axis=0)
    x1 = len(sd) - 1
    i = int(len(sd) * search_from)
    while i < len(sd):
        if sd[i] < thr:
            j = i
            while j < len(sd) and sd[j] < thr:
                j += 1
            if j - i >= min_run:
                x1 = i - 1
                break
            i = j
        else:
            i += 1
    live = a[:, : x1 + 1].std(axis=1) > thr
    if not live.any():
        return 0, 0, a.shape[1], a.shape[0]
    y0 = int(np.argmax(live))
    y1 = len(live) - 1 - int(np.argmax(live[::-1]))
    return 0, y0, x1 + 1, y1 - y0 + 1

def region_window(a, thr=8.0):
    """Trim uniform borders on all four sides."""
    cs, rs = a.std(axis=0) > thr, a.std(axis=1) > thr
    if not cs.any() or not rs.any():
        return 0, 0, a.shape[1], a.shape[0]
    x0 = int(np.argmax(cs)); x1 = len(cs) - 1 - int(np.argmax(cs[::-1]))
    y0 = int(np.argmax(rs)); y1 = len(rs) - 1 - int(np.argmax(rs[::-1]))
    return x0, y0, x1 - x0 + 1, y1 - y0 + 1

def taskbar_top(a, thr=120, min_frac=0.6):
    """An OS taskbar is a uniformly bright band flush with the bottom.

    A fixed bottom-percentage trim is the obvious approach and it is wrong: it
    removes the black padding *below* the bar and leaves the bar itself.
    """
    rm = a.mean(axis=1); h = len(rm); y = h - 1
    while y > 0 and rm[y] < thr:
        y -= 1
    if y < h * min_frac:
        return h
    while y > 0 and rm[y] > thr:
        y -= 1
    return y + 1

# ---------------------------------------------------------------- frame source
def frame_from_video(video, at, dest):
    subprocess.run(["ffmpeg", "-v", "error", "-ss", str(at), "-i", video,
                    "-frames:v", "1", "-q:v", "2", dest, "-y"], check=False)
    if not os.path.exists(dest):
        sys.exit(f"could not extract a frame at {at}s from {video}")
    return dest

# ---------------------------------------------------------------- the drawing
def draw_markers(im, markers, th):
    w, h = im.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    R = max(int(th["marker_min_px"]), int(w * th["marker_scale"]))
    try:
        font = ImageFont.truetype(th["marker_font"], int(R * 1.15))
    except (OSError, TypeError):
        font = ImageFont.load_default()

    fill, txt = hex_rgb(th["marker_fill"]), hex_rgb(th["marker_text"])
    ring = hex_rgb(th["marker_ring"])

    for i, m in enumerate(markers, start=1):
        tx = min(max(m["x"] * w, 3), w - 3)
        ty = min(max(m["y"] * h, 3), h - 3)
        dirn = m.get("dir", "ul")
        off = R * 1.9
        sx = -1 if "l" in dirn else 1
        sy = -1 if "u" in dirn else 1
        bx, by = tx + sx * off, ty + sy * off
        if bx < R + 10 or bx > w - R - 10:
            bx = tx - sx * off
        if by < R + 10 or by > h - R - 10:
            by = ty - sy * off
        bx = min(max(bx, R + 10), w - R - 10)
        by = min(max(by, R + 10), h - R - 10)

        # Leader line + ringed dot. The badge never sits on the control, because
        # a badge on a label hides the label the reader is being sent to find.
        import math
        ang = math.atan2(ty - by, tx - bx)
        d.line([bx + math.cos(ang) * (R + 3), by + math.sin(ang) * (R + 3), tx, ty],
               fill=ring + (235,), width=max(3, R // 8))
        d.ellipse([tx - R * 0.30, ty - R * 0.30, tx + R * 0.30, ty + R * 0.30],
                  outline=ring + (255,), width=max(3, R // 8))
        d.ellipse([tx - R * 0.11, ty - R * 0.11, tx + R * 0.11, ty + R * 0.11], fill=ring + (255,))

        d.ellipse([bx - R - 4, by - R - 4, bx + R + 4, by + R + 4], fill=txt + (240,))
        d.ellipse([bx - R, by - R, bx + R, by + R], fill=fill + (255,))
        s = numeral(i, th["numerals"])
        bb = d.textbbox((0, 0), s, font=font)
        d.text((bx - (bb[2] - bb[0]) / 2 - bb[0], by - (bb[3] - bb[1]) / 2 - bb[1]),
               s, font=font, fill=txt)

    im = Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")
    if th.get("figure_border"):
        ImageDraw.Draw(im).rectangle([0, 0, w - 1, h - 1],
                                     outline=hex_rgb(th["figure_border"]), width=2)
    return im

# ---------------------------------------------------------------------- driver
DEFAULT_THEME = {
    "marker_fill": "#e8d5a7", "marker_text": "#0d1b2a", "marker_ring": "#e8d5a7",
    "marker_font": None, "marker_scale": 0.0175, "marker_min_px": 24,
    "numerals": "latin", "figure_border": "#5a5446", "jpeg_quality": 90,
}

def build(spec, outdir, video=None, theme=None, tmpdir=None):
    th = dict(DEFAULT_THEME)
    th.update(theme or {})
    os.makedirs(outdir, exist_ok=True)
    tmpdir = tmpdir or os.path.join(outdir, "_raw")
    os.makedirs(tmpdir, exist_ok=True)
    made = []

    for f in spec["figures"]:
        fid = f["id"]
        if "src" in f:
            src = f["src"]
            if not os.path.isabs(src):
                src = os.path.join(spec.get("_base", "."), src)
        else:
            if not video:
                sys.exit(f"figure {fid} has `at` but no --video was given")
            src = frame_from_video(video, f["at"], os.path.join(tmpdir, f"{fid}.jpg"))

        im = Image.open(src).convert("RGB")
        gray = np.asarray(im.convert("L"), dtype=np.float32)

        mode = f.get("region", "full")
        if mode == "share":
            rx, ry, rw, rh = region_share(gray)
        elif mode == "window":
            rx, ry, rw, rh = region_window(gray)
        elif isinstance(mode, (list, tuple)):
            W, H = im.size
            rx, ry, rw, rh = (int(mode[0] * W), int(mode[1] * H),
                              int(mode[2] * W), int(mode[3] * H))
        else:
            rx, ry, rw, rh = 0, 0, im.size[0], im.size[1]
        im = im.crop((rx, ry, rx + rw, ry + rh))

        for (x0, y0, x1, y1) in f.get("blur", []):
            box = (int(x0 * rw), int(y0 * rh), int(x1 * rw), int(y1 * rh))
            im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(10)), box)

        bottom = rh
        if f.get("taskbar"):
            bottom = taskbar_top(np.asarray(im.convert("L"), dtype=np.float32))

        t = f.get("trim", {})
        cx0, cy0 = int(t.get("left", 0) * rw), int(t.get("top", 0) * rh)
        cx1 = int(rw - t.get("right", 0) * rw)
        cy1 = min(bottom, int(rh - t.get("bottom", 0) * rh))
        im = im.crop((cx0, cy0, cx1, cy1))

        # Marker coordinates are fractions of the REGION (before blur/taskbar/trim),
        # so trims can be re-tuned without re-deriving every position.
        markers = []
        for m in f.get("markers", []):
            markers.append({"x": (m["x"] * rw - cx0) / max(1, im.size[0]),
                            "y": (m["y"] * rh - cy0) / max(1, im.size[1]),
                            "dir": m.get("dir", "ul")})
        im = draw_markers(im, markers, th)
        out = os.path.join(outdir, f"{fid}.jpg")
        im.save(out, quality=th["jpeg_quality"], optimize=True)
        made.append((fid, im.size, len(markers)))
        print(f"  {fid:>6}  {im.size[0]}x{im.size[1]}  {len(markers)} marker(s)")
    return made

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("figures"); ap.add_argument("outdir")
    ap.add_argument("--video"); ap.add_argument("--theme")
    a = ap.parse_args()
    spec = json.load(open(a.figures, encoding="utf-8"))
    spec["_base"] = os.path.dirname(os.path.abspath(a.figures))
    theme = json.load(open(a.theme, encoding="utf-8")).get("marker", {}) if a.theme else {}
    if a.theme:
        t = json.load(open(a.theme, encoding="utf-8"))
        theme = dict(t.get("marker", {}))
        theme.setdefault("numerals", t.get("numerals", "latin"))
        theme.setdefault("figure_border", t.get("figure", {}).get("border"))
        fonts = t.get("fonts", {}).get("files", [])
        heavy = [f for f in fonts if int(f.get("weight", 400)) >= 700]
        if heavy:
            theme.setdefault("marker_font", os.path.expanduser(heavy[-1]["path"]))
    print(f"building {len(spec['figures'])} figures -> {a.outdir}")
    build(spec, a.outdir, a.video, theme)

if __name__ == "__main__":
    main()
