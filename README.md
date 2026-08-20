# Illustrated Guide PDF

**Turn any screen recording into a print-ready, step-by-step PDF manual — with numbered click markers, leader lines, per-figure legends, a cover page, table of contents, and closing reference cards.**

![Demo](demo/demo.gif)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## What This Tool Does

**Illustrated Guide PDF** is a Python-based pipeline that transforms screen recordings — software demos, onboarding sessions, tutorials, lectures, walkthroughs — into polished, professional PDF documentation. Every step in the finished guide includes a screenshot with **numbered amber markers** pointing at the exact UI controls the reader needs to find, connected by **leader lines** to a **legend** that names each one.

The pipeline is **themeable**: colors, fonts, page size, numerals (Latin, Arabic-Indic, Persian, Devanagari), text direction (LTR or RTL), and marker styling are all controlled by a single JSON file. The same workflow produces a corporate-branded English guide, an Arabic RTL manual with Arabic-Indic numerals, or anything in between.

### Key Features

- **Numbered click markers with leader lines** — badges are offset from the target so they never hide the UI label the reader is looking for
- **Per-figure legends** — each marker gets a numbered caption explaining what the control *is for*, not just what it's called
- **Full document structure** — cover page, front matter (callouts, prerequisite lists, table of contents), numbered sections with steps, and closing reference cards
- **Arabic RTL support** — full right-to-left layout with logical CSS properties, Arabic-Indic numerals, and bidirectional text handling
- **Themeable branding** — one JSON file controls the entire visual identity; ship the same guide for multiple brands without touching content
- **Font embedding** — OTF/TTF/WOFF fonts are base64-embedded into the HTML, so the PDF is fully portable with selectable, searchable text
- **Validation pipeline** — `check.py` catches the three mistakes that matter: missing figure references, mismatched marker/legend counts, and unused figures
- **Ink-coverage analysis** — the PDF checker reports per-page ink density so you can tune figure width and avoid half-empty pages
- **Region-aware cropping** — automatic detection of meeting participant tiles (via column-variance, not brightness), OS taskbars, browser chrome, and letterbox borders

---

## Quick Start

### Prerequisites

| Tool | Required For | Install |
|------|-------------|---------|
| **Python 3.8+** with `Pillow` + `numpy` | All scripts | `pip install Pillow numpy` |
| **ffmpeg / ffprobe** | Video frame extraction | `apt install ffmpeg` |
| **ImageMagick** (`montage`) | Contact sheets for review | `apt install imagemagick` |
| **poppler-utils** (`pdfinfo`, `pdftoppm`) | PDF validation + preview | `apt install poppler-utils` |
| **Chrome / Chromium** | HTML → PDF rendering | headless mode, no GUI needed |
| **puppeteer-core** (optional) | Page numbers in PDF | `npm install puppeteer-core` |

### 5-Step Workflow

```bash
# 1. Survey the recording — generates contact sheets every 60 seconds
python3 scripts/survey.py RECORDING.mp4 work/ --every 60

# 2. Extract frames and draw markers — produces figs/f01.jpg, f02.jpg, ...
python3 scripts/shots.py figures.json figs/ --video RECORDING.mp4 --theme theme.json

# 3. Validate — checks figure references, marker/legend counts, unused figures
python3 scripts/check.py content.json figures.json --figdir figs/

# 4. Build HTML and render PDF
python3 scripts/build.py content.json theme.json figs/ guide.html
python3 scripts/topdf.py guide.html guide.pdf --theme theme.json --footer "ACME · Guide"

# 5. Verify — ink coverage per page + visual spot-check
python3 scripts/check.py content.json figures.json --pdf guide.pdf
pdftoppm -png -r 90 guide.pdf pv/p
```

That's it. The output is a print-ready A4 PDF with embedded fonts, professional layout, and annotated screenshots.

---

## How It Works

### The Four Authoring Files

| File | Purpose | Authored By |
|------|---------|-------------|
| `figures.json` | Frame timestamps, crop regions, marker positions | You (from contact sheets) |
| `content.json` | All text: cover, sections, steps, legends, reference cards | You |
| `theme.json` | Colors, fonts, page size, numerals, marker styling | You (or use a template) |
| `figs/` | Generated screenshots with markers burned in | `shots.py` — never hand-edit |

### The Pipeline

```
RECORDING.mp4
     │
     ▼
 survey.py ──► contact sheets (pick timestamps)
     │
     ▼
 shots.py ──► figs/f01.jpg, f02.jpg ... (frames + markers)
     │
     ▼
 check.py ──► validation (marker count = legend count?)
     │
     ▼
 build.py ──► guide.html (styled, themed, embedded fonts)
     │
     ▼
 topdf.py ──► guide.pdf (print-ready, Chrome headless)
     │
     ▼
 check.py --pdf ──► ink coverage report (tune page density)
```

### Marker System

Markers are **fractional coordinates** (0–1) relative to the cropped figure region, not the raw frame. This means you can re-tune a trim or crop without recalculating every marker position.

Each marker has:
- `x`, `y` — fractional position within the region
- `dir` — badge direction (`ul`, `ur`, `dl`, `dr`) — the badge is offset in this direction and a leader line connects it to the target point
- Automatic edge clamping — badges near frame edges flip direction automatically

The badge **never sits on top of the control** — it's offset by ~2× the marker radius, with a thin leader line pointing at the exact spot. This is by design: a badge that hides the label defeats the purpose.

---

## Theming

A theme is a single JSON file. Nothing else in the pipeline needs to change to rebrand a guide.

```jsonc
{
  "name": "acme",
  "page":     { "size": "A4", "margin": { "top": "11mm", "right": "12mm", "bottom": "13mm", "left": "12mm" } },
  "numerals": "latin",              // latin | arabic-indic | persian | devanagari
  "colors": {
    "ink":        "#0d1b2a",        // headings, cover ground, marker text
    "text":       "#1e2a3a",        // body copy
    "accent":     "#c7b572",        // rules, bullets, tick boxes, section rule
    "accentSoft": "#e8d5a7",        // marker fill, step badges, cover title
    "paper":      "#ffffff",
    "coverText":  "#f3efe3"
  },
  "fonts": {
    "family":   "Acme Sans",
    "fallback": "system-ui, sans-serif",
    "files": [ { "path": "~/fonts/AcmeSans-Regular.otf", "weight": 400 },
               { "path": "~/fonts/AcmeSans-Bold.otf",    "weight": 700 } ]
  },
  "figure": { "width": "152mm", "radius": "2mm", "border": "#5a5446" },
  "cover":  { "style": "panel", "padding": "40mm 20mm 24mm", "radius": "2mm", "titleSize": "38pt" },
  "marker": { "marker_fill": "#e8d5a7", "marker_text": "#0d1b2a", "marker_ring": "#e8d5a7" }
}
```

### Shipped Themes

| Theme | Style | Direction |
|-------|-------|-----------|
| `theme.corporate.json` | Blue, professional | LTR |
| `theme.lumina.json` | Navy + champagne, Arabic | RTL |
| `theme.mono.json` | Black, white, one accent — safe default | LTR |

### RTL and Non-Latin Scripts

Set `content.dir` to `rtl` and `content.lang` appropriately — the layout uses logical CSS properties throughout and mirrors automatically. Numerals (`latin`, `arabic-indic`, `persian`, `devanagari`) affect badges, legends, the table of contents, and the numbers burned into figures.

---

## Content Structure

```jsonc
{
  "lang": "ar", "dir": "rtl", "stepsWord": "خطوات",
  "cover":    { "brand": "", "title": "", "subtitle": "", "chips": [], "note": "" },
  "front":    [ /* callout | list | toc | note */ ],
  "sections": [ { "n": "1", "title": "", "intro": "",
                  "steps": [ { "fig": "f01", "title": "", "body": "", "legend": ["", ""] } ] } ],
  "back":     [ /* cards | final | note */ ]
}
```

### Block Types

| Block | Use For |
|-------|---------|
| `callout` | The one warning a reader must not miss |
| `list` | Bulleted prerequisites |
| `toc` | Auto-generated from sections |
| `cards` | Closing reference cards (grid or checklist style) |
| `final` | One closing line, set large |
| `note` | Small muted paragraph |

`body` and legend entries accept inline HTML — `<b>` is the useful one, for the literal UI label the reader must find on screen.

---

## Best Practices for Great Guides

### Do

- **Say what a control *is for*, not what it is called.** "Generate — the number next to it is what it will cost" beats "the Generate button."
- **Crop the recording chrome out** — screen-share pills, OS taskbars, participant tiles. A figure that still looks like a video call reads as a screenshot of a meeting, not a manual.
- **Expect one marker correction pass.** Marker positions are estimates until you've seen them land on the actual figure. Montage the output, look at it, adjust. This is normal, not a failure.
- **Check ink coverage.** One figure ≈ 20% ink, two ≈ 40%. If most pages sit near 20%, shrink `figure.width` by ~6mm and rebuild.

### Don't

- **Never put a numbered badge on the control it points at.** It hides the label the reader was sent to find. The scripts offset the badge and draw a leader line — keep it that way.
- **Never invent a screenshot.** If a moment was not captured, use the adjacent real states and say so, rather than compositing one that never existed.
- **Don't skip the validation step.** `check.py` catches the three mistakes that matter: a step pointing at a figure that doesn't exist, a legend without one entry per marker, and a built figure no step ever shows.

---

## Use Cases

- **Software onboarding manuals** — turn a demo recording into a "How to use X" document
- **SOP documentation** — standard operating procedures with annotated screenshots
- **UAT session guides** — User Acceptance Testing walkthroughs with exact click paths
- **Training handouts** — lecture or workshop recordings become study materials
- **Multi-language documentation** — same pipeline, different theme + content JSON
- **Client-facing tutorials** — branded guides for your product or service

---

## Repository Structure

```
illustrated-guide-pdf/
├── SKILL.md                          # Skill manifest + workflow
├── README.md                         # This file
├── scripts/
│   ├── survey.py                     # Extract contact sheets from video
│   ├── shots.py                      # Extract frames + draw numbered markers
│   ├── check.py                      # Validate content/figures + PDF ink analysis
│   ├── build.py                      # Build styled HTML from content + theme
│   └── topdf.py                      # Render HTML → PDF via Chrome headless
├── references/
│   ├── AUTHORING.md                  # JSON schemas, marker coordinates, page density
│   └── THEMING.md                    # Theme fields, print palettes, RTL, fonts
└── assets/
    ├── content.example.json          # Minimal content template
    ├── figures.example.json          # Minimal figures template
    ├── theme.corporate.json          # Blue LTR theme
    ├── theme.lumina.json             # Navy + champagne RTL Arabic theme
    ├── theme.mono.json               # Black/white safe default theme
    └── example-real/
        ├── content.json              # Full 24-step Arabic guide spec
        ├── figures.json              # Full 74-marker figures spec
        └── README.md                 # How to run the real example
```

---

## Requirements Detail

### Python Dependencies

```bash
pip install Pillow numpy
```

### System Dependencies

```bash
# Ubuntu / Debian
sudo apt install ffmpeg imagemagick poppler-utils chromium-browser

# macOS (Homebrew)
brew install ffmpeg imagemagick poppler chromium
```

### Chrome / Chromium

The `topdf.py` script launches Chrome in headless mode to render HTML → PDF. No GUI is needed. Puppeteer-core is optional and only adds page numbers to the PDF footer.

---

## License

MIT License — see [LICENSE](LICENSE).

## Contributing

Pull requests welcome. If you add a new theme, please include a screenshot of a sample guide using it.

## Credits

Built with Python, Pillow, ImageMagick, ffmpeg, and Chrome Headless. The marker drawing system uses fractional coordinates with automatic edge clamping and leader-line routing.