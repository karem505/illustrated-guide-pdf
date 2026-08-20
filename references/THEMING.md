# Theming

A theme is one JSON file. Nothing else in the pipeline needs to change to move a
guide from one brand to another.

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
    "rule":       "#d8d2c2",        // hairlines and card borders
    "muted":      "#6b7280",        // captions, intros
    "paper":      "#ffffff",
    "calloutBg":  "#fdfbf5",
    "coverText":  "#f3efe3"
  },
  "fonts": {
    "family":   "Acme Sans",
    "fallback": "system-ui, sans-serif",
    "files": [ { "path": "~/fonts/AcmeSans-Regular.otf", "weight": 400 },
               { "path": "~/fonts/AcmeSans-Bold.otf",    "weight": 700 },
               { "path": "~/fonts/AcmeSans-Black.otf",   "weight": 900 } ]
  },
  "figure": { "width": "152mm", "radius": "2mm", "border": "#5a5446" },
  "cover":  { "style": "panel", "padding": "40mm 20mm 24mm", "radius": "2mm", "titleSize": "38pt" },
  "marker": { "marker_fill": "#e8d5a7", "marker_text": "#0d1b2a", "marker_ring": "#e8d5a7" }
}
```

## Picking colours for print

A screen brand palette is not a print palette. Two rules carry most of it:

1. **Flip dark-mode brands.** If the product's UI is dark, do **not** set
   `paper` dark to match. Ink on white is what a school or office printer does
   well, and the screenshots supply all the dark the page needs. Keep the brand's
   dark as `ink` (headings, cover, marker text) and its highlight as `accent`.
2. **The marker must beat the screenshot.** Markers sit on top of the product's
   own UI. Pick `marker_fill` so it is unlike anything in the interface —
   against a dark UI a warm light fill wins; against a light UI a saturated one
   does. If the product's own accent is that colour, choose a different one.

Ship-able starting points are in `assets/`: `theme.lumina.json` (dark navy +
champagne, RTL), `theme.corporate.json` (blue, LTR), `theme.mono.json` (black,
white, one accent — the safe default when the brand is unknown).

## Fonts

`fonts.files` are base64-embedded into the HTML, so the PDF is portable and the
text stays selectable and searchable. `.otf`, `.ttf`, `.woff`, `.woff2` all work.
A missing path is skipped with a warning and the `fallback` stack is used, so a
theme never hard-fails on a machine without the brand font.

The heaviest weight listed is also used to draw the numerals inside the markers,
so include a bold or black cut if you can.

## RTL and non-Latin scripts

Set `content.dir` to `rtl` and `content.lang` appropriately; the layout uses
logical properties throughout and mirrors on its own.

- Set `numerals` to match the language — the badges, the legend and the contents
  all follow it, and so do the markers burnt into the figures.
- Any **quotation in another script needs its own `dir`** on the block (see
  `callout.quote.dir`), or its closing punctuation lands at the wrong end.
- Product names and UI labels stay in their original script. A reader hunting for
  a button labelled `GENERATE` needs to see `GENERATE`, not a translation.
