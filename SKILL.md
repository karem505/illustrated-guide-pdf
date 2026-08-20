---
name: illustrated-guide-pdf
description: >-
  Build a styled, print-ready step-by-step PDF manual from a screen recording or
  a folder of screenshots — with numbered click markers, leader lines, per-figure
  legends, a cover, contents and closing reference cards. Use when asked to turn a
  lecture, demo, walkthrough, onboarding session or tutorial recording into a
  guide, handout, manual, SOP or "how to use X" document; when asked for
  screenshots with numbered callouts showing where to click; or to re-skin an
  existing guide for another product, brand or language (LTR or RTL). Not for
  slide decks, marketing one-pagers, or PDFs without screenshots.
---

# Illustrated step-by-step guide → PDF

Turns a recording (or loose screenshots) into a manual where every step has a
screenshot, numbered badges pointing at the exact controls, and a legend naming
each one. Brand, colours, fonts, numerals and text direction come from a theme
file, so the same pipeline serves any product or company.

## The four artefacts you author

| File | What it holds |
|---|---|
| `figures.json` | where each screenshot comes from, how to crop it, where the markers go |
| `content.json` | the words: cover, front matter, sections → steps → legends, closing cards |
| `theme.json` | colours, fonts, page size, numerals, figure width, marker styling |
| `figs/` | generated — do not hand-edit |

Start by copying `assets/content.example.json`, `assets/figures.example.json` and
the closest `assets/theme.*.json` into the working directory.

## Workflow

**1 — Survey the recording** (skip if you already have screenshots)

```bash
python3 scripts/survey.py RECORDING.mp4 work/ --every 60
```

Read the contact sheets it writes, and note the timestamp of every moment you
want. Those numbers become `at` values. Sample more finely (`--every 15`) around
a busy stretch.

**2 — Draft `figures.json`, build, and look**

```bash
python3 scripts/shots.py figures.json figs/ --video RECORDING.mp4 --theme theme.json
```

Then **actually look at the output** — montage them and read the images:

```bash
cd figs && montage f*.jpg -tile 2x2 -geometry 830x520+4+18 \
  -background '#111' -label '%t' -pointsize 24 -fill '#e8d5a7' ../check.png
```

Marker positions are estimates until you have seen them land. Expect one
correction pass; that is normal, not a failure.

**3 — Write `content.json`, then validate before rendering**

```bash
python3 scripts/check.py content.json figures.json --figdir figs/
```

Catches the three mistakes that matter: a step pointing at a figure that does not
exist, a legend that does not have one entry per marker, and a built figure no
step ever shows.

**4 — Build and render**

```bash
python3 scripts/build.py content.json theme.json figs/ guide.html
python3 scripts/topdf.py guide.html guide.pdf --theme theme.json --footer "ACME · Guide"
```

**5 — Check the pages, not just the file size**

```bash
python3 scripts/check.py content.json figures.json --pdf guide.pdf
pdftoppm -png -r 90 guide.pdf pv/p     # then read a few pages as images
```

Ink coverage tells you where pages are half empty: one figure ≈ 20%, two ≈ 40%.
If most pages sit near 20%, shrink `figure.width` in the theme by ~6mm and
rebuild — see `references/AUTHORING.md`.

## Rules that keep the output usable

- **Never put a numbered badge on the control it points at.** It hides the label
  the reader was sent to find. The scripts offset the badge and draw a leader
  line; keep it that way.
- **One legend entry per marker, in marker order.** `check.py` enforces it.
- **Crop the recording chrome out** — screen-share pills, OS taskbars, participant
  tiles. A figure that still looks like a video call reads as a screenshot of a
  meeting, not as a manual.
- **Say what a control *is for*, not what it is called.** "Generate — the number
  next to it is what it will cost" beats "the Generate button".
- **Never invent a screenshot.** If a moment was not captured, use the adjacent
  real states and say so, rather than compositing one that never existed.

## Details

- `references/AUTHORING.md` — the JSON schemas, finding marker coordinates,
  page-density tuning, and the traps (bidi, taskbars, dark UIs).
- `references/THEMING.md` — theme fields, print-palette guidance, embedding fonts,
  RTL and non-Latin numerals.

## Requirements

`ffmpeg`/`ffprobe` (only for video input), ImageMagick (`montage`), Python with
`Pillow` + `numpy`, `poppler-utils` (`pdfinfo`, `pdftoppm`), and Chrome/Chromium.
`puppeteer-core` is optional and only adds page numbers.
