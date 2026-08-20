#!/usr/bin/env python3
"""Turn content.json + theme.json + a figures directory into a print-ready HTML.

    python3 build.py content.json theme.json FIGDIR OUT.html

The HTML is self-contained apart from the figures, which are referenced
relatively — keep OUT.html next to FIGDIR (or pass --embed to inline them).
"""
import argparse, base64, json, mimetypes, os, sys

NUMERALS = {
    "latin": "0123456789", "arabic-indic": "٠١٢٣٤٥٦٧٨٩",
    "devanagari": "०१२३४५६७८९", "persian": "۰۱۲۳۴۵۶۷۸۹",
}

def num(n, sys_):
    d = NUMERALS.get(sys_, NUMERALS["latin"])
    return "".join(d[int(c)] for c in str(n))

def font_face(family, files):
    out = []
    for f in files:
        path = os.path.expanduser(f["path"])
        if not os.path.exists(path):
            print(f"  ! font missing, skipping: {path}", file=sys.stderr)
            continue
        ext = os.path.splitext(path)[1].lower()
        fmt = {".woff2": "woff2", ".woff": "woff", ".ttf": "truetype", ".otf": "opentype"}.get(ext, "opentype")
        mime = {"woff2": "font/woff2", "woff": "font/woff",
                "truetype": "font/ttf", "opentype": "font/otf"}[fmt]
        b64 = base64.b64encode(open(path, "rb").read()).decode()
        out.append(f'''      @font-face {{
        font-family: "{family}";
        src: url("data:{mime};base64,{b64}") format("{fmt}");
        font-weight: {f.get("weight", 400)}; font-style: {f.get("style", "normal")}; font-display: block;
      }}''')
    return "\n".join(out)

def esc(s):
    return s  # content is authored, not user input; inline HTML in strings is intentional

def render(content, theme, figdir, embed=False, base="."):
    c, t = content, theme
    dir_ = c.get("dir", "ltr")
    lang = c.get("lang", "en")
    numsys = t.get("numerals", "latin")
    col = t["colors"]; pg = t["page"]; fig = t.get("figure", {})
    fam = t.get("fonts", {}).get("family", "system-ui")
    fallback = t.get("fonts", {}).get("fallback", "system-ui, sans-serif")
    faces = font_face(fam, t.get("fonts", {}).get("files", []))
    m = pg.get("margin", {})
    mt, mr, mb, ml = m.get("top", "12mm"), m.get("right", "12mm"), m.get("bottom", "14mm"), m.get("left", "12mm")

    def img_src(fid):
        p = os.path.join(figdir, f"{fid}.jpg")
        if not os.path.exists(p):
            sys.exit(f"missing figure: {p}")
        if embed:
            mime = mimetypes.guess_type(p)[0] or "image/jpeg"
            return f"data:{mime};base64," + base64.b64encode(open(p, "rb").read()).decode()
        return os.path.relpath(p, base)

    # ---- front / back matter blocks -------------------------------------
    def toc_html():
        rows = []
        for s in c["sections"]:
            rows.append(f'<div class="toc"><span class="tocn">{s["n"]}</span>'
                        f'<span class="toct">{s["title"]}</span>'
                        f'<span class="tocc">{num(len(s["steps"]), numsys)} {c.get("stepsWord","steps")}</span></div>')
        return "".join(rows)

    def block(b):
        k = b.get("type")
        if k == "callout":
            q = ""
            if b.get("quote"):
                qd = b["quote"].get("dir", dir_)
                align = "left" if qd == "ltr" else "right"
                # An excerpt in the other script needs its own dir, or bidi drags
                # its closing punctuation to the wrong end.
                q = f'<div class="q" dir="{qd}" style="text-align:{align}">{b["quote"]["text"]}</div>'
            extra = "".join(f"<p>{p}</p>" for p in b.get("paras", []))
            return f'<div class="callout"><h2>{b["title"]}</h2><p>{b["body"]}</p>{q}{extra}</div>'
        if k == "list":
            li = "".join(f"<li>{i}</li>" for i in b["items"])
            return f'<div class="blk"><h2>{b["title"]}</h2><ul>{li}</ul></div>'
        if k == "toc":
            return f'<div class="blk"><h2>{b.get("title","Contents")}</h2>{toc_html()}</div>'
        if k == "cards":
            cards = []
            for cd in b["cards"]:
                if cd.get("kind") == "checks":
                    items = "".join(f'<div class="chk"><span class="box"></span><span>{i}</span></div>'
                                    for i in cd["items"])
                else:
                    items = '<div class="grid">' + "".join(
                        f'<div class="gi"><span>{num(i, numsys)}</span><span>{v}</span></div>'
                        for i, v in enumerate(cd["items"], 1)) + "</div>"
                cards.append(f'<div class="card"><h3>{cd["title"]}</h3>{items}</div>')
            head = f'<h2 class="backhead">{b["title"]}</h2>' if b.get("title") else ""
            return head + "".join(cards)
        if k == "final":
            return f'<div class="final">{b["text"]}</div>'
        if k == "note":
            return f'<p class="note">{b["text"]}</p>'
        return ""

    front = "".join(block(b) for b in c.get("front", []))
    back = "".join(block(b) for b in c.get("back", []))

    # ---- sections and steps ---------------------------------------------
    body, n = [], 0
    for s in c["sections"]:
        body.append(f'''    <div class="sechead"><div class="secn">{s["n"]}</div>
      <div><h2>{s["title"]}</h2>{f'<p class="secintro">{s["intro"]}</p>' if s.get("intro") else ""}</div></div>''')
        for st in s["steps"]:
            n += 1
            lg = "".join(f'<div class="lg"><span class="lgn">{num(i, numsys)}</span>'
                         f'<span class="lgt">{v}</span></div>'
                         for i, v in enumerate(st.get("legend", []), 1))
            figure = (f'<figure><img src="{img_src(st["fig"])}" alt="{st["title"]}" /></figure>'
                      if st.get("fig") else "")
            body.append(f'''    <article class="step">
      <div class="sthead"><span class="stn">{num(n, numsys)}</span><h3>{st["title"]}</h3></div>
      {f'<p class="sttext">{st["body"]}</p>' if st.get("body") else ""}
      {figure}
      {f'<div class="legend">{lg}</div>' if lg else ""}
    </article>''')

    cov = c.get("cover", {})
    chips = "".join(f'<span class="chip">{x}</span>' for x in cov.get("chips", []))
    cover_style = t.get("cover", {}).get("style", "panel")
    cover_h = "273mm" if cover_style == "panel" else "297mm"
    cover_margin = "0" if cover_style == "panel" else f"-{mt} -{mr} -{mb}"

    return f'''<!doctype html>
<html lang="{lang}" dir="{dir_}">
  <head>
    <meta charset="UTF-8" />
    <title>{cov.get("title","Guide")}</title>
    <style>
{faces}
      :root {{
        --ink: {col["ink"]}; --text: {col["text"]}; --accent: {col["accent"]};
        --accent-soft: {col.get("accentSoft", col["accent"])}; --rule: {col.get("rule","#ddd")};
        --muted: {col.get("muted","#6b7280")}; --paper: {col.get("paper","#fff")};
        --callout-bg: {col.get("calloutBg","#fafafa")}; --cover-text: {col.get("coverText","#f3efe3")};
      }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      body {{ font-family: "{fam}", {fallback}; color: var(--text); background: var(--paper);
              -webkit-font-smoothing: antialiased; }}
      @page {{ size: {pg.get("size","A4")}; margin: {mt} {mr} {mb} {ml}; }}

      .cover {{
        position: relative; height: {cover_h}; margin: {cover_margin};
        background: var(--ink); color: var(--cover-text);
        padding: {t.get("cover",{}).get("padding","40mm 20mm 24mm")};
        border-radius: {t.get("cover",{}).get("radius","2mm")};
        display: flex; flex-direction: column; page-break-after: always;
      }}
      .cover .brand {{ font-size: 11pt; letter-spacing: .22em; color: var(--accent-soft); direction: ltr; }}
      .cover h1 {{ margin-top: 14mm; font-size: {t.get("cover",{}).get("titleSize","38pt")};
                   font-weight: 900; color: var(--accent-soft); line-height: 1.22; }}
      .cover .sub {{ margin-top: 8mm; font-size: 14pt; font-weight: 500; line-height: 1.6; opacity: .88; }}
      .cover .rule {{ margin-top: 12mm; width: 70mm; height: 2px; background: var(--accent-soft); }}
      .cover .meta {{ margin-top: auto; display: flex; gap: 5mm; flex-wrap: wrap; }}
      .cover .chip {{ padding: 2.6mm 6mm; border: 1px solid currentColor; border-radius: 20mm;
                      font-size: 9.5pt; color: var(--accent-soft); }}
      .cover .cnote {{ margin-top: 7mm; font-size: 9pt; opacity: .62; line-height: 1.6; }}

      h2 {{ font-size: 16pt; font-weight: 900; color: var(--ink); }}
      .callout {{ border: 1.6px solid var(--accent); border-radius: 3mm; padding: 6mm 7mm;
                  margin-bottom: 6mm; background: var(--callout-bg); page-break-inside: avoid; }}
      .callout h2 {{ font-size: 13.5pt; margin-bottom: 2.5mm; }}
      .callout p {{ font-size: 10.5pt; line-height: 1.65; }}
      .callout .q {{ margin-top: 3.5mm; padding-inline-start: 4mm;
                     border-inline-start: 2px solid var(--accent); font-size: 10pt;
                     color: var(--muted); line-height: 1.6; }}
      .callout p + p {{ margin-top: 3mm; }}
      .blk {{ margin-bottom: 6mm; }}
      .blk h2 {{ font-size: 13pt; margin-bottom: 3mm; }}
      .blk ul {{ list-style: none; }}
      .blk li {{ font-size: 10.5pt; line-height: 1.55; margin-bottom: 2mm;
                 padding-inline-start: 6mm; position: relative; }}
      .blk li::before {{ content: ""; position: absolute; inset-inline-start: 0; top: 2.4mm;
                         width: 2.2mm; height: 2.2mm; border-radius: 50%; background: var(--accent); }}
      .toc {{ display: flex; align-items: center; gap: 4mm; padding: 2.6mm 0;
              border-bottom: 1px solid var(--rule); }}
      .tocn {{ flex: 0 0 auto; width: 8mm; height: 8mm; border-radius: 50%; border: 1px solid var(--accent);
               display: flex; align-items: center; justify-content: center;
               font-size: 9.5pt; font-weight: 700; color: var(--ink); }}
      .toct {{ flex: 1; font-size: 11.5pt; font-weight: 700; color: var(--ink); }}
      .tocc {{ font-size: 9pt; color: var(--muted); }}

      .sechead {{ display: flex; gap: 5mm; align-items: flex-start; border-top: 2px solid var(--accent);
                  padding-top: 3mm; margin: 3mm 0; page-break-after: avoid; page-break-inside: avoid; }}
      .secn {{ flex: 0 0 auto; width: 9.5mm; height: 9.5mm; border-radius: 50%;
               background: var(--ink); color: var(--accent-soft); display: flex;
               align-items: center; justify-content: center; font-size: 12pt; font-weight: 900; }}
      .secintro {{ margin-top: 1.5mm; font-size: 10pt; color: var(--muted); line-height: 1.55; }}

      .step {{ page-break-inside: avoid; margin-bottom: 5mm; }}
      .sthead {{ display: flex; align-items: center; gap: 3.5mm; }}
      .stn {{ flex: 0 0 auto; width: 9mm; height: 9mm; border-radius: 50%;
              background: var(--accent-soft); border: 1.4px solid var(--ink);
              display: flex; align-items: center; justify-content: center;
              font-size: 10.5pt; font-weight: 900; color: var(--ink); }}
      .sthead h3 {{ font-size: 12.5pt; font-weight: 900; color: var(--ink); }}
      .sttext {{ margin: 2mm 0 2.5mm; font-size: 10pt; line-height: 1.55; }}
      .sttext b, .lgt b {{ color: var(--ink); font-weight: 900; }}
      figure {{ text-align: center; line-height: 0; }}
      figure img {{ width: {fig.get("width","152mm")}; border-radius: {fig.get("radius","2mm")}; }}
      .legend {{ margin: 2.5mm auto 0; display: grid; grid-template-columns: 1fr 1fr;
                 gap: 1.2mm 6mm; max-width: {fig.get("width","152mm")}; }}
      .lg {{ display: flex; gap: 2.5mm; align-items: flex-start; }}
      .lgn {{ flex: 0 0 auto; width: 5.6mm; height: 5.6mm; border-radius: 50%;
              background: var(--accent-soft); border: 1px solid var(--ink); display: flex;
              align-items: center; justify-content: center; font-size: 8pt; font-weight: 900;
              color: var(--ink); margin-top: .4mm; }}
      .lgt {{ font-size: 9pt; line-height: 1.4; }}

      .backhead {{ page-break-before: always; margin-bottom: 5mm; }}
      .card {{ border: 1px solid var(--rule); border-radius: 3mm; padding: 6mm 7mm;
               margin-bottom: 6mm; page-break-inside: avoid; }}
      .card h3 {{ font-size: 12.5pt; font-weight: 900; color: var(--ink); margin-bottom: 3mm; }}
      .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2.4mm 6mm; }}
      .gi {{ display: flex; gap: 3mm; font-size: 10.5pt; }}
      .gi span:first-child {{ flex: 0 0 auto; width: 6.5mm; height: 6.5mm; border-radius: 50%;
              border: 1px solid var(--accent); display: flex; align-items: center;
              justify-content: center; font-size: 9pt; font-weight: 700; color: var(--ink); }}
      .chk {{ display: flex; gap: 3mm; font-size: 10.5pt; margin-bottom: 2.4mm; align-items: flex-start; }}
      .chk .box {{ flex: 0 0 auto; width: 4.6mm; height: 4.6mm; border: 1.4px solid var(--accent);
                   border-radius: 1mm; margin-top: .6mm; }}
      .final {{ margin-top: 4mm; text-align: center; font-size: 12.5pt; font-weight: 900;
                color: var(--ink); border-top: 2px solid var(--accent); padding-top: 5mm; }}
      .note {{ font-size: 9.5pt; color: var(--muted); line-height: 1.6; }}
    </style>
  </head>
  <body>
    <section class="cover">
      <div class="brand">{cov.get("brand","")}</div>
      <h1>{cov.get("title","")}</h1>
      <div class="sub">{cov.get("subtitle","")}</div>
      <div class="rule"></div>
      <div class="meta">{chips}</div>
      {f'<div class="cnote">{cov["note"]}</div>' if cov.get("note") else ""}
    </section>

{front}
{chr(10).join(body)}
{back}
  </body>
</html>
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content"); ap.add_argument("theme")
    ap.add_argument("figdir"); ap.add_argument("out")
    ap.add_argument("--embed", action="store_true", help="inline figures as data URIs")
    a = ap.parse_args()
    content = json.load(open(a.content, encoding="utf-8"))
    theme = json.load(open(a.theme, encoding="utf-8"))

    steps = sum(len(s["steps"]) for s in content["sections"])
    html = render(content, theme, a.figdir, a.embed, os.path.dirname(os.path.abspath(a.out)) or ".")
    open(a.out, "w", encoding="utf-8").write(html)
    print(f"{a.out}: {os.path.getsize(a.out):,} bytes | {len(content['sections'])} sections | {steps} steps")

if __name__ == "__main__":
    main()
