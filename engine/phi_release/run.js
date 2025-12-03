import { phiRelease } from "./index.js";

(async () => {
  try {
    await phiRelease();
    console.log("\n🟩 Φ-Release Completed");
  } catch (e) {
    console.error("\n⛔ Release Failed");
    console.error(e);
    process.exit(1);
  }
})();
