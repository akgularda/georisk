import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const expectedShapeKeys = ["iran", "israel", "sudan", "ukraine", "syria", "colombia", "taiwan", "lebanon"];
const generatedFile = path.join(process.cwd(), "src", "lib", "country-shapes.ts");

if (!existsSync(generatedFile)) {
  console.error(`Missing generated shape registry: ${generatedFile}`);
  process.exit(1);
}

const source = readFileSync(generatedFile, "utf8");

for (const shapeKey of expectedShapeKeys) {
  const shapePattern = new RegExp(`${shapeKey}:\\s*"([^"]+)"`);
  const match = source.match(shapePattern);
  if (!match) {
    console.error(`Missing generated SVG path for shape key: ${shapeKey}`);
    process.exit(1);
  }

  if (!match[1]?.trim()) {
    console.error(`Generated SVG path is empty for shape key: ${shapeKey}`);
    process.exit(1);
  }
}

console.log(`Validated ${expectedShapeKeys.length} generated country silhouettes.`);
