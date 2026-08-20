#!/usr/bin/env python3
"""Pre-flight and post-flight checks.

    python3 check.py content.json figures.json [--figdir DIR] [--pdf OUT.pdf]

Pre-flight  — every step points at a figure that exists in figures.json, and each
              step's legend has exactly as many entries as that figure has markers.
Post-flight — per-page ink coverage, which is how you spot half-empty pages
              (a page with one figure reads ~20%, with two ~40%).
"""
import argparse, glob, json, os, subprocess, sys, tempfile

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content"); ap.add_argument("figures")
    ap.add_argument("--figdir"); ap.add_argument("--pdf")
    a = ap.parse_args()

    content = json.load(open(a.content, encoding="utf-8"))
    figs = {f["id"]: f for f in json.load(open(a.figures, encoding="utf-8"))["figures"]}
    problems, steps = [], 0

    for s in content["sections"]:
        for st in s["steps"]:
            steps += 1
            fid = st.get("fig")
            if not fid:
                continue
            if fid not in figs:
                problems.append(f"step '{st['title']}' -> unknown figure '{fid}'")
                continue
            want = len(figs[fid].get("markers", []))
            got = len(st.get("legend", []))
            if want != got:
                problems.append(f"{fid}: {want} marker(s) but {got} legend entr(ies)")
            if a.figdir and not os.path.exists(os.path.join(a.figdir, f"{fid}.jpg")):
                problems.append(f"{fid}: not built in {a.figdir}")

    used = {st.get("fig") for s in content["sections"] for st in s["steps"]}
    for fid in figs:
        if fid not in used:
            problems.append(f"{fid}: built but never referenced by a step")

    print(f"{steps} steps, {len(figs)} figures")
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  ✗ " + p)
    else:
        print("  ✓ every step has a figure, and every legend matches its marker count")

    if a.pdf and os.path.exists(a.pdf):
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["pdftoppm", "-png", "-r", "55", a.pdf, os.path.join(td, "p")],
                           check=False, capture_output=True)
            try:
                import numpy as np
                from PIL import Image
            except ImportError:
                return
            print("\npage  ink%   (a page holding one figure ≈ 20%, two ≈ 40%)")
            for f in sorted(glob.glob(os.path.join(td, "p-*.png"))):
                arr = np.asarray(Image.open(f).convert("L"))
                ink = (arr < 235).mean() * 100
                n = os.path.basename(f).split("-")[-1].split(".")[0]
                print(f"{n:>4}  {ink:5.1f}  {'#' * int(ink / 3)}")

    sys.exit(1 if problems else 0)

if __name__ == "__main__":
    main()
