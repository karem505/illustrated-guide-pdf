#!/usr/bin/env python3
"""Render guide.html to PDF.

    python3 topdf.py guide.html out.pdf [--theme theme.json] [--footer "TEXT"]

Uses headless Chrome. If puppeteer-core is available it is preferred, because it
is the only way to get real page numbers in the footer; otherwise it falls back
to Chrome's own --print-to-pdf, which produces the same pages minus the footer.
"""
import argparse, glob, json, os, shutil, subprocess, sys, tempfile

CHROMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
           "microsoft-edge", "/usr/bin/google-chrome",
           "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]

PUPPETEER_HINTS = [
    "~/node_modules/puppeteer-core", "./node_modules/puppeteer-core",
    "~/projects/*/node_modules/puppeteer-core", "~/*/node_modules/puppeteer-core",
]

def find_chrome():
    for c in CHROMES:
        p = shutil.which(c) or (c if os.path.exists(c) else None)
        if p:
            return p
    sys.exit("no Chrome/Chromium found — install one, or set CHROME_PATH")

def find_puppeteer():
    if os.environ.get("PUPPETEER_CORE"):
        return os.environ["PUPPETEER_CORE"]
    for h in PUPPETEER_HINTS:
        for m in glob.glob(os.path.expanduser(h)):
            entry = os.path.join(m, "lib/esm/puppeteer/puppeteer-core.js")
            if os.path.exists(entry):
                return entry
    return None

JS = r'''
import puppeteer from "%(mod)s";
const b = await puppeteer.launch({executablePath: process.env.CHROME_BIN,
  headless: "new", args: ["--no-sandbox", "--font-render-hinting=none"]});
const p = await b.newPage();
const problems = [];
p.on("pageerror", e => problems.push("JS " + e.message));
p.on("requestfailed", r => problems.push("MISSING " + r.url().slice(0, 120)));
await p.goto("file://%(html)s", {waitUntil: "networkidle0"});
await p.evaluate(() => document.fonts.ready);
await p.pdf({path: "%(pdf)s", format: "%(size)s", printBackground: true,
  displayHeaderFooter: %(hf)s, headerTemplate: "<div></div>",
  footerTemplate: `<div style="width:100%%;font-size:7pt;color:#8b8578;padding:0 %(ml)s;
    font-family:Arial,sans-serif;display:flex;justify-content:space-between;">
    <span>%(footer)s</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`,
  margin: {top:"%(mt)s", bottom:"%(mb)s", left:"%(ml)s", right:"%(mr)s"}});
console.log(problems.length ? "PROBLEMS:\n" + problems.slice(0,8).join("\n") : "clean");
await b.close();
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html"); ap.add_argument("pdf")
    ap.add_argument("--theme"); ap.add_argument("--footer", default="")
    ap.add_argument("--no-puppeteer", action="store_true")
    a = ap.parse_args()

    size, m = "A4", {"top": "12mm", "right": "12mm", "bottom": "14mm", "left": "12mm"}
    if a.theme:
        t = json.load(open(a.theme, encoding="utf-8")).get("page", {})
        size = t.get("size", size); m.update(t.get("margin", {}))

    chrome = os.environ.get("CHROME_PATH") or find_chrome()
    html = os.path.abspath(a.html); pdf = os.path.abspath(a.pdf)
    mod = None if a.no_puppeteer else find_puppeteer()

    if mod:
        js = JS % {"mod": mod, "html": html, "pdf": pdf, "size": size,
                   "hf": "true" if a.footer else "false", "footer": a.footer,
                   "mt": m["top"], "mb": m["bottom"], "ml": m["left"], "mr": m["right"]}
        with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as f:
            f.write(js); script = f.name
        env = dict(os.environ, CHROME_BIN=chrome)
        r = subprocess.run(["node", script], capture_output=True, text=True, env=env)
        os.unlink(script)
        if r.returncode == 0:
            print(r.stdout.strip() or "clean")
        else:
            print("puppeteer failed, falling back to Chrome CLI:\n" + r.stderr.strip()[:400],
                  file=sys.stderr)
            mod = None
    if not mod:
        # Chrome's own printer. Honours @page size/margins; no page numbers.
        subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
                        "--no-pdf-header-footer", f"--print-to-pdf={pdf}",
                        f"file://{html}"], check=False, capture_output=True)
        if a.footer:
            print("note: page numbers need puppeteer-core; rendered without a footer",
                  file=sys.stderr)

    if not os.path.exists(pdf):
        sys.exit("PDF was not produced")
    info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    pages = next((l.split(":")[1].strip() for l in info.splitlines() if l.startswith("Pages")), "?")
    print(f"{pdf}: {os.path.getsize(pdf):,} bytes, {pages} pages")

if __name__ == "__main__":
    main()
