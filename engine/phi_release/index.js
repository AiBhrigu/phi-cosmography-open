import { buildLayers } from "./builder.js";
import { runDiff } from "./diff.js";
import { inspectDOM } from "./inspector.js";
import { detectBreakage } from "./breakage.js";

export async function phiRelease() {
  console.log("🜂 Φ-Release Engine v2 — Start\n");

  await buildLayers();
  await runDiff();
  await inspectDOM();
  await detectBreakage();

  console.log("\n🜂 Φ-Release Engine v2 — Done");
}
