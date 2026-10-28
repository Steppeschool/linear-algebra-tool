from browser import window
_M = window.Math

def _print(*a, sep=' ', end='\n'):
    window.__pyout(sep.join(str(x) for x in a) + end)

def _fmt(x):
    if abs(x) < 5e-13:
        x = 0.0
    if x == int(x) and abs(x) < 1e12:
        return str(int(x)) + "."
    return ("%.4f" % x).rstrip("0")

class ndarray:
    def __init__(self, data):
        if isinstance(data, ndarray):
            data = data.tolist()
        data = list(data)
        if len(data) and isinstance(data[0], (list, tuple, ndarray)):
            rows = [list(r.tolist() if isinstance(r, ndarray) else r) for r in data]
            n = len(rows[0])
            for r in rows:
                if len(r) != n:
                    raise ValueError("all rows of a matrix need the same length")
            self.d = [[float(x) for x in r] for r in rows]
            self.shape = (len(rows), n)
        else:
            self.d = [float(x) for x in data]
            self.shape = (len(self.d),)
    @property
    def ndim(self):
        return len(self.shape)
    @property
    def T(self):
        if self.ndim == 1:
            return ndarray(self.d)
        return ndarray([[self.d[i][j] for i in range(self.shape[0])] for j in range(self.shape[1])])
    def copy(self):
        return ndarray(self.tolist())
    def astype(self, t=None):
        return ndarray(self.tolist())
    def tolist(self):
        return [list(r) for r in self.d] if self.ndim == 2 else list(self.d)
    def __len__(self):
        return self.shape[0]
    def __iter__(self):
        for k in range(self.shape[0]):
            yield self[k]
    def __getitem__(self, k):
        if isinstance(k, tuple):
            i, j = k
            if isinstance(i, int) and isinstance(j, int):
                return self.d[i][j]
            rows = self.d[i] if isinstance(i, slice) else [self.d[i]]
            out = [r[j] if isinstance(j, slice) else [r[j]] for r in rows]
            if isinstance(i, int):
                return ndarray(out[0])
            if isinstance(j, int):
                return ndarray([r[0] for r in out])
            return ndarray(out)
        v = self.d[k]
        if isinstance(k, slice) and self.ndim == 1:
            return ndarray(v)
        return ndarray(v) if isinstance(v, list) else v
    def __setitem__(self, k, val):
        if isinstance(k, tuple):
            self.d[k[0]][k[1]] = float(val)
        else:
            self.d[k] = list(val) if self.ndim == 2 else float(val)
    def __matmul__(self, o):
        o = asarray(o)
        if self.ndim == 2 and o.ndim == 2:
            if self.shape[1] != o.shape[0]:
                raise ValueError("matmul: shapes %s and %s don't line up" % (self.shape, o.shape))
            return ndarray([[sum(self.d[i][k] * o.d[k][j] for k in range(self.shape[1])) for j in range(o.shape[1])] for i in range(self.shape[0])])
        if self.ndim == 2 and o.ndim == 1:
            if self.shape[1] != o.shape[0]:
                raise ValueError("matmul: shapes %s and %s don't line up" % (self.shape, o.shape))
            return ndarray([sum(self.d[i][k] * o.d[k] for k in range(self.shape[1])) for i in range(self.shape[0])])
        if self.ndim == 1 and o.ndim == 2:
            return o.T @ self
        return sum(a * b for a, b in zip(self.d, o.d))
    def __rmatmul__(self, o):
        return asarray(o) @ self
    def _ew(self, o, f):
        if isinstance(o, (int, float)):
            if self.ndim == 2:
                return ndarray([[f(x, o) for x in r] for r in self.d])
            return ndarray([f(x, o) for x in self.d])
        o = asarray(o)
        if o.shape != self.shape:
            raise ValueError("shapes %s and %s don't match" % (self.shape, o.shape))
        if self.ndim == 2:
            return ndarray([[f(a, b) for a, b in zip(r, s)] for r, s in zip(self.d, o.d)])
        return ndarray([f(a, b) for a, b in zip(self.d, o.d)])
    def __add__(self, o): return self._ew(o, lambda a, b: a + b)
    def __radd__(self, o): return self._ew(o, lambda a, b: b + a)
    def __sub__(self, o): return self._ew(o, lambda a, b: a - b)
    def __rsub__(self, o): return self._ew(o, lambda a, b: b - a)
    def __mul__(self, o): return self._ew(o, lambda a, b: a * b)
    def __rmul__(self, o): return self._ew(o, lambda a, b: b * a)
    def __truediv__(self, o): return self._ew(o, lambda a, b: a / b)
    def __neg__(self): return self * -1
    def __repr__(self):
        if self.ndim == 1:
            return "array([" + ", ".join(_fmt(x) for x in self.d) + "])"
        cells = [[_fmt(x) for x in r] for r in self.d]
        w = max(len(c) for r in cells for c in r)
        lines = ["[" + ", ".join(c.rjust(w) for c in r) + "]" for r in cells]
        return "array([" + (",\n       ").join(lines) + "])"
    __str__ = __repr__

def asarray(x):
    return x if isinstance(x, ndarray) else ndarray(x)

class _NS:
    pass

np = _NS()
np.ndarray = ndarray
np.array = lambda x, dtype=None: ndarray(x)
np.asarray = asarray
np.copy = lambda a: asarray(a).copy()
np.pi = _M.PI
np.e = _M.E
def _ufunc(f):
    def g(x):
        if isinstance(x, ndarray):
            return ndarray([[f(v) for v in r] for r in x.d]) if x.ndim == 2 else ndarray([f(v) for v in x.d])
        return f(x)
    return g
np.cos = _ufunc(lambda v: _M.cos(v))
np.sin = _ufunc(lambda v: _M.sin(v))
np.tan = _ufunc(lambda v: _M.tan(v))
np.sqrt = _ufunc(lambda v: _M.sqrt(v))
np.abs = _ufunc(lambda v: abs(v))
np.radians = _ufunc(lambda v: v * _M.PI / 180)
np.deg2rad = np.radians
np.degrees = _ufunc(lambda v: v * 180 / _M.PI)
np.round = lambda x, n=0: _ufunc(lambda v: round(v, n))(x)
np.eye = lambda n: ndarray([[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)])
np.identity = np.eye
np.zeros = lambda s: ndarray([[0.0] * s[1] for _ in range(s[0])]) if isinstance(s, (tuple, list)) else ndarray([0.0] * s)
np.dot = lambda a, b: asarray(a) @ b
np.matmul = np.dot
def _allclose(a, b, atol=1e-8):
    a = asarray(a); b = asarray(b)
    fa = sum(a.d, []) if a.ndim == 2 else a.d
    fb = sum(b.d, []) if b.ndim == 2 else b.d
    return len(fa) == len(fb) and all(abs(x - y) <= atol + 1e-5 * abs(y) for x, y in zip(fa, fb))
np.allclose = _allclose

def _det(a):
    a = asarray(a)
    n = a.shape[0]
    if a.ndim != 2 or a.shape[1] != n:
        raise ValueError("det needs a square matrix")
    if n == 1:
        return a.d[0][0]
    if n == 2:
        return a.d[0][0] * a.d[1][1] - a.d[0][1] * a.d[1][0]
    return sum(((-1) ** j) * a.d[0][j] * _det([r[:j] + r[j + 1:] for r in a.d[1:]]) for j in range(n))
def _rref(a, tol=1e-10):
    a = asarray(a)
    R = [list(r) for r in a.d] if a.ndim == 2 else [list(a.d)]
    m, n = len(R), len(R[0])
    pivots = []
    row = 0
    for col in range(n):
        if row >= m:
            break
        best = max(range(row, m), key=lambda i: abs(R[i][col]))
        if abs(R[best][col]) < tol:
            continue
        R[row], R[best] = R[best], R[row]
        p = R[row][col]
        R[row] = [v / p for v in R[row]]
        for i in range(m):
            if i != row and abs(R[i][col]) > tol:
                f = R[i][col]
                R[i] = [v - f * w for v, w in zip(R[i], R[row])]
        pivots.append(col)
        row += 1
    R = [[0.0 if abs(v) < tol else v for v in r] for r in R]
    return ndarray(R), pivots
def _inv(a):
    a = asarray(a)
    n = a.shape[0]
    if a.ndim != 2 or a.shape[1] != n:
        raise ValueError("only square matrices have an inverse, got shape %s" % (a.shape,))
    if abs(_det(a)) < 1e-12:
        raise ValueError("LinAlgError: singular matrix (det = 0), it has no inverse")
    aug = ndarray([r + [1.0 if i == j else 0.0 for j in range(n)] for i, r in enumerate(a.tolist())])
    R, piv = _rref(aug)
    return ndarray([r[n:] for r in R.d])
def _rank(a):
    return len(_rref(a)[1])
def lu(a):
    """A = LU by elimination without row exchanges. Raises if a pivot is zero."""
    a = asarray(a)
    n = a.shape[0]
    U = [list(r) for r in a.d]
    L = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for k in range(n):
        if abs(U[k][k]) < 1e-12:
            raise ValueError("zero pivot in row %d: this matrix needs a row exchange (PA = LU)" % (k + 1))
        for i in range(k + 1, n):
            l = U[i][k] / U[k][k]
            L[i][k] = l
            U[i] = [v - l * w for v, w in zip(U[i], U[k])]
    U = [[0.0 if abs(v) < 1e-12 else v for v in r] for r in U]
    return ndarray(L), ndarray(U)
def rref(a):
    """Reduced row echelon form. Returns (R, pivot_columns), columns counted from 0."""
    return _rref(a)
def _norm(v):
    v = asarray(v)
    f = sum(v.d, []) if v.ndim == 2 else v.d
    return _M.sqrt(sum(x * x for x in f))
np.ones = lambda s: ndarray([[1.0] * s[1] for _ in range(s[0])]) if isinstance(s, (tuple, list)) else ndarray([1.0] * s)
np.sum = lambda a: sum(sum(asarray(a).d, []) if asarray(a).ndim == 2 else asarray(a).d)
np.mean = lambda a: np.sum(a) / (asarray(a).shape[0] * (asarray(a).shape[1] if asarray(a).ndim == 2 else 1))
np.outer = lambda a, b: ndarray([[x * y for y in asarray(b).d] for x in asarray(a).d])
np.arange = lambda *a: ndarray([float(v) for v in range(*[int(x) for x in a])])
def _lstsq(A, b, rcond=None):
    """Least squares: the x that makes |Ax - b| smallest. Returns (x, residual, rank, None) like NumPy."""
    A = asarray(A); b = asarray(b)
    x = _inv(A.T @ A) @ (A.T @ b)
    e = b - A @ x
    return x, ndarray([e @ e]), _rank(A), None
def _qr(A):
    """A = QR by Gram-Schmidt. Q has orthonormal columns, R is upper triangular."""
    A = asarray(A); m, n = A.shape
    qs = []
    for j in range(n):
        v = A[:, j]
        for q in qs:
            v = v - (q @ A[:, j]) * q
        L = _norm(v)
        if L < 1e-12:
            raise ValueError("the columns are dependent, so Gram-Schmidt cannot continue")
        qs.append(v / L)
    Q = np.column_stack(qs)
    return Q, Q.T @ A
np.linalg = _NS()
np.linalg.det = _det
np.linalg.inv = _inv
np.linalg.norm = _norm
np.linalg.solve = lambda A, b: _inv(A) @ asarray(b)
np.linalg.matrix_rank = _rank
np.linalg.lstsq = _lstsq
np.linalg.qr = _qr
np.hstack = lambda ms: ndarray([sum([asarray(m).d[i] if asarray(m).ndim == 2 else [asarray(m).d[i]] for m in ms], []) for i in range(asarray(ms[0]).shape[0])])
np.vstack = lambda ms: ndarray(sum([asarray(m).tolist() if asarray(m).ndim == 2 else [asarray(m).tolist()] for m in ms], []))
np.triu = lambda a: ndarray([[v if j >= i else 0.0 for j, v in enumerate(r)] for i, r in enumerate(asarray(a).d)])
np.tril = lambda a: ndarray([[v if j <= i else 0.0 for j, v in enumerate(r)] for i, r in enumerate(asarray(a).d)])
np.column_stack = lambda vs: ndarray([[asarray(v).d[i] for v in vs] for i in range(len(asarray(vs[0]).d))])

def combo(A, x, b=None):
    A = asarray(A); x = asarray(x)
    if A.shape != (2, 2) or x.shape != (2,):
        raise ValueError("combo() needs a 2x2 matrix A and a vector x with 2 entries")
    window.__pycombo(A.tolist(), x.tolist(), [] if b is None else asarray(b).tolist())

def rowpic(A, b):
    A = asarray(A); b = asarray(b)
    if A.shape != (2, 2) or b.shape != (2,):
        raise ValueError("rowpic() needs a 2x2 matrix A and a right-hand side b with 2 entries")
    window.__pyrows(A.tolist(), b.tolist())

def table(*items):
    """Draw matrices and vectors side by side. Each item: M, or (label, M), or (label, M, pivot_columns)."""
    out = []
    for k, it in enumerate(items):
        if isinstance(it, tuple):
            label = str(it[0]); M = asarray(it[1]); piv = list(it[2]) if len(it) > 2 else []
        else:
            label = ""; M = asarray(it); piv = []
        out.append([label, M.tolist() if M.ndim == 2 else [[v] for v in M.d], piv, M.ndim])
    window.__pytable(out)

def nullpic(A, x, b=None):
    """Input plane of a 2x2 matrix: its nullspace, your x, and (with b) every solution of Ax = b."""
    A = asarray(A); x = asarray(x)
    if A.shape != (2, 2) or x.shape != (2,):
        raise ValueError("nullpic() needs a 2x2 matrix A and a vector x with 2 entries")
    window.__pynull(A.tolist(), x.tolist(), [] if b is None else asarray(b).tolist())

def arrows(*items):
    """Draw vectors from the origin in order, joined by dashed steps. Each item: v or ("label", v)."""
    out = []
    for k, it in enumerate(items):
        label, v = (str(it[0]), asarray(it[1])) if isinstance(it, tuple) else ("v%d" % (k + 1), asarray(it))
        if v.shape != (2,):
            raise ValueError("arrows() draws 2D vectors, got shape %s" % (v.shape,))
        out.append([label, v.tolist()])
    window.__pyarrows(out, True)

def proj(a, b, p=None):
    """Project b onto the line through a. Pass your own p to check it; leave it out and the lab computes it."""
    a = asarray(a); b = asarray(b)
    if a.shape != (2,) or b.shape != (2,):
        raise ValueError("proj() needs two vectors a and b with 2 entries each")
    if a @ a < 1e-12:
        raise ValueError("a is the zero vector, so there is no line to project onto")
    auto = p is None
    p = (a @ b) / (a @ a) * a if auto else asarray(p)
    if p.shape != (2,):
        raise ValueError("p must be a vector with 2 entries")
    window.__pyproj(a.tolist(), b.tolist(), p.tolist(), auto)

def fit(t, b, C, D):
    """Data points (t, b) and the line C + D t through them, with the errors drawn."""
    t = asarray(t); b = asarray(b)
    if t.ndim != 1 or t.shape != b.shape:
        raise ValueError("fit() needs t and b as vectors of the same length")
    window.__pyfit(t.tolist(), b.tolist(), float(C), float(D))

def vectors(*items):
    """Draw vectors from the origin, no chain. Each item: v or ("label", v). Shows dot products."""
    out = []
    for k, it in enumerate(items):
        label, v = (str(it[0]), asarray(it[1])) if isinstance(it, tuple) else ("v%d" % (k + 1), asarray(it))
        if v.shape != (2,):
            raise ValueError("vectors() draws 2D vectors, got shape %s" % (v.shape,))
        out.append([label, v.tolist()])
    window.__pyarrows(out, False)

def four(A):
    """The four subspaces of a 2x2 matrix: input plane on the left, output plane on the right."""
    A = asarray(A)
    if A.shape != (2, 2):
        raise ValueError("four() needs a 2x2 matrix")
    window.__pyfour(A.tolist())

def show(M, *vectors):
    M = asarray(M)
    if M.shape != (2, 2):
        raise ValueError("show() needs a 2x2 matrix, got shape %s" % (M.shape,))
    window.__pyshow(M.tolist(), [asarray(v).tolist() for v in vectors])

def _hint(kind, msg):
    m = msg.lower()
    if kind == "SyntaxError" and ("never closed" in m or "unmatched" in m or "unexpected eof" in m):
        return "A bracket is not closed. Every ( or [ needs its ) or ]."
    if kind in ("SyntaxError", "IndentationError") and "indent" in m:
        return "Lines inside the same block must start at the same column. Check the spaces at the start of the line."
    if kind == "SyntaxError":
        return "Python could not read this line. Look for a missing comma, bracket or quote, or = written instead of ==."
    if kind == "NameError":
        return "A name is used before it has a value. Check the spelling, or define it on an earlier line."
    if "singular" in m or "no inverse" in m:
        return "This matrix has no inverse because its determinant is 0: it squashes the plane."
    if "shape" in m or "line up" in m or "match" in m or "same length" in m:
        return "The sizes do not fit. A matrix with n columns needs a vector with n entries."
    if kind == "ZeroDivisionError":
        return "Something was divided by zero. Is a pivot or a determinant equal to 0?"
    if kind == "TypeError":
        return "A value has the wrong type. Use np.array([...]) for vectors and matrices, and @ to multiply them."
    if kind in ("IndexError", "KeyError"):
        return "That position does not exist. Rows and columns are counted from 0."
    return ""

def run(src):
    ns = {'np': np, 'show': show, 'combo': combo, 'rowpic': rowpic, 'table': table, 'nullpic': nullpic, 'four': four, 'arrows': arrows, 'vectors': vectors, 'proj': proj, 'fit': fit, 'lu': lu, 'rref': rref, 'print': _print, '__name__': '__main__'}
    try:
        exec(compile(src, 'lesson.py', 'exec'), ns)
    except SyntaxError as e:
        msg = str(e.args[0]) if e.args else str(e)
        window.__pyerr("Line %s: %s" % (e.lineno, msg))
        window.__pyhint(_hint(type(e).__name__, msg))
    except Exception as e:
        ln = None
        tb = e.__traceback__
        while tb is not None:
            try:
                if tb.tb_frame.f_code.co_filename == 'lesson.py':
                    ln = tb.tb_lineno
            except Exception:
                pass
            tb = tb.tb_next
        window.__pyerr(("Line %s: " % ln if ln else "") + type(e).__name__ + ": " + str(e))
        window.__pyhint(_hint(type(e).__name__, str(e)))

window.__pyrun = run
window.__pyready()
