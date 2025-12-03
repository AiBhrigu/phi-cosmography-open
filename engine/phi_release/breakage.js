import fs from "fs";
import path from "path";

export async function detectBreakage() {
  console.log("\n💥 Φ-Breakage Detector v1.0 — start");

  if (!fs.existsSync("site/index.html"))
    throw new Error("index.html missing.");

  const all = scan("site");
  const dup = findDup(all);

  if (dup.length) {
    console.log("⚠️ Duplicates:");
    dup.forEach((d) => console.log(" → " + d));
  }

  console.log("💥 Φ-Breakage Detector v1.0 — done.");
}

function scan(dir) {
  let out = [];
  for (const i of fs.readdirSync(dir)) {
    const fp = path.join(dir, i);
    const st = fs.statSync(fp);
    if (st.isDirectory()) out = out.concat(scan(fp));
    else out.push(i);
  }
  return out;
}

function findDup(a) {
  return a.filter((v, i) => a.indexOf(v) !== i);
}
