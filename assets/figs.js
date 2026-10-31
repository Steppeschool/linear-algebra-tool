/* Animated figures for the lesson text (3Blue1Brown-style: grid, coloured arrows, moving pictures).
   Markup: <figure class="fig"><div class="fig-svg" data-fig='{"type":"combo", ...}'></div><figcaption>…</figcaption></figure>
   Every figure plays when it scrolls into view, loops, and has a pause button and a scrubber. */
(() => {
  const NS = "http://www.w3.org/2000/svg";
  const U = 34;                                   // pixels per unit
  const ease = t => t < .5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const seg = (t, a, b) => ease(clamp((t - a) / (b - a)));
  let DP = 1;                                     // decimals shown in labels; data plots (Kalman course) use 2
  const fmt = x => { const f = 10 ** DP, r = Math.round(x * f) / f; return (r < 0 ? "−" : "") + Math.abs(r).toFixed(Number.isInteger(r) ? 0 : (Math.round(r * 10) === r * 10 ? 1 : DP)); };
  const vfmt = v => `(${fmt(v[0])}, ${fmt(v[1])})`;
  const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
  const mul = (c, a) => [c * a[0], c * a[1]];
  const app = (M, v) => [M[0][0] * v[0] + M[0][1] * v[1], M[1][0] * v[0] + M[1][1] * v[1]];
  const mm = (A, B) => [[A[0][0] * B[0][0] + A[0][1] * B[1][0], A[0][0] * B[0][1] + A[0][1] * B[1][1]],
                        [A[1][0] * B[0][0] + A[1][1] * B[1][0], A[1][0] * B[0][1] + A[1][1] * B[1][1]]];
  const lerpM = (A, B, s) => A.map((r, i) => r.map((x, j) => x + (B[i][j] - x) * s));
  const I = [[1, 0], [0, 1]];
  const add3 = (a, b) => a.map((x, i) => x + b[i]), mul3 = (c, a) => a.map(x => c * x);
  const COL = { i: "var(--ihat)", j: "var(--jhat)", a: "var(--accent)", k: "var(--ink)", m: "var(--muted)" };
  const F = [[0, 0], [.5, 0], [.5, 1], [1.3, 1], [1.3, 1.5], [.5, 1.5], [.5, 2], [1.6, 2], [1.6, 2.5], [0, 2.5]];
  const SQ = [[0, 0], [1, 0], [1, 1], [0, 1]];

  function make(el) {
    const cfg = JSON.parse(el.getAttribute("data-fig"));
    const [x0, x1, y0, y1] = cfg.view || (cfg.xr ? [0, (cfg.w || 520) / U, 0, (cfg.h || 250) / U] : [-4, 6, -3, 6]);
    const W = (x1 - x0) * U, H = (y1 - y0) * U;
    const X = x => (x - x0) * U, Y = y => (y1 - y) * U;
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("role", "img");
    svg.style.maxWidth = Math.min(W, 560) + "px";
    const fig = el.closest("figure");
    if (fig) { const c = fig.querySelector("figcaption"); if (c) svg.setAttribute("aria-label", c.textContent); }
    el.appendChild(svg);
    const ctrl = document.createElement("div"); ctrl.className = "fig-ctrl";
    ctrl.innerHTML = '<button type="button" aria-label="Pause">❚❚</button><input type="range" min="0" max="1000" value="0" aria-label="Scrub"><span class="fig-read"></span>';
    el.appendChild(ctrl);
    const [btn, range, read] = ctrl.children;

    let out;                                       // group redrawn every frame
    const mk = (tag, a, parent = out) => { const e = document.createElementNS(NS, tag); for (const k in a) e.setAttribute(k, a[k]); parent.appendChild(e); return e; };
    // static grid
    const g0 = document.createElementNS(NS, "g"); svg.appendChild(g0);
    if (!cfg.type.endsWith("3d") && !cfg.xr && !["matvec", "matmul", "steps"].includes(cfg.type)) {
    for (let x = Math.ceil(x0); x <= x1; x++) mk("line", { x1: X(x), y1: 0, x2: X(x), y2: H, class: x ? "fg-grid" : "fg-axis" }, g0);
    for (let y = Math.ceil(y0); y <= y1; y++) mk("line", { x1: 0, y1: Y(y), x2: W, y2: Y(y), class: y ? "fg-grid" : "fg-axis" }, g0);
    for (let x = Math.ceil(x0); x <= x1; x++) if (x && x !== x1) { const e = mk("text", { x: X(x), y: Y(0) + 14, class: "fg-num" }, g0); e.textContent = x < 0 ? "−" + -x : x; }
    for (let y = Math.ceil(y0); y <= y1; y++) if (y && y !== y1) { const e = mk("text", { x: X(0) - 6, y: Y(y) + 4, class: "fg-num fg-num-y" }, g0); e.textContent = y < 0 ? "−" + -y : y; }
    }
    out = document.createElementNS(NS, "g"); svg.appendChild(out);

    const arrow = (p, q, col, label, opts = {}) => {
      const dx = X(q[0]) - X(p[0]), dy = Y(q[1]) - Y(p[1]), L = Math.hypot(dx, dy);
      if (L < 1) return;
      const ux = dx / L, uy = dy / L, h = Math.min(11, L * .45), w = h * .55;
      const bx = X(q[0]) - ux * h, by = Y(q[1]) - uy * h;
      mk("line", { x1: X(p[0]), y1: Y(p[1]), x2: bx, y2: by, style: `stroke:${COL[col] || col};stroke-width:${opts.w || 3};opacity:${opts.o ?? 1}`, "stroke-linecap": "round" });
      mk("polygon", { points: `${X(q[0])},${Y(q[1])} ${bx - uy * w},${by + ux * w} ${bx + uy * w},${by - ux * w}`, style: `fill:${COL[col] || col};opacity:${opts.o ?? 1}` });
      // label on top of every arrow: its name and its numbers, e.g. "v = (2, 1)"
      const faint = (opts.o ?? 1) < .5 || opts.nocoords;
      const val = opts.val || [q[0] - p[0], q[1] - p[1]];
      const s = faint ? (label || "") : label ? `${label} = ${vfmt(val)}` : vfmt(val);
      if (s && !(faint && !label)) {
        const off = opts.lab || [ux >= -.2 ? 8 : -8, uy <= .2 ? -9 : 17];
        text(q, s, col, off, ux < -.2 ? "end" : "start");
      }
    };
    const text = (q, s, col, off = [8, -8], anchor = "start") => {
      // keep the label inside the picture: estimate its width and slide it back in if it would be cut off
      const wpx = s.length * 7.3; let x = X(q[0]) + off[0], y = Y(q[1]) + off[1];
      if (anchor === "start" && x + wpx > W - 3) { x = W - 3; anchor = "end"; }
      if (anchor === "end" && x - wpx < 3) { x = 3; anchor = "start"; }
      y = Math.max(13, Math.min(H - 4, y));
      const t = mk("text", { x, y, class: "fg-lab", "text-anchor": anchor, style: `fill:${COL[col] || col}` });
      t.textContent = s;
    };
    const dot = (q, col, r = 3.5, o = 1) => mk("circle", { cx: X(q[0]), cy: Y(q[1]), r, style: `fill:${COL[col] || col};opacity:${o}` });
    const ring = q => mk("circle", { cx: X(q[0]), cy: Y(q[1]), r: 7, class: "fg-target" });
    const lineThrough = (d, col, cls = "fg-span") => {
      const L = 40 / Math.hypot(d[0], d[1] || 1e-9);
      mk("line", { x1: X(-d[0] * L), y1: Y(-d[1] * L), x2: X(d[0] * L), y2: Y(d[1] * L), class: cls, style: `stroke:${COL[col] || col}` });
    };
    const poly = (pts, cls) => mk("polygon", { points: pts.map(p => `${X(p[0])},${Y(p[1])}`).join(" "), class: cls });
    const grid = M => {                              // the moved graph paper
      for (let k = Math.floor(Math.min(x0, y0)) - 4; k <= Math.ceil(Math.max(x1, y1)) + 4; k++) {
        const a = app(M, [k, -30]), b = app(M, [k, 30]), c = app(M, [-30, k]), d = app(M, [30, k]);
        mk("line", { x1: X(a[0]), y1: Y(a[1]), x2: X(b[0]), y2: Y(b[1]), class: "fg-moved" });
        mk("line", { x1: X(c[0]), y1: Y(c[1]), x2: X(d[0]), y2: Y(d[1]), class: "fg-moved" });
      }
    };
    const shape = M => poly((cfg.shape === "square" ? SQ : F).map(p => app(M, p)), "fg-shape");

    // Matrix pictures drawn as tables of numbers: a highlighted row meets a highlighted column.
    const cellW = cfg.cw || .95, cellH = .8;               // cw: wider cells for 3-character entries like −12
    const matAt = (M, x, y, o = {}) => {             // top-left corner at (x, y); o.row / o.col highlight; o.show(i,j) hides entries
      const m = M.length, n = M[0].length;
      if (o.row != null) mk("rect", { x: X(x), y: Y(y - o.row * cellH), width: n * cellW * U, height: cellH * U, rx: 6, class: "fg-hi", style: `fill:${COL[o.rc || "i"]}` });
      if (o.col != null) mk("rect", { x: X(x + o.col * cellW), y: Y(y), width: cellW * U, height: m * cellH * U, rx: 6, class: "fg-hi", style: `fill:${COL[o.cc || "j"]}` });
      for (let i = 0; i < m; i++) for (let j = 0; j < n; j++) {
        if (o.show && !o.show(i, j)) continue;
        const e = mk("text", { x: X(x + (j + .5) * cellW), y: Y(y - (i + .5) * cellH) + 5, class: "fg-cell" });
        e.textContent = fmt(M[i][j]);
      }
      if (o.bar != null) mk("line", { x1: X(x + o.bar * cellW), y1: Y(y) + 4, x2: X(x + o.bar * cellW), y2: Y(y - m * cellH) - 4, class: "fg-br" });
      (o.piv || []).forEach(([i, j]) => mk("circle", { cx: X(x + (j + .5) * cellW), cy: Y(y - (i + .5) * cellH), r: 14, class: "fg-piv" }));
      const h = m * cellH * U, x0p = X(x) - 4, x1p = X(x + n * cellW) + 4, y0p = Y(y) + 2;
      mk("path", { d: `M${x0p + 6},${y0p} h-6 v${h - 4} h6 M${x1p - 6},${y0p} h6 v${h - 4} h-6`, class: "fg-br" });
    };
    const sym = (x, y, s) => { const e = mk("text", { x: X(x), y: Y(y) + 6, class: "fg-sym" }); e.textContent = s; };
    const table = (t, kind) => {
      const A = cfg.A, B = kind === "vec" ? cfg.x.map(v => [v]) : cfg.B;
      const m = A.length, n = A[0].length, p = B[0].length;
      const C = A.map(r => B[0].map((_, j) => r.reduce((s, a, k) => s + a * B[k][j], 0)));
      const top = (cfg.view || [0, 0, 0, 0])[3] - .4, xA = .4, xB = xA + n * cellW + 1, xC = xB + p * cellW + 1.1;
      sym(xA + n * cellW + .5, top - m * cellH / 2, "·"); sym(xB + p * cellW + .55, top - m * cellH / 2, "=");
      const cols = kind === "vec" && cfg.mode === "cols";
      const steps = cols ? n : m * p, k = Math.min(steps - 1, Math.floor(t * steps * 1.0001)), sub = t * steps - k;
      let line = "";
      if (cols) {                                   // column way: x_j times column j, added up
        const j = k;
        matAt(A, xA, top, { col: j, cc: j % 2 ? "j" : "i" }); matAt(B, xB, top, { row: j, rc: j % 2 ? "j" : "i" });
        const done = sub > .5 || k === steps - 1 && t >= 1;
        matAt(C, xC, top, { show: () => j === n - 1 && done });
        line = A[0].map((_, jj) => jj <= j ? `${fmt(B[jj][0])}·(${A.map(r => fmt(r[jj])).join(", ")})` : null).filter(Boolean).join(" + ");
        if (j === n - 1 && done) line += ` = (${C.map(r => fmt(r[0])).join(", ")})`;
      } else {                                      // row way: row i dotted with column j gives entry (i, j)
        const i = Math.floor(k / p), j = k % p, done = sub > .45 || t >= 1;
        matAt(A, xA, top, { row: i }); matAt(B, xB, top, { col: j });
        matAt(C, xC, top, { row: done ? i : null, rc: "a", show: (r, c) => r * p + c < k || (r * p + c === k && done) });
        line = `row ${i + 1} · ${kind === "vec" ? (cfg.xname || "x") : "column " + (j + 1)} = ` + A[i].map((a, q) => `${fmt(a)}·${fmt(B[q][j])}`).join(" + ") + (done ? ` = ${fmt(C[i][j])}` : "");
      }
      const e = mk("text", { x: X(xA), y: Y(top - Math.max(m, n) * cellH - .7) + 4, class: "fg-calc" }); e.textContent = line;
      return "";
    };

    // ---- data plots (Kalman course): cfg.xr = [xmin, xmax], cfg.yr = [ymin, ymax] in data units ----
    const ML = 40, MB = 26, MT = 10, MR = 12;
    const PX = x => ML + (x - cfg.xr[0]) / (cfg.xr[1] - cfg.xr[0]) * (W - ML - MR);
    const PY = y => H - MB - (y - cfg.yr[0]) / (cfg.yr[1] - cfg.yr[0]) * (H - MB - MT);
    const frame = (o = {}) => {                       // light grid with tick labels and axis titles
      const ticks = (lo, hi, n) => { const s = Math.pow(10, Math.floor(Math.log10((hi - lo) / n))), st = [1, 2, 5, 10].map(k => k * s).find(k => (hi - lo) / k <= n) || s * 10, out = []; for (let v = Math.ceil(lo / st) * st; v <= hi + 1e-9; v += st) out.push(+v.toFixed(6)); return out; };
      ticks(cfg.xr[0], cfg.xr[1], 8).forEach(v => { mk("line", { x1: PX(v), y1: MT, x2: PX(v), y2: H - MB, class: "fg-grid" }); const e = mk("text", { x: PX(v), y: H - MB + 14, class: "fg-num" }); e.textContent = fmt(v); });
      if (!o.noy) ticks(cfg.yr[0], cfg.yr[1], 5).forEach(v => { mk("line", { x1: ML, y1: PY(v), x2: W - MR, y2: PY(v), class: "fg-grid" }); const e = mk("text", { x: ML - 5, y: PY(v) + 4, class: "fg-num fg-num-y" }); e.textContent = fmt(v); });
      mk("line", { x1: ML, y1: H - MB, x2: W - MR, y2: H - MB, class: "fg-axis" });
      if (cfg.xlabel) { const e = mk("text", { x: W - MR, y: H - 2, class: "fg-num", style: "text-anchor:end" }); e.textContent = cfg.xlabel.trim(); }
      if (cfg.ylabel && !o.noy) { const e = mk("text", { x: ML + 4, y: MT + 10, class: "fg-num", style: "text-anchor:start" }); e.textContent = cfg.ylabel; }
    };
    const pdf = (x, m, v) => Math.exp(-(x - m) * (x - m) / (2 * v)) / Math.sqrt(2 * Math.PI * v);
    const bellPath = (m, v, k, col, o = {}) => {      // one bell curve, scaled by k, filled
      const n = 120, pts = [];
      for (let i = 0; i <= n; i++) { const x = cfg.xr[0] + (cfg.xr[1] - cfg.xr[0]) * i / n; pts.push([PX(x), PY(k * pdf(x, m, v))]); }
      mk("path", { d: `M${PX(cfg.xr[0])},${PY(0)} L` + pts.map(q => q.join(",")).join(" L") + ` L${PX(cfg.xr[1])},${PY(0)} Z`, style: `fill:${COL[col] || col};fill-opacity:${o.fo ?? .14};stroke:${COL[col] || col};stroke-width:${o.w || 2.2};opacity:${o.o ?? 1}` });
      if (o.label) { const e = mk("text", { x: PX(m), y: PY(k * pdf(m, m, v)) - 6, class: "fg-lab", "text-anchor": "middle", style: `fill:${COL[col] || col}` }); e.textContent = o.label; }
    };
    const fuse = (m1, v1, m2, v2) => { const K = v1 / (v1 + v2); return [m1 + K * (m2 - m1), (1 - K) * v1, K]; };
    const rnd = (() => { let s = cfg.seed || 7; return () => { s = (s * 16807) % 2147483647; return s / 2147483647; }; })();
    const gauss01 = () => { const u = Math.max(1e-9, rnd()), v = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
    const Z = Array.from({ length: 400 }, gauss01);   // fixed random draws, so dots don't jump between frames
    const draw = {
      bell(t) {                                    // bell curves; optional samples falling in; optional fusion of the first two
        frame({ noy: true });
        const B = cfg.bells, k = cfg.k || 1;
        const n = cfg.samples || 0;
        if (n) { const s = Math.floor(n * seg(t, .05, .7)), b = B[0]; for (let i = 0; i < s; i++) { const x = b.mu + Math.sqrt(b.var) * Z[i % 400]; mk("circle", { cx: PX(x), cy: PY(0) - 6 - (i % 4) * 5, r: 3, style: `fill:${COL[b.col || "i"]};opacity:.55` }); } }
        B.forEach((b, i) => bellPath(b.mu, b.var, k, b.col || ["i", "j", "a"][i], { label: b.label, fo: cfg.fuse ? .08 : .14, o: cfg.fuse && t > .5 ? .55 : 1 }));
        if (cfg.fuse) {
          const [m, v, K] = fuse(B[0].mu, B[0].var, B[1].mu, B[1].var), s = seg(t, .35, .75);
          if (s > 0) {                               // the fused bell slides in from the first bell and narrows
            const mm = B[0].mu + (m - B[0].mu) * s, vv = B[0].var + (v - B[0].var) * s;
            bellPath(mm, vv, k, "a", { label: s >= 1 ? (cfg.flabel || "fused") : "", fo: .22, w: 3 });
          }
          return s >= 1 ? `fused: μ = ${fmt(m)}, σ² = ${fmt(v)},  K = ${fmt(K)}` : "";
        }
        return B.map(b => `${b.label || "μ"}: μ = ${fmt(b.mu)}, σ = ${fmt(Math.sqrt(b.var))}`).join("   ");
      },
      cycle(t) {                                   // one 1D Kalman step: predict (slide right, widen), then correct (fuse with the measurement)
        frame({ noy: true });
        const { x0, P0, u, Q, z, R } = cfg, k = cfg.k || 1;
        const s1 = seg(t, .08, .38), xp = x0 + u * s1, Pp = P0 + Q * s1;
        if (s1 > 0 && s1 < 1) bellPath(x0, P0, k, "m", { fo: .05, o: .5 });
        bellPath(xp, Pp, k, "i", { label: s1 >= 1 ? "predicted" : "estimate", fo: t > .5 ? .06 : .14, o: t > .75 ? .6 : 1 });
        const s2 = seg(t, .45, .58);
        if (s2 > 0) bellPath(z, R, k, "j", { label: "measurement", o: s2, fo: .1 });
        const s3 = seg(t, .65, .92);
        if (s3 > 0) { const [m, v, K] = fuse(x0 + u, P0 + Q, z, R); bellPath(x0 + u + (m - x0 - u) * s3, P0 + Q + (v - P0 - Q) * s3, k, "a", { label: s3 >= 1 ? "corrected" : "", fo: .22, w: 3 });
          if (s3 >= 1) return `correct: x = ${fmt(m)}, P = ${fmt(v)}  (K = ${fmt(K)})`; }
        if (s2 > 0) return `measurement z = ${fmt(z)}, R = ${fmt(R)}`;
        if (s1 >= 1) return `predict: x = ${fmt(x0 + u)}, P = ${fmt(P0)} + ${fmt(Q)} = ${fmt(P0 + Q)}`;
        return `start: x = ${fmt(x0)}, P = ${fmt(P0)}`;
      },
      track(t) {                                   // a signal over time: truth, noisy readings, estimate (with a ±2σ band)
        frame();
        const T = cfg.t, n = T.length, m = Math.max(1, Math.ceil(n * seg(t, 0, .9)));
        const poly = (ys, cls, col, extra = "") => mk("polyline", { points: T.slice(0, m).map((x, i) => `${PX(x)},${PY(ys[i])}`).join(" "), class: cls, style: `stroke:${COL[col] || col};fill:none;${extra}` });
        if (cfg.band && cfg.est) {
          const up = T.slice(0, m).map((x, i) => `${PX(x)},${PY(cfg.est[i] + 2 * cfg.band[i])}`), dn = T.slice(0, m).map((x, i) => `${PX(x)},${PY(cfg.est[i] - 2 * cfg.band[i])}`).reverse();
          mk("polygon", { points: up.concat(dn).join(" "), style: "fill:var(--accent);fill-opacity:.12;stroke:none" });
        }
        if (cfg.truth) poly(cfg.truth, "fg-truth", "k", "stroke-width:2;stroke-dasharray:6 5;opacity:.7");
        if (cfg.meas) T.slice(0, m).forEach((x, i) => cfg.meas[i] != null && mk("circle", { cx: PX(x), cy: PY(cfg.meas[i]), r: 3.2, style: "fill:var(--jhat);opacity:.75" }));
        (cfg.lines || []).forEach(L => poly(L.y, "", L.col || "i", "stroke-width:2.4"));
        if (cfg.est) poly(cfg.est, "", "a", "stroke-width:2.8");
        const keys = [cfg.truth && "dashed = truth", cfg.meas && "dots = " + (cfg.mname || "readings"), ...(cfg.lines || []).map(L => L.label), cfg.est && "line = " + (cfg.ename || "estimate")].filter(Boolean);
        return `step ${m} of ${n}   ·   ${keys.join(" · ")}`;
      },
      ellipse(t) {                                 // a covariance ellipse (1σ and 2σ) with sample points; optional move by F: P becomes F P Fᵀ
        const P = cfg.P, chol = A => { const a = Math.sqrt(A[0][0]), b = A[1][0] / a, c = Math.sqrt(Math.max(0, A[1][1] - b * b)); return [[a, 0], [b, c]]; };
        const L = chol(P), M = cfg.F ? lerpM(I, cfg.F, seg(t, .3, .8)) : I, ML2 = mm(M, L), c0 = cfg.mean || [0, 0];
        if (cfg.F) grid(M);
        const ring = (r, cls) => poly(Array.from({ length: 72 }, (_, k) => add(c0, mul(r, app(ML2, [Math.cos(k * Math.PI / 36), Math.sin(k * Math.PI / 36)])))), cls);
        ring(2, "fg-ell2"); ring(1, "fg-ell1");
        for (let i = 0; i < (cfg.n || 60); i++) { const q = add(c0, app(ML2, [Z[(2 * i) % 400], Z[(2 * i + 1) % 400]])); dot(q, "a", 2.6, .5); }
        const Pn = cfg.F ? mm(mm(cfg.F, P), [[cfg.F[0][0], cfg.F[1][0]], [cfg.F[0][1], cfg.F[1][1]]]) : P, Pt = cfg.F && t > .8 ? Pn : P;
        return `P = [${fmt(Pt[0][0])}  ${fmt(Pt[0][1])};  ${fmt(Pt[1][0])}  ${fmt(Pt[1][1])}]` + (cfg.F ? (t > .8 ? "   (after F: F P Fᵀ)" : "   (before)") : "");
      },
      tangent(t) {                                 // zoom in on a curve until it looks straight: the tangent line is the linear approximation
        const f = new Function("x", "with (Math) { return " + cfg.f + "; }"), x0 = cfg.x0, y0 = f(x0), h = 1e-5, d = (f(x0 + h) - f(x0 - h)) / (2 * h);
        const z = Math.pow(cfg.zoom || 8, seg(t, .15, .85));      // magnification around (x0, f(x0))
        frame();
        const pts = []; for (let i = 0; i <= 200; i++) { const x = cfg.xr[0] + (cfg.xr[1] - cfg.xr[0]) * i / 200, xx = x0 + (x - x0) / z; pts.push(`${PX(x)},${PY(y0 + (f(xx) - y0) * z)}`); }
        mk("polyline", { points: pts.join(" "), style: "fill:none;stroke:var(--ihat);stroke-width:2.6" });
        mk("line", { x1: PX(cfg.xr[0]), y1: PY(y0 + d * (cfg.xr[0] - x0)), x2: PX(cfg.xr[1]), y2: PY(y0 + d * (cfg.xr[1] - x0)), style: "stroke:var(--accent);stroke-width:2;stroke-dasharray:7 5" });
        mk("circle", { cx: PX(x0), cy: PY(y0), r: 5, style: "fill:var(--ink)" });
        return `zoom ×${fmt(z)}   ·   slope at ${cfg.xname || "x"} = ${fmt(x0)}: ${fmt(d)}`;
      },
      radars(t) {                                  // range-only sensors: each radar knows only the distance, a circle; the robot sits where the circles meet
        const R = cfg.radars, p = cfg.robot, s = seg(t, .05, .7);
        R.forEach((r, i) => {
          const d = Math.hypot(p[0] - r[0], p[1] - r[1]) * s, col = ["i", "j", "a"][i % 3];
          if (cfg.sigma) mk("circle", { cx: X(r[0]), cy: Y(r[1]), r: d * U, style: `fill:none;stroke:${COL[col]};stroke-width:${2 * cfg.sigma * U};stroke-opacity:.15` });
          mk("circle", { cx: X(r[0]), cy: Y(r[1]), r: d * U, style: `fill:none;stroke:${COL[col]};stroke-width:2` });
          mk("rect", { x: X(r[0]) - 6, y: Y(r[1]) - 6, width: 12, height: 12, rx: 2, style: `fill:${COL[col]}` });
          text(r, `radar ${i + 1}`, col, [9, 16]);
        });
        if (s >= 1) { dot(p, "k", 5.5); text(p, `robot ${vfmt(p)}`, "k", [10, -10]);
          return R.map((r, i) => `d${i + 1} = ${fmt(Math.hypot(p[0] - r[0], p[1] - r[1]))}`).join(",  "); }
        return "each radar only knows a distance: a circle";
      },
      add(t) {                                     // v, then w from the tip of v, then the sum
        const { v, w } = cfg, s = seg(t, .1, .55), base = mul(s, v);
        arrow([0, 0], v, "i", "v");
        arrow(base, add(base, w), "j", "w");
        const o = seg(t, .6, .85);
        if (o > 0) arrow([0, 0], add(v, w), "a", "v + w", { o });
        return o > .5 ? `v + w = ${vfmt(add(v, w))}` : "walk along v, then along w";
      },
      scale(t) {                                   // c·v sweeps along the line through v
        const { v } = cfg, [a, b] = cfg.range || [-2, 3], c = a + (b - a) * ease(t);
        lineThrough(v, "i");
        arrow([0, 0], v, "m", "", { o: .35, w: 2 });
        arrow([0, 0], mul(c, v), "i", "cv");
        return `c = ${fmt(c)}   cv = ${vfmt(mul(c, v))}`;
      },
      combo(t) {                                   // c·v + d·w for many c, d: the dots fill the span
        // many (c, d) pairs spread evenly over a square (golden-ratio sequence); the arrows glide from one to the next
        const { v, w } = cfg, n = cfg.n || 18, A = cfg.amp || 2.4;
        const pick = k => k ? [A * (2 * ((k * .6180339) % 1) - 1), A * (2 * ((k * .7548777 + .37) % 1) - 1)] : [1, 1];
        if (cfg.span === "line") lineThrough(v, "a", "fg-span fg-span-on");
        const f = t * n, k0 = Math.floor(f), s = ease(f - k0);
        for (let k = 0; k <= Math.min(k0, n); k++) dot(app([[v[0], w[0]], [v[1], w[1]]], pick(k)), "a", 3, .6);
        const P = pick(k0), Q = pick(Math.min(k0 + 1, n));
        const c = P[0] + (Q[0] - P[0]) * s, d = P[1] + (Q[1] - P[1]) * s, cv = mul(c, v);
        arrow([0, 0], cv, "i", "cv", { nocoords: true });
        arrow(cv, add(cv, mul(d, w)), "j", "dw", { nocoords: true });
        const p = add(cv, mul(d, w));
        arrow([0, 0], p, "a", "cv + dw", { w: 2.4 });
        return `c = ${fmt(c)}, d = ${fmt(d)}`;
      },
      cols(t) {                                    // x·(column 1) + y·(column 2) reaches b
        const { a1, a2, x, b } = cfg, [n1, n2] = cfg.names || ["col 1", "col 2"];
        if (b) { ring(b); text(b, cfg.bname || "b", "k", [10, 16]); }
        arrow([0, 0], a1, "i", "", { o: .3, w: 2 }); arrow([0, 0], a2, "j", "", { o: .3, w: 2 });
        const s1 = x[0] * seg(t, .05, .45), s2 = x[1] * seg(t, .5, .9), p = mul(s1, a1);
        arrow([0, 0], p, "i", `${fmt(s1)}·${n1}`);
        if (s2) arrow(p, add(p, mul(s2, a2)), "j", `${fmt(s2)}·${n2}`);
        if (t > .92 && b) dot(b, "a", 5);
        return t > .92 && b ? `${fmt(x[0])}·${n1} + ${fmt(x[1])}·${n2} = ${cfg.bname || "b"}` : "";
      },
      rows(t) {                                    // each equation is a line; the answer is where they cross
        const [e1, e2] = cfg.eqs, col = ["i", "j"];
        [e1, e2].forEach((e, k) => {
          const s = seg(t, .05 + .35 * k, .35 + .35 * k); if (!s) return;
          const [a, b, c] = e, p0 = Math.abs(b) > Math.abs(a) ? [0, c / b] : [c / a, 0], d = [-b, a], L = 30 * s / Math.hypot(...d);
          mk("line", { x1: X(p0[0] - d[0] * L), y1: Y(p0[1] - d[1] * L), x2: X(p0[0] + d[0] * L), y2: Y(p0[1] + d[1] * L), class: "fg-row", style: `stroke:${COL[col[k]]}` });
        });
        const det = e1[0] * e2[1] - e1[1] * e2[0];
        if (t > .8 && det) { const p = [(e1[2] * e2[1] - e1[1] * e2[2]) / det, (e1[0] * e2[2] - e1[2] * e2[0]) / det]; dot(p, "a", 5); text(p, vfmt(p), "k", [10, -10]); return `the lines cross at ${vfmt(p)}`; }
        return "";
      },
      transform(t) {                               // the whole plane moves; the landmarks land on the columns
        const M = lerpM(I, cfg.M, seg(t, .1, .8));
        (cfg.lines || []).forEach(d => lineThrough(d, "a", "fg-span fg-span-on"));   // fixed lines, e.g. eigenvector directions
        if (cfg.grid !== false) grid(M);
        if (cfg.circle) poly(Array.from({ length: 72 }, (_, k) => app(M, [Math.cos(k * Math.PI / 36), Math.sin(k * Math.PI / 36)])), "fg-shape");
        else if (cfg.shape !== "none") shape(M);
        if (cfg.landmarks !== false) { arrow([0, 0], app(M, [1, 0]), "i", "", { w: 3 }); arrow([0, 0], app(M, [0, 1]), "j", "", { w: 3 }); }
        (cfg.vecs || []).forEach((v, k) => arrow([0, 0], app(M, v.v || v), "a", v.label || ""));
        return t > .8 ? `(1, 0) → ${vfmt(cfg.M.map(r => r[0]))},  (0, 1) → ${vfmt(cfg.M.map(r => r[1]))}` : "";
      },
      proj(t) {                                    // drop b straight down onto the line through a: p, and the error e
        const { a, b } = cfg, k = (a[0] * b[0] + a[1] * b[1]) / (a[0] * a[0] + a[1] * a[1]), p = mul(k, a), s = seg(t, .3, .75);
        lineThrough(a, "i");
        arrow([0, 0], a, "i", "a"); arrow([0, 0], b, "j", "b");
        const q = add(b, mul(s, add(p, mul(-1, b))));
        mk("line", { x1: X(b[0]), y1: Y(b[1]), x2: X(q[0]), y2: Y(q[1]), class: "fg-leg", style: "stroke:var(--muted)" });
        if (s >= 1) {
          const e = add(b, mul(-1, p)), u = mul(.3 / Math.hypot(...a), a), w = mul(.3 / (Math.hypot(...e) || 1), e);
          poly([p, add(p, u), add(add(p, u), w), add(p, w)], "fg-right");
          arrow([0, 0], p, "a", "p"); text(add(p, mul(.5, e)), "e", "m", [8, 0]);
          return `p = ${vfmt(p)},  e = b − p = ${vfmt(e)}`;
        }
        return "";
      },
      fit(t) {                                     // data points and the best straight line, with the vertical errors
        const { pts } = cfg, n = pts.length, St = pts.reduce((s, q) => s + q[0], 0), Sb = pts.reduce((s, q) => s + q[1], 0),
          Stt = pts.reduce((s, q) => s + q[0] * q[0], 0), Stb = pts.reduce((s, q) => s + q[0] * q[1], 0),
          D = (n * Stb - St * Sb) / (n * Stt - St * St), C = (Sb - D * St) / n, s = seg(t, .3, .8);
        const [C0, D0] = cfg.start || [Sb / n, 0], c = C0 + (C - C0) * s, d = D0 + (D - D0) * s;
        const [x0, x1] = [(cfg.view || [-1, 6])[0], (cfg.view || [-1, 6])[1]];
        mk("line", { x1: X(x0), y1: Y(c + d * x0), x2: X(x1), y2: Y(c + d * x1), class: "fg-row", style: "stroke:var(--accent)" });
        pts.forEach(q => { mk("line", { x1: X(q[0]), y1: Y(q[1]), x2: X(q[0]), y2: Y(c + d * q[0]), class: "fg-leg", style: "stroke:var(--ihat)" }); dot(q, "k", 4.5); });
        const E = pts.reduce((S, q) => S + (q[1] - c - d * q[0]) ** 2, 0);
        return `line ${fmt(c)} ${d < 0 ? "−" : "+"} ${fmt(Math.abs(d))}t,  sum of squared errors ${fmt(E)}`;
      },
      length(t) {                                  // Pythagoras: the two legs, then the arrow
        const { v } = cfg, s1 = seg(t, .05, .35), s2 = seg(t, .4, .65), s3 = seg(t, .7, .9);
        if (s1) { mk("line", { x1: X(0), y1: Y(0), x2: X(v[0] * s1), y2: Y(0), class: "fg-leg", style: "stroke:var(--ihat)" }); }
        if (s1 >= 1) text([v[0] / 2, 0], fmt(v[0]), "i", [-4, -8]);
        if (s2) { mk("line", { x1: X(v[0]), y1: Y(0), x2: X(v[0]), y2: Y(v[1] * s2), class: "fg-leg", style: "stroke:var(--jhat)" }); }
        if (s2 >= 1) text([v[0], v[1] / 2], fmt(v[1]), "j", [8, 4]);
        if (s3) arrow([0, 0], mul(s3, v), "a", s3 >= 1 ? "v" : "");
        const L = Math.hypot(v[0], v[1]);
        return s3 >= 1 ? `length = √(${fmt(v[0])}² + ${fmt(v[1])}²) = ${fmt(L)}` : "";
      },
      dotangle(t) {                                // w turns around; watch the sign of v · w
        const { v } = cfg, r = cfg.r || 2.2, th = (cfg.from || 0) + 2 * Math.PI * t, w = [r * Math.cos(th), r * Math.sin(th)];
        const d = v[0] * w[0] + v[1] * w[1], right = Math.abs(d) < .08 * Math.hypot(...v) * r;
        if (right) { const u = mul(.35 / Math.hypot(...v), v), q = mul(.35 / r, w); poly([[0, 0], u, add(u, q), q], "fg-right"); }
        arrow([0, 0], v, "i", "v"); arrow([0, 0], w, "j", "w");
        return right ? "v · w = 0: a right angle" : `v · w = ${fmt(d)}  ${d > 0 ? "(same side: angle under 90°)" : "(opposite side: angle over 90°)"}`;
      },
      elimrows(t) {                                // elimination in the row picture: line 2 turns, the crossing point stays
        const [e1, e2] = cfg.eqs, e3 = cfg.after, s = seg(t, .25, .75), e = e2.map((v, i) => v + (e3[i] - v) * s);
        const L = (q, col, cls, o = 1) => { const [a, b, c] = q, p0 = Math.abs(b) > Math.abs(a) ? [0, c / b] : [c / a, 0], d = [-b, a], k = 30 / Math.hypot(...d);
          mk("line", { x1: X(p0[0] - d[0] * k), y1: Y(p0[1] - d[1] * k), x2: X(p0[0] + d[0] * k), y2: Y(p0[1] + d[1] * k), class: cls, style: `stroke:${COL[col]};opacity:${o}` }); };
        L(e1, "i", "fg-row"); if (s > 0) L(e2, "j", "fg-row", .25); L(e, "j", "fg-row");
        const det = e1[0] * e2[1] - e1[1] * e2[0];
        if (det) { const p = [(e1[2] * e2[1] - e1[1] * e2[2]) / det, (e1[0] * e2[2] - e1[2] * e2[0]) / det]; dot(p, "a", 5); text(p, vfmt(p), "k", [10, -10]); }
        const eq = q => `${fmt(q[0])}x ${q[1] < 0 ? "−" : "+"} ${fmt(Math.abs(q[1]))}y = ${fmt(q[2])}`;
        return s >= 1 ? `new equation 2: ${eq(e3)}  (same crossing point)` : `equation 2: ${eq(e)}`;
      },
      steps(t) {                                   // a matrix changing step by step, with a note for each step
        const S = cfg.steps, k = Math.min(S.length - 1, Math.floor(t * S.length * 1.0001)), st = S[k];
        const top = (cfg.view || [0, 0, 0, 0])[3] - .4;
        matAt(st.M, .6, top, { row: st.row, rc: "a", bar: cfg.bar, piv: st.piv });
        const e = mk("text", { x: X(.6), y: Y(top - st.M.length * cellH - .7) + 4, class: "fg-calc" }); e.textContent = st.note || "";
        return `step ${k + 1} of ${S.length}`;
      },
      matvec(t) { return table(t, "vec"); },
      matmul(t) { return table(t, "mat"); },
      span3d(t) {                                  // 3D: two columns sweep out a flat sheet; a third may lift off it
        const th = -0.6 + 2 * Math.PI * t, ph = .42, c = Math.cos(th), s = Math.sin(th);
        const P = q => { const u = q[0] * c - q[1] * s, d = q[0] * s + q[1] * c; return [u, q[2] * Math.cos(ph) - d * Math.sin(ph)]; };
        for (let k = -3; k <= 3; k++) {             // floor grid (up = 0)
          const a = P([k, -3, 0]), b = P([k, 3, 0]), e = P([-3, k, 0]), f = P([3, k, 0]);
          mk("line", { x1: X(a[0]), y1: Y(a[1]), x2: X(b[0]), y2: Y(b[1]), class: "fg-grid" });
          mk("line", { x1: X(e[0]), y1: Y(e[1]), x2: X(f[0]), y2: Y(f[1]), class: "fg-grid" });
        }
        [[[3.4, 0, 0], "x"], [[0, 3.4, 0], "y"], [[0, 0, 3.4], "z"]].forEach(([q, n]) => { arrow([0, 0], P(q), "m", n, { w: 1.4, o: .7, nocoords: true }); });
        const [a, b, e] = cfg.cols, R = cfg.r || 2.2;
        const corners = [[-R, -R], [R, -R], [R, R], [-R, R]].map(([p, q]) => P(add3(mul3(p, a), mul3(q, b))));
        poly(corners, "fg-sheet");
        const nm = cfg.names || ["col 1", "col 2", "col 3"];
        const v3 = q => `(${q.map(fmt).join(", ")})`;
        arrow([0, 0], P(a), "i", `${nm[0]} ${v3(a)}`, { nocoords: true }); arrow([0, 0], P(b), "j", `${nm[1]} ${v3(b)}`, { nocoords: true });
        if (e) arrow([0, 0], P(e), "a", `${nm[2]} ${v3(e)}`, { nocoords: true });
        (cfg.pts || []).forEach(p => { dot(P(p.p), p.on ? "a" : "k", 4.5); text(P(p.p), p.label, "k", [8, -8]); });
        return cfg.read || "";
      },
      compose(t) {                                 // B first, then A
        const { A, B } = cfg;
        const M = t < .5 ? lerpM(I, B, seg(t, .05, .42)) : mm(lerpM(I, A, seg(t, .55, .92)), B);
        grid(M); shape(M);
        arrow([0, 0], app(M, [1, 0]), "i"); arrow([0, 0], app(M, [0, 1]), "j");
        return t < .5 ? `step 1: ${cfg.nB || "B"}` : `step 2: ${cfg.nA || "A"}  (so ${cfg.nA || "A"}${cfg.nB || "B"})`;
      },
    };

    let t = 0, playing = true, last = 0, hold = 0, visible = false;
    const DUR = cfg.dur || (cfg.type === "track" ? 9000 : cfg.type === "cycle" ? 9000 : cfg.type === "steps" ? 3000 * cfg.steps.length : cfg.type === "matvec" || cfg.type === "matmul" ? 2600 * (cfg.mode === "cols" ? cfg.A[0].length : cfg.A.length * (cfg.B ? cfg.B[0].length : 1)) : cfg.type === "span3d" ? 16000 : cfg.type === "combo" ? (cfg.n || 18) * 1100 : 6500);   // combo: about one new dot per second
    const render = () => { out.replaceChildren(); DP = cfg.dp ?? (cfg.xr ? 2 : 1); read.textContent = draw[cfg.type](t) || ""; DP = 1; range.value = Math.round(t * 1000); };
    const loop = now => {
      if (playing && visible) {
        const dt = last ? now - last : 0;
        if (t >= 1) { hold += dt; if (hold > 1600) { t = 0; hold = 0; } }
        else t = Math.min(1, t + dt / DUR);
        render();
      }
      last = now; requestAnimationFrame(loop);
    };
    const setPlay = p => { playing = p; btn.textContent = p ? "❚❚" : "▶"; btn.setAttribute("aria-label", p ? "Pause" : "Play"); };
    btn.onclick = () => { if (!playing && t >= 1) t = 0; setPlay(!playing); };
    range.oninput = () => { setPlay(false); t = range.value / 1000; render(); };
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) { t = 1; setPlay(false); }
    new IntersectionObserver(es => es.forEach(e => visible = e.isIntersecting), { threshold: .3 }).observe(el);
    render(); requestAnimationFrame(loop);
  }

  const run = (root = document) => root.querySelectorAll(".fig-svg[data-fig]:not([data-done])").forEach(el => {
    el.setAttribute("data-done", "");
    try { make(el); } catch (e) { console.error("figure", e); }
  });
  window.LAFigs = { run };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => run()); else run();
})();
