import { phiRelease } from "./index.js";

(async () => {
  try {
    await phiRelease();
    console.log("🟩 Φ-Release Completed");
  } catch (err) {
    console.error("⛔ Release Failed");
    console.error(err);
  }
})();
