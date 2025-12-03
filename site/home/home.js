document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("phi-home-root");

  root.innerHTML = `
    <canvas id="phi-sun-core"></canvas>

    <div class="phi-home-container">
      <h1 class="phi-title">Φ-Cosmography</h1>
      <p class="phi-sub">Golden-Ratio Space-Mapping Framework</p>

      <div class="phi-nav">
        <a href="../φ-atlas/atlas.html">Atlas</a>
        <a href="../φ-floors/floors.html">Floors</a>
        <a href="../φ-helion/helion.html">Helion φ⁵</a>
        <a href="../φ-inner/core.html">Inner Core</a>
        <a href="../φ-domain/x.html">X-Domain</a>
      </div>

      <div class="ascii-block">${asciiSun()}</div>

      <p class="phi-build">Φ-Build v2.1 — Stable</p>
    </div>
  `;

  // --- φ SunCore background ---
  const c = document.getElementById("phi-sun-core");
  const ctx = c.getContext("2d");

  function resize() {
    c.width = window.innerWidth;
    c.height = window.innerHeight;
  }

  function draw() {
    ctx.clearRect(0, 0, c.width, c.height);

    const x = c.width / 2;
    const y = c.height / 2;
    const r = Math.min(x, y) * 0.55;

    const g = ctx.createRadialGradient(x, y, r*0.2, x, y, r);
    g.addColorStop(0, "rgba(255,230,150,0.9)");
    g.addColorStop(0.6, "rgba(255,230,150,0.15)");
    g.addColorStop(1, "rgba(255,230,150,0)");

    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();

    requestAnimationFrame(draw);
  }

  resize();
  draw();
  window.addEventListener("resize", resize);
});

function asciiSun() {
  return `
                 .      .
            .      *       .
       .     .    |    .      .
           .    \\ | /     .
        .     .  \\|/  .         .
       ------------*------------
        .     .  /|\\    .     .
           .    / | \\      .
       .      .    |   .       .
                .     .
  `;
}
