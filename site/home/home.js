document.addEventListener("DOMContentLoaded", () => {
  const r = document.getElementById("phi-home-root");

  r.innerHTML = `
    <canvas id="phi-sun-core"></canvas>

    <div class="phi-home-container">
      <h1 class="phi-title">Φ-Cosmography</h1>
      <p class="phi-sub">Golden-Ratio Space-Mapping Framework</p>

      <div class="phi-nav">
        <a href="φ-atlas/atlas.html">Atlas</a>
        <a href="φ-floors/floors.html">Floors</a>
        <a href="φ-helion/helion.html">Helion</a>
        <a href="φ-inner/core.html">Inner Core</a>
        <a href="φ-domain/x.html">X-Domain</a>
      </div>

      <p class="phi-build">Φ-Build v1.8 — SunCore</p>
    </div>
  `;

  // --- φ SunCore ---
  const c = document.getElementById("phi-sun-core");
  const ctx = c.getContext("2d");

  function resize() {
    c.width  = window.innerWidth;
    c.height = window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  function loop() {
    ctx.clearRect(0, 0, c.width, c.height);

    const x = c.width / 2;
    const y = c.height / 2;
    const r = Math.min(c.width, c.height) * 0.28;

    // outer glow
    const g1 = ctx.createRadialGradient(x, y, r * 0.2, x, y, r * 1.3);
    g1.addColorStop(0, "rgba(255,220,150,0.45)");
    g1.addColorStop(1, "rgba(0,0,0,0)");

    ctx.fillStyle = g1;
    ctx.beginPath();
    ctx.arc(x, y, r * 1.3, 0, Math.PI*2);
    ctx.fill();

    // core
    const g2 = ctx.createRadialGradient(x, y, r * 0.1, x, y, r);
    g2.addColorStop(0, "rgba(255,235,180,0.95)");
    g2.addColorStop(1, "rgba(255,200,120,0.15)");

    ctx.fillStyle = g2;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI*2);
    ctx.fill();

    requestAnimationFrame(loop);
  }
  loop();
});
