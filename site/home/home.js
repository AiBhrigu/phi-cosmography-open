document.addEventListener("DOMContentLoaded", () => {

  const root = document.getElementById("phi-home-root");

  root.innerHTML = `
    <h1 class="phi-title">Phi-Cosmography</h1>
    <p class="phi-sub">Golden-Ratio Space-Mapping Framework</p>

    <div class="phi-nav">
      <a href="../φ-atlas/atlas.html">Atlas</a>
      <a href="../φ-floors/floors.html">Floors</a>
      <a href="../φ-helion/helion.html">Helion</a>
      <a href="../φ-inner/core.html">Inner Core</a>
      <a href="../φ-domain/x.html">X-Domain</a>
    </div>

    <pre class="ascii-block">${ascii()}</pre>

    <p class="phi-build">Build v2.3 — Φ-Stable</p>
  `;

  // SunCore canvas
  const c = document.getElementById("phi-sun-core");
  const ctx = c.getContext("2d");

  function resize() {
    c.width = window.innerWidth;
    c.height = window.innerHeight;
  }

  function draw() {
    ctx.clearRect(0, 0, c.width, c.height);

    const cx = c.width / 2;
    const cy = c.height / 2;
    const r = Math.min(c.width, c.height) * 0.18;

    const grad = ctx.createRadialGradient(cx, cy, r * 0.1, cx, cy, r * 1.4);
    grad.addColorStop(0.0, "rgba(247,212,125,1)");
    grad.addColorStop(0.25, "rgba(247,212,125,0.55)");
    grad.addColorStop(1.0, "rgba(0,0,0,0)");

    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(cx, cy, r * 1.4, 0, Math.PI * 2);
    ctx.fill();
  }

  resize();
  draw();

  window.addEventListener("resize", () => {
    resize();
    draw();
  });
});

function ascii() {
  return `
         .       .      .
       .     *       .      *
         .   .   .       .
      *         .        *
         .      .    .
     .    .   \\ | /   .
          .  -- O --  .
     .        / | \\     *
        *       .      .
           .        .
  `;
}
