/* Loads a lesson from linearalgebra.steppeschool.com into another page (Kajabi).
   Usage: <div class="la-embed" data-la-src="https://linearalgebra.steppeschool.com/embed/lesson-1/column-space.html"></div>
          <script src="https://linearalgebra.steppeschool.com/assets/embed.js"></script> */
(() => {
  const root = document.querySelector("[data-la-src]");
  if (!root) return;
  const base = new URL(root.getAttribute("data-la-src")).origin + "/";

  // Break out of the host page's narrow content column: span the window (max 1380px), centred.
  const widen = () => {
    const vw = document.documentElement.clientWidth, w = Math.min(vw - 32, 1380);
    document.querySelectorAll(".la-embed").forEach(el => {
      el.style.marginLeft = el.style.marginRight = "0"; el.style.width = "";
      const r = el.getBoundingClientRect();
      if (r.width >= w - 1) return;
      el.style.width = w + "px";
      el.style.maxWidth = "none";
      el.style.marginLeft = ((vw - w) / 2 - r.left) + "px";
    });
  };
  widen();
  addEventListener("resize", widen);
  new ResizeObserver(widen).observe(document.documentElement);
  const load = src => new Promise((ok, fail) => { const s = document.createElement("script"); s.src = src; s.onload = ok; s.onerror = fail; document.body.appendChild(s); return s; });
  // Members-only lessons are stored sealed (AES-GCM); the key is in the Kajabi lesson body: data-la-key="...".
  const b64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
  const unseal = async doc => {
    const box = doc.getElementById("la-sealed");
    if (!box) return doc;
    const k = root.getAttribute("data-la-key");
    if (!k) throw new Error("This lesson needs data-la-key");
    const { iv, ct } = JSON.parse(box.textContent);
    const key = await crypto.subtle.importKey("raw", b64(k), "AES-GCM", false, ["decrypt"]);
    const plain = await crypto.subtle.decrypt({ name: "AES-GCM", iv: b64(iv) }, key, b64(ct));
    return new DOMParser().parseFromString("<body>" + new TextDecoder().decode(plain) + "</body>", "text/html");
  };
  fetch(root.getAttribute("data-la-src")).then(r => r.text()).then(async html => {
    const doc = await unseal(new DOMParser().parseFromString(html, "text/html"));
    const cfg = JSON.parse(doc.getElementById("la-config").textContent);
    cfg.assets = base + "assets/";
    root.innerHTML = doc.body.querySelector("main").outerHTML;
    window.SLIDE = cfg;
    const b = document.createElement("script"); b.id = "brython"; b.src = "https://cdn.jsdelivr.net/npm/brython@3.12.4/brython.min.js";
    await new Promise((ok, fail) => { b.onload = ok; b.onerror = fail; document.body.appendChild(b); });
    await load(base + "assets/lab.js");
  }).catch(e => { root.innerHTML = '<p style="padding:16px">This lesson could not be loaded. Please refresh the page.</p>'; console.error(e); });
})();
