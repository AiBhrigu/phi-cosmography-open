// Φ-SunCore v100 — живое ядро ORION OpenSite v2
// λ = 1.889, Golden decay + shift field

const lambda = 1.889;

export function initSunCore() {
  const canvas = document.getElementById("phi-suncore");
  const ctx = canvas.getContext("2d");

  resize();
  window.addEventListener("resize", resize);

  let t = 0;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight * 0.4;
  }

  function draw() {
    const w = canvas.width;
    const h = canvas.height;
    const r = Math.min(w, h) * 0.25;

    ctx.clearRect(0, 0, w, h);

    // центральная точка
    const cx = w / 2;
    const cy = h / 2;

    // φ-яркость (пульсация)
    const brightness = 0.6 + 0.4 * Math.sin(t * 0.02);

    // λ-затухание (1/r² mod λ)
    const decay = 1 / Math.pow((1 + brightness) * lambda, 2);

    // круг Солнца
    const grd = ctx.createRadialGradient(cx, cy, r * 0.2, cx, cy, r);
    grd.addColorStop(0, `rgba(255, 220, 120, ${1 * decay})`);
    grd.addColorStop(1, `rgba(255, 150, 40, ${0.05 * decay})`);

    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, 2 * Math.PI);
    ctx.fillStyle = grd;
    ctx.fill();

    // φ-rays
    for (let i = 0; i < 21; i++) {
      const angle = i * (Math.PI * 2 / 21);
      const rx = cx + Math.cos(angle) * r * 1.4;
      const ry = cy + Math.sin(angle) * r * 1.4;

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(rx, ry);
      ctx.strokeStyle = `rgba(255, 200, 120, ${0.15 * decay})`;
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    t += 1;
    requestAnimationFrame(draw);
  }

  draw();
}

window.addEventListener("DOMContentLoaded", initSunCore);
