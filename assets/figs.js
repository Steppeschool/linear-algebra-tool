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
    for (let x = Math.ceil(x0); x <= x1; x++) mk("line", { x1: X(x), y1: 0, x2: X(x), y2: H, class: x ? "fg-grid" : "fg-axis" }, g0);
    for (let y = Math.ceil(y0); y <= y1; y++) mk("line", { x1: 0, y1: Y(y), x2: W, y2: Y(y), class: y ? "fg-grid" : "fg-axis" }, g0);
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
        const { v, w } = cfg, n = cfg.n || 70, A = cfg.amp || 2.4;
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
        grid(M); shape(M);
        arrow([0, 0], app(M, [1, 0]), "i", "", { w: 3 }); arrow([0, 0], app(M, [0, 1]), "j", "", { w: 3 });
        return t > .8 ? `(1, 0) → ${vfmt(cfg.M.map(r => r[0]))},  (0, 1) → ${vfmt(cfg.M.map(r => r[1]))}` : "";
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
    const DUR = cfg.dur || 5200;
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
