# Authoring reference

## figures.json

```jsonc
{ "figures": [ {
  "id": "f01",                  // becomes figs/f01.jpg; steps reference it by this
  "at": 420,                    // seconds into --video …
  "src": "shots/panel.png",     // … or an image path, relative to figures.json
  "region": "share",            // full | share | window | [x, y, w, h] fractions
  "taskbar": true,              // detect and cut an OS taskbar at the bottom
  "blur": [[0.36, 0.085, 0.74, 0.145]],
  "trim": { "top": 0.135, "right": 0, "bottom": 0, "left": 0 },
  "markers": [ { "x": 0.33, "y": 0.09, "dir": "dr" } ]
} ] }
```

**Order of operations:** source → region → blur → taskbar → trim → markers.

**Marker coordinates are fractions of the *region*, before blur/taskbar/trim.**
That is deliberate: you can re-tune a trim without re-deriving every position.

`dir` puts the badge up-left (`ul`, default), `ur`, `dl` or `dr` of its target,
and flips automatically if that would run off the edge.

### Region modes

| mode | use for |
|---|---|
| `full` | a clean screenshot, nothing to remove |
| `share` | meeting/webinar recording: shared screen left, participant tiles right |
| `window` | a frame with uniform letterbox borders |
| `[x,y,w,h]` | anything else; fractions of the frame |

`share` finds the dead gutter between the shared screen and the tiles by
**per-column standard deviation, not brightness.** Dark application UIs are almost
black, so a brightness threshold reads real content as letterbox and crops it
away. Variance does not care how dark pixels are, only whether they differ.

### Finding marker coordinates without guessing

Build the figures first, montage them at a known tile width, read the montage,
and convert: `fraction = (pixel_in_tile) / (tile_width)`. Estimating from a
montage lands within about 2%, which is close enough — the leader line absorbs
the rest. Then look at the built figures and correct the few that missed.

If a marker must sit near an edge, keep it: the script clamps the badge inside
the frame and the leader still points at the true spot.

## content.json

```jsonc
{
  "lang": "ar", "dir": "rtl", "stepsWord": "steps",
  "cover":    { "brand": "", "title": "", "subtitle": "", "chips": [], "note": "" },
  "front":    [ /* callout | list | toc | note */ ],
  "sections": [ { "n": "1", "title": "", "intro": "",
                  "steps": [ { "fig": "f01", "title": "", "body": "", "legend": ["", ""] } ] } ],
  "back":     [ /* cards | final | note */ ]
}
```

Block types:

- `callout` — `{title, body, quote:{text,dir}, paras:[]}`. Use for the one warning
  a reader must not miss. **Give a quote in another script its own `dir`**, or
  bidi drags its closing punctuation to the wrong end of the line.
- `list` — `{title, items:[]}`; bulleted prerequisites.
- `toc` — `{title}`; generated from the sections.
- `cards` — `{title, cards:[{title, kind:"grid"|"checks", items:[]}]}`. `checks`
  renders empty tick boxes; `grid` renders a numbered two-column reference.
- `final` — one closing line, set large.
- `note` — small muted paragraph.

`body` and legend entries accept inline HTML — `<b>` is the useful one, for the
literal UI label the reader must find on screen.

## Page density

A step block is roughly `title + body + figure + legend`. The figure dominates.
On A4 with default margins there is ~272mm of usable height:

| `figure.width` | figure height (16:9-ish) | step block | steps per page |
|---|---|---|---|
| 186mm (full) | ~110mm | ~150mm | 1 |
| 158mm | ~94mm | ~134mm | 2, unless a section header intervenes |
| 152mm | ~90mm | ~130mm | 2 comfortably |

Section headers cost ~15mm and use `page-break-after: avoid`, so a header plus
two steps will not fit — that is the usual cause of a stray half-empty page.
Shrinking the figure by 6mm is almost always the cheapest fix; the apparent size
loss is a few percent and screenshots stay well above 200 DPI at these widths.

Run `check.py --pdf` and read the ink column before deciding anything.

## Traps

- **A fixed bottom-percentage trim does not remove a taskbar.** It removes the
  black padding *below* it and leaves the bar. Use `"taskbar": true`.
- **Chrome only honours a negative margin on some sides**, so a full-bleed cover
  can come out with an uneven white frame. `cover.style: "panel"` fills the
  content box exactly and is deterministic.
- **`gsap`-style callback text does not apply here**, but a related trap does:
  always look at the built figure. A marker that reads fine as coordinates can sit
  on top of the label it points at.
- **Do not composite a screenshot that never existed.** If the recording skipped
  a moment, use the real adjacent states and say so in the body text.
