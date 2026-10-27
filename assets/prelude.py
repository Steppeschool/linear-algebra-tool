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
            if isinstance(i, slice) and isinstance(j, int):
                return ndarray([r[j] for r in self.d][i])
            if isinstance(i, int) and isinstance(j, slice):
                return ndarray(self.d[i][j])
            return self.d[i][j]
        v = self.d[k]
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
def _inv(a):
    a = asarray(a)
    if a.shape != (2, 2):
        raise ValueError("this prototype inverts 2x2 matrices only")
    d = _det(a)
    if abs(d) < 1e-12:
        raise ValueError("LinAlgError: singular matrix (det = 0), it has no inverse")
    (p, q), (r, s) = a.d
    return ndarray([[s / d, -q / d], [-r / d, p / d]])
def _norm(v):
    v = asarray(v)
    f = sum(v.d, []) if v.ndim == 2 else v.d
    return _M.sqrt(sum(x * x for x in f))
np.linalg = _NS()
np.linalg.det = _det
np.linalg.inv = _inv
np.linalg.norm = _norm
np.linalg.solve = lambda A, b: _inv(A) @ asarray(b)
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

def show(M, *vectors):
    M = asarray(M)
    if M.shape != (2, 2):
        raise ValueError("show() needs a 2x2 matrix, got shape %s" % (M.shape,))
    window.__pyshow(M.tolist(), [asarray(v).tolist() for v in vectors])

def run(src):
    ns = {'np': np, 'show': show, 'combo': combo, 'rowpic': rowpic, 'print': _print, '__name__': '__main__'}
    try:
        exec(compile(src, 'lesson.py', 'exec'), ns)
    except SyntaxError as e:
        window.__pyerr("SyntaxError on line %s: %s" % (e.lineno, e.args[0] if e.args else e))
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
        window.__pyerr(type(e).__name__ + ": " + str(e) + ("   (line %s)" % ln if ln else ""))

window.__pyrun = run
window.__pyready()
