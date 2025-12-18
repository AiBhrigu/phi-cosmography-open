import fs from "node:fs";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:4173";
const ROUTES = (process.env.ROUTES || "/ /start /cosmography /map /orion /frey /dao")
  .split(/\s+/).filter(Boolean);

let playwright;
try {
  playwright = await import("playwright");
} catch {
  console.error("Playwright not found. Install deps first (npm/pnpm/yarn) or add playwright as devDependency.");
  process.exit(2);
}

const { chromium } = playwright;

const outDir = process.env.OUT_DIR || "/tmp/fp3";
const outErrors = `${outDir}/console_errors.json`;
const outReqFail = `${outDir}/request_failures.json`;
const outSummary = `${outDir}/console_summary.txt`;

fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage();

const allConsoleErrors = [];
const allRequestFailures = [];

page.on("pageerror", (err) => {
  allConsoleErrors.push({
    type: "pageerror",
    message: String(err?.message || err),
    stack: String(err?.stack || ""),
  });
});

page.on("console", (msg) => {
  if (msg.type() === "error") {
    allConsoleErrors.push({
      type: "console.error",
      message: msg.text(),
      location: msg.location(),
    });
  }
});

page.on("requestfailed", (req) => {
  const failure = req.failure();
  allRequestFailures.push({
    url: req.url(),
    method: req.method(),
    resourceType: req.resourceType(),
    failure: failure ? { errorText: failure.errorText } : null,
  });
});

const perRoute = [];

for (const route of ROUTES) {
  const url = `${BASE_URL}${route === "/" ? "" : route}`;
  const beforeErr = allConsoleErrors.length;
  const beforeReq = allRequestFailures.length;

  try {
    await page.goto(url, { waitUntil: "networkidle", timeout: 60_000 });
    await page.waitForTimeout(500);
  } catch (e) {
    allConsoleErrors.push({
      type: "goto-failed",
      message: `Failed to load ${url}`,
      detail: String(e?.message || e),
    });
  }

  perRoute.push({
    route,
    url,
    consoleErrors: allConsoleErrors.slice(beforeErr),
    requestFailures: allRequestFailures.slice(beforeReq),
  });
}

await browser.close();

fs.writeFileSync(outErrors, JSON.stringify({ baseUrl: BASE_URL, routes: ROUTES, perRoute, allConsoleErrors }, null, 2));
fs.writeFileSync(outReqFail, JSON.stringify({ baseUrl: BASE_URL, routes: ROUTES, perRoute, allRequestFailures }, null, 2));

const total = allConsoleErrors.length;
const lines = [];
lines.push(`FP3 Console Scan`);
lines.push(`BASE_URL: ${BASE_URL}`);
lines.push(`ROUTES: ${ROUTES.join(" ")}`);
lines.push(`TOTAL console errors: ${total}`);
lines.push("");

for (const r of perRoute) {
  lines.push(`- ${r.route} -> errors: ${r.consoleErrors.length}, request_failed: ${r.requestFailures.length}`);
  for (const e of r.consoleErrors.slice(0, 10)) {
    lines.push(`    * ${e.type}: ${e.message}`);
  }
}

fs.writeFileSync(outSummary, lines.join("\n"));
console.log(lines.join("\n"));

process.exit(total === 0 ? 0 : 1);
