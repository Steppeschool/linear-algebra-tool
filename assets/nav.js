/* Chapter and lesson menus in the top bar: one open at a time, close on outside click or Esc. */
(() => {
  const menus = [...document.querySelectorAll("details.menu")];
  menus.forEach(m => m.addEventListener("toggle", () => { if (m.open) menus.forEach(o => { if (o !== m) o.open = false; }); }));
  document.addEventListener("click", e => { if (!e.target.closest("details.menu")) menus.forEach(m => m.open = false); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") menus.forEach(m => m.open = false); });
})();
