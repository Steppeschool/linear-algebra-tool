/* Linear Algebra, Live: shared lab for every slide page.
   Each page sets window.SLIDE = {slug, lesson, preview, check}. */
(() => {
const S = window.SLIDE;

const $ = id => document.getElementById(id);
const near = (a, b, t = 1e-6) => Math.abs(a - b) < t;
const eqM = (A, B) => A && near(A[0][0], B[0][0]) && near(A[0][1], B[0][1]) && near(A[1][0], B[1][0]) && near(A[1][1], B[1][1]);
const det = M => M[0][0] * M[1][1] - M[0][1] * M[1][0];
const mx = (a, b, c, d) => `<span class="mx"><span class="c1">${a}</span><span class="c2">${b}</span><span class="c1">${c}</span><span class="c2">${d}</span></span>`;
const vec = (a, b, cls = "") => `<span class="vec ${cls}"><span>${a}</span><span>${b}</span></span>`;
const ROT30 = [[Math.cos(Math.PI/6), -Math.sin(Math.PI/6)],[Math.sin(Math.PI/6), Math.cos(Math.PI/6)]];
const Ax = V => [V.A[0][0]*V.x[0] + V.A[0][1]*V.x[1], V.A[1][0]*V.x[0] + V.A[1][1]*V.x[1]];
const isT = V => V && V.kind === "transform";
const isC = V => V && V.kind === "combo";
const isR = V => V && V.kind === "rows";
const isTab = V => V && V.kind === "table";
const isN = V => V && V.kind === "null";
const isF = V => V && V.kind === "four";
const isA = V => V && V.kind === "arrows";
const isP = V => V && V.kind === "proj";
const isFit = V => V && V.kind === "fit";
const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
const projOf = (a, b) => { const k = dot(a, b) / dot(a, a); return a.map(v => k * v); };
function bestFit(t, b){ const n = t.length, St = t.reduce((s, v) => s + v, 0), Stt = dot(t, t), Sb = b.reduce((s, v) => s + v, 0), Stb = dot(t, b);
  const d = n * Stt - St * St; if (Math.abs(d) < 1e-12) return null; return [(Stt * Sb - St * Stb) / d, (n * Stb - St * Sb) / d]; }
const sse = (t, b, C, D) => t.reduce((s, v, i) => s + (b[i] - C - D * v) ** 2, 0);
const arrowVec = (V, name) => { const it = V && V.items && V.items.find(t => t.label === name); return it ? it.v : null; };
const flat = M => Array.isArray(M) ? M.flat(Infinity) : [M];
const close = (a, b, t = 1e-6) => a != null && b != null && flat(a).length === flat(b).length && flat(a).every((v, i) => Math.abs(v - flat(b)[i]) < t);
const isZero = v => v != null && flat(v).every(x => Math.abs(x) < 1e-9);
const item = (V, name) => { const it = V && V.items && V.items.find(t => t.label === name); return it ? it.M : null; };
const itemVec = (V, name) => { const M = item(V, name); return M ? M.map(r => r[0]) : null; };
const lastItem = V => V && V.items && V.items.length ? V.items[V.items.length - 1].M : null;
const col = M => M ? M.map(r => r[0]) : null;
const matvec = (A, x) => A.map(r => r.reduce((s, a, i) => s + a * x[i], 0));
const matmul = (A, B) => A.map(r => B[0].map((_, j) => r.reduce((s, a, k) => s + a * B[k][j], 0)));
const T = M => M[0].map((_, j) => M.map(r => r[j]));
const isUpper = M => M && M.every((r, i) => r.every((v, j) => j >= i || Math.abs(v) < 1e-9));
function rankOf(M){ const R = M.map(r => r.slice()); let rank = 0; const m = R.length, n = R[0].length;
  for (let c = 0; c < n && rank < m; c++){ let p = rank; for (let i = rank; i < m; i++) if (Math.abs(R[i][c]) > Math.abs(R[p][c])) p = i;
    if (Math.abs(R[p][c]) < 1e-9) continue; [R[rank], R[p]] = [R[p], R[rank]];
    for (let i = rank + 1; i < m; i++){ const f = R[i][c] / R[rank][c]; for (let j = c; j < n; j++) R[i][j] -= f * R[rank][j]; } rank++; }
  return rank; }
const nonzero = M => M.some(r => r.some(v => Math.abs(v) > 1e-9));
function mul(A, B){return [[A[0][0]*B[0][0]+A[0][1]*B[1][0], A[0][0]*B[0][1]+A[0][1]*B[1][1]],[A[1][0]*B[0][0]+A[1][1]*B[1][0], A[1][0]*B[0][1]+A[1][1]*B[1][1]]]}


// The check is written in the page as a JS expression over V (what was drawn) and n (runs).
const check = eval("(V, n) => (" + S.check + ")");

/* ---------- per-viewer storage (optional; the page works without it) ---------- */
function load(k){ try { return JSON.parse(localStorage.getItem("la:" + k)); } catch(e){ return null; } }
function store(k, v){ try { if (v === null) localStorage.removeItem("la:" + k); else localStorage.setItem("la:" + k, JSON.stringify(v)); } catch(e){} }
const doneKey = "done:" + S.lesson;
let done = new Set(load(doneKey) || []);
function markDone(){ done.add(S.slug); store(doneKey, [...done]); paintSteps(); }
function paintSteps(){ document.querySelectorAll(".step[data-slug]").forEach(a => a.classList.toggle("done", done.has(a.dataset.slug))); }

/* ---------- plane drawing ---------- */
const cv = $("cv"), ctx = cv.getContext("2d");
let A = [[1,0],[0,1]], from = A, to = A, t0 = 0, anim = false;
let view = S.preview, last = null, runs = 0;
const I2 = [[1,0],[0,1]];
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const css = n => getComputedStyle(document.querySelector(".la-embed") || document.documentElement).getPropertyValue(n).trim();
function size(){const r = cv.getBoundingClientRect(), d = devicePixelRatio || 1; cv.width = Math.round(r.width*d); cv.height = Math.round(r.height*d); ctx.setTransform(d,0,0,d,0,0); draw();}
function setView(V, fromSlider){ view = V; if (!fromSlider) renderSliders(); setTarget(V.kind === "transform" ? V.M : I2); setLegend(); draw(); }
function setTarget(M){from = A.map(r => r.slice()); to = M; t0 = performance.now(); if (reduce){A = M; draw(); return;} if(!anim){anim = true; requestAnimationFrame(step);} }
function step(now){let k = Math.min(1, (now - t0)/750); const e = k<.5 ? 4*k*k*k : 1 - Math.pow(-2*k+2,3)/2;
  A = [[from[0][0]+(to[0][0]-from[0][0])*e, from[0][1]+(to[0][1]-from[0][1])*e],[from[1][0]+(to[1][0]-from[1][0])*e, from[1][1]+(to[1][1]-from[1][1])*e]];
  draw(); if (k < 1) requestAnimationFrame(step); else anim = false;}
function setLegend(){
  const sw = (c, t) => `<span><i style="background:var(${c})"></i>${t}</span>`;
  $("legend").innerHTML = view.kind === "transform" ? sw("--ihat","(1, 0) lands on column 1") + sw("--jhat","(0, 1) lands on column 2")
    : view.kind === "combo" ? sw("--ihat","x₁ · column 1") + sw("--jhat","x₂ · column 2") + sw("--accent","Ax")
    : view.kind === "rows" ? sw("--ihat","equation 1") + sw("--jhat","equation 2")
    : view.kind === "null" ? sw("--accent","nullspace N(A)") + (view.b && view.b.length ? sw("--ihat","all solutions of Ax = b") : "") + sw("--ink","your x")
    : view.kind === "proj" ? sw("--ink","b") + sw("--ihat","line through a") + sw("--accent","p, the projection") + sw("--jhat","error e = b − p")
    : view.kind === "fit" ? sw("--ink","data points") + sw("--accent","your line C + Dt") + sw("--jhat","errors") + sw("--muted","best line")
    : view.kind === "arrows" ? view.items.map((it, k) => sw(PALETTE[k % PALETTE.length], it.label)).join("")
    : view.kind === "four" ? sw("--ihat","row space") + sw("--accent","nullspace") + sw("--jhat","column space") + sw("--muted","left nullspace")
    : "";
}
function nonzeroRow(A){ return A.find(r => Math.hypot(r[0], r[1]) > 1e-9) || null; }
function particular(V){ if (!V.b || V.b.length !== 2) return null; const r = nonzeroRow(V.A); if (!r) return null;
  const i = V.A.indexOf(r), t = V.b[i] / (r[0]*r[0] + r[1]*r[1]), xp = [t*r[0], t*r[1]];
  const ax = matvec(V.A, xp); return near(ax[0], V.b[0], 1e-6) && near(ax[1], V.b[1], 1e-6) ? xp : null; }
function rowSolution(V){ const d = det(V.A); if (Math.abs(d) < 1e-12) return null; return [(V.b[0]*V.A[1][1] - V.A[0][1]*V.b[1])/d, (V.A[0][0]*V.b[1] - V.A[1][0]*V.b[0])/d]; }
function extent(){
  const V = view; let pts = [];
  if (V.kind === "combo"){ const a1=[V.A[0][0],V.A[1][0]], a2=[V.A[0][1],V.A[1][1]], p1=[a1[0]*V.x[0], a1[1]*V.x[0]], r=Ax(V); pts = [a1, a2, p1, r]; if (V.b.length===2) pts.push(V.b); }
  else if (V.kind === "rows"){ const s = rowSolution(V); pts = s ? [s] : []; }
  else if (V.kind === "arrows"){ pts = V.items.map(it => it.v); }
  else if (V.kind === "proj"){ pts = [V.a, V.b, V.p]; }
  else if (V.kind === "null"){ const xs = [V.x]; const xp = particular(V); if (xp) xs.push(xp); pts = xs; }
  else if (V.kind !== "transform") return 3;
  else { const M = to, F = [[1,0],[0,1],[1,1],[2.3,2.05],[1.3,2.05],[2.3,1.75],[1.6,0.3]];
    return Math.max(2.6, ...F.map(([x,y]) => Math.max(Math.abs(M[0][0]*x+M[0][1]*y), Math.abs(M[1][0]*x+M[1][1]*y))), ...(V.vecs||[]).map(([x,y]) => Math.max(Math.abs(M[0][0]*x+M[0][1]*y), Math.abs(M[1][0]*x+M[1][1]*y)))) * 1.18; }
  return Math.max(2.5, ...pts.map(p => Math.max(Math.abs(p[0]), Math.abs(p[1])))) * 1.2;
}
function label(p, text, col, dx=8, dy=-8){ ctx.fillStyle = col; ctx.font = `600 12.5px ${css("--f-mono")}`; ctx.fillText(text, p[0]+dx, p[1]+dy); }
function fmt(v){ if (Math.abs(v) < 5e-10) return "0"; const r = Math.round(v * 1000) / 1000; return String(r).replace("-", "−"); }
function renderTable(){
  const box = $("tablebox");
  box.innerHTML = view.items.map(it => {
    const M = it.M, piv = new Set(it.piv || []), cols = M[0].length;
    const cells = M.map(r => r.map((v, j) => `<span class="${piv.has(j) ? "pv" : ""}">${fmt(v)}</span>`).join("")).join("");
    return `<div class="tm"><div class="tm-label">${it.label.replace(/&/g,"&amp;").replace(/</g,"&lt;")}</div><div class="tm-grid" style="grid-template-columns:repeat(${cols},auto)">${cells}</div><div class="tm-dim">${M.length}×${cols}</div></div>`;
  }).join("");
  const anyPiv = view.items.some(it => it.piv && it.piv.length);
  $("readout").innerHTML = anyPiv ? '<span class="hi">highlighted columns = pivot columns</span>' : `<span>${view.items.length} item${view.items.length === 1 ? "" : "s"}</span>`;
}
function draw(){
  const w = cv.clientWidth, h = cv.clientHeight; if (!w || !h) return;
  ctx.clearRect(0,0,w,h);
  const box = $("tablebox");
  if (view.kind === "table"){ box.hidden = false; renderTable(); return; }
  box.hidden = true;
  if (view.kind === "four"){ drawFour(w, h); return; }
  if (view.kind === "arrows"){ drawArrows(w, h); return; }
  if (view.kind === "fit"){ drawFit(w, h); return; }
  const ext = extent(), s = Math.min(w, h) / (2*ext), ox = w/2, oy = h/2;
  const P = (x, y) => [ox + (A[0][0]*x + A[0][1]*y)*s, oy - (A[1][0]*x + A[1][1]*y)*s];
  const Q = (x, y) => [ox + x*s, oy - y*s];
  const N = Math.ceil(Math.max(w, h) / s) + 2;
  const st = N > 60 ? 5 : N > 30 ? 2 : 1;
  const f = v => (Math.abs(v)<5e-4?0:v).toFixed(2), g = v => +(+f(v)).toFixed(2);
  const O = Q(0,0);
  if (view.kind === "transform"){
    ctx.lineWidth = 1; ctx.strokeStyle = css("--grid-ref");
    for (let i=-N;i<=N;i+=st){line(Q(i,-N),Q(i,N)); line(Q(-N,i),Q(N,i));}
  }
  ctx.strokeStyle = css("--grid"); ctx.lineWidth = 1;
  for (let i=-N;i<=N;i+=st){ if (i) { line(P(i,-N),P(i,N)); line(P(-N,i),P(N,i)); } }
  ctx.strokeStyle = css("--muted"); ctx.globalAlpha = .6; ctx.lineWidth = 1.4; line(P(-N,0),P(N,0)); line(P(0,-N),P(0,N)); ctx.globalAlpha = 1;
  if (view.kind === "transform"){
    poly([P(0,0),P(1,0),P(1,1),P(0,1)], css("--area"), css("--accent"), 1.2);
    const F = [[1.3,0.3],[1.6,0.3],[1.6,1.1],[2.1,1.1],[2.1,1.4],[1.6,1.4],[1.6,1.75],[2.3,1.75],[2.3,2.05],[1.3,2.05]];
    poly(F.map(p => P(p[0],p[1])), css("--shape"), null, 0, .85);
    (view.vecs||[]).forEach(v => arrow(P(0,0), P(v[0],v[1]), css("--accent"), 2.4));
    arrow(P(0,0), P(1,0), css("--ihat"), 3.2);
    arrow(P(0,0), P(0,1), css("--jhat"), 3.2);
    const d = det(A);
    $("readout").innerHTML = `<span>A = [[${g(A[0][0])}, ${g(A[0][1])}], [${g(A[1][0])}, ${g(A[1][1])}]]</span><span class="hi">det = ${f(d)}</span>${Math.abs(d)<1e-3?'<span>collapsed</span>':d<0?'<span>flipped</span>':''}`;
  } else if (view.kind === "combo"){
    const V = view, a1=[V.A[0][0],V.A[1][0]], a2=[V.A[0][1],V.A[1][1]], dep = Math.abs(det(V.A)) < 1e-9;
    if (dep && nonzero(V.A)){ const dir = Math.hypot(...a1) > 1e-9 ? a1 : a2; const k = 4*N/Math.hypot(...dir);
      ctx.strokeStyle = css("--accent"); ctx.globalAlpha = .2; ctx.lineWidth = 10; line(Q(-dir[0]*k,-dir[1]*k), Q(dir[0]*k,dir[1]*k)); ctx.globalAlpha = 1; }
    ctx.setLineDash([5,5]); ctx.globalAlpha = .75;
    arrow(O, Q(...a1), css("--ihat"), 1.6); arrow(O, Q(...a2), css("--jhat"), 1.6);
    ctx.setLineDash([]); ctx.globalAlpha = 1;
    label(Q(...a1), "column 1", css("--ihat")); label(Q(...a2), "column 2", css("--jhat"));
    const p1 = [a1[0]*V.x[0], a1[1]*V.x[0]], r = Ax(V);
    arrow(O, Q(...p1), css("--ihat"), 3.2); arrow(Q(...p1), Q(...r), css("--jhat"), 3.2); arrow(O, Q(...r), css("--accent"), 3.8);
    label(Q(...r), "Ax", css("--accent"), 10, 4);
    let hit = "";
    if (V.b.length === 2){ const B = Q(...V.b); ctx.strokeStyle = css("--ink"); ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(B[0], B[1], 9, 0, 7); ctx.stroke(); label(B, "b", css("--ink"), 12, -10);
      hit = near(r[0], V.b[0]) && near(r[1], V.b[1]) ? '<span class="good">Ax = b</span>' : `<span>b = (${g(V.b[0])}, ${g(V.b[1])})</span>`; }
    $("readout").innerHTML = `<span>x = (${g(V.x[0])}, ${g(V.x[1])})</span><span class="hi">Ax = (${g(r[0])}, ${g(r[1])})</span>${hit}<span>${dep ? (nonzero(V.A) ? "C(A) is a line" : "C(A) is a point") : "C(A) is the plane"}</span>`;
  } else if (view.kind === "proj"){
    const V = view, far = 4*N, u = Math.hypot(...V.a), k = far / u, e = [V.b[0]-V.p[0], V.b[1]-V.p[1]], ae = dot(V.a, e), ok = close(V.p, projOf(V.a, V.b));
    ctx.strokeStyle = css("--ihat"); ctx.globalAlpha = .28; ctx.lineWidth = 7; line(Q(-V.a[0]*k, -V.a[1]*k), Q(V.a[0]*k, V.a[1]*k)); ctx.globalAlpha = 1;
    if (Math.hypot(...e) > 1e-6 && Math.hypot(...V.p) > 1e-6 && Math.abs(ae) < 1e-6){ const pu = V.p.map(v => v / Math.hypot(...V.p)), eu = e.map(v => v / Math.hypot(...e)), r = 0.22 * ext / 2.5;
      const c1 = Q(V.p[0] - pu[0]*r*Math.sign(dot(V.p, V.a)), V.p[1] - pu[1]*r*Math.sign(dot(V.p, V.a))), c3 = Q(V.p[0] + eu[0]*r, V.p[1] + eu[1]*r), c2 = Q(V.p[0] - pu[0]*r*Math.sign(dot(V.p, V.a)) + eu[0]*r, V.p[1] - pu[1]*r*Math.sign(dot(V.p, V.a)) + eu[1]*r);
      ctx.strokeStyle = css("--jhat"); ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(...c1); ctx.lineTo(...c2); ctx.lineTo(...c3); ctx.stroke(); }
    ctx.setLineDash([6, 5]); ctx.strokeStyle = css("--jhat"); ctx.lineWidth = 2.4; line(Q(...V.p), Q(...V.b)); ctx.setLineDash([]);
    arrow(O, Q(...V.a), css("--ihat"), 3); label(Q(...V.a), "a", css("--ihat"), 8, 16);
    arrow(O, Q(...V.b), css("--ink"), 3); label(Q(...V.b), "b", css("--ink"));
    arrow(O, Q(...V.p), css("--accent"), 3.6); label(Q(...V.p), "p", css("--accent"), 10, 4);
    $("readout").innerHTML = `<span class="hi">p = (${g(V.p[0])}, ${g(V.p[1])})</span><span>e = (${g(e[0])}, ${g(e[1])})</span><span${Math.abs(ae) < 1e-6 ? ' class="good"' : ""}>a · e = ${g(ae)}</span>` +
      (ok ? '<span class="good">p is the closest point on the line</span>' : '<span>not yet: e must be perpendicular to a</span>');
  } else if (view.kind === "null"){
    const V = view, r = nonzeroRow(V.A), far = 4*N, d = det(V.A);
    let nd = null;
    if (!r) { ctx.fillStyle = css("--area"); ctx.fillRect(0, 0, w, h); }
    else if (Math.abs(d) < 1e-9){ nd = [-r[1], r[0]]; const k = far / Math.hypot(...nd);
      ctx.strokeStyle = css("--accent"); ctx.globalAlpha = .35; ctx.lineWidth = 8; line(Q(-nd[0]*k, -nd[1]*k), Q(nd[0]*k, nd[1]*k)); ctx.globalAlpha = 1;
      label(Q(nd[0]*1.6/Math.hypot(...nd)*2, nd[1]*1.6/Math.hypot(...nd)*2), "N(A)", css("--accent")); }
    const xp = particular(V);
    if (xp && nd){ const k = far / Math.hypot(...nd); ctx.strokeStyle = css("--ihat"); ctx.lineWidth = 2.6; line(Q(xp[0]-nd[0]*k, xp[1]-nd[1]*k), Q(xp[0]+nd[0]*k, xp[1]+nd[1]*k)); }
    arrow(O, Q(...V.x), css("--ink"), 3); label(Q(...V.x), "x", css("--ink"), 10, -6);
    const ax = matvec(V.A, V.x);
    let status;
    if (V.b && V.b.length === 2) status = near(ax[0], V.b[0]) && near(ax[1], V.b[1]) ? '<span class="good">Ax = b</span>' : `<span>b = (${g(V.b[0])}, ${g(V.b[1])})</span>`;
    else status = isZero(ax) ? '<span class="good">Ax = 0</span>' : "";
    $("readout").innerHTML = `<span>x = (${g(V.x[0])}, ${g(V.x[1])})</span><span class="hi">Ax = (${g(ax[0])}, ${g(ax[1])})</span>${status}<span>${!r ? "N(A) is the whole plane" : nd ? "N(A) is a line" : "N(A) is only 0"}</span>`;
  } else {
    const V = view, cols = [css("--ihat"), css("--jhat")], far = 4*N;
    for (let i = 0; i < 2; i++){ const [a, c] = V.A[i], rr = V.b[i]; ctx.strokeStyle = cols[i]; ctx.lineWidth = 2.6;
      if (Math.abs(c) > 1e-12) line(Q(-far, (rr + a*far)/c), Q(far, (rr - a*far)/c)); else if (Math.abs(a) > 1e-12) line(Q(rr/a, -far), Q(rr/a, far)); }
    const sol = rowSolution(V);
    if (sol){ const S = Q(...sol); ctx.fillStyle = css("--ink"); ctx.beginPath(); ctx.arc(S[0], S[1], 5, 0, 7); ctx.fill(); label(S, `(${g(sol[0])}, ${g(sol[1])})`, css("--ink"), 10, -10); }
    const coef = (v, first) => { const m = Math.abs(v), sgn = v < 0 ? (first ? "−" : "− ") : (first ? "" : "+ "); return sgn + (m === 1 ? "" : m); };
    const eq = i => { const a = g(V.A[i][0]), c = g(V.A[i][1]); const parts = [];
      if (a) parts.push(coef(a, true) + "x"); if (c) parts.push(coef(c, !parts.length) + "y");
      return `${parts.join(" ") || "0"} = ${g(V.b[i])}`.replace("−", "−"); };
    $("readout").innerHTML = `<span style="color:var(--ihat)">${eq(0)}</span><span style="color:var(--jhat)">${eq(1)}</span><span>${sol ? "the lines meet once" : rankOf(V.A.map((r, i) => [r[0], r[1], V.b[i]])) > rankOf(V.A) ? "parallel lines: no solution" : "same line: infinitely many solutions"}</span>`;
  }
  ctx.fillStyle = css("--ink"); ctx.beginPath(); ctx.arc(O[0], O[1], 3.2, 0, 7); ctx.fill();
}
const PALETTE = ["--ink", "--ihat", "--jhat", "--accent", "--muted"];
function drawArrows(w, h){
  const ext = extent(), s = Math.min(w, h) / (2*ext), ox = w/2, oy = h/2;
  const Q = (x, y) => [ox + x*s, oy - y*s], N = Math.ceil(Math.max(w, h) / s) + 2;
  ctx.strokeStyle = css("--grid"); ctx.lineWidth = 1;
  for (let i = -N; i <= N; i++){ if (i){ line(Q(i, -N), Q(i, N)); line(Q(-N, i), Q(N, i)); } }
  ctx.strokeStyle = css("--muted"); ctx.globalAlpha = .6; ctx.lineWidth = 1.4; line(Q(-N, 0), Q(N, 0)); line(Q(0, -N), Q(0, N)); ctx.globalAlpha = 1;
  const its = view.items, f = v => +(+(Math.abs(v) < 5e-4 ? 0 : v).toFixed(3));
  const chain = view.chain !== false;
  if (chain) for (let k = 1; k < its.length; k++){ ctx.setLineDash([5, 5]); ctx.strokeStyle = css("--muted"); ctx.lineWidth = 1.4; line(Q(...its[k-1].v), Q(...its[k].v)); ctx.setLineDash([]); }
  // later arrows first so the starting vector stays on top when they coincide
  for (let k = its.length - 1; k >= 0; k--){ const c = css(PALETTE[k % PALETTE.length]); arrow(Q(0, 0), Q(...its[k].v), c, k === 0 ? 3.6 : 2.8); }
  const back0 = chain && its.length > 1 && near(its[0].v[0], its[its.length-1].v[0]) && near(its[0].v[1], its[its.length-1].v[1]);
  const seen = [];
  its.forEach((it, k) => { if (back0 && k === its.length - 1) return; const P = Q(...it.v); const dup = seen.filter(p => Math.hypot(p[0]-P[0], p[1]-P[1]) < 14).length; seen.push(P);
    label(P, it.label, css(PALETTE[k % PALETTE.length]), 10, -8 + dup*16); });
  if (back0){ const P = Q(...its[0].v); ctx.strokeStyle = css("--ok"); ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(P[0], P[1], 11, 0, 7); ctx.stroke();
    label(P, "back to " + its[0].label + " ✓", css("--ok"), 16, 18); }
  ctx.fillStyle = css("--ink"); ctx.beginPath(); ctx.arc(ox, oy, 3.2, 0, 7); ctx.fill();
  const dots = !chain && its.length >= 2 ? (() => { const a = its[0].v, b = its[1].v, d = dot(a, b), c = d / (Math.hypot(...a) * Math.hypot(...b) || 1);
    return `<span${Math.abs(d) < 1e-6 ? ' class="good"' : ' class="hi"'}>${its[0].label} · ${its[1].label} = ${f(d)}</span><span>angle = ${f(Math.acos(Math.max(-1, Math.min(1, c))) * 180 / Math.PI)}°</span>`; })() : "";
  const back = chain && its.length > 1 && near(its[0].v[0], its[its.length-1].v[0]) && near(its[0].v[1], its[its.length-1].v[1]);
  $("readout").innerHTML = its.map(it => `<span>${it.label} = (${f(it.v[0])}, ${f(it.v[1])})</span>`).join("") + (back ? '<span class="good">back where it started</span>' : "") + dots;
}
function drawFit(w, h){
  const V = view, best = bestFit(V.t, V.b), pad = 44;
  let t0 = Math.min(...V.t), t1 = Math.max(...V.t); if (t1 - t0 < 1e-9){ t0 -= 1; t1 += 1; } const tm = (t1 - t0) * .15; t0 -= tm; t1 += tm;
  const ys = [...V.b, V.C + V.D*t0, V.C + V.D*t1, 0]; let y0 = Math.min(...ys), y1 = Math.max(...ys); if (y1 - y0 < 1e-9){ y0 -= 1; y1 += 1; } const ym = (y1 - y0) * .12; y0 -= ym; y1 += ym;
  const X = t => pad + (t - t0) / (t1 - t0) * (w - pad - 16), Y = y => h - pad + 8 - (y - y0) / (y1 - y0) * (h - pad - 24);
  const step = v => { const r = Math.pow(10, Math.floor(Math.log10(v))); return v / r > 5 ? r * 2 : v / r > 2 ? r : r / 2; };
  const st = step((t1 - t0) / 2), sy = step((y1 - y0) / 2);
  ctx.font = `500 11px ${css("--f-mono")}`; ctx.lineWidth = 1;
  for (let t = Math.ceil(t0 / st) * st; t <= t1; t += st){ ctx.strokeStyle = css("--grid"); line([X(t), Y(y0)], [X(t), Y(y1)]); ctx.fillStyle = css("--muted"); ctx.fillText(fmt(t), X(t) - 6, h - pad + 24); }
  for (let y = Math.ceil(y0 / sy) * sy; y <= y1; y += sy){ ctx.strokeStyle = css("--grid"); line([X(t0), Y(y)], [X(t1), Y(y)]); ctx.fillStyle = css("--muted"); ctx.fillText(fmt(y), 6, Y(y) + 4); }
  ctx.strokeStyle = css("--muted"); ctx.globalAlpha = .6; ctx.lineWidth = 1.4; if (y0 < 0 && y1 > 0) line([X(t0), Y(0)], [X(t1), Y(0)]); if (t0 < 0 && t1 > 0) line([X(0), Y(y0)], [X(0), Y(y1)]); ctx.globalAlpha = 1;
  ctx.fillStyle = css("--muted"); ctx.fillText("t", w - 14, h - pad + 24);
  const atBest = best && near(V.C, best[0], 1e-3) && near(V.D, best[1], 1e-3);
  if (best && !atBest){ ctx.setLineDash([3, 5]); ctx.strokeStyle = css("--muted"); ctx.lineWidth = 1.6; line([X(t0), Y(best[0] + best[1]*t0)], [X(t1), Y(best[0] + best[1]*t1)]); ctx.setLineDash([]); }
  V.t.forEach((t, i) => { ctx.setLineDash([5, 4]); ctx.strokeStyle = css("--jhat"); ctx.lineWidth = 2.2; line([X(t), Y(V.b[i])], [X(t), Y(V.C + V.D*t)]); ctx.setLineDash([]); });
  ctx.strokeStyle = css("--accent"); ctx.lineWidth = 3; line([X(t0), Y(V.C + V.D*t0)], [X(t1), Y(V.C + V.D*t1)]);
  V.t.forEach((t, i) => { ctx.fillStyle = css("--ink"); ctx.beginPath(); ctx.arc(X(t), Y(V.b[i]), 5, 0, 7); ctx.fill(); });
  const E = sse(V.t, V.b, V.C, V.D), Eb = best ? sse(V.t, V.b, best[0], best[1]) : null;
  $("readout").innerHTML = `<span>C = ${fmt(V.C)}, D = ${fmt(V.D)}</span><span class="hi">E = sum of e² = ${fmt(E)}</span>` + (Eb == null ? "" : atBest ? '<span class="good">smallest possible E</span>' : `<span>smallest possible: ${fmt(Eb)}</span>`);
}
function drawFour(w, h){
  const M = view.A, r = rankOf(M), gap = 18, wide = w > 560;
  const pw = wide ? (w - gap) / 2 : w, ph = wide ? h : (h - gap) / 2;
  const panels = [{x0: 0, y0: 0, title: "Input space (x)"}, {x0: wide ? pw + gap : 0, y0: wide ? 0 : ph + gap, title: "Output space (Ax)"}];
  const rowDir = nonzeroRow(M), colDir = (() => { const c1 = [M[0][0], M[1][0]], c2 = [M[0][1], M[1][1]]; return Math.hypot(...c1) > 1e-9 ? c1 : Math.hypot(...c2) > 1e-9 ? c2 : null; })();
  const perp = v => v ? [-v[1], v[0]] : null;
  panels.forEach((p, k) => {
    const s = Math.min(pw, ph) / 6.5, ox = p.x0 + pw/2, oy = p.y0 + ph/2 + 8, R = Math.max(pw, ph);
    const Q = (x, y) => [ox + x*s, oy - y*s];
    ctx.save(); ctx.beginPath(); ctx.rect(p.x0, p.y0, pw, ph); ctx.clip();
    ctx.strokeStyle = css("--grid"); ctx.lineWidth = 1; const n = Math.ceil(R / s);
    for (let i = -n; i <= n; i++){ if (i){ line(Q(i, -n), Q(i, n)); line(Q(-n, i), Q(n, i)); } }
    ctx.strokeStyle = css("--muted"); ctx.globalAlpha = .6; line(Q(-n, 0), Q(n, 0)); line(Q(0, -n), Q(0, n)); ctx.globalAlpha = 1;
    const big = (dir, color, name, dashed) => { if (!dir) return; const u = Math.hypot(...dir), kk = 3*n/u;
      ctx.strokeStyle = color; ctx.lineWidth = 3; ctx.setLineDash(dashed ? [7, 6] : []); line(Q(-dir[0]*kk, -dir[1]*kk), Q(dir[0]*kk, dir[1]*kk)); ctx.setLineDash([]);
      label(Q(dir[0]/u*2.4, dir[1]/u*2.4), name, color, 8, -8); };
    const fill = (color, name) => { ctx.fillStyle = color; ctx.globalAlpha = .12; ctx.fillRect(p.x0, p.y0, pw, ph); ctx.globalAlpha = 1; label([p.x0 + 14, p.y0 + ph - 16], name, color, 0, 0); };
    if (k === 0){
      if (r === 2) fill(css("--ihat"), "row space = whole plane, nullspace = {0}");
      else if (r === 1){ big(rowDir, css("--ihat"), "row space"); big(perp(rowDir), css("--accent"), "nullspace"); }
      else fill(css("--accent"), "nullspace = whole plane");
    } else {
      if (r === 2) fill(css("--jhat"), "column space = whole plane, left nullspace = {0}");
      else if (r === 1){ big(colDir, css("--jhat"), "column space"); big(perp(colDir), css("--muted"), "left nullspace", true); }
      else fill(css("--muted"), "left nullspace = whole plane");
    }
    ctx.fillStyle = css("--ink"); ctx.beginPath(); ctx.arc(ox, oy, 3, 0, 7); ctx.fill();
    ctx.restore();
    ctx.fillStyle = css("--muted"); ctx.font = `600 12px ${css("--f-body")}`; ctx.fillText(p.title.toUpperCase(), p.x0 + 12, p.y0 + 18);
    if (k === 0 && wide){ ctx.strokeStyle = css("--line"); ctx.lineWidth = 1; line([pw + gap/2, 10], [pw + gap/2, h - 10]); }
  });
  $("readout").innerHTML = `<span class="hi">rank r = ${r}</span><span>dim row space = ${r}</span><span>dim nullspace = ${2 - r}</span><span>dim column space = ${r}</span><span>dim left nullspace = ${2 - r}</span>`;
}
function line(a,b){ctx.beginPath(); ctx.moveTo(a[0],a[1]); ctx.lineTo(b[0],b[1]); ctx.stroke();}
function poly(pts, fill, stroke, lw, alpha=1){ctx.beginPath(); pts.forEach((p,i)=> i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1])); ctx.closePath(); ctx.globalAlpha = alpha; ctx.fillStyle = fill; ctx.fill(); ctx.globalAlpha = 1; if (stroke){ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke();}}
function arrow(a, b, col, lw){const dx=b[0]-a[0], dy=b[1]-a[1], L=Math.hypot(dx,dy); ctx.strokeStyle=col; ctx.fillStyle=col; ctx.lineWidth=lw; ctx.lineCap="round";
  if (L < 2) return; const ux=dx/L, uy=dy/L, hs=Math.min(12, L*.45);
  line(a, [b[0]-ux*hs*.8, b[1]-uy*hs*.8]); ctx.beginPath(); ctx.moveTo(b[0],b[1]); ctx.lineTo(b[0]-ux*hs-uy*hs*.55, b[1]-uy*hs+ux*hs*.55); ctx.lineTo(b[0]-ux*hs+uy*hs*.55, b[1]-uy*hs-ux*hs*.55); ctx.closePath(); ctx.fill();}
new ResizeObserver(size).observe(cv);
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
new MutationObserver(draw).observe(document.documentElement, {attributes:true, attributeFilter:["data-theme"]});

/* ---------- editor ---------- */
const ta = $("src"), hl = $("hl"), gut = $("gutter");
function esc(s){return s.replace(/&/g,"&amp;").replace(/</g,"&lt;")}
function highlight(src){
  const re = /(#[^\n]*)|("(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*')|\b(\d+\.?\d*(?:e-?\d+)?)\b|\b(import|as|from|def|return|for|in|if|else|elif|while|True|False|None|and|or|not|lambda|class)\b|\b([A-Za-z_]\w*)(?=\()/g;
  let out = "", lastI = 0, m;
  while ((m = re.exec(src))){ out += esc(src.slice(lastI, m.index));
    const cls = m[1]?"com":m[2]?"str":m[3]?"num":m[4]?"kw":"fn"; out += `<span class="tk-${cls}">${esc(m[0])}</span>`; lastI = re.lastIndex; }
  return out + esc(src.slice(lastI)) + "\n";
}
function sync(){
  hl.innerHTML = highlight(ta.value);
  const n = ta.value.split("\n").length; gut.textContent = Array.from({length:n},(_, i)=>i+1).join("\n");
  ta.style.height = "auto"; ta.style.height = Math.max(ta.scrollHeight, 200) + "px";
  ta.style.width = Math.max(hl.scrollWidth, $("codewrap").clientWidth) + "px";
  store("code:" + S.slug, ta.value === original ? null : ta.value);
}
ta.addEventListener("input", sync);
ta.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter"){ e.preventDefault(); run(); return; }
  if (e.key === "Tab"){ e.preventDefault(); const s = ta.selectionStart, en = ta.selectionEnd; ta.setRangeText("    ", s, en, "end"); sync(); }
  if (e.key === "Enter" && !e.shiftKey){ const s = ta.selectionStart; const ls = ta.value.lastIndexOf("\n", s-1)+1; const ind = ta.value.slice(ls, s).match(/^\s*/)[0] + (/:\s*$/.test(ta.value.slice(ls, s)) ? "    " : "");
    if (ind){ e.preventDefault(); ta.setRangeText("\n"+ind, s, ta.selectionEnd, "end"); sync(); } }
});

/* ---------- output + python ---------- */
const out = $("out");
let ready = false;
window.__pyout = s => { const sp = document.createElement("span"); sp.textContent = s; out.appendChild(sp); out.scrollTop = out.scrollHeight; };
window.__pyhint = h => { if (!h) return; const sp = document.createElement("span"); sp.className = "hint"; sp.textContent = "Hint: " + h + "\n"; out.appendChild(sp); out.scrollTop = out.scrollHeight; };
window.__pyerr = s => { const sp = document.createElement("span"); sp.className = "err"; sp.textContent = s + "\n"; out.appendChild(sp); out.scrollTop = out.scrollHeight; };
const L2 = M => Array.from(M).map(r => Array.from(r));
window.__pyshow = (M, vs) => { last = {kind:"transform", M:L2(M), vecs:L2(vs).filter(v => v.length === 2)}; setView(last); };
window.__pycombo = (M, x, b) => { last = {kind:"combo", A:L2(M), x:Array.from(x), b:Array.from(b)}; setView(last); };
window.__pyrows = (M, b) => { last = {kind:"rows", A:L2(M), b:Array.from(b)}; setView(last); };
window.__pytable = items => { last = {kind:"table", items: Array.from(items).map(t => ({label: String(t[0]), M: L2(t[1]), piv: Array.from(t[2]).map(Number), ndim: Number(t[3])}))};
  last.items.forEach(it => { if (it.ndim === 1) it.vec = it.M.map(r => r[0]); }); setView(last); };
window.__pynull = (M, x, b) => { last = {kind:"null", A:L2(M), x:Array.from(x), b:Array.from(b)}; setView(last); };
window.__pyproj = (a, b, p, auto) => { last = {kind:"proj", a:Array.from(a), b:Array.from(b), p:Array.from(p), auto:!!auto}; setView(last); };
window.__pyfit = (t, b, C, D) => { last = {kind:"fit", t:Array.from(t).map(Number), b:Array.from(b).map(Number), C:Number(C), D:Number(D)}; setView(last); };
window.__pyarrows = (items, chain) => { last = {kind:"arrows", chain: chain !== false, items: Array.from(items).map(t => ({label: String(t[0]), v: Array.from(t[1]).map(Number)}))}; setView(last); };
window.__pyfour = M => { last = {kind:"four", A:L2(M)}; setView(last); };
window.__pyready = () => { ready = true; clearInterval(loadTimer); $("pystatus").textContent = "Python ready"; $("pystatus").classList.add("ready"); $("run").disabled = false; };
let loadDots = 0; const loadTimer = setInterval(() => { if (ready) return; loadDots = (loadDots + 1) % 4; $("pystatus").textContent = "Starting Python" + ".".repeat(loadDots); }, 450);
setTimeout(() => { if (!ready) $("pystatus").textContent = "Still loading Python… (first visit only)"; }, 6000);
function sys(msg){ const sp = document.createElement("span"); sp.className = "sys"; sp.textContent = msg + "\n"; out.appendChild(sp); }
function run(){
  if (!ready) return;
  out.textContent = ""; last = null;
  const src = ta.value.replace(/^[ \t]*import numpy as np[ \t]*$/m, "");
  const t = performance.now();
  try { window.__pyrun(src); } catch(err){ window.__pyerr(String(err && err.message || err)); }
  runs += 1;
  sys(`— ran in ${Math.round(performance.now()-t)} ms` + (last ? "" : " · nothing was drawn (call a drawing function such as show, proj or fit)"));
  if (last && check(last, runs)) markDone();
  renderTask();
}
$("run").onclick = run;
$("clear").onclick = () => out.textContent = "";
$("reset").onclick = () => { ta.value = original; sync(); };


/* ---------- sliders: change the numbers without typing ---------- */
const SL = {
  combo: V => [["x₁", "x", 0, -5, 5, .5], ["x₂", "x", 1, -5, 5, .5]],
  null: V => [["x₁", "x", 0, -5, 5, .5], ["x₂", "x", 1, -5, 5, .5]],
  transform: V => [["a", "M", [0,0], -3, 3, .25], ["b", "M", [0,1], -3, 3, .25], ["c", "M", [1,0], -3, 3, .25], ["d", "M", [1,1], -3, 3, .25]],
  four: V => [["a", "A", [0,0], -6, 6, 1], ["b", "A", [0,1], -6, 6, 1], ["c", "A", [1,0], -6, 6, 1], ["d", "A", [1,1], -6, 6, 1]],
  rows: V => [["b₁", "b", 0, -12, 12, 1], ["b₂", "b", 1, -12, 12, 1]],
  proj: V => V.auto ? [["b₁", "b", 0, -5, 5, .5], ["b₂", "b", 1, -5, 5, .5], ["a₁", "a", 0, -4, 4, .5], ["a₂", "a", 1, -4, 4, .5]] : null,
  fit: V => { const bf = bestFit(V.t, V.b) || [0, 0], r = v => Math.round(v * 10) / 10;
    return [["C", "C", null, r(bf[0]) - 4, r(bf[0]) + 4, .1], ["D", "D", null, r(bf[1]) - 3, r(bf[1]) + 3, .1]]; },
};
function getv(V, key, idx){ if (idx === null) return V[key]; return Array.isArray(idx) ? V[key][idx[0]][idx[1]] : V[key][idx]; }
function setv(V, key, idx, val){ if (idx === null){ V[key] = val; return; } if (Array.isArray(idx)) V[key][idx[0]][idx[1]] = val; else V[key][idx] = val; }
function renderSliders(){
  let box = $("sliders");
  if (!box){ box = document.createElement("div"); box.id = "sliders"; box.className = "sliders"; document.querySelector(".figure").appendChild(box); }
  const spec = SL[view.kind] ? SL[view.kind](view) : null;
  if (!spec || (view.kind === "rows" && (!view.b || view.b.length !== 2))){ box.hidden = true; box.innerHTML = ""; return; }
  box.hidden = false;
  const fmtv = v => String(+v.toFixed(3)).replace("-", "−");
  box.innerHTML = '<div class="sl-h">Drag to try values</div>' + spec.map(([lab, key, idx, lo, hi, st], k) => {
    const v = getv(view, key, idx);
    return `<label class="sl"><span class="sl-l">${lab}</span><input type="range" id="sl${k}" min="${lo}" max="${hi}" step="${st}" value="${v}"><span class="sl-v" id="slv${k}">${fmtv(v)}</span></label>`;
  }).join("");
  spec.forEach(([lab, key, idx], k) => {
    $("sl" + k).addEventListener("input", e => {
      const V = JSON.parse(JSON.stringify(view)); const val = +e.target.value;
      setv(V, key, idx, val); $("slv" + k).textContent = fmtv(val);
      if (V.kind === "transform"){ A = V.M.map(r => r.slice()); to = A; }
      if (V.kind === "proj"){ if (Math.hypot(...V.a) < 1e-9) return; V.p = projOf(V.a, V.b); }
      last = V; setView(V, true); runs += 1;
      if (check(last, runs)) markDone(); renderTask();
    });
  });
}

/* ---------- page wiring ---------- */
const original = ta.defaultValue;
const saved = load("code:" + S.slug);
if (typeof saved === "string") ta.value = saved;
const narrow = matchMedia("(max-width: 1020px)");
function renderTask(){
  if (!$("exercise")) return;
  const ok = done.has(S.slug);
  $("exercise").classList.toggle("ok", ok);
  $("hint").textContent = ok ? "Done. Move on when you're ready." : narrow.matches ? "Edit the code below and press Run." : "Edit the code below and press Run. The picture is on the right.";
}
narrow.addEventListener("change", renderTask);
document.addEventListener("keydown", e => {
  if (e.target === ta) return;
  const a = e.key === "ArrowRight" ? $("next") : e.key === "ArrowLeft" ? $("prev") : null;
  if (a && a.getAttribute("href")) location.href = a.getAttribute("href");
});
sync(); setView(S.preview); renderTask(); paintSteps();

/* ---------- start Python ---------- */
function boot(){
  fetch(S.assets + "prelude.py").then(r => r.text()).then(src => __BRYTHON__.runPythonSource(src))
    .catch(e => { $("pystatus").textContent = "Python failed to load"; console.error(e); });
}
if (window.__BRYTHON__) boot(); else document.getElementById("brython").addEventListener("load", boot);
})();
