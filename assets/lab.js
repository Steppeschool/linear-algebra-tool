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
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function size(){const r = cv.getBoundingClientRect(), d = devicePixelRatio || 1; cv.width = Math.round(r.width*d); cv.height = Math.round(r.height*d); ctx.setTransform(d,0,0,d,0,0); draw();}
function setView(V){ view = V; setTarget(V.kind === "transform" ? V.M : I2); setLegend(); draw(); }
function setTarget(M){from = A.map(r => r.slice()); to = M; t0 = performance.now(); if (reduce){A = M; draw(); return;} if(!anim){anim = true; requestAnimationFrame(step);} }
function step(now){let k = Math.min(1, (now - t0)/750); const e = k<.5 ? 4*k*k*k : 1 - Math.pow(-2*k+2,3)/2;
  A = [[from[0][0]+(to[0][0]-from[0][0])*e, from[0][1]+(to[0][1]-from[0][1])*e],[from[1][0]+(to[1][0]-from[1][0])*e, from[1][1]+(to[1][1]-from[1][1])*e]];
  draw(); if (k < 1) requestAnimationFrame(step); else anim = false;}
function setLegend(){
  const sw = (c, t) => `<span><i style="background:var(${c})"></i>${t}</span>`;
  $("legend").innerHTML = view.kind === "transform" ? sw("--ihat","(1, 0) lands on column 1") + sw("--jhat","(0, 1) lands on column 2")
    : view.kind === "combo" ? sw("--ihat","x₁ · column 1") + sw("--jhat","x₂ · column 2") + sw("--accent","Ax")
    : sw("--ihat","equation 1") + sw("--jhat","equation 2");
}
function rowSolution(V){ const d = det(V.A); if (Math.abs(d) < 1e-12) return null; return [(V.b[0]*V.A[1][1] - V.A[0][1]*V.b[1])/d, (V.A[0][0]*V.b[1] - V.A[1][0]*V.b[0])/d]; }
function extent(){
  const V = view; let pts = [];
  if (V.kind === "combo"){ const a1=[V.A[0][0],V.A[1][0]], a2=[V.A[0][1],V.A[1][1]], p1=[a1[0]*V.x[0], a1[1]*V.x[0]], r=Ax(V); pts = [a1, a2, p1, r]; if (V.b.length===2) pts.push(V.b); }
  else if (V.kind === "rows"){ const s = rowSolution(V); pts = s ? [s] : []; }
  else return 4.2;
  return Math.max(2.5, ...pts.map(p => Math.max(Math.abs(p[0]), Math.abs(p[1])))) * 1.2;
}
function label(p, text, col, dx=8, dy=-8){ ctx.fillStyle = col; ctx.font = `600 12.5px ${css("--f-mono")}`; ctx.fillText(text, p[0]+dx, p[1]+dy); }
function draw(){
  const w = cv.clientWidth, h = cv.clientHeight; if (!w || !h) return;
  ctx.clearRect(0,0,w,h);
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
  } else {
    const V = view, cols = [css("--ihat"), css("--jhat")], far = 4*N;
    for (let i = 0; i < 2; i++){ const [a, c] = V.A[i], rr = V.b[i]; ctx.strokeStyle = cols[i]; ctx.lineWidth = 2.6;
      if (Math.abs(c) > 1e-12) line(Q(-far, (rr + a*far)/c), Q(far, (rr - a*far)/c)); else if (Math.abs(a) > 1e-12) line(Q(rr/a, -far), Q(rr/a, far)); }
    const sol = rowSolution(V);
    if (sol){ const S = Q(...sol); ctx.fillStyle = css("--ink"); ctx.beginPath(); ctx.arc(S[0], S[1], 5, 0, 7); ctx.fill(); label(S, `(${g(sol[0])}, ${g(sol[1])})`, css("--ink"), 10, -10); }
    const eq = i => { const a = g(V.A[i][0]), c = g(V.A[i][1]); return `${a}x ${c < 0 ? "−" : "+"} ${Math.abs(c)}y = ${g(V.b[i])}`; };
    $("readout").innerHTML = `<span style="color:var(--ihat)">${eq(0)}</span><span style="color:var(--jhat)">${eq(1)}</span><span>${sol ? "the lines meet once" : "parallel lines"}</span>`;
  }
  ctx.fillStyle = css("--ink"); ctx.beginPath(); ctx.arc(O[0], O[1], 3.2, 0, 7); ctx.fill();
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
window.__pyerr = s => { const sp = document.createElement("span"); sp.className = "err"; sp.textContent = s + "\n"; out.appendChild(sp); out.scrollTop = out.scrollHeight; };
const L2 = M => Array.from(M).map(r => Array.from(r));
window.__pyshow = (M, vs) => { last = {kind:"transform", M:L2(M), vecs:L2(vs).filter(v => v.length === 2)}; setView(last); };
window.__pycombo = (M, x, b) => { last = {kind:"combo", A:L2(M), x:Array.from(x), b:Array.from(b)}; setView(last); };
window.__pyrows = (M, b) => { last = {kind:"rows", A:L2(M), b:Array.from(b)}; setView(last); };
window.__pyready = () => { ready = true; $("pystatus").textContent = "Python ready"; $("pystatus").classList.add("ready"); $("run").disabled = false; };
function sys(msg){ const sp = document.createElement("span"); sp.className = "sys"; sp.textContent = msg + "\n"; out.appendChild(sp); }
function run(){
  if (!ready) return;
  out.textContent = ""; last = null;
  const src = ta.value.replace(/^[ \t]*import numpy as np[ \t]*$/m, "");
  const t = performance.now();
  try { window.__pyrun(src); } catch(err){ window.__pyerr(String(err && err.message || err)); }
  runs += 1;
  sys(`— ran in ${Math.round(performance.now()-t)} ms` + (last ? "" : " · nothing was drawn (use show, combo or rowpic)"));
  if (last && check(last, runs)) markDone();
  renderTask();
}
$("run").onclick = run;
$("clear").onclick = () => out.textContent = "";
$("reset").onclick = () => { ta.value = original; sync(); };


/* ---------- page wiring ---------- */
const original = ta.defaultValue;
const saved = load("code:" + S.slug);
if (typeof saved === "string") ta.value = saved;
const narrow = matchMedia("(max-width: 1020px)");
function renderTask(){
  const ok = done.has(S.slug);
  $("exercise").classList.toggle("ok", ok);
  $("hint").textContent = ok ? "Done. Move on when you're ready." : narrow.matches ? "Edit the code below and press Run." : "Edit the code on the right and press Run.";
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
