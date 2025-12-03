document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("phi-home-root");

  root.innerHTML = `
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

      <p class="phi-build">Φ-Build v2.0 — Pre-Patent Shell</p>
    </div>
  `;

  const c = document.getElementById("phi-sun-core");
  const ctx = c.getContext("2d");

  function resize() {
    c.width = window.innerWidth;
    c.height = window.innerHeight;
  }

  function loop() {
    ctx.clearRect(0, 0, c.width, c.height);

    const x = c.width / 2;
    const y = c.height / 2;
    const r = Math.min(c.width, c.height) * 0.23;

    const g = ctx.createRadialGradient(x, y, r * 0.1, x, y, r);
    g.addColorStop(0, "rgba(255,220,120,1)");
    g.addColorStop(0.45, "rgba(255,200,90,0.7)");
    g.addColorStop(1, "rgba(255,180,60,0)");

    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();

    requestAnimationFrame(loop);
  }

  resize();
  window.addEventListener("resize", resize);
  loop();
});
