import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const sourceFile = path.join(process.cwd(), "data", "country-boundaries.geojson");
const targetFile = path.join(process.cwd(), "src", "lib", "country-shapes.ts");

const svgSize = 360;
const padding = 34;

const shapeKeyToIso3 = {
  iran: "IRN",
  israel: "ISR",
  sudan: "SDN",
  ukraine: "UKR",
  syria: "SYR",
  colombia: "COL",
  taiwan: "TWN",
  lebanon: "LBN",
};

function round(value) {
  return Number(value.toFixed(2));
}

function collectRings(geometry) {
  if (!geometry) {
    throw new Error("Missing geometry.");
  }

  if (geometry.type === "Polygon") {
    return geometry.coordinates;
  }

  if (geometry.type === "MultiPolygon") {
    return geometry.coordinates.flat();
  }

  throw new Error(`Unsupported geometry type: ${geometry.type}`);
}

function projectPoint([lon, lat], cosLat) {
  return [lon * cosLat, -lat];
}

function toPath(rings) {
  const rawPoints = rings.flat();
  const latitudes = rawPoints.map(([, lat]) => lat);
  const minLatitude = Math.min(...latitudes);
  const maxLatitude = Math.max(...latitudes);
  const centerLatitude = (minLatitude + maxLatitude) / 2;
  const cosLat = Math.cos((centerLatitude * Math.PI) / 180);
  const projectedPoints = rawPoints.map((point) => projectPoint(point, cosLat));

  const xs = projectedPoints.map(([x]) => x);
  const ys = projectedPoints.map(([, y]) => y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const width = maxX - minX;
  const height = maxY - minY;

  if (width <= 0 || height <= 0) {
    throw new Error("Invalid shape bounds.");
  }

  const scale = Math.min((svgSize - padding * 2) / width, (svgSize - padding * 2) / height);
  const offsetX = (svgSize - width * scale) / 2 - minX * scale;
  const offsetY = (svgSize - height * scale) / 2 - minY * scale;

  return rings
    .map((ring) => {
      return ring
        .map((point, index) => {
          const [x, y] = projectPoint(point, cosLat);
          const command = index === 0 ? "M" : "L";
          return `${command}${round(x * scale + offsetX)} ${round(y * scale + offsetY)}`;
        })
        .concat("Z")
        .join("");
    })
    .join("");
}

const source = JSON.parse(readFileSync(sourceFile, "utf8"));

const shapes = Object.entries(shapeKeyToIso3).map(([shapeKey, iso3]) => {
  const feature = source.features.find((candidate) => candidate.properties?.ISO_A3 === iso3);
  if (!feature) {
    throw new Error(`Missing source feature for ${shapeKey} (${iso3}).`);
  }

  return {
    shapeKey,
    iso3,
    name: feature.properties.NAME,
    path: toPath(collectRings(feature.geometry)),
  };
});

const output = `import type { CountryShapeKey } from "@/lib/types";

export const COUNTRY_SHAPE_KEYS = ${JSON.stringify(shapes.map((shape) => shape.shapeKey))} as const satisfies readonly CountryShapeKey[];

export const countryShapeIso3: Record<CountryShapeKey, string> = {
${shapes.map((shape) => `  ${shape.shapeKey}: "${shape.iso3}",`).join("\n")}
};

export const countryShapeNames: Record<CountryShapeKey, string> = {
${shapes.map((shape) => `  ${shape.shapeKey}: "${shape.name}",`).join("\n")}
};

export const countryShapes: Record<CountryShapeKey, string> = {
${shapes.map((shape) => `  ${shape.shapeKey}: "${shape.path}",`).join("\n")}
};
`;

writeFileSync(targetFile, output);
console.log(`Generated ${shapes.length} country silhouettes at ${targetFile}`);
