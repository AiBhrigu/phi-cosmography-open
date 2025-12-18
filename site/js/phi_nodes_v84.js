/* ============================================================
   Φ-v8.4 — Node Resonance Engine
   Ties into orbital motion (phi_orbits_v83.js)
   ============================================================ */

const LAMBDA = 1.618;

const nodeCanvas = document.createElement("canvas");
nodeCanvas.id = "phi-nodes-canvas";
nodeCanvas.style.position = "fixed";
nodeCanvas.style.top = "0";
nodeCanvas.style.left = "0";
nodeCanvas.style.zIndex = "6";
nodeCanvas.style.pointerEvents = "none";
document.body.appendChild(nodeCanvas);

const nctx = nodeCanvas.getContext("2d");

function resizeNodes() {
  nodeCanvas.width = window.innerWidth;
  nodeCanvas.height = window.innerHeight;
}
resizeNodes();
window.addEventListener("resize", resizeNodes);

let nodeAngles = {
  venus: 0,
  earth: Math.PI/2,
  mars:  Math.PI
};

function drawNodes() {
  nctx.clearRect(0, 0, nodeCanvas.width, nodeCanvas.height);

  drawNode("venus", 180);
  drawNode("earth", 250);
  drawNode("mars",  320);

  requestAnimationFrame(drawNodes);
}

function drawNode(name, radius) {
  nodeAngles[name] += 0.0020 * LAMBDA;

  const cx = nodeCanvas.width / 2;
  const cy = nodeCanvas.height / 2;

  const x = cx + radius * Math.cos(nodeAngles[name]);
  const y = cy + radius * Math.sin(nodeAngles[name]);

  nctx.beginPath();
  nctx.fillStyle = "rgba(255,215,140,0.85)";
  nctx.shadowBlur = 18;
  nctx.shadowColor = "rgba(255,210,150,0.75)";
  nctx.arc(x, y, 4, 0, Math.PI * 2);
  nctx.fill();
}

drawNodes();
