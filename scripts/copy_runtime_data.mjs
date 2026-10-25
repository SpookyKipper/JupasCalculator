// Copy the runtime-fetched dataset into dist/ so the built site is self-contained
// for any static host (the GitHub Pages workflow also copies these files).
import { cp, mkdir } from "node:fs/promises";
import { dirname } from "node:path";

const files = [
  ["data/processed/JUPAS_2027_Unified_Data.json", "dist/data/processed/JUPAS_2027_Unified_Data.json"],
  ["data/processed/JUPAS_2027_Unified_Data.version", "dist/data/processed/JUPAS_2027_Unified_Data.version"],
  ["data/processed/programme_details_2027.json", "dist/data/processed/programme_details_2027.json"],
  ["data/raw/subjects.canonical.json", "dist/data/raw/subjects.canonical.json"],
];
for (const [src, dst] of files) {
  await mkdir(dirname(dst), { recursive: true });
  await cp(src, dst);
}
console.log(`Copied ${files.length} runtime data files into dist/`);
