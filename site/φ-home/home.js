const canvas = document.getElementById("phi-bg");
const ctx = canvas.getContext("2d");

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

window.addEventListener("resize", resize);
resize();

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const cx = canvas.width / 2;
  const cy = canvas.height / 2;

  // solar glow
  const grd = ctx.createRadialGradient(cx, cy, 0, cx, cy, canvas.width * 0.6);
  grd.addColorStop(0, "rgba(255,255,200,0.65)");
  grd.addColorStop(1, "rgba(0,0,0,0)");

  ctx.fillStyle = grd;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // φ-Orbital rings
  const base = 80;
  const phi = 1.618;

  for (let i = 0; i < 7; i++) {
    ctx.beginPath();
    ctx.strokeStyle = "rgba(255,230,180,0.12)";
    ctx.lineWidth = 1;
    ctx.arc(cx, cy, base * Math.pow(phi, i), 0, Math.PI * 2);
    ctx.stroke();
  }

  requestAnimationFrame(draw);
}

draw();
