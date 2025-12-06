// Φ-Navigation v2 — фрактальная навигация ORION OpenSite v2

const PAGES = {
  "atlas": "phi_atlas.html",
  "floors": "phi_floors.html",
  "helion": "phi_helion.html",
  "inner": "phi_inner_core.html",
  "x": "phi_x_domain.html"
};

export function initPhiNav() {
  document.querySelectorAll("[data-phi-nav]").forEach(el => {
    el.addEventListener("click", () => {
      const page = el.getAttribute("data-phi-nav");
      if (PAGES[page]) {
        window.location.href = PAGES[page];
      }
    });
  });
}

window.addEventListener("DOMContentLoaded", initPhiNav);
