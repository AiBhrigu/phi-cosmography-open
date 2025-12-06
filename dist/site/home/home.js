function ascii() {
return `
        .       *        .       .
   *         .        .        *
        .       φ       .
   .    '   .       .       *     .
`;
}

document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("phi-home-root");

  root.innerHTML = `
    <canvas id="phi-dome"></canvas>

    <div id="phi-home-ui">
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

      <p class="phi-build">Build v3.0 — Φ-Dome Stable</p>
    </div>
  `;

  // ===== Φ-DOME CANVAS RENDER =====
  const c = document.getElementById("phi-dome");
  const ctx = c.getContext("2d");

  function resize() {
    c.width = window.innerWidth;
    c.height = window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  const stars = Array.from({ length: 300 }).map(() => ({
    x: Math.random() * c.width,
    y: Math.random() * c.height,
    r: Math.random() * 1.2 + 0.2,
    a: Math.random() * Math.PI * 2
  }));

  function draw() {
    ctx.clearRect(0, 0, c.width, c.height);

    // radial dome
    const g = ctx.createRadialGradient(
      c.width/2, c.height/2, 0,
      c.width/2, c.height/2, c.height*0.7
    );
    g.addColorStop(0, "#f7d47d22");
    g.addColorStop(1, "#000000ff");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, c.width, c.height);

    // stars
    ctx.fillStyle = "#f7d47d88";
    stars.forEach(s => {
      s.a += 0.002;
      const pulse = Math.sin(s.a) * 0.5 + 0.5;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r * (0.5 + pulse), 0, Math.PI*2);
      ctx.fill();
    });

    requestAnimationFrame(draw);
  }
  draw();
});
