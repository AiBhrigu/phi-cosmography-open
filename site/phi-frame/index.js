// φ-Frame v1.0 — Static Boundary Shell
// Static-only, symbolic, no-light, no-math, no-runtime, IP-shield strict
// Pure export with no side effects

export const phiFrame = {
  id: "phi-frame-v1",
  name: "φ-Frame v1.0",
  boundary: "static-light-boundary-shell",
  scope: "static-only",
  semantics: "symbolic",
  notes: [
    "no-light",
    "no-math",
    "no-runtime",
    "ip-shield-strict",
  ],
  layers: [
    { id: "shell", role: "boundary", mode: "static" },
    { id: "frame", role: "anchor", mode: "fixed" },
    { id: "field", role: "placeholder", mode: "void" },
  ],
};

export default phiFrame;
