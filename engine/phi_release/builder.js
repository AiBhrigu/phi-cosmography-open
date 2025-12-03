import fs from "fs";
import path from "path";

const LAYERS = ["φ-core", "φ-light", "φ-rays", "φ-field", "φ-layers"];

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

    snapshot(layer);
  }

  console.log("\n🜂 Φ-Builder v1.0 — done.");
}

function snapshot(layer) {
  const logDir = "engine/logs";
  if (!fs.existsSync(logDir)) fs.mkdirSync(logDir, { recursive: true });

  const t = new Date().toISOString().replace(/[:.]/g, "-");
  fs.writeFileSync(`${logDir}/snapshot_${layer}_${t}.log`, `${layer} snapshot @ ${t}`);
}
