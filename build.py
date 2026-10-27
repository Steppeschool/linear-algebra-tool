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
    {"n": 1, "dir": "lesson-1", "title": "Columns first",
     "sections": "Strang §1.1, §1.3, §2.1, §2.4, §5.3, §8.1",
     "summary": "Linear combinations, Ax as a mix of columns, the column space, row and column pictures, "
                "matrices that move the plane, and why AB is not BA."},
]
PLANNED = [
    ("Elimination and A = LU", "§2.2, §2.3, §2.6"),
    ("Inverses, transposes and permutations", "§2.5, §2.7"),
    ("The four subspaces", "Chapter 3"),
    ("Orthogonality and least squares", "Chapter 4"),
    ("Determinants", "Chapter 5"),
    ("Eigenvalues and eigenvectors", "Chapter 6"),
    ("SVD and PCA", "Chapter 7"),
]

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


def slide_page(lesson, slides, i):
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
    steps = "".join(
        f'<a class="step{" on" if j == i else ""}" href="../{t["slug"]}/" data-slug="{t["slug"]}"'
        f'{" aria-current=\"page\"" if j == i else ""} title="{e(t["seo_title"])}">{j + 1}</a>'
        for j, t in enumerate(slides))
    prev = (f'<a class="btn" id="prev" href="../{slides[i - 1]["slug"]}/">← Back</a>' if i > 0
            else f'<a class="btn" id="prev" href="../">← Overview</a>')
    nxt = (f'<a class="btn primary" id="next" href="../{slides[i + 1]["slug"]}/">Next →</a>' if i < len(slides) - 1
           else '<a class="btn primary" id="next" href="../../">All lessons →</a>')
    config = {"slug": s["slug"], "lesson": lesson["dir"], "assets": prefix + "assets/",
              "preview": json.loads(s["preview"]), "check": s["check"]}
    return head(title, s["description"], url, prefix, "article", jsonld) + f"""<header class="top">
  <div class="course"><b><a href="{prefix}" style="color:inherit;text-decoration:none">{SITE}</a></b><span>Lesson {lesson['n']} · {e(lesson['title'])} · Strang, chapter 1</span></div>
  <nav class="steps" aria-label="Slides in this lesson">{steps}</nav>
</header>

<main class="app">
  <article class="page">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{prefix}">All lessons</a> › <a href="../">Lesson {lesson['n']}</a></nav>
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
      <div class="plane"><canvas id="cv" aria-label="The plane"></canvas></div>
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
      <pre class="out" id="out"><span class="sys">Press Run. show(A), combo(A, x, b) and rowpic(A, b) draw on the plane.</span></pre>
    </div>
  </aside>
</main>
{footer()}
<script>window.SLIDE = {json.dumps(config, ensure_ascii=False)};</script>
<script id="brython" src="{BRYTHON}" defer></script>
<script src="{prefix}assets/lab.js" defer></script>
</body>
</html>
"""


def lesson_page(lesson, slides):
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
    return head(title, desc, url, prefix, jsonld=jsonld) + f"""<div class="home">
  <nav class="crumbs" aria-label="Breadcrumb" style="padding-top:8px"><a href="{prefix}">All lessons</a></nav>
  <section class="hero">
    <div class="kicker">Lesson {lesson['n']} · {e(lesson['sections'])}</div>
    <h1>{e(lesson['title'])}</h1>
    <p>{e(lesson['summary'])} Eight short slides. Each one has an everyday picture, a worked example and Python you can run right on the page.</p>
    <div class="cta"><a class="btn primary" href="{slides[0]['slug']}/">Start the lesson →</a></div>
  </section>
  <h2 class="section-title">Slides</h2>
  <div class="cards">{cards}</div>
</div>
{footer()}</body>
</html>
"""


def home_page(lessons_built):
    url = BASE + "/"
    title = f"{SITE}: Interactive Linear Algebra with Python"
    desc = ("Learn linear algebra by running it. Short visual lessons with live Python in your browser, "
            "following Gilbert Strang's Introduction to Linear Algebra. Built for robotics and engineering.")
    cards = ""
    for lesson, slides in lessons_built:
        cards += (f'<a class="card" href="{lesson["dir"]}/"><span class="n">Lesson {lesson["n"]} · {e(lesson["sections"])}</span>'
                  f'<h3>{e(lesson["title"])}</h3><p>{e(lesson["summary"])}</p></a>')
    for k, (name, secs) in enumerate(PLANNED, start=len(lessons_built) + 1):
        cards += (f'<div class="card soon"><span class="n">Lesson {k} · {e(secs)} · coming soon</span>'
                  f'<h3>{e(name)}</h3></div>')
    first = lessons_built[0]
    jsonld = dict(COURSE, **{"@context": "https://schema.org", "inLanguage": "en", "isAccessibleForFree": True})
    return head(title, desc, url, "", jsonld=jsonld) + f"""<div class="home">
  <section class="hero">
    <div class="kicker">Steppeschool · free interactive course</div>
    <h1>Linear algebra you can run.</h1>
    <p>Short visual lessons. Read a slide, change the Python underneath, press Run and watch the plane move. The order follows Gilbert Strang's <i>Introduction to Linear Algebra</i>, and the examples come from robotics and engineering.</p>
    <div class="cta"><a class="btn primary" href="{first[0]['dir']}/{first[1][0]['slug']}/">Start lesson 1 →</a><a class="btn" href="#lessons">See all lessons</a></div>
  </section>
  <h2 class="section-title" id="lessons">Lessons</h2>
  <div class="cards">{cards}</div>
  <h2 class="section-title">How it works</h2>
  <div class="panel">
    <p>Every slide explains one idea with an everyday picture first: a boat with two thrusters, a shopping basket, a mirror. Then comes the maths, a worked example with real numbers, and where the idea shows up in drones, IMUs and robot arms.</p>
    <p>Next to the text is a lab. The Python runs in your browser, nothing to install. Call <code>show(A)</code>, <code>combo(A, x, b)</code> or <code>rowpic(A, b)</code> and the plane redraws. Each slide ends with a small exercise that checks your answer.</p>
  </div>
  <div class="signup">
    <p><b>New lessons by email.</b> Get a free Steppeschool account and we'll tell you when the next lesson is out. It also includes the free STM32 motor control mini-course and the Kalman filter notebook.</p>
    <a class="btn primary" href="{SIGNUP}">Get a free account</a>
  </div>
</div>
{footer()}</body>
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
    for lesson in LESSONS:
        files = sorted((ROOT / "content" / lesson["dir"]).glob("*.html"))
        slides = [parse(f) for f in files]
        built.append((lesson, slides))
        out = ROOT / lesson["dir"]
        out.mkdir(exist_ok=True)
        (out / "index.html").write_text(lesson_page(lesson, slides), encoding="utf-8")
        urls.append(f"{BASE}/{lesson['dir']}/")
        for i, s in enumerate(slides):
            d = out / s["slug"]
            d.mkdir(exist_ok=True)
            (d / "index.html").write_text(slide_page(lesson, slides, i), encoding="utf-8")
            urls.append(f"{BASE}/{lesson['dir']}/{s['slug']}/")
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
