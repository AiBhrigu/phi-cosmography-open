import fs from "fs";
import path from "path";
import crypto from "crypto";

const LAYERS = ["φ-core", "φ-light", "φ-rays", "φ-field", "φ-layers"];

export async function runDiff() {
  console.log("\n🔍 Φ-Diff v1.0 — start");

  const prev = "engine/logs/prev_state";
  const curr = "engine/logs/curr_state";

  if (!fs.existsSync(prev)) fs.mkdirSync(prev, { recursive: true });
  if (!fs.existsSync(curr)) fs.mkdirSync(curr, { recursive: true });

  let found = false;

  for (const layer of LAYERS) {
    const mp = path.join("site", layer, "manifest.json");
    const m = JSON.parse(fs.readFileSync(mp));

    const hash = checksum(layer, m.files);
    fs.writeFileSync(`${curr}/${layer}.hash`, hash);

    const prevFile = `${prev}/${layer}.hash`;

    if (fs.existsSync(prevFile)) {
      const old = fs.readFileSync(prevFile, "utf8");
      if (old !== hash) {
        console.log(`⚠️  Diff: ${layer}`);
        found = true;
      }
    }

    fs.writeFileSync(prevFile, hash);
  }

  console.log(found ? "🟧 Diffs found" : "🟩 No diffs");
  console.log("🔍 Φ-Diff v1.0 — done.");
}

function checksum(layer, files = []) {
  const h = crypto.createHash("sha256");
  for (const f of files) h.update(fs.readFileSync(`site/${layer}/${f}`));
  return h.digest("hex");
}
