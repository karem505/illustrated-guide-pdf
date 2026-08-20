#!/usr/bin/env python3
"""Survey a screen recording: pull one frame per interval and tile them into
labelled contact sheets so you can find the moments worth screenshotting.

    python3 survey.py RECORDING.mp4 OUTDIR [--every 60] [--from 0] [--to 0]
                      [--cols 4] [--rows 4] [--width 480]

Writes OUTDIR/frames/mNNN.jpg and OUTDIR/sheet0.png, sheet1.png, ...
Each tile is labelled with its timestamp in seconds, which is what you feed to
`shots.py` as a figure's `at`.

Requires: ffmpeg, ffprobe, ImageMagick (montage).
"""
import argparse, os, subprocess, sys

def run(cmd, **kw):
    return subprocess.run(cmd, check=False, capture_output=True, text=True, **kw)

def duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path])
    if r.returncode != 0:
        sys.exit(f"ffprobe failed: {r.stderr.strip()}")
    return float(r.stdout.strip())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("outdir")
    ap.add_argument("--every", type=int, default=60, help="seconds between frames")
    ap.add_argument("--from", dest="start", type=int, default=0)
    ap.add_argument("--to", dest="end", type=int, default=0, help="0 = end of file")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--rows", type=int, default=4)
    ap.add_argument("--width", type=int, default=480, help="tile width in px")
    a = ap.parse_args()

    end = a.end or int(duration(a.video))
    frames_dir = os.path.join(a.outdir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    times = list(range(a.start, end, a.every))
    print(f"video is {end}s; sampling {len(times)} frames every {a.every}s")
    shots = []
    for t in times:
        out = os.path.join(frames_dir, f"t{t:06d}.jpg")
        # -ss before -i is a fast keyframe seek: essential on long recordings.
        run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", a.video,
             "-frames:v", "1", "-vf", f"scale={a.width}:-1", "-q:v", "4", out, "-y"])
        if os.path.exists(out):
            shots.append((t, out))

    per = a.cols * a.rows
    for g in range((len(shots) + per - 1) // per):
        batch = shots[g * per:(g + 1) * per]
        sheet = os.path.join(a.outdir, f"sheet{g}.png")
        cmd = ["montage"]
        for t, p in batch:
            cmd += ["-label", f"{t}s", p]
        cmd += ["-tile", f"{a.cols}x{a.rows}",
                "-geometry", f"{a.width}x+3+3",
                "-background", "#111", "-pointsize", "16", "-fill", "white", sheet]
        run(cmd)
        print(f"  {sheet}  ({batch[0][0]}s .. {batch[-1][0]}s)")

    print(f"\nRead the sheets, note the timestamps you want, then list them as "
          f"`at` values in figures.json.")

if __name__ == "__main__":
    main()
