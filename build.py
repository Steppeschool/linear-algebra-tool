#!/usr/bin/env python3
"""Build the static site from content/.

Each slide is one file in content/lesson-N/NN-slug.html with a front-matter
header and four parts (lead, key, prose, code). This script writes one real
HTML page per slide, so search engines see the full text without running
JavaScript, plus the home page, lesson overviews, sitemap.xml and robots.txt.

Run:  python build.py
"""
import base64
import datetime
import os
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
# Steppeschool brand assets, served from the Kajabi site so they always match steppeschool.com
LOGO = "https://kajabi-storefronts-production.kajabi-cdn.com/kajabi-storefronts-production/file-uploads/themes/2162900525/settings_images/5034abc-0d31-78f6-fa6d-4ec283cec8ac_steppeschool_logo.png"
FAVICON = "https://kajabi-storefronts-production.kajabi-cdn.com/kajabi-storefronts-production/file-uploads/sites/2148737716/images/7e33af1-8e03-fa-2023-c1572eec2d14_steppeschool_favicon.png"
COURSE_OUTCOMES = [
    "Solve any system Ax = b, by hand and in NumPy, and say when it has no solution",
    "Fit the best line to noisy sensor data with least squares",
    "Tell from the eigenvalues whether a system settles down or blows up",
    "Compress an image and find the main direction in your data with the SVD and PCA",
    "Follow the matrix maths in robotics, control and machine learning",
]
CHECKOUT = "https://www.steppeschool.com/offers/57ZvEAFX/checkout"   # "Lifetime Access": $20 once, Linear Algebra, Live only
LOGIN = "https://www.steppeschool.com/login"
LOCK_FROM = 4   # lessons 1-3 are free; 4+ are members-only (public pages show a teaser)
# Local test builds only (in a copy of the repo, never pushed): LA_UNLOCK=1 builds every lesson in full.
UNLOCK_ALL = os.environ.get("LA_UNLOCK") == "1"
# The key that seals members-only embeds. It lives OUTSIDE the repo and only appears in the Kajabi lesson bodies.
# Members-only lesson sources live OUTSIDE the public repo too (GitHub Pages would publish content/ otherwise).
PREMIUM_CONTENT = pathlib.Path(os.environ.get("LA_PREMIUM", "/mnt/user-data/outputs/linear-algebra-premium/content"))


def content_dir(lesson):
    return (PREMIUM_CONTENT if lesson["n"] >= LOCK_FROM else ROOT / "content") / lesson["dir"]


KEYFILE = pathlib.Path(os.environ.get("LA_KEYFILE", "/mnt/user-data/outputs/linear-algebra-premium/embed-key.txt"))


def locked(lesson):
    return lesson["n"] >= LOCK_FROM and not UNLOCK_ALL


def seal(text):
    """AES-GCM encrypt a members-only embed so the public repo only holds ciphertext (embed.js decrypts it in Kajabi)."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if not KEYFILE.exists():
        raise SystemExit(f"Missing {KEYFILE}: the embed key must exist before building members-only lessons.")
    key = base64.b64decode(KEYFILE.read_text().strip())
    iv = os.urandom(12)
    ct = AESGCM(key).encrypt(iv, text.encode("utf-8"), None)
    return json.dumps({"iv": base64.b64encode(iv).decode(), "ct": base64.b64encode(ct).decode()})

LESSONS = [
    {"n": 1, "dir": "lesson-1", "path": "vectors-and-matrices", "seo_title": "Vectors, Linear Combinations and Matrix Multiplication",
     "seo_desc": "Learn vectors, linear combinations, Ax as a mix of columns, the column space and matrix multiplication with interactive Python. Free lesson following Professor Strang.", "title": "Columns first", "chapter": "Strang, chapter 1",
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
    {"n": 5, "dir": "lesson-5", "path": "orthogonality-and-least-squares", "seo_title": "Orthogonality, Projections and the Least Squares Method",
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
OUTCOMES = {1: ['Read Ax as a mix of the columns of A, the idea everything else builds on', 'Predict where a matrix sends any point of the plane', 'Combine two moves into one matrix, and know why the order matters'], 2: ['Solve a system of equations the way a computer does', 'Spot at a glance when a system has no solution or infinitely many', 'Factor A = LU once and reuse it to solve fast'], 3: ["Undo a matrix, and know when it can't be undone", 'Invert any 2 × 2 in your head, and bigger ones with Gauss-Jordan', 'Use transposes and permutations without second-guessing'], 4: ['Write down every solution of Ax = b, not just one', 'Find the rank, a basis and the dimension of any subspace', 'Draw the big picture of the four subspaces and use it'], 5: ['Fit the best line to noisy sensor data', 'Project any vector onto a line or a plane', 'Turn any basis into an orthonormal one with Gram-Schmidt'], 6: ['Read area, volume and invertibility from one number', 'Compute any determinant three different ways', "Solve small systems with Cramer's rule and find cross products"], 7: ['Tell whether a system settles down or blows up', 'Find eigenvalues and eigenvectors by hand and in NumPy', 'Spot a positive definite matrix, a bowl, at a glance'], 8: ['Compress an image and keep only what matters', 'Find the main direction in your data with PCA', 'Take any matrix apart as turn, stretch, turn']}
for _l, _c in zip(LESSONS, [1, 2, 2, 3, 4, 5, 6, 7]):
    _l["ch"] = _c
    _l["outcomes"] = OUTCOMES[_l["n"]]
    if _l["n"] >= LOCK_FROM:
        _l["seo_desc"] = _l["seo_desc"].replace(" Free lesson.", "")
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
  <div class="topnav"><a class="logo" href="https://www.steppeschool.com" aria-label="Steppeschool"><img src="{LOGO}" alt="Steppeschool" width="108" height="24"></a><a class="brand" href="{prefix}">{SITE}</a><nav class="crumbnav" aria-label="Chapters and lessons">{nav}</nav></div>
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


# Vectors in the text, written (a, b), are shown as columns.
# one entry of a column vector: numbers, fractions, single-letter symbols and short sums like "2c − d"
ENTRY = r"[−\-+]?\s*(?:(?:\d+(?:\.\d+)?|[½⅓⅔¼¾])?(?:√\d+)?(?:/\d+)?)?\s*(?:(?:cos|sin)\s*)?(?:[a-zA-Zθλσπ](?:[₀-₉ᵢⱼ]+|\d)?)?"
TERM = rf"(?:{ENTRY})(?:\s*[+−\-·/]\s*(?:{ENTRY}))*"
TUP = re.compile(rf"(?<![a-z0-9_)\]⁻¹ᵀ])\(\s*({TERM}\s*(?:,\s*{TERM}\s*){{1,4}})\)")
SKIP = re.compile(r"(<(code|pre|script|textarea|style)\b.*?</\2>|<[^>]+>)", re.S)

def good(entries):
    for x in entries:
        x = x.strip()
        if not x or not re.search(r"[\d½⅓⅔¼¾a-zA-Zθλσπ]", x):
            return False
        if re.search(r"[a-zA-Z]{2,}", re.sub(r"\b(cos|sin)\b", "", x)):   # a word, not a vector entry
            return False
    return True

def vecify(html):
    out, pos = [], 0
    for m in SKIP.finditer(html):
        out.append(_sub(html[pos:m.start()])); out.append(m.group(0)); pos = m.end()
    out.append(_sub(html[pos:]))
    return "".join(out)

def _sub(text):
    def rep(m):
        entries = [x.strip() for x in m.group(1).split(",")]
        if not good(entries):
            return m.group(0)
        return '<span class="vec">' + "".join(f"<span>{x}</span>" for x in entries) + "</span>"
    return TUP.sub(rep, text)

VEC_FIELDS = ("lead", "key", "ideas", "prose", "examples", "problems", "intro")


def parse(path):
    text = path.read_text(encoding="utf-8")
    _, head, body = text.split("---\n", 2)
    meta = {}
    for line in head.strip().splitlines():
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip()
    parts = dict(re.findall(r"<!-- (\w+) -->\n(.*?)(?=\n<!-- \w+ -->\n|\Z)", body, re.S))
    meta.update({k: v.strip("\n") for k, v in parts.items()})
    for k in VEC_FIELDS:
        if meta.get(k):
            meta[k] = vecify(meta[k])
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
<link rel="icon" type="image/png" href="{FAVICON}">
<link rel="apple-touch-icon" href="{FAVICON}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/assets/cover.jpg">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="720">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{prefix}assets/lesson.css">{ld}
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4ZV1YVD90H"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-4ZV1YVD90H');
document.addEventListener('click',function(ev){{var a=ev.target.closest&&ev.target.closest('a[href*="/offers/"]');if(a)gtag('event','begin_checkout',{{currency:'USD',value:20,link_url:a.href,page_path:location.pathname}});}});</script>
</head>
<body>
"""


def footer():
    return f"""<footer class="foot">
  Follows the order and notation of Professor Gilbert Strang's <i>Introduction to Linear Algebra</i>, 5th edition (2016); § numbers refer to that book.
  Explanations, examples and code are original. Made by <a href="https://www.steppeschool.com">Steppeschool</a>.
</footer>
""" + UNLOCK_DIALOG


UNLOCK_DIALOG = f"""<dialog class="unlock" id="unlock" aria-labelledby="unlock-h">
  <form method="dialog"><button class="x" aria-label="Close">×</button></form>
  <div class="kicker">The full course</div>
  <h2 id="unlock-h">From Ax = b to PCA, by running it</h2>
  <p class="sub">Lessons 1 to 3 are free. Finish all eight and you will be able to:</p>
  <ul class="perks outcomes-list">{"".join(f"<li>{o}.</li>" for o in COURSE_OUTCOMES)}</ul>
  <p class="incl"><b>You get:</b> all 8 lessons with Python labs · every worked example and solution · 5 extra problems per lesson · your progress tracked · answers to your questions · every future update.</p>
  <div class="price"><b>$20</b> once · lifetime access</div>
  <a class="btn primary go" href="{CHECKOUT}" target="_blank" rel="noopener">Continue to checkout →</a>
  <p class="login">Already a member? <a href="{LOGIN}" target="_blank" rel="noopener">Log in to the course</a></p>
</dialog>
"""


def upsell(lesson):
    """Free lessons: a gentle offer for the full course at the end of every slide (stripped from Kajabi embeds)."""
    if lesson["n"] >= LOCK_FROM:
        return ""
    return f"""  <div class="upsell">
    <p><b>Enjoying lesson {lesson['n']}?</b> Get the full course: all 8 lessons through the SVD and PCA, your progress saved lesson by lesson, every solution and 5 extra problems per lesson. <span class="nowrap">$20 once, yours for life.</span></p>
    <button class="btn primary" type="button" data-unlock>See the full course</button>
  </div>
"""


def lock_panel(what, items, lesson=None):
    li = "".join(f"<li>{x}</li>" for x in items)
    hook = (f'<p class="hook">Finish lesson {lesson["n"]} and you will be able to: '
            f'<b>{lesson["outcomes"][0][0].lower() + lesson["outcomes"][0][1:]}.</b></p>') if lesson else ""
    return f"""<section class="locked" aria-label="Members only">
      <div class="lock-ic" aria-hidden="true">🔒</div>
      <h2>{'Keep reading with the full course' if what == 'slide' else f'The rest of this {what} is in the full course'}</h2>
      {hook}<p class="small" style="margin:0 0 6px">Still locked here:</p>
      <ul>{li}</ul>
      <button class="btn primary" type="button" data-unlock>Get the full course</button>
      <p class="small">$20 once, lifetime access. Lessons 1 to 3 stay free.</p>
    </section>"""


def count(block, cls):
    return len(re.findall(rf'<(?:div|section) class="{cls}"', block or ""))


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


PROVIDER = {"@type": "Organization", "name": "Steppeschool", "url": "https://www.steppeschool.com"}
COURSE = {"@type": "Course", "name": SITE, "url": BASE + "/",
          "description": "Interactive linear algebra lessons with live Python, following Professor Gilbert Strang's Introduction to Linear Algebra.",
          "provider": PROVIDER}


def example_items(s):
    """One list per slide: the worked examples first (up to 3), then the strongest problems, 5 in total.
    Each item is (title, question_html, solution_html)."""
    items = []
    for sec in re.findall(r'<section class="example">(.*?)</section>', s.get("examples") or "", re.S)[:3]:
        t = re.search(r"<h3>(.*?)</h3>", sec, re.S)
        title = re.sub(r"^\s*Example\s*\d+\s*[·:.-]\s*", "", t.group(1)).strip() if t else ""
        body = sec[t.end():] if t else sec
        k = body.find('<div class="worked">')
        q, sol = (body[:k], body[k:]) if k >= 0 else (body, "")
        items.append((title, q.strip(), sol.strip()))
    probs = []
    for j, p in enumerate(re.findall(r'<div class="problem">.*?</details>\s*</div></div>', s.get("problems") or "", re.S)):
        body = re.search(r'<div class="pbody">(.*)', p, re.S).group(1)
        q = body.split('<details class="sol">')[0]
        sol = re.search(r'<div class="solbody">(.*?)</div></details>', body, re.S).group(1)
        probs.append((j, "", q.strip(), sol.strip()))
    room = 5 - len(items)
    best = sorted(probs, key=lambda x: -len(re.sub("<[^>]+>", "", x[3])))[:max(0, room)]
    items += [(t, q, sol) for _, t, q, sol in sorted(best)]
    return items


def examples_block(s):
    """The slide's examples. Example 1 shows its solution; the others keep it behind 'Show solution'.
    On the public page of a members lesson only example 1 is open; the rest show as locked titles."""
    items = example_items(s)
    if not items:
        return ""
    lock = s.get("lock_examples")
    out = []
    for n, (title, q, sol) in enumerate(items, 1):
        head = f"Example {n}" + (f" · {title}" if title else "")
        if lock and n > 1:
            out.append(f'<button class="locked-stub" type="button" data-unlock><span>🔒</span><b>{e(re.sub("<[^>]+>", "", head))}</b><em>Members</em></button>')
            continue
        solution = (f'<details class="sol"{" open" if n == 1 else ""}><summary><span class="s-show">Show solution</span>'
                    f'<span class="s-hide">Hide solution</span></summary><div class="solbody">{sol}</div></details>') if sol else ""
        out.append(f'<section class="example"><h3>{head}</h3>\n{q}\n{solution}\n</section>')
    return f'<h2 class="practice-h">Examples</h2><div class="examples">{"".join(out)}</div>'


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



# Reader comments (giscus, backed by GitHub Discussions on the public linear-algebra-tool repo).
# Leave GISCUS_CATEGORY_ID empty to build without comments.
GISCUS_REPO = "Steppeschool/linear-algebra-tool"
GISCUS_REPO_ID = "R_kgDOVYeydQ"
GISCUS_CATEGORY = "Announcements"
GISCUS_CATEGORY_ID = "DIC_kwDOVYeydc4DJ7vP"


def comments():
    if not GISCUS_CATEGORY_ID:
        return ""
    return f"""<section class="comments" aria-label="Comments">
  <h2>Questions and comments</h2>
  <p>Stuck on something, or found a mistake? Ask here and I'll answer. You sign in with GitHub.</p>
  <div id="giscus"></div>
</section>
<script>
(function () {{
  var s = document.createElement("script");
  s.src = "https://giscus.app/client.js";
  var a = {{"repo": "{GISCUS_REPO}", "repo-id": "{GISCUS_REPO_ID}", "category": "{GISCUS_CATEGORY}",
    "category-id": "{GISCUS_CATEGORY_ID}", "mapping": "specific", "term": location.hostname + location.pathname,
    "strict": "1", "reactions-enabled": "1", "emit-metadata": "0", "input-position": "top",
    "theme": "preferred_color_scheme", "lang": "en", "loading": "lazy"}};
  for (var k in a) s.setAttribute("data-" + k, a[k]);
  s.crossOrigin = "anonymous"; s.async = true;
  document.getElementById("giscus").appendChild(s);
}})();
</script>"""


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
    {examples_block(s)}
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

{upsell(lesson)}
  <div class="after">
    <div class="nav">
      {prev}
      <span class="count">{i + 1} / {len(slides)}</span>
      {nxt}
    </div>
  </div>
</main>
{comments()}
{footer()}
<script>window.SLIDE = {json.dumps(config, ensure_ascii=False)};</script>
<script id="brython" src="{BRYTHON}" defer></script>
<script src="{prefix}assets/lab.js" defer></script>
<script src="{prefix}assets/nav.js" defer></script>
<script src="{prefix}assets/figs.js" defer></script>
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
    <div class="unlock-teaser">
      <p><b>Want more problems?</b> Members get five extra problems for every lesson, with worked solutions, and lessons 4 to 8 in full.</p>
      <button class="btn primary" type="button" data-unlock>See what members get</button>
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
{comments()}
{footer()}
<script>window.SLIDE = {json.dumps(config, ensure_ascii=False)};</script>
<script id="brython" src="{BRYTHON}" defer></script>
<script src="{prefix}assets/lab.js" defer></script>
<script src="{prefix}assets/nav.js" defer></script>
<script src="{prefix}assets/figs.js" defer></script>
</body>
</html>
"""


def lesson_page(lesson, slides, practice=None):
    prefix = "../"
    url = f"{BASE}/{lesson['path']}/"
    title = f"{lesson['seo_title']} | {SITE}"
    desc = lesson["seo_desc"]
    lock = locked(lesson)
    badge = '<span class="lockbadge preview">Free preview</span>' if lock else ""
    cards = "".join(
        f'<a class="card pic" href="{s["slug"]}/">{badge}{thumb(prefix + card_img(lesson, s["slug"]), "Open slide", s["title"], card_label(lesson, s["slug"]))}'
        f'<span class="n">{j + 1:02d} · {e(s["kicker"])}</span>'
        f'<h3>{e(s["seo_title"])}</h3><p>{e(s["description"])}</p></a>' for j, s in enumerate(slides))
    jsonld = {"@context": "https://schema.org", "@type": "ItemList", "name": title,
              "itemListElement": [{"@type": "ListItem", "position": j + 1, "url": f"{url}{s['slug']}/", "name": s["seo_title"]}
                                  for j, s in enumerate(slides)]}
    if practice:
        cards += (f'<a class="card pic practice-card" href="practice/">{badge}'
                  f'{thumb(prefix + card_img(lesson, "practice"), "Practise", "Worked examples and problems with hidden solutions.", card_label(lesson, "practice"))}'
                  f'<span class="n">✎ · Practice</span>'
                  f'<h3>Worked examples and problems</h3><p>{e(practice["description"])}</p></a>')
    return head(title, desc, url, prefix, jsonld=jsonld) + topnav(prefix, lesson) + f"""<div class="home">
  <section class="hero">
    <div class="kicker">Chapter {lesson['ch']} · Lesson {lesson['n']} · {e(lesson['sections'])}{' · Free preview' if lock else ''}</div>
    <h1>{e(lesson['title'])}</h1>
    <div class="outcomes"><b>By the end of this lesson you can</b><ul>{"".join(f"<li>{e(o)}</li>" for o in lesson["outcomes"])}</ul></div>
    <p>{e(lesson['summary'])} {len(slides)} short slides, then worked examples and problems. Each slide has an everyday picture, a worked example and Python you can run right on the page.</p>
    {'<p class="members-note">Free preview: most of every slide is yours to read, with its Python lab. Members get the full text, every example with its solution, and five extra problems per lesson.</p>' if lock else ''}
    <div class="cta"><a class="btn primary" href="{slides[0]['slug']}/">Start the lesson →</a>{'<button class="btn" type="button" data-unlock>Get the full course</button>' if lock else '<button class="btn" type="button" data-unlock>Full course: $20, lifetime</button>'}</div>
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
            "following Professor Gilbert Strang's textbook. Built for engineers.")
    chname = {c["n"]: c["title"] for c in CHAPTERS}
    row = ""
    for lesson, slides, _ in lessons_built:
        badge = '<span class="lockbadge preview">Free preview</span>' if locked(lesson) else '<span class="lockbadge free">Free</span>'
        row += (f'<a class="card pic" href="{lesson["path"]}/">{badge}{thumb(card_img(lesson, slides[0]["slug"]), "Start lesson", f"{len(slides)} slides with live Python.", (f"Lesson {lesson['n']}", lesson["title"]))}'
                f'<span class="n">Chapter {lesson["ch"]} · {e(chname[lesson["ch"]])}</span>'
                f'<h3>{e(lesson["title"])}</h3><p>{e(lesson["summary"])}</p></a>')
    cards = f'<div class="cards all">{row}</div>'
    first = lessons_built[0]
    jsonld = dict(COURSE, **{"@context": "https://schema.org", "inLanguage": "en", "isAccessibleForFree": True})
    return head(title, desc, url, "", jsonld=jsonld) + topnav("") + f"""<div class="home">
  <section class="hero">
    <div class="hero-text">
      <div class="kicker">Steppeschool · interactive course · first 3 lessons free</div>
      <h1>Linear algebra you can run.</h1>
      <p class="promise">Linear algebra is the language of engineering. Robots, drones, Kalman filters and AI all use it. Learn it by running Python on every page.</p>
      <div class="cta"><a class="btn primary" href="{first[0]['path']}/{first[1][0]['slug']}/">Start lesson 1 →</a><a class="btn" href="#lessons">See all lessons</a><button class="btn" type="button" data-unlock>Full course: $20, lifetime</button></div>
      <p class="hero-note">8 short lessons · Python in your browser, nothing to install · Based on Professor Gilbert Strang's <i>Introduction to Linear Algebra</i></p>
    </div>
    <div class="hero-art"><img src="assets/hero.webp" alt="" width="590" height="600"></div>
  </section>
  <div class="outcomes wide"><b>After the course you can</b><ul>{"".join(f"<li>{e(o)}</li>" for o in COURSE_OUTCOMES)}</ul></div>
  <h2 class="section-title" id="lessons">Lessons</h2>
  {cards}
  <h2 class="section-title">How it works</h2>
  <div class="panel wide">
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


def teaser(page, start, lock_html):
    """Public version of a members-only page: keep the opening (title, lead, key idea), drop the rest and the lab."""
    a = page.index(start)
    b = page.index('<div class="after">')
    page = page[:a] + lock_html + "\n  </article>\n\n  " + page[b:]
    page = re.sub(r'<script>window\.SLIDE = .*?</script>\n<script id="brython"[^>]*></script>\n<script src="[^"]*lab\.js" defer></script>\n', '', page)
    return page.replace('"isAccessibleForFree": true', '"isAccessibleForFree": false')


def slide_teaser(lesson, s, page):
    if s["slug"] == "recap":
        items = ["The full lesson review", plural(count(s.get("problems"), "problem"), "review problem") + " with step-by-step solutions",
                 "A Python sandbox for the whole lesson", "Five extra members-only problems with worked solutions"]
    else:
        items = ["The full explanation, with an everyday picture and where it shows up in engineering",
                 plural(count(s.get("examples"), "example"), "worked example") + " with real numbers",
                 plural(count(s.get("problems"), "problem"), "practice problem") + " with step-by-step solutions",
                 "A Python lab you edit and run in the browser, with an exercise that checks your answer"]
    return teaser(page, '<div class="prose">', lock_panel("slide", items))


def scramble(fragment, seed):
    """Unreadable stand-in for members-only text: same shape, random letters, tags kept. Shown blurred."""
    import random
    rnd = random.Random(seed)
    low, up = "abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    def text(t):
        return "".join(rnd.choice(low) if c.islower() else rnd.choice(up) if c.isupper()
                       else str(rnd.randint(0, 9)) if c.isdigit() else c if c.isspace() or c in ".,:;()=+−-" else rnd.choice(low)
                       for c in html.unescape(t))
    return re.sub(r"(?<=>)([^<]+)", lambda m: e(text(m.group(1))), "<x>" + fragment)[3:]


def public_slide(lesson, slides, i, next_lesson, practice):
    """Members lesson, public version: most of the explanation, the first worked example and the lab stay open;
    the end of the explanation fades out under a blur, the other examples and problems show as locked titles."""
    s = dict(slides[i])
    secs = re.split(r"(?=<h3>)", s["prose"].strip())
    secs = [x for x in secs if x.strip()]
    k = len(secs)
    keep = max(1, k - max(1, round(k / 3))) if k > 1 else 1
    shown, hidden = "".join(secs[:keep]), "".join(secs[keep:])
    if not hidden:   # one long section: cut it by paragraphs instead
        paras = re.split(r"(?=<p>|<div class=\"worked\">)", shown)
        cut = max(1, (2 * len(paras)) // 3)
        shown, hidden = "".join(paras[:cut]), "".join(paras[cut:])
    n_ex = len(example_items(s))
    items = (["The rest of this explanation"] +
             ([plural(n_ex - 1, "more example") + " with step-by-step solutions"] if n_ex > 1 else []) +
             ["Five extra members-only problems with worked solutions"])
    fade = (f'<div class="fade-wrap"><div class="fade-text" aria-hidden="true" data-nosnippet>{scramble(hidden, s["slug"])}</div>'
            f'{lock_panel("slide", items, lesson)}</div>')
    s["prose"] = shown + "\n" + fade
    s["lock_examples"] = True
    page = slide_page(lesson, slides[:i] + [s] + slides[i + 1:], i, next_lesson, practice)
    page = re.sub(r'\s*<details class="review">.*?\n  </details>', "", page, flags=re.S)   # the review nests <details>
    assert 'class="review"' not in page
    return page.replace('"isAccessibleForFree": true', '"isAccessibleForFree": false')


def practice_teaser(lesson, pr, page):
    items = [plural(count(pr.get("examples"), "example"), "worked example") + " covering the whole lesson",
             plural(count(pr.get("problems"), "problem"), "problem") + " with full solutions",
             "A Python sandbox to check your answers"]
    return teaser(page, '<h2 class="practice-h">Worked examples</h2>', lock_panel("practice set", items, lesson))


def write_embed(lesson, slug, page):
    """Fragment for embedding a page in the Kajabi members' course (not indexed). Members-only lessons are sealed."""
    main = re.search(r'<main class="lesson">.*?</main>', page, re.S).group(0)
    main = re.sub(r'\s*<div class="after">.*?</div>\s*</div>\s*(?=</main>)', '\n', main, flags=re.S)
    main = main.replace('href="../../', f'href="{BASE}/').replace('src="../../', f'src="{BASE}/')
    main = re.sub(r'\s*<div class="signup">.*?</div>', '', main, flags=re.S)   # members already have an account
    main = re.sub(r'\s*<div class="unlock-teaser">.*?</div>', '', main, flags=re.S)
    main = re.sub(r'\s*<div class="upsell">.*?</div>', '', main, flags=re.S)
    cfg = re.search(r'window\.SLIDE = (\{.*?\});</script>', page).group(1)
    ed = ROOT / "embed" / lesson["dir"]
    ed.mkdir(parents=True, exist_ok=True)
    body = f'{main}\n<script type="application/json" id="la-config">{cfg}</script>'
    if lesson["n"] >= LOCK_FROM:
        body = f'<script type="application/json" id="la-sealed">{seal(body)}</script>'
    (ed / f"{slug}.html").write_text(
        f'<!doctype html><html><head><meta charset="utf-8"><meta name="robots" content="noindex"></head><body>\n{body}\n</body></html>\n',
        encoding="utf-8")


def main():
    urls = [BASE + "/"]
    built = []
    available = [l for l in LESSONS if any(content_dir(l).glob("[0-9]*.html"))]
    if len(available) < len(LESSONS):
        raise SystemExit(f"Missing lesson sources (members-only sources are read from {PREMIUM_CONTENT}).")
    for lesson in available:
        files = sorted(content_dir(lesson).glob("[0-9]*.html"))
        pf = content_dir(lesson) / "practice.html"
        BUILT.append((lesson, [parse(f) for f in files], None))   # no separate practice page any more
    built = BUILT
    for li, (lesson, slides, practice) in enumerate(BUILT):
        next_lesson = BUILT[li + 1][0] if li + 1 < len(BUILT) else None
        practice_src = (content_dir(lesson) / "practice.html").exists()
        out = ROOT / lesson["path"]
        out.mkdir(exist_ok=True)
        (out / "index.html").write_text(lesson_page(lesson, slides, practice), encoding="utf-8")
        urls.append(f"{BASE}/{lesson['path']}/")
        for i, s in enumerate(slides):
            d = out / s["slug"]
            d.mkdir(exist_ok=True)
            page = slide_page(lesson, slides, i, next_lesson, practice)
            write_embed(lesson, s["slug"], page)
            (d / "index.html").write_text(public_slide(lesson, slides, i, next_lesson, practice) if locked(lesson) else page,
                                          encoding="utf-8")
            urls.append(f"{BASE}/{lesson['path']}/{s['slug']}/")
        if practice_src:   # old practice links go to the recap slide
            d = out / "practice"
            d.mkdir(exist_ok=True)
            (d / "index.html").write_text(redirect_page(f"/{lesson['path']}/{slides[-1]['slug']}/"), encoding="utf-8")
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
