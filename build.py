#!/usr/bin/env python3
"""Build the static site from content/.

Each slide is one file in content/lesson-N/NN-slug.html with a front-matter
header and four parts (lead, key, prose, code). This script writes one real
HTML page per slide, so search engines see the full text without running
JavaScript, plus the home page, lesson overviews, sitemap.xml and robots.txt.

Run:  python build.py
"""
import datetime
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
BASE = "https://linearalgebra.steppeschool.com"
SITE = "Linear Algebra, Live"
BRYTHON = "https://cdn.jsdelivr.net/npm/brython@3.12.4/brython.min.js"
FONTS = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700"
         "&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap")
SIGNUP = "https://www.steppeschool.com/offers/JwLxrqg8/checkout"
TODAY = datetime.date.today().isoformat()

LESSONS = [
    {"n": 1, "dir": "lesson-1", "title": "Columns first", "chapter": "Strang, chapter 1",
     "sections": "Strang §1.1, §1.3, §2.1, §2.4, §5.3, §8.1",
     "summary": "Linear combinations, Ax as a mix of columns, the column space, row and column pictures, "
                "matrices that move the plane, and why AB is not BA."},
    {"n": 2, "dir": "lesson-2", "title": "Elimination and A = LU", "chapter": "Strang, chapter 2",
     "sections": "Strang §2.2, §2.3, §2.6",
     "summary": "How a computer solves Ax = b: subtract rows until the system is a triangle, solve from the bottom up, "
                "and record the steps as A = LU."},
    {"n": 3, "dir": "lesson-3", "title": "Inverses, transposes and permutations", "chapter": "Strang, chapter 2",
     "sections": "Strang §2.5, §2.7",
     "summary": "The matrix that undoes A, when it exists, how Gauss-Jordan finds it, what the transpose does, "
                "and the matrices that reorder rows."},
    {"n": 4, "dir": "lesson-4", "title": "The four subspaces", "chapter": "Strang, chapter 3",
     "sections": "Strang §3.1 to §3.5",
     "summary": "Subspaces, the nullspace, pivot and free columns, the complete solution to Ax = b, "
                "independence and dimension, and the big picture of the four subspaces."},
]
for _l, _c in zip(LESSONS, [1, 2, 2, 3]):
    _l["ch"] = _c
CHAPTERS = [
    {"n": 1, "title": "Introduction to vectors"},
    {"n": 2, "title": "Solving linear equations"},
    {"n": 3, "title": "Vector spaces and subspaces"},
    {"n": 4, "title": "Orthogonality", "planned": ["Orthogonality and least squares"]},
    {"n": 5, "title": "Determinants", "planned": ["Determinants"]},
    {"n": 6, "title": "Eigenvalues and eigenvectors", "planned": ["Eigenvalues and eigenvectors"]},
    {"n": 7, "title": "The singular value decomposition", "planned": ["SVD and PCA"]},
]
PLANNED = [(t, f"Chapter {c['n']}") for c in CHAPTERS for t in c.get("planned", [])]
BUILT = []   # filled in main(): list of (lesson, slides, practice)


def chapter_of(lesson):
    return next(c for c in CHAPTERS if c["n"] == lesson["ch"])


def topnav(prefix, lesson=None, steps_html=""):
    """Top bar: course name, chapter menu, lesson menu, slide steps."""
    built = [l for l, _, _ in BUILT]
    groups = ""
    for c in CHAPTERS:
        ls = [l for l in built if l["ch"] == c["n"]]
        cur = lesson is not None and c["n"] == lesson["ch"]
        items = "".join(
            f'<a class="menu-item{" on" if lesson is not None and l["n"] == lesson["n"] else ""}" href="{prefix}{l["dir"]}/">Lesson {l["n"]} · {e(l["title"])}</a>' for l in ls)
        items += "".join(f'<span class="menu-item soon">{e(t)} · coming soon</span>' for t in c.get("planned", []))
        groups += f'<div class="menu-group{" on" if cur else ""}"><span class="menu-h">Chapter {c["n"]} · {e(c["title"])}</span>{items}</div>'
    if lesson is None:
        ch_label = "Chapters"
    else:
        ch = chapter_of(lesson)
        ch_label = f'Chapter {ch["n"]}<span class="hide-sm"> · {e(ch["title"])}</span>'
    nav = f'<details class="menu"><summary>{ch_label}</summary><div class="menu-list">{groups}</div></details>'
    if lesson is not None:
        same = [l for l in built if l["ch"] == lesson["ch"]]
        _, slides, practice = next(t for t in BUILT if t[0]["n"] == lesson["n"])
        items = "".join(
            f'<a class="menu-item{" on" if l["n"] == lesson["n"] else ""}" href="{prefix}{l["dir"]}/">Lesson {l["n"]} · {e(l["title"])}</a>' for l in same)
        inside = "".join(f'<a class="menu-item sub" href="{prefix}{lesson["dir"]}/{s["slug"]}/">{j + 1}. {e(s["seo_title"])}</a>' for j, s in enumerate(slides))
        if practice:
            inside += f'<a class="menu-item sub" href="{prefix}{lesson["dir"]}/practice/">✎ Examples and problems</a>'
        nav += (f'<span class="sep">›</span><details class="menu"><summary>Lesson {lesson["n"]}<span class="hide-sm"> · {e(lesson["title"])}</span></summary>'
                f'<div class="menu-list"><div class="menu-group"><span class="menu-h">Chapter {lesson["ch"]} lessons</span>{items}</div>'
                f'<div class="menu-group"><span class="menu-h">In this lesson</span>{inside}</div></div></details>')
    return f"""<header class="top">
  <div class="topnav"><a class="brand" href="{prefix}">{SITE}</a><nav class="crumbnav" aria-label="Chapters and lessons">{nav}</nav></div>
  {f'<nav class="steps" aria-label="Steps in this lesson">{steps_html}</nav>' if steps_html else ""}
</header>
"""


def steps_for(lesson, slides, practice, current, rel):
    """Numbered step links for the slides plus a practice step. rel = path from current page to the lesson folder."""
    out = "".join(
        f'<a class="step{" on" if current == t["slug"] else ""}" href="{rel}{t["slug"]}/" data-slug="{t["slug"]}"'
        f'{" aria-current=\"page\"" if current == t["slug"] else ""} title="{e(t["seo_title"])}">{j + 1}</a>'
        for j, t in enumerate(slides))
    if practice:
        on = current == "practice"
        out += (f'<a class="step practice{" on" if on else ""}" href="{rel}practice/"{" aria-current=\"page\"" if on else ""} '
                f'title="Examples and problems">✎</a>')
    return out

e = html.escape


def parse(path):
    text = path.read_text(encoding="utf-8")
    _, head, body = text.split("---\n", 2)
    meta = {}
    for line in head.strip().splitlines():
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip()
    parts = dict(re.findall(r"<!-- (\w+) -->\n(.*?)(?=\n<!-- \w+ -->\n|\Z)", body, re.S))
    meta.update({k: v.strip("\n") for k, v in parts.items()})
    return meta


def head(title, description, url, prefix, og_type="website", jsonld=None):
    ld = f'\n<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{prefix}assets/lesson.css">{ld}
</head>
<body>
"""


def footer():
    return f"""<footer class="foot">
  Follows the order and notation of Gilbert Strang, <i>Introduction to Linear Algebra</i>, 5th edition (2016); § numbers refer to that book.
  Explanations, examples and code are original. Made by <a href="https://www.steppeschool.com">Steppeschool</a>.
</footer>
"""


PROVIDER = {"@type": "Organization", "name": "Steppeschool", "url": "https://www.steppeschool.com"}
COURSE = {"@type": "Course", "name": SITE, "url": BASE + "/",
          "description": "Interactive linear algebra lessons with live Python, following Gilbert Strang's Introduction to Linear Algebra.",
          "provider": PROVIDER}


def slide_page(lesson, slides, i, next_lesson=None, practice=None):
    s = slides[i]
    prefix = "../../"
    url = f"{BASE}/{lesson['dir']}/{s['slug']}/"
    title = f"{s['seo_title']} | {SITE}"
    jsonld = [
        {"@context": "https://schema.org", "@type": "LearningResource", "name": s["seo_title"],
         "headline": s["title"], "description": s["description"], "url": url, "inLanguage": "en",
         "learningResourceType": "Interactive lesson", "educationalLevel": "Beginner",
         "isAccessibleForFree": True, "author": PROVIDER, "isPartOf": COURSE},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE, "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": f"Lesson {lesson['n']}: {lesson['title']}", "item": f"{BASE}/{lesson['dir']}/"},
            {"@type": "ListItem", "position": 3, "name": s["seo_title"], "item": url}]},
    ]
    steps = steps_for(lesson, slides, practice, s["slug"], "../")
    prev = (f'<a class="btn" id="prev" href="../{slides[i - 1]["slug"]}/">← Back</a>' if i > 0
            else f'<a class="btn" id="prev" href="../">← Overview</a>')
    if i < len(slides) - 1:
        nxt = f'<a class="btn primary" id="next" href="../{slides[i + 1]["slug"]}/">Next →</a>'
    elif practice:
        nxt = '<a class="btn primary" id="next" href="../practice/">Practice →</a>'
    elif next_lesson:
        nxt = f'<a class="btn primary" id="next" href="../../{next_lesson["dir"]}/">Lesson {next_lesson["n"]} →</a>'
    else:
        nxt = '<a class="btn primary" id="next" href="../../">All lessons →</a>'

    config = {"slug": s["slug"], "lesson": lesson["dir"], "assets": prefix + "assets/",
              "preview": json.loads(s["preview"]), "check": s["check"]}
    return head(title, s["description"], url, prefix, "article", jsonld) + topnav(prefix, lesson, steps) + f"""

<main class="app">
  <article class="page">
    <div class="kicker">{e(s['kicker'])}</div>
    <h1>{e(s['title'])}</h1>
    <p class="lead">{s['lead']}</p>
    <div class="key">{s['key']}</div>
    <div class="prose">
{s['prose']}
    </div>
    <div class="exercise" id="exercise">
      <span class="tag">Exercise</span>
      <span class="task">{e(s['task'])}</span>
      <span class="hint" id="hint">Edit the code in the lab and press Run.</span>
    </div>
    <div class="nav">
      {prev}
      <span class="count">{i + 1} / {len(slides)}</span>
      {nxt}
    </div>
  </article>

  <aside class="lab" aria-label="Lab">
    <figure class="figure" style="margin:0">
      <div class="plane"><canvas id="cv" aria-label="The plane"></canvas><div class="tablebox" id="tablebox" hidden></div></div>
      <figcaption class="figcap"><div class="legend" id="legend"></div><div class="readout" id="readout"></div></figcaption>
    </figure>
    <div class="editor-card">
      <div class="bar">
        <span class="file">slide_{i + 1}.py</span>
        <span class="status" id="pystatus">Loading Python…</span>
        <button class="btn" id="reset">Reset</button>
        <button class="btn primary" id="run" disabled>Run ▸</button>
      </div>
      <div class="editor">
        <div class="gutter" id="gutter">1</div>
        <div class="code" id="codewrap">
          <pre id="hl" aria-hidden="true"></pre>
          <textarea id="src" spellcheck="false" autocapitalize="off" autocomplete="off" aria-label="Python code">{e(s['code'])}</textarea>
        </div>
      </div>
      <div class="outhead"><span>Output · Ctrl+Enter runs</span><button id="clear">Clear</button></div>
      <pre class="out" id="out"><span class="sys">Press Run to execute this slide's code. Ctrl+Enter works too.</span></pre>
    </div>
  </aside>
</main>
{footer()}
<script>window.SLIDE = {json.dumps(config, ensure_ascii=False)};</script>
<script id="brython" src="{BRYTHON}" defer></script>
<script src="{prefix}assets/lab.js" defer></script>
<script src="{prefix}assets/nav.js" defer></script>
</body>
</html>
"""


def practice_page(lesson, slides, pr, next_lesson):
    prefix = "../../"
    url = f"{BASE}/{lesson['dir']}/practice/"
    title = f"{pr['seo_title']} | {SITE}"
    jsonld = [
        {"@context": "https://schema.org", "@type": "LearningResource", "name": pr["seo_title"],
         "description": pr["description"], "url": url, "inLanguage": "en",
         "learningResourceType": "Practice problems", "educationalLevel": "Beginner",
         "isAccessibleForFree": True, "author": PROVIDER, "isPartOf": COURSE},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE, "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": f"Lesson {lesson['n']}: {lesson['title']}", "item": f"{BASE}/{lesson['dir']}/"},
            {"@type": "ListItem", "position": 3, "name": "Examples and problems", "item": url}]},
    ]
    steps = steps_for(lesson, slides, pr, "practice", "../")
    prev = f'<a class="btn" id="prev" href="../{slides[-1]["slug"]}/">← Back</a>'
    nxt = (f'<a class="btn primary" id="next" href="../../{next_lesson["dir"]}/">Lesson {next_lesson["n"]} →</a>' if next_lesson
           else '<a class="btn primary" id="next" href="../../">All lessons →</a>')
    config = {"slug": "practice", "lesson": lesson["dir"], "assets": prefix + "assets/",
              "preview": {"kind": "transform", "M": [[1, 0], [0, 1]]}, "check": "false"}
    return head(title, pr["description"], url, prefix, "article", jsonld) + topnav(prefix, lesson, steps) + f"""
<main class="app">
  <article class="page">
    <div class="kicker">Lesson {lesson['n']} · Examples and problems</div>
    <h1>Practice: {e(lesson['title'])}</h1>
    <p class="lead">{pr['intro']}</p>
    <h2 class="practice-h">Worked examples</h2>
    <div class="examples">
{pr['examples']}
    </div>
    <h2 class="practice-h">Problems</h2>
    <div class="problems">
{pr['problems']}
    </div>
    <div class="signup">
      <p><b>Want more problems?</b> More practice sets are on the way. Get a free Steppeschool account and we'll tell you when they're out.</p>
      <a class="btn primary" href="{SIGNUP}">Get a free account</a>
    </div>
    <div class="nav">
      {prev}
      <span class="count">Practice</span>
      {nxt}
    </div>
  </article>

  <aside class="lab" aria-label="Lab">
    <figure class="figure" style="margin:0">
      <div class="plane"><canvas id="cv" aria-label="The plane"></canvas><div class="tablebox" id="tablebox" hidden></div></div>
      <figcaption class="figcap"><div class="legend" id="legend"></div><div class="readout" id="readout"></div></figcaption>
    </figure>
    <div class="editor-card">
      <div class="bar">
        <span class="file">sandbox.py</span>
        <span class="status" id="pystatus">Loading Python…</span>
        <button class="btn" id="reset">Reset</button>
        <button class="btn primary" id="run" disabled>Run ▸</button>
      </div>
      <div class="editor">
        <div class="gutter" id="gutter">1</div>
        <div class="code" id="codewrap">
          <pre id="hl" aria-hidden="true"></pre>
          <textarea id="src" spellcheck="false" autocapitalize="off" autocomplete="off" aria-label="Python code">{e(pr['code'])}</textarea>
        </div>
      </div>
      <div class="outhead"><span>Output · Ctrl+Enter runs</span><button id="clear">Clear</button></div>
      <pre class="out" id="out"><span class="sys">A sandbox: check your answers here. Ctrl+Enter runs.</span></pre>
    </div>
  </aside>
</main>
{footer()}
<script>window.SLIDE = {json.dumps(config, ensure_ascii=False)};</script>
<script id="brython" src="{BRYTHON}" defer></script>
<script src="{prefix}assets/lab.js" defer></script>
<script src="{prefix}assets/nav.js" defer></script>
</body>
</html>
"""


def lesson_page(lesson, slides, practice=None):
    prefix = "../"
    url = f"{BASE}/{lesson['dir']}/"
    title = f"Lesson {lesson['n']}: {lesson['title']} | {SITE}"
    desc = f"Interactive linear algebra lesson {lesson['n']}: {lesson['summary']} Every slide has live Python."
    cards = "".join(
        f'<a class="card" href="{s["slug"]}/"><span class="n">{j + 1:02d} · {e(s["kicker"])}</span>'
        f'<h3>{e(s["seo_title"])}</h3><p>{e(s["description"])}</p></a>' for j, s in enumerate(slides))
    jsonld = {"@context": "https://schema.org", "@type": "ItemList", "name": title,
              "itemListElement": [{"@type": "ListItem", "position": j + 1, "url": f"{url}{s['slug']}/", "name": s["seo_title"]}
                                  for j, s in enumerate(slides)]}
    if practice:
        cards += (f'<a class="card practice-card" href="practice/"><span class="n">✎ · Practice</span>'
                  f'<h3>Worked examples and problems</h3><p>{e(practice["description"])}</p></a>')
    return head(title, desc, url, prefix, jsonld=jsonld) + topnav(prefix, lesson) + f"""<div class="home">
  <section class="hero">
    <div class="kicker">Chapter {lesson['ch']} · Lesson {lesson['n']} · {e(lesson['sections'])}</div>
    <h1>{e(lesson['title'])}</h1>
    <p>{e(lesson['summary'])} {len(slides)} short slides, then worked examples and problems. Each slide has an everyday picture, a worked example and Python you can run right on the page.</p>
    <div class="cta"><a class="btn primary" href="{slides[0]['slug']}/">Start the lesson →</a></div>
  </section>
  <h2 class="section-title">Slides</h2>
  <div class="cards">{cards}</div>
</div>
{footer()}<script src="{prefix}assets/nav.js" defer></script>
</body>
</html>
"""


def home_page(lessons_built):
    url = BASE + "/"
    title = f"{SITE}: Interactive Linear Algebra with Python"
    desc = ("Learn linear algebra by running it. Short visual lessons with live Python in your browser, "
            "following Gilbert Strang's Introduction to Linear Algebra. Built for robotics and engineering.")
    cards = ""
    k = len(lessons_built)
    for c in CHAPTERS:
        row = ""
        for lesson, slides, _ in lessons_built:
            if lesson["ch"] == c["n"]:
                row += (f'<a class="card" href="{lesson["dir"]}/"><span class="n">Lesson {lesson["n"]} · {e(lesson["sections"])}</span>'
                        f'<h3>{e(lesson["title"])}</h3><p>{e(lesson["summary"])}</p></a>')
        for name in c.get("planned", []):
            k += 1
            row += (f'<div class="card soon"><span class="n">Lesson {k} · coming soon</span><h3>{e(name)}</h3></div>')
        cards += f'<h3 class="chapter-title" id="chapter-{c["n"]}">Chapter {c["n"]} · {e(c["title"])}</h3><div class="cards">{row}</div>'
    first = lessons_built[0]
    jsonld = dict(COURSE, **{"@context": "https://schema.org", "inLanguage": "en", "isAccessibleForFree": True})
    return head(title, desc, url, "", jsonld=jsonld) + topnav("") + f"""<div class="home">
  <section class="hero">
    <div class="kicker">Steppeschool · free interactive course</div>
    <h1>Linear algebra you can run.</h1>
    <p>Short visual lessons. Read a slide, change the Python underneath, press Run and watch the plane move. The order follows Gilbert Strang's <i>Introduction to Linear Algebra</i>, and the examples come from robotics and engineering.</p>
    <div class="cta"><a class="btn primary" href="{first[0]['dir']}/{first[1][0]['slug']}/">Start lesson 1 →</a><a class="btn" href="#lessons">See all lessons</a></div>
  </section>
  <h2 class="section-title" id="lessons">Lessons</h2>
  {cards}
  <h2 class="section-title">How it works</h2>
  <div class="panel">
    <p>Every slide explains one idea with an everyday picture first: a boat with two thrusters, a shopping basket, a mirror. Then comes the maths, a worked example with real numbers, and where the idea shows up in drones, IMUs and robot arms.</p>
    <p>Next to the text is a lab. The Python runs in your browser, nothing to install. Functions like <code>show(A)</code>, <code>combo(A, x, b)</code>, <code>nullpic(A, x)</code> and <code>four(A)</code> draw on the plane, and <code>table(...)</code> lays out matrices with their pivots. Each slide ends with a small exercise that checks your answer.</p>
  </div>
  <div class="signup">
    <p><b>New lessons by email.</b> Get a free Steppeschool account and we'll tell you when the next lesson is out. It also includes the free STM32 motor control mini-course and the Kalman filter notebook.</p>
    <a class="btn primary" href="{SIGNUP}">Get a free account</a>
  </div>
</div>
{footer()}<script src="assets/nav.js" defer></script>
</body>
</html>
"""


def redirect_page(target):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{SITE}</title>
<link rel="canonical" href="{BASE}{target}"><meta http-equiv="refresh" content="0; url={target}">
<meta name="robots" content="noindex"></head>
<body><a href="{target}">Continue to {SITE}</a></body></html>
"""


def main():
    urls = [BASE + "/"]
    built = []
    available = [l for l in LESSONS if any((ROOT / "content" / l["dir"]).glob("[0-9]*.html"))]
    for lesson in available:
        files = sorted((ROOT / "content" / lesson["dir"]).glob("[0-9]*.html"))
        pf = ROOT / "content" / lesson["dir"] / "practice.html"
        BUILT.append((lesson, [parse(f) for f in files], parse(pf) if pf.exists() else None))
    built = BUILT
    for li, (lesson, slides, practice) in enumerate(BUILT):
        next_lesson = BUILT[li + 1][0] if li + 1 < len(BUILT) else None
        out = ROOT / lesson["dir"]
        out.mkdir(exist_ok=True)
        (out / "index.html").write_text(lesson_page(lesson, slides, practice), encoding="utf-8")
        urls.append(f"{BASE}/{lesson['dir']}/")
        for i, s in enumerate(slides):
            d = out / s["slug"]
            d.mkdir(exist_ok=True)
            (d / "index.html").write_text(slide_page(lesson, slides, i, next_lesson, practice), encoding="utf-8")
            urls.append(f"{BASE}/{lesson['dir']}/{s['slug']}/")
        if practice:
            d = out / "practice"
            d.mkdir(exist_ok=True)
            (d / "index.html").write_text(practice_page(lesson, slides, practice, next_lesson), encoding="utf-8")
            urls.append(f"{BASE}/{lesson['dir']}/practice/")
    (ROOT / "index.html").write_text(home_page(built), encoding="utf-8")
    # old single-page URL from the first prototype
    (ROOT / "lessons").mkdir(exist_ok=True)
    (ROOT / "lessons" / "01-columns-first.html").write_text(
        redirect_page(f"/{LESSONS[0]['dir']}/{built[0][1][0]['slug']}/"), encoding="utf-8")
    sitemap = "".join(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sitemap}</urlset>\n',
        encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
    print(f"Built {len(urls)} pages.")


if __name__ == "__main__":
    main()
