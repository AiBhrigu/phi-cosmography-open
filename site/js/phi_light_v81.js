/* ======================================================
   Φ-Light Engine v8.1
   — φ-параллакс
   — λ-поток (1.618)
   — real-breathing золотой свет
   ====================================================== */

const L = 1.618;   // λ-константа
const layers = [];

for (let i = 1; i <= 7; i++) {
  layers.push(document.getElementById(`phi-layer-${i}`));
}

/* PARALLAX + λ-wave breathing */
document.addEventListener('mousemove', (ev) => {
  const x = (ev.clientX / window.innerWidth  - 0.5);
  const y = (ev.clientY / window.innerHeight - 0.5);

  layers.forEach((layer, i) => {
    const depth = (i + 1) * 0.7;
    layer.style.transform =
      `translate(${x * depth * L * 5}px, ${y * depth * L * 5}px)`;
  });
});

/* Golden breathing */
let t = 0;
function animate() {
  t += 0.008;
  const pulse = (Math.sin(t * L) + 1) / 2;

  layers.forEach((layer, i) => {
    const glow = 8 + pulse * (i * 6);
    layer.style.boxShadow =
      `0 0 ${glow}px rgba(255, 210, 140, ${0.05 + pulse * 0.15})`;
  });

  requestAnimationFrame(animate);
}
animate();
