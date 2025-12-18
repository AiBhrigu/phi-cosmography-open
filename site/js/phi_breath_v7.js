const flakes = [];
for (let i = 1; i <= 12; i++) {
  flakes.push(`/phi-cosmography-open/assets/phi_flakes/flake_${i}.svg`);
}

const canvas = document.getElementById("phi-breath");
const ctx = canvas.getContext("2d");

let W, H;
function resize() {
  W = canvas.width = window.innerWidth;
  H = canvas.height = window.innerHeight;
}
window.addEventListener('resize', resize);
resize();

// λ — фрактальный коэффициент
const LAMBDA = 1.618;

const particles = [];

function spawn() {
  for (let i = 0; i < 24; i++) {
    particles.push({
      x: Math.random() * W,
      y: Math.random() * H,
      r: 8 + Math.random() * 12,
      vx: (Math.random() - 0.5) * 0.25 * LAMBDA,
      vy: (Math.random() - 0.5) * 0.25 * LAMBDA,
      orbit: Math.random() * Math.PI * 2,
      img: new Image()
    });
  }

  for (let p of particles) {
    p.img.src = flakes[Math.floor(Math.random() * flakes.length)];
  }
}

spawn();

let t = 0;

function tick() {
  t += 0.01;

  ctx.clearRect(0, 0, W, H);

  for (let p of particles) {
    // λ-модуляция скорости (дыхание)
    const pulse = 1 + 0.12 * Math.sin(t * LAMBDA);

    p.x += p.vx * pulse;
    p.y += p.vy * pulse;

    // микро-орбитальное смещение
    p.orbit += 0.0025 * LAMBDA;
    p.x += Math.cos(p.orbit) * 0.15;
    p.y += Math.sin(p.orbit) * 0.15;

    // перезапуск за пределами экрана
    if (p.x < -50) p.x = W + 50;
    if (p.x > W + 50) p.x = -50;
    if (p.y < -50) p.y = H + 50;
    if (p.y > H + 50) p.y = -50;

    ctx.globalAlpha = 0.70;
    ctx.drawImage(p.img, p.x, p.y, p.r, p.r);
  }

  requestAnimationFrame(tick);
}

tick();
