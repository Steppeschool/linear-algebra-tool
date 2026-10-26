# Linear Algebra, Live

Slide lessons with a Python editor underneath. Learners read a slide, edit the code, press Run, and the plane on the slide redraws.

The course follows the order and notation of Gilbert Strang, *Introduction to Linear Algebra*, 5th edition (2016). Each slide is tagged with the section it matches. Slide text is original; nothing is copied from the book.

## Lessons

| # | Lesson | Strang sections | File |
|---|---|---|---|
| 1 | Columns first | §1.1, §1.3, §2.1, §2.4, §5.3, §8.1 | `lessons/01-columns-first.html` |
| 2 | Elimination and A = LU | §2.2, §2.3, §2.6 | planned |

## Run locally

Open `lessons/01-columns-first.html` in a browser, or serve the folder:

```
python -m http.server
```

Python runs in the browser with [Brython](https://brython.info) and a small NumPy-compatible subset (`array`, `@`, `column_stack`, `linalg.solve/det/inv`, `cos`, `sin`, `radians`…). The plan for the hosted version is to switch to Pyodide so learners get real NumPy.

## Drawing API used in the lessons

- `show(A, *vectors)`: the plane after the transformation A
- `combo(A, x, b=None)`: column picture, Ax as x₁·column 1 + x₂·column 2
- `rowpic(A, b)`: row picture, one line per equation
