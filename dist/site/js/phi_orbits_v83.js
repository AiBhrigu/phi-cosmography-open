/* ============================================================
   Φ-v8.3 — Orbital Dynamics Engine
   Earth · Venus · Mars — golden-ratio motion (λ = 1.889)
   ============================================================ */

const L = 1.889;

// орбитальные параметры (условные, без эфемерид)
const orbits = [
  { name: "venus", r: 180, speed: 0.0045 * L, color: "rgba(255,220,140,0.22)" },
  { name: "earth", r: 250, speed: 0.0030 * L, color: "rgba(255,220,140,0.30)" },
  { name: "mars",  r: 320, speed: 0.0024 * L, color: "rgba(255,220,140,0.18)" }
];

let angles = {
  venus: 0,
  earth: Math.PI,
  mars: Math.PI / 2
};

const centerX = window.innerWidth / 2;
const centerY = window.innerHeight / 2;

function animateOrbits() {
  const ctx = window.phiOrbitCtx;
  if (!ctx) return;

  const W = window.innerWidth;
  const H = window.innerHeight;

  ctx.clearRect(0, 0, W, H);

  // рисуем орбиты
  orbits.forEach(o => {
    ctx.beginPath();
    ctx.arc(centerX, centerY, o.r, 0, Math.PI * 2);
    ctx.strokeStyle = o.color;
    ctx.lineWidth = 0.6;
    ctx.stroke();
  });

  // рисуем движущиеся планеты
  orbits.forEach(o => {
    angles[o.name] += o.speed;

    const x = centerX + Math.cos(angles[o.name]) * o.r;
    const y = centerY + Math.sin(angles[o.name]) * o.r;

    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fillStyle = o.color.replace("0.30","0.9").replace("0.22","0.9").replace("0.18","0.9");
    ctx.fill();
  });

  requestAnimationFrame(animateOrbits);
}

window.startPhiOrbits = () => {
  const canvas = document.createElement("canvas");
  canvas.id = "phi-orbits";
  canvas.style.position = "fixed";
  canvas.style.top = 0;
  canvas.style.left = 0;
  canvas.style.width = "100%";
  canvas.style.height = "100%";
  canvas.style.zIndex = 4;
  canvas.style.pointerEvents = "none";

  document.body.appendChild(canvas);

  window.phiOrbitCtx = canvas.getContext("2d");

  const resize = () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  };
  window.addEventListener('resize', resize);
  resize();

  animateOrbits();
};
