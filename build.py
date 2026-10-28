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
import shutil

ROOT = pathlib.Path(__file__).parent
BASE = "https://linearalgebra.steppeschool.com"
SITE = "Linear Algebra, Live"
BRYTHON = "https://cdn.jsdelivr.net/npm/brython@3.12.4/brython.min.js"
FONTS = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700"
         "&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap")
SIGNUP = "https://www.steppeschool.com/offers/JwLxrqg8/checkout"
TODAY = datetime.date.today().isoformat()

LESSONS = [
    {"n": 1, "dir": "lesson-1", "path": "vectors-and-matrices", "seo_title": "Vectors, Linear Combinations and Matrix Multiplication",
     "seo_desc": "Learn vectors, linear combinations, Ax as a mix of columns, the column space and matrix multiplication with interactive Python. Free lesson following Strang.", "title": "Columns first", "chapter": "Strang, chapter 1",
     "sections": "Strang §1.1, §1.3, §2.1, §2.4, §5.3, §8.1",
     "summary": "Linear combinations, Ax as a mix of columns, the column space, row and column pictures, "
                "matrices that move the plane, and why AB is not BA."},
    {"n": 2, "dir": "lesson-2", "path": "gaussian-elimination-and-lu", "seo_title": "Gaussian Elimination and LU Decomposition",
     "seo_desc": "Solve Ax = b by Gaussian elimination: pivots, back substitution, elimination matrices and A = LU, with live Python in your browser. Free lesson.", "title": "Elimination and A = LU", "chapter": "Strang, chapter 2",
     "sections": "Strang §2.2, §2.3, §2.6",
     "summary": "How a computer solves Ax = b: subtract rows until the system is a triangle, solve from the bottom up, "
                "and record the steps as A = LU."},
    {"n": 3, "dir": "lesson-3", "path": "inverse-transpose-permutation", "seo_title": "Inverse Matrix, Transpose and Permutation Matrices",
     "seo_desc": "The inverse matrix, the 2x2 inverse formula, Gauss-Jordan, transposes, symmetric and permutation matrices, with interactive Python. Free lesson.", "title": "Inverses, transposes and permutations", "chapter": "Strang, chapter 2",
     "sections": "Strang §2.5, §2.7",
     "summary": "The matrix that undoes A, when it exists, how Gauss-Jordan finds it, what the transpose does, "
                "and the matrices that reorder rows."},
    {"n": 4, "dir": "lesson-4", "path": "vector-spaces-and-four-subspaces", "seo_title": "Vector Spaces, Null Space and the Four Subspaces",
     "seo_desc": "Subspaces, the null space, rref and special solutions, the complete solution to Ax = b, basis, dimension and the four fundamental subspaces. Free lesson.", "title": "The four subspaces", "chapter": "Strang, chapter 3",
     "sections": "Strang §3.1 to §3.5",
     "summary": "Subspaces, the nullspace, pivot and free columns, the complete solution to Ax = b, "
                "independence and dimension, and the big picture of the four subspaces."},
    {"n": 5, "dir": "lesson-5", "path": "orthogonality-and-least-squares", "seo_title": "Orthogonality, Projections and Least Squares",
     "seo_desc": "Orthogonal subspaces, projection onto a line, projection matrices, least squares line fitting and Gram-Schmidt, with interactive Python. Free lesson.", "title": "Orthogonality and least squares", "chapter": "Strang, chapter 4",
     "sections": "Strang §4.1 to §4.4",
     "summary": "Perpendicular subspaces, projections, the best answer when Ax = b has no solution, "
                "fitting lines to data, and orthonormal bases built by Gram-Schmidt."},
    {"n": 6, "dir": "lesson-6", "path": "determinants", "seo_title": "Determinants: Area, Properties, Cofactors and Cramer's Rule",
     "seo_desc": "What the determinant measures, its three rules, computing it from pivots or cofactors, Cramer's rule, the inverse formula and cross products. Free lesson.", "title": "Determinants", "chapter": "Strang, chapter 5",
     "sections": "Strang §5.1 to §5.3",
     "summary": "The number that says how much a matrix stretches area and volume: its rules, how to compute it, "
                "Cramer's rule, the inverse formula, and areas, volumes and cross products."},
    {"n": 7, "dir": "lesson-7", "path": "eigenvalues-and-eigenvectors", "seo_title": "Eigenvalues and Eigenvectors: Intuition and Diagonalization",
     "seo_desc": "Eigenvalues and eigenvectors with live Python: det(A − λI) = 0, diagonalization, stability, Markov steady states, symmetric and positive definite matrices.", "title": "Eigenvalues and eigenvectors", "chapter": "Strang, chapter 6",
     "sections": "Strang §6.1, §6.2, §6.4, §6.5",
     "summary": "The directions a matrix does not turn: how to find them, A = XΛX⁻¹ and powers, stability and steady states, "
                "symmetric matrices and positive definite bowls."},
    {"n": 8, "dir": "lesson-8", "path": "svd-and-pca", "seo_title": "Singular Value Decomposition (SVD) and PCA, Visually",
     "seo_desc": "The SVD with live Python: every matrix as turn, stretch, turn, singular values, rank-one pieces, image compression, PCA and the pseudoinverse.", "title": "The SVD and PCA", "chapter": "Strang, chapter 7",
     "sections": "Strang §7.1 to §7.4",
     "summary": "Every matrix taken apart: turn, stretch, turn. Singular values, the most important pieces of a matrix, "
                "image compression, principal component analysis and the pseudoinverse."},
]
for _l, _c in zip(LESSONS, [1, 2, 2, 3, 4, 5, 6, 7]):
    _l["ch"] = _c
CHAPTERS = [
    {"n": 1, "title": "Introduction to vectors"},
    {"n": 2, "title": "Solving linear equations"},
    {"n": 3, "title": "Vector spaces and subspaces"},
    {"n": 4, "title": "Orthogonality"},
    {"n": 5, "title": "Determinants"},
    {"n": 6, "title": "Eigenvalues and eigenvectors"},
    {"n": 7, "title": "The singular value decomposition"},
]
PLANNED = [(t, f"Chapter {c['n']}") for c in CHAPTERS for t in c.get("planned", [])]
BUILT = []   # filled in main(): list of (lesson, slides, practice)


def chapter_of(lesson):
    return next(c for c in CHAPTERS if c["n"] == lesson["ch"])


def topnav(prefix, lesson=None, steps_html="", current=None):
    """Top bar: course name, chapter menu, lesson menu, slide steps."""
    built = [l for l, _, _ in BUILT]
    groups, later = "", ""
    for c in CHAPTERS:
        ls = [l for l in built if l["ch"] == c["n"]]
        cur = lesson is not None and c["n"] == lesson["ch"]
        if not ls:
            later += (f'<div class="ch soon"><div class="ch-head"><span class="ch-num">{c["n"]}</span>'
                      f'<span class="ch-title">{e(c["title"])}</span></div></div>')
            continue
        items = "".join(
            f'<a class="ls{" on" if lesson is not None and l["n"] == lesson["n"] else ""}" href="{prefix}{l["path"]}/">'
            f'<span class="ls-num">Lesson {l["n"]}</span><span class="ls-title">{e(l["title"])}</span></a>' for l in ls)
        groups += (f'<div class="ch{" on" if cur else ""}"><div class="ch-head"><span class="ch-num">{c["n"]}</span>'
                   f'<span class="ch-title">{e(c["title"])}</span></div><div class="ch-lessons">{items}</div></div>')
    if later:
        groups += f'<div class="menu-sub">Coming soon</div><div class="ch-later">{later}</div>'
    if lesson is None:
        ch_label = "Chapters"
    else:
        ch = chapter_of(lesson)
        ch_label = f'Chapter {ch["n"]}<span class="hide-sm"> · {e(ch["title"])}</span>'
    nav = f'<details class="menu"><summary>{ch_label}</summary><div class="menu-list chapters"><div class="menu-sub">Chapters</div>{groups}</div></details>'
    if lesson is not None:
        same = [l for l in built if l["ch"] == lesson["ch"]]
        _, slides, practice = next(t for t in BUILT if t[0]["n"] == lesson["n"])
        items = "".join(
            f'<a class="ls{" on" if l["n"] == lesson["n"] else ""}" href="{prefix}{l["path"]}/">'
            f'<span class="ls-num">Lesson {l["n"]}</span><span class="ls-title">{e(l["title"])}</span></a>' for l in same)
        inside = "".join(
            f'<a class="ls{" on" if current == s["slug"] else ""}" href="{prefix}{lesson["path"]}/{s["slug"]}/"><span class="ls-num">{j + 1}</span>'
            f'<span class="ls-title">{e(s["seo_title"])}</span></a>' for j, s in enumerate(slides))
        if practice:
            inside += (f'<a class="ls{" on" if current == "practice" else ""}" href="{prefix}{lesson["path"]}/practice/"><span class="ls-num">✎</span>'
                       f'<span class="ls-title">Examples and problems</span></a>')
        nav += (f'<span class="sep">›</span><details class="menu"><summary>Lesson {lesson["n"]}<span class="hide-sm"> · {e(lesson["title"])}</span></summary>'
                f'<div class="menu-list"><div class="menu-sub">Chapter {lesson["ch"]} lessons</div><div class="ch-lessons flat">{items}</div>'
                f'<div class="menu-sub">In lesson {lesson["n"]}</div><div class="ch-lessons flat slides">{inside}</div></div></details>')
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
                f'title="Examples and problems">✎ Practice</a>')
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
    # Google shows about 60 characters: keep the brand suffix only when it fits
    if title.endswith(" | " + SITE) and len(title) > 62:
        title = title[: -len(" | " + SITE)]
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


def more_block(s):
    """Extra problems for this slide, collapsed behind a clear button. Solutions stay hidden inside."""
    if not s.get("problems"):
        return ""
    n = s["problems"].count('class="problem"')
    recap = s["slug"] == "recap"
    title = "Review problems" if recap else "More examples to try"
    return (f'<details class="more"{" open" if recap else ""}><summary><span class="pl-icon">✎</span><span class="rv-text"><b>{title}</b>'
            f'<span>{n} problems with step-by-step solutions. Try each one before you open its solution.</span></span>'
            f'<span class="rv-toggle"><span class="s-show">Show</span><span class="s-hide">Hide</span></span></summary>'
            f'<div class="problems">{s["problems"]}</div></details>')


def review_block(pr):
    """The lesson review (examples + problems), collapsed, shown above the lab on every slide."""
    if not pr:
        return ""
    return f"""  <details class="review">
    <summary><span class="pl-icon">✎</span><span class="rv-text"><b>Lesson review</b><span>3 worked examples and 5 mixed problems with solutions</span></span><span class="rv-toggle"><span class="s-show">Open</span><span class="s-hide">Close</span></span></summary>
    <div class="review-body">
      <h2 class="practice-h">Worked examples</h2>
      <div class="examples">{pr['examples']}</div>
      <h2 class="practice-h">Problems</h2>
      <div class="problems">{pr['problems']}</div>
    </div>
  </details>
"""


CARD_LABEL = {
    "linear-combinations": "Linear combinations", "matrix-vector-multiplication": "Matrix times vector",
    "column-space": "Column space", "row-and-column-picture": "Rows and columns",
    "linear-transformations": "Transformations", "matrix-multiplication-order": "AB ≠ BA",
    "reflection-matrix": "Reflection", "gaussian-elimination": "Elimination",
    "pivots-and-back-substitution": "Pivots", "zero-pivots-and-singular-systems": "Zero pivots",
    "elimination-matrices": "Elimination matrices", "lu-decomposition": "A = LU",
    "inverse-matrix": "The inverse", "inverse-2x2-formula": "2 × 2 inverse", "inverse-of-a-product": "Inverse of AB",
    "gauss-jordan": "Gauss-Jordan", "transpose-and-symmetric-matrices": "Transpose", "permutation-matrices": "Permutations",
    "vector-spaces-and-subspaces": "Subspaces", "null-space": "Nullspace", "rref-and-special-solutions": "Special solutions",
    "complete-solution": "Complete solution", "independence-basis-dimension": "Basis and dimension",
    "four-fundamental-subspaces": "Four subspaces", "orthogonal-subspaces": "Orthogonality",
    "projection-onto-a-line": "Projection", "projection-matrix": "Projection matrix", "least-squares": "Least squares",
    "fitting-a-line": "Line fitting", "orthonormal-bases": "Orthonormal bases", "gram-schmidt": "Gram-Schmidt",
    "determinant-as-area": "Determinant", "properties-of-determinants": "Three rules",
    "determinant-from-pivots": "Det from pivots", "cofactor-formula": "Cofactors",
    "cramers-rule-and-inverse": "Cramer's rule", "area-volume-cross-product": "Cross product",
    "eigenvectors": "Eigenvectors", "finding-eigenvalues": "det(A − λI) = 0", "diagonalization": "A = XΛX⁻¹",
    "powers-and-stability": "Stability", "symmetric-matrices": "Symmetric matrices", "positive-definite-matrices": "Positive definite",
    "svd-geometry": "Turn, stretch, turn", "singular-values": "Singular values", "svd-rank-one-pieces": "Rank-one pieces",
    "image-compression": "Image compression", "principal-component-analysis": "PCA", "pseudoinverse-and-condition-number": "Pseudoinverse",
    "recap": "Recap", "practice": "Practice",
}


def card_label(lesson, slug):
    return f"Lesson {lesson['n']}", CARD_LABEL.get(slug, "")


def card_img(lesson, slug):
    """Path (from the site root) of a slide's illustration; recap and practice share one each."""
    f = ROOT / "assets" / "cards" / f"{lesson['dir']}--{slug}.webp"
    if f.exists():
        return f"assets/cards/{f.name}"
    return "assets/cards/practice.webp" if slug == "practice" else "assets/cards/recap.webp"


def ideas_text(s, k=3):
    items = re.findall(r"<li>(.*?)</li>", s.get("ideas", ""), re.S)
    return [re.sub(r"<[^>]+>", "", t).strip() for t in items[:k]]


def thumb(src, peek_title, items, label=None):
    line = e(items) if isinstance(items, str) else e(items[0]) if items else ""
    tl = f'<span class="tlabel"><small>{e(label[0])}</small>{e(label[1])}</span>' if label and label[1] else ""
    return (f'<span class="thumb"><img src="{src}" alt="" loading="lazy" decoding="async" width="640" height="360">{tl}'
            f'<span class="peek"><span class="peek-t">{line}</span><span class="peek-go">{e(peek_title)} →</span></span></span>')


def slide_page(lesson, slides, i, next_lesson=None, practice=None):
    s = slides[i]
    prefix = "../../"
    url = f"{BASE}/{lesson['path']}/{s['slug']}/"
    title = f"{s['seo_title']} | {SITE}"
    jsonld = [
        {"@context": "https://schema.org", "@type": "LearningResource", "name": s["seo_title"],
         "headline": s["title"], "description": s["description"], "url": url, "inLanguage": "en",
         "learningResourceType": "Interactive lesson", "educationalLevel": "Beginner",
         "isAccessibleForFree": True, "author": PROVIDER, "isPartOf": COURSE},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE, "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": f"Lesson {lesson['n']}: {lesson['title']}", "item": f"{BASE}/{lesson['path']}/"},
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
        nxt = f'<a class="btn primary" id="next" href="../../{next_lesson["path"]}/">Lesson {next_lesson["n"]} →</a>'
    else:
        nxt = '<a class="btn primary" id="next" href="../../">All lessons →</a>'

    config = {"slug": s["slug"], "lesson": lesson["dir"], "assets": prefix + "assets/",
              "preview": json.loads(s["preview"]), "check": s["check"]}
    return head(title, s["description"], url, prefix, "article", jsonld) + topnav(prefix, lesson, steps, s["slug"]) + f"""

<main class="lesson">
  <article class="page">
    <div class="slide-head"><div>
    <div class="kicker">{e(s['kicker'])}</div>
    <h1>{e(s['title'])}</h1>
    <p class="lead">{s['lead']}</p>
    </div><span class="thumb slide-art"><img src="{prefix}{card_img(lesson, s['slug'])}" alt="" width="640" height="360" decoding="async"><span class="tlabel"><small>Lesson {lesson['n']} · slide {i + 1}</small>{e(CARD_LABEL.get(s['slug'], ''))}</span></span></div>
    <div class="key">{s['key']}</div>
    {f'<div class="ideas-box"><div class="ideas-h">Key ideas</div>{s["ideas"]}</div>' if s.get("ideas") else ""}
    <div class="prose">
{s['prose']}
    </div>
    {f'<h2 class="practice-h">Worked examples</h2><div class="examples">{s["examples"]}</div>' if s.get("examples") else ""}
    {more_block(s)}
  </article>
{review_block(practice)}
  <section class="labsec" aria-label="Lab">
    <div class="exercise" id="exercise">
      <span class="tag">Exercise</span>
      <span class="task">{e(s['task'])}</span>
      <span class="hint" id="hint">Edit the code and press Run.</span>
    </div>
    <div class="lab">
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
      <figure class="figure">
        <div class="plane"><canvas id="cv" aria-label="The plane"></canvas><div class="tablebox" id="tablebox" hidden></div></div>
        <figcaption class="figcap"><div class="legend" id="legend"></div><div class="readout" id="readout"></div></figcaption>
      </figure>
    </div>
  </section>

  <div class="after">
    <div class="nav">
      {prev}
      <span class="count">{i + 1} / {len(slides)}</span>
      {nxt}
    </div>
  </div>
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
    url = f"{BASE}/{lesson['path']}/practice/"
    title = f"{pr['seo_title']} | {SITE}"
    jsonld = [
        {"@context": "https://schema.org", "@type": "LearningResource", "name": pr["seo_title"],
         "description": pr["description"], "url": url, "inLanguage": "en",
         "learningResourceType": "Practice problems", "educationalLevel": "Beginner",
         "isAccessibleForFree": True, "author": PROVIDER, "isPartOf": COURSE},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE, "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": f"Lesson {lesson['n']}: {lesson['title']}", "item": f"{BASE}/{lesson['path']}/"},
            {"@type": "ListItem", "position": 3, "name": "Examples and problems", "item": url}]},
    ]
    steps = steps_for(lesson, slides, pr, "practice", "../")
    prev = f'<a class="btn" id="prev" href="../{slides[-1]["slug"]}/">← Back</a>'
    nxt = (f'<a class="btn primary" id="next" href="../../{next_lesson["path"]}/">Lesson {next_lesson["n"]} →</a>' if next_lesson
           else '<a class="btn primary" id="next" href="../../">All lessons →</a>')
    config = {"slug": "practice", "lesson": lesson["dir"], "assets": prefix + "assets/",
              "preview": {"kind": "transform", "M": [[1, 0], [0, 1]]}, "check": "false"}
    return head(title, pr["description"], url, prefix, "article", jsonld) + topnav(prefix, lesson, steps, "practice") + f"""
<main class="lesson">
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
  </article>

  <section class="labsec" aria-label="Sandbox">
    <h2 class="practice-h" style="margin:0">Sandbox</h2>
    <div class="lab">
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
      <figure class="figure">
        <div class="plane"><canvas id="cv" aria-label="The plane"></canvas><div class="tablebox" id="tablebox" hidden></div></div>
        <figcaption class="figcap"><div class="legend" id="legend"></div><div class="readout" id="readout"></div></figcaption>
      </figure>
    </div>
  </section>

  <div class="after">
    <div class="nav">
      {prev}
      <span class="count">Practice</span>
      {nxt}
    </div>
  </div>
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
    url = f"{BASE}/{lesson['path']}/"
    title = f"{lesson['seo_title']} | {SITE}"
    desc = lesson["seo_desc"]
    cards = "".join(
        f'<a class="card pic" href="{s["slug"]}/">{thumb(prefix + card_img(lesson, s["slug"]), "Open slide", s["title"], card_label(lesson, s["slug"]))}'
        f'<span class="n">{j + 1:02d} · {e(s["kicker"])}</span>'
        f'<h3>{e(s["seo_title"])}</h3><p>{e(s["description"])}</p></a>' for j, s in enumerate(slides))
    jsonld = {"@context": "https://schema.org", "@type": "ItemList", "name": title,
              "itemListElement": [{"@type": "ListItem", "position": j + 1, "url": f"{url}{s['slug']}/", "name": s["seo_title"]}
                                  for j, s in enumerate(slides)]}
    if practice:
        cards += (f'<a class="card pic practice-card" href="practice/">'
                  f'{thumb(prefix + card_img(lesson, "practice"), "Practise", "Worked examples and problems with hidden solutions.", card_label(lesson, "practice"))}'
                  f'<span class="n">✎ · Practice</span>'
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
    desc = ("Learn linear algebra by running it: short visual lessons with live Python in your browser, "
            "following Gilbert Strang's textbook. Built for engineers.")
    cards = ""
    k = len(lessons_built)
    for c in CHAPTERS:
        row = ""
        for lesson, slides, _ in lessons_built:
            if lesson["ch"] == c["n"]:
                row += (f'<a class="card pic" href="{lesson["path"]}/">{thumb(card_img(lesson, slides[0]["slug"]), "Start lesson", f"{len(slides)} slides with live Python.", (f"Lesson {lesson['n']}", lesson["title"]))}'
                        f'<span class="n">Lesson {lesson["n"]} · {e(lesson["sections"])}</span>'
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
    <p>Short visual lessons. Read a slide, change the Python underneath, press Run and watch the plane move. The order follows Gilbert Strang's <i>Introduction to Linear Algebra</i>, and the examples come from robotics and engineering. Eight lessons take you from adding two arrows all the way to eigenvalues, the SVD and PCA.</p>
    <div class="cta"><a class="btn primary" href="{first[0]['path']}/{first[1][0]['slug']}/">Start lesson 1 →</a><a class="btn" href="#lessons">See all lessons</a></div>
  </section>
  <h2 class="section-title" id="lessons">Lessons</h2>
  {cards}
  <h2 class="section-title">How it works</h2>
  <div class="panel">
    <p>Every slide explains one idea with an everyday picture first: a boat with two thrusters, a shopping basket, a mirror. Then comes the maths, a worked example with real numbers, and where the idea shows up in drones, IMUs and robot arms.</p>
    <p>Next to the text is a lab. The Python runs in your browser, nothing to install. Functions like <code>show(A)</code>, <code>combo(A, x, b)</code>, <code>proj(a, b)</code>, <code>eigpic(A, v)</code> and <code>svdpic(A, θ)</code> draw on the plane, and <code>table(...)</code> lays out matrices with their pivots. Each slide ends with a small exercise that checks your answer.</p>
  </div>
  <div class="signup">
    <p><b>Updates by email.</b> Get a free Steppeschool account and we'll tell you when new lessons and problem sets are out. It also includes the free STM32 motor control mini-course and the Kalman filter notebook.</p>
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
        out = ROOT / lesson["path"]
        out.mkdir(exist_ok=True)
        (out / "index.html").write_text(lesson_page(lesson, slides, practice), encoding="utf-8")
        urls.append(f"{BASE}/{lesson['path']}/")
        for i, s in enumerate(slides):
            d = out / s["slug"]
            d.mkdir(exist_ok=True)
            (d / "index.html").write_text(slide_page(lesson, slides, i, next_lesson, practice), encoding="utf-8")
            # fragment for embedding the slide in the Kajabi members' course (not indexed)
            page = (d / "index.html").read_text(encoding="utf-8")
            main = re.search(r'<main class="lesson">.*?</main>', page, re.S).group(0)
            main = re.sub(r'\s*<div class="after">.*?</div>\s*</div>\s*(?=</main>)', '\n', main, flags=re.S)
            main = main.replace('href="../../', f'href="{BASE}/').replace('src="../../', f'src="{BASE}/')
            cfg = re.search(r'window\.SLIDE = (\{.*?\});</script>', page).group(1)
            ed = ROOT / "embed" / lesson["dir"]
            ed.mkdir(parents=True, exist_ok=True)
            (ed / f"{s['slug']}.html").write_text(
                f'<!doctype html><html><head><meta charset="utf-8"><meta name="robots" content="noindex"></head><body>\n{main}\n'
                f'<script type="application/json" id="la-config">{cfg}</script>\n</body></html>\n', encoding="utf-8")
            urls.append(f"{BASE}/{lesson['path']}/{s['slug']}/")
        if practice:
            d = out / "practice"
            d.mkdir(exist_ok=True)
            (d / "index.html").write_text(practice_page(lesson, slides, practice, next_lesson), encoding="utf-8")
            urls.append(f"{BASE}/{lesson['path']}/practice/")
    for lesson, slides, practice in BUILT:
        old = ROOT / lesson["dir"]
        if old.exists():
            shutil.rmtree(old)
        for sub in [""] + [s["slug"] + "/" for s in slides] + (["practice/"] if practice else []):
            (old / sub).mkdir(parents=True, exist_ok=True)
            (old / sub / "index.html").write_text(redirect_page(f"/{lesson['path']}/{sub}"), encoding="utf-8")
    (ROOT / "index.html").write_text(home_page(built), encoding="utf-8")
    # old single-page URL from the first prototype
    (ROOT / "lessons").mkdir(exist_ok=True)
    (ROOT / "lessons" / "01-columns-first.html").write_text(
        redirect_page(f"/{LESSONS[0]['path']}/{built[0][1][0]['slug']}/"), encoding="utf-8")
    sitemap = "".join(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sitemap}</urlset>\n',
        encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /embed/\n\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
    print(f"Built {len(urls)} pages.")


if __name__ == "__main__":
    main()
