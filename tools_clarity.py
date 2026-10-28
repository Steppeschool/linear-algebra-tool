"""Extract what a student actually reads on a lesson, as plain text, for an independent clarity review.

Usage: python3 tools_clarity.py <lesson-url-folder> [out.txt]
e.g.   python3 tools_clarity.py orthogonality-and-least-squares /tmp/l5.txt

Reads the built pages (not the content sources), so the reviewer sees exactly what is published:
headline, lead, key formula, key ideas, explanation, worked examples, problems (solutions kept,
marked as hidden), and the exercise with its starter code. No author notes, no build files.
"""
import html, pathlib, re, sys

ROOT = pathlib.Path(__file__).parent


def text(fragment):
    f = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", fragment, flags=re.S)
    f = re.sub(r'<span class="mx" style="grid-template-columns:repeat\((\d+),auto\)">(.*?)</span></span>',
               lambda m: matrix(m.group(1), m.group(2) + "</span>"), f, flags=re.S)
    f = re.sub(r"<summary>.*?</summary>", "[hidden solution, shown when the student clicks]: ", f, flags=re.S)
    f = re.sub(r"</(p|div|li|h3|h2|h1|section|tr)>", "\n", f)
    f = re.sub(r"<li>", "- ", f)
    f = re.sub(r"<[^>]+>", "", f)
    f = html.unescape(f)
    return re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t]+", " ", f)).strip()


def matrix(cols, cells):
    vals = re.findall(r"<span[^>]*>(.*?)</span>", cells)
    n = int(cols)
    rows = [vals[i:i + n] for i in range(0, len(vals), n)]
    return "[" + "; ".join(" ".join(r) for r in rows) + "]"


def page(path):
    s = path.read_text(encoding="utf-8")
    art = re.search(r'<article class="page">(.*?)</article>', s, re.S)
    out = text(art.group(1)) if art else ""
    rv = re.search(r'<details class="review">(.*?)</details>', s, re.S)
    ex = re.search(r'<div class="exercise[^"]*" id="exercise">(.*?)</div>\s*</div>', s, re.S)
    code = re.search(r'<textarea[^>]*id="src"[^>]*>(.*?)</textarea>', s, re.S)
    if ex:
        out += "\n\nEXERCISE: " + text(ex.group(1))
    if code:
        out += "\n\nSTARTER CODE (the student edits this and presses Run; a picture appears beside it):\n" + html.unescape(code.group(1))
    return out


def main():
    folder = ROOT / sys.argv[1]
    order = re.findall(r'<a class="card pic(?: practice-card)?" href="([^"]+)/"', (folder / "index.html").read_text(encoding="utf-8"))
    parts = []
    for i, slug in enumerate(order, 1):
        parts.append(f"\n\n========== PAGE {i}: {slug} ==========\n\n" + page(folder / slug / "index.html"))
    out = "".join(parts).strip() + "\n"
    if len(sys.argv) > 2:
        pathlib.Path(sys.argv[2]).write_text(out, encoding="utf-8")
    else:
        print(out)


if __name__ == "__main__":
    main()
