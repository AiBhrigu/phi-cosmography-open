import fs from "fs";
import path from "path";

const LAYERS = ["φ-core", "φ-light", "φ-rays", "φ-field", "φ-layers", "φ-home"];

export async function buildLayers() {
  console.log("⚙️  Φ-Builder v1.0 — start\n");

  for (const layer of LAYERS) {
    const layerPath = path.join("site", layer);
    const manifestPath = path.join(layerPath, "manifest.json");

    if (!fs.existsSync(layerPath)) throw new Error(`Missing layer: ${layer}`);
    if (!fs.existsSync(manifestPath)) throw new Error(`Missing manifest for: ${layer}`);

    const manifest = JSON.parse(fs.readFileSync(manifestPath));
    console.log(`🜂 Building layer: ${layer}`);

    for (const file of manifest.files || []) {
      const fp = path.join(layerPath, file);
      if (!fs.existsSync(fp)) throw new Error(`Missing: ${fp}`);
    }
  }

  console.log("\n🜂 Φ-Builder v1.0 — done.");
}
