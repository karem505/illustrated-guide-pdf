# A real, complete spec

`content.json` + `figures.json` from a shipped 17-page guide: an Arabic (RTL)
manual for a generative-video tool, built from a 96-minute meeting recording —
24 steps, 6 sections, 74 markers.

The figures are not included (they are ~4 MB and specific to that recording), but
the spec is complete and runnable against the source video:

```bash
python3 ../../scripts/shots.py figures.json figs/ --video REC.mp4 --theme ../theme.lumina.json
python3 ../../scripts/build.py content.json ../theme.lumina.json figs/ guide.html
python3 ../../scripts/topdf.py guide.html guide.pdf --theme ../theme.lumina.json --footer "…"
```

Use it as the shape to copy: note how every `legend` has exactly one entry per
marker, how each entry names what the control is *for*, and how the English ToS
quotation in the front-matter callout carries its own `dir: "ltr"`.
