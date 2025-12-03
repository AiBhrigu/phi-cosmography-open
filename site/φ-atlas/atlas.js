// Φ-Atlas v2 — фрактальная карта космографии

const lambda = 1.889;

function initAtlas() {
  const canvas = document.getElementById("phi-atlas");
  const ctx = canvas.getContext("2d");

  resize();
  window.addEventListener("resize", resize);

  let t = 0;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight * 0.8;
  }

  function draw() {
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    // φ-grid
    const step = w / 21;
    ctx.strokeStyle = "rgba(255, 220, 120, 0.08)";
    ctx.lineWidth = 1;

    for (let x = 0; x < w; x += step) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }

    for (let y = 0; y < h; y += step) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Helion node
    const cx = w / 2;
    const cy = h / 2;

    const pulse = 1 + 0.1 * Math.sin(t * 0.03);

    ctx.beginPath();
    ctx.arc(cx, cy, 18 * pulse, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255, 210, 100, 0.85)";
    ctx.fill();

    ctx.beginPath();
    ctx.arc(cx, cy, 36 * pulse, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(255, 210, 100, 0.45)";
    ctx.lineWidth = 2;
    ctx.stroke();

    // φ-rays
    for (let i = 0; i < 8; i++) {
      const a = i * (Math.PI * 2 / 8);
      const x = cx + Math.cos(a) * 200;
      const y = cy + Math.sin(a) * 200;

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(x, y);
      ctx.strokeStyle = "rgba(255, 200, 120, 0.2)";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    t++;
    requestAnimationFrame(draw);
  }

  draw();
}

window.addEventListener("DOMContentLoaded", initAtlas);
