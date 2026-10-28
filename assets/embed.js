/* Loads a lesson from linearalgebra.steppeschool.com into another page (Kajabi).
   Usage: <div class="la-embed" data-la-src="https://linearalgebra.steppeschool.com/embed/lesson-1/column-space.html"></div>
          <script src="https://linearalgebra.steppeschool.com/assets/embed.js"></script> */
(() => {
  const root = document.querySelector("[data-la-src]");
  if (!root) return;
  const base = new URL(root.getAttribute("data-la-src")).origin + "/";
  const load = src => new Promise((ok, fail) => { const s = document.createElement("script"); s.src = src; s.onload = ok; s.onerror = fail; document.body.appendChild(s); return s; });
  fetch(root.getAttribute("data-la-src")).then(r => r.text()).then(async html => {
    const doc = new DOMParser().parseFromString(html, "text/html");
    const cfg = JSON.parse(doc.getElementById("la-config").textContent);
    cfg.assets = base + "assets/";
    root.innerHTML = doc.body.querySelector("main").outerHTML;
    window.SLIDE = cfg;
    const b = document.createElement("script"); b.id = "brython"; b.src = "https://cdn.jsdelivr.net/npm/brython@3.12.4/brython.min.js";
    await new Promise((ok, fail) => { b.onload = ok; b.onerror = fail; document.body.appendChild(b); });
    await load(base + "assets/lab.js");
  }).catch(e => { root.innerHTML = '<p style="padding:16px">This lesson could not be loaded. Please refresh the page.</p>'; console.error(e); });
})();
