import fs from "fs";
import { JSDOM } from "jsdom";

export async function inspectDOM() {
  console.log("\n🧩 Φ-Inspector v1.0 — start");

  const html = fs.readFileSync("site/index.html", "utf8");
  const dom = new JSDOM(html);
  const doc = dom.window.document;

  let total = 0;
  let heavy = 0;

  function walk(n) {
    total++;
    if (n.childNodes.length > 10) heavy++;
    n.childNodes.forEach(walk);
  }

  walk(doc.body);

  fs.writeFileSync("engine/logs/dom_report.txt", `DOM nodes: ${total}\nHeavy: ${heavy}`);
  console.log(`   DOM nodes: ${total}`);
  console.log(`   heavy: ${heavy}`);

  console.log("🧩 Φ-Inspector v1.0 — done.");
}
