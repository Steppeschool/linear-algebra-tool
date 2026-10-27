# Linear Algebra, Live

Slide lessons with a Python editor underneath. Learners read a slide, edit the code, press Run, and the plane on the slide redraws.

The course follows the order and notation of Gilbert Strang, *Introduction to Linear Algebra*, 5th edition (2016). Each slide is tagged with the section it matches. Slide text is original; nothing is copied from the book.

## Lessons

| # | Lesson | Strang sections | File |
|---|---|---|---|
| 1 | Columns first | §1.1, §1.3, §2.1, §2.4, §5.3, §8.1 | `lesson-1/` |
| 2 | Elimination and A = LU | §2.2, §2.3, §2.6 | `lesson-2/` |
| 3 | Inverses, transposes and permutations | §2.5, §2.7 | `lesson-3/` |
| 4 | The four subspaces | §3.1 to §3.5 | `lesson-4/` |

## Run locally

Serve the folder (the lab loads `assets/prelude.py`, so it needs a web server, not file://):

```
python -m http.server
```

Python runs in the browser with [Brython](https://brython.info) and a small NumPy-compatible subset (`array`, `@`, `column_stack`, `linalg.solve/det/inv`, `cos`, `sin`, `radians`…). The plan for the hosted version is to switch to Pyodide so learners get real NumPy.

## Drawing API used in the lessons

- `show(A, *vectors)`: the plane after the transformation A
- `combo(A, x, b=None)`: column picture, Ax as x₁·column 1 + x₂·column 2
- `rowpic(A, b)`: row picture, one line per equation
- `table(("label", M), ("R", R, pivots), ...)`: matrices and vectors side by side, pivot columns highlighted
- `nullpic(A, x, b=None)`: input plane with the nullspace, your x, and every solution of Ax = b
- `four(A)`: the four subspaces of a 2x2 matrix, input plane and output plane
- Helpers: `lu(A)`, `rref(A)`, `np.linalg.inv/solve/det/matrix_rank`, `np.hstack`, `np.eye`

## How the site is built (SEO)

Every slide is its own page with the full text in the HTML, its own title, description, canonical URL and structured data, so search engines can index each idea separately.

- Edit content in `content/lesson-N/NN-slug.html` (front matter + lead, key, prose, code).
- Shared look and lab: `assets/lesson.css`, `assets/lab.js`, `assets/prelude.py`.
- Run `python build.py` to regenerate `index.html`, `lesson-N/…/index.html`, `sitemap.xml` and `robots.txt`, then commit. GitHub Pages serves the repo root.

## Practice pages

Each lesson has `content/lesson-N/practice.html`: three worked examples and five problems with solutions that open on click. It builds to `lesson-N/practice/`. Extra problems for a future paid set are kept outside this repository, because everything in it is published by GitHub Pages.
