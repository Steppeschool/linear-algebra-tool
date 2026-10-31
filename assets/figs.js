/* Animated figures for the lesson text (3Blue1Brown-style: grid, coloured arrows, moving pictures).
   Markup: <figure class="fig"><div class="fig-svg" data-fig='{"type":"combo", ...}'></div><figcaption>…</figcaption></figure>
   Every figure plays when it scrolls into view, loops, and has a pause button and a scrubber. */
(() => {
  const NS = "http://www.w3.org/2000/svg";
  const U = 34;                                   // pixels per unit
  const ease = t => t < .5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const seg = (t, a, b) => ease(clamp((t - a) / (b - a)));
  const fmt = x => { const r = Math.round(x * 10) / 10; return (r < 0 ? "−" : "") + Math.abs(r).toFixed(Number.isInteger(r) ? 0 : 1); };
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
    const [x0, x1, y0, y1] = cfg.view || [-4, 6, -3, 6];
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
    if (!cfg.type.endsWith("3d") && !["matvec", "matmul", "steps"].includes(cfg.type)) {
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
      if (label) text(q, label, col, opts.lab);
    };
    const text = (q, s, col, off = [8, -8]) => {
      const t = mk("text", { x: X(q[0]) + off[0], y: Y(q[1]) + off[1], class: "fg-lab", style: `fill:${COL[col] || col}` });
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
        line = `row ${i + 1} · ${kind === "vec" ? "x" : "column " + (j + 1)} = ` + A[i].map((a, q) => `${fmt(a)}·${fmt(B[q][j])}`).join(" + ") + (done ? ` = ${fmt(C[i][j])}` : "");
      }
      const e = mk("text", { x: X(xA), y: Y(top - Math.max(m, n) * cellH - .7) + 4, class: "fg-calc" }); e.textContent = line;
      return "";
    };
    const draw = {
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
        arrow([0, 0], cv, "i", "cv");
        arrow(cv, add(cv, mul(d, w)), "j", "dw");
        const p = add(cv, mul(d, w));
        arrow([0, 0], p, "a", "", { w: 2.4 });
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
        [[[3.4, 0, 0], "x"], [[0, 3.4, 0], "y"], [[0, 0, 3.4], "z"]].forEach(([q, n]) => { arrow([0, 0], P(q), "m", n, { w: 1.4, o: .7 }); });
        const [a, b, e] = cfg.cols, R = cfg.r || 2.2;
        const corners = [[-R, -R], [R, -R], [R, R], [-R, R]].map(([p, q]) => P(add3(mul3(p, a), mul3(q, b))));
        poly(corners, "fg-sheet");
        arrow([0, 0], P(a), "i", "col 1"); arrow([0, 0], P(b), "j", "col 2");
        if (e) arrow([0, 0], P(e), "a", "col 3");
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
    const DUR = cfg.dur || (cfg.type === "steps" ? 3000 * cfg.steps.length : cfg.type === "matvec" || cfg.type === "matmul" ? 2600 * (cfg.mode === "cols" ? cfg.A[0].length : cfg.A.length * (cfg.B ? cfg.B[0].length : 1)) : cfg.type === "span3d" ? 16000 : cfg.type === "combo" ? (cfg.n || 18) * 1100 : 6500);   // combo: about one new dot per second
    const render = () => { out.replaceChildren(); read.textContent = draw[cfg.type](t) || ""; range.value = Math.round(t * 1000); };
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
