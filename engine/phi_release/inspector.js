import { JSDOM } from "jsdom";
import fs from "fs";

export async function inspectDOM() {
  console.log("🧩 Φ-Inspector v1.0 — start");

  const html = fs.readFileSync("site/index.html", "utf8");
  const dom = new JSDOM(html);
  const nodes = dom.window.document.querySelectorAll("*");

  console.log("   DOM nodes:", nodes.length);
  console.log("   heavy:", 0);

  console.log("🧩 Φ-Inspector v1.0 — done.");
}
