const fs = require("fs");
const path = require("path");

const rootDir = path.resolve(__dirname, "..");
const webNext = path.join(rootDir, "apps", "web", ".next");
const rootNext = path.join(rootDir, ".next");
const webPublic = path.join(rootDir, "apps", "web", "public");
const rootPublic = path.join(rootDir, "public");

if (fs.existsSync(webNext)) {
  if (fs.existsSync(rootNext)) {
    fs.rmSync(rootNext, { recursive: true, force: true });
  }
  fs.cpSync(webNext, rootNext, { recursive: true });
  console.log("[SYNC] Copied apps/web/.next -> .next at project root");
}

if (fs.existsSync(webPublic) && !fs.existsSync(rootPublic)) {
  fs.cpSync(webPublic, rootPublic, { recursive: true });
  console.log("[SYNC] Copied apps/web/public -> public at project root");
}
