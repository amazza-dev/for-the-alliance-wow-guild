// Checks the built site for missing files, broken in-page links and oversized assets.
import { readFileSync, existsSync, statSync, readdirSync } from "node:fs";
import { join } from "node:path";

const DIR = "public";
const html = readFileSync(join(DIR, "index.html"), "utf8");
const errors = [];

// 1. every local file the page references must exist
const refs = new Set();
for (const m of html.matchAll(/\b(src|href|srcset)="([^"]+)"/g)) {
  if (m[2].includes("${")) continue; // built in script at runtime
  const parts = m[1] === "srcset" ? m[2].split(",") : [m[2]];
  for (const part of parts) {
    const url = part.trim().split(/\s+/)[0];
    if (!url || /^(https?:|mailto:|tel:|data:|#)/.test(url)) continue;
    refs.add(url.split(/[?#]/)[0]);
  }
}
for (const m of html.matchAll(/url\(["']?([^"')]+)["']?\)/g)) {
  if (!/^(https?:|data:)/.test(m[1])) refs.add(m[1]);
}
for (const f of refs) {
  if (!existsSync(join(DIR, f))) errors.push(`Missing file referenced by the page: ${f}`);
}

// 2. every in-page link (#id) must point at an element that exists
const ids = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]));
for (const m of html.matchAll(/href="#([^"]*)"/g)) {
  if (m[1] && !ids.has(m[1])) errors.push(`Link to #${m[1]} has no matching element`);
}

// 3. keep assets light enough for phones
const LIMIT_MB = 3;
for (const f of readdirSync(DIR)) {
  const mb = statSync(join(DIR, f)).size / 1048576;
  if (mb > LIMIT_MB) errors.push(`${f} is ${mb.toFixed(1)} MB (limit ${LIMIT_MB} MB)`);
}

// 4. files in public/ that nothing uses (warning only)
const unused = readdirSync(DIR).filter(f => f !== "index.html" && !refs.has(f));
if (unused.length) console.warn(`Unused files in public/: ${unused.join(", ")}`);

if (errors.length) {
  console.error(errors.map(e => `✗ ${e}`).join("\n"));
  process.exit(1);
}
console.log(`✓ ${refs.size} referenced files present, ${ids.size} ids, all in-page links resolve`);
