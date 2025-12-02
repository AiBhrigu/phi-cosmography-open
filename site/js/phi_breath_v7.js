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

const particles = [];
for (let i = 0; i < 36; i++) {
  particles.push({
    x: Math.random() * W,
    y: Math.random() * H,
    s: 0.4 + Math.random() * 0.9,
    speed: 0.3 + Math.random() * 0.6,
    img: flakes[Math.floor(Math.random() * flakes.length)],
    angle: Math.random() * Math.PI * 2
  });
}

function loop() {
  ctx.clearRect(0, 0, W, H);

  particles.forEach(p => {
    p.y += p.speed;
    p.angle += 0.003;
    p.x += Math.sin(p.angle) * 0.4;

    if (p.y > H + 20) {
      p.y = -20;
      p.x = Math.random() * W;
    }

    const img = new Image();
    img.src = p.img;
    ctx.save();
    ctx.globalAlpha = 0.5;
    ctx.translate(p.x, p.y);
    ctx.scale(p.s, p.s);
    ctx.drawImage(img, -16, -16, 32, 32);
    ctx.restore();
  });

  requestAnimationFrame(loop);
}

loop();
