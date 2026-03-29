import fs from "node:fs";
import path from "node:path";

const projectRoot = process.cwd();
const contentRoot = path.join(projectRoot, "content");
const countryDataSource = fs.readFileSync(path.join(projectRoot, "src", "data", "countries.ts"), "utf8");
const allowedCountrySlugs = new Set([...countryDataSource.matchAll(/\bslug:\s*"([^"]+)"/g)].map((match) => match[1]));
const staticInternalRoutes = new Set([
  "/",
  "/about",
  "/countries",
  "/forecasts",
  "/methodology",
  "/methodology/data",
  "/methodology/model",
  "/methodology/backtesting",
  "/reports",
]);

if (allowedCountrySlugs.size === 0) {
  throw new Error("Could not derive allowed country slugs from src/data/countries.ts");
}

function readMdxFiles(dirPath) {
  return fs
    .readdirSync(dirPath)
    .filter((fileName) => fileName.endsWith(".mdx"))
    .map((fileName) => ({
      fileName,
      fullPath: path.join(dirPath, fileName),
      source: fs.readFileSync(path.join(dirPath, fileName), "utf8"),
    }));
}

function parseFrontmatter(source, fileLabel) {
  const match = source.match(/export const frontmatter = (\{[\s\S]*?\n\});/);
  if (!match) {
    throw new Error(`Missing frontmatter export in ${fileLabel}`);
  }
  return Function(`"use strict"; return (${match[1]});`)();
}

function extractInternalLinks(source) {
  return [...source.matchAll(/\[[^\]]+\]\((\/[^)\s]+)\)/g)].map((match) => match[1]);
}

function validateRequiredFields(frontmatter, fields, fileLabel, errors) {
  for (const field of fields) {
    if (!(field in frontmatter)) {
      errors.push(`${fileLabel}: missing required frontmatter field "${field}"`);
    }
  }
}

const errors = [];
const reportFiles = readMdxFiles(path.join(contentRoot, "reports"));
const methodologyFiles = readMdxFiles(path.join(contentRoot, "methodology"));

const reportSlugs = new Set();
for (const file of reportFiles) {
  const frontmatter = parseFrontmatter(file.source, file.fileName);
  validateRequiredFields(
    frontmatter,
    ["title", "slug", "date", "updatedAt", "authors", "summary", "region", "countries", "targets", "horizon", "tags", "forecastVersion", "confidenceBand", "sources", "heroMetric", "draft", "toc"],
    file.fileName,
    errors,
  );

  const expectedSlug = file.fileName.replace(/\.mdx$/, "");
  if (frontmatter.slug !== expectedSlug) {
    errors.push(`${file.fileName}: slug "${frontmatter.slug}" does not match filename "${expectedSlug}"`);
  }
  if (reportSlugs.has(frontmatter.slug)) {
    errors.push(`${file.fileName}: duplicate report slug "${frontmatter.slug}"`);
  }
  reportSlugs.add(frontmatter.slug);

  for (const countrySlug of frontmatter.countries ?? []) {
    if (!allowedCountrySlugs.has(countrySlug)) {
      errors.push(`${file.fileName}: unknown country slug "${countrySlug}"`);
    }
  }
}

const methodologySlugs = new Set();
for (const file of methodologyFiles) {
  const frontmatter = parseFrontmatter(file.source, file.fileName);
  validateRequiredFields(frontmatter, ["title", "slug", "date", "updatedAt", "summary", "tags", "draft"], file.fileName, errors);

  const expectedSlug = file.fileName.replace(/\.mdx$/, "");
  if (frontmatter.slug !== expectedSlug) {
    errors.push(`${file.fileName}: slug "${frontmatter.slug}" does not match filename "${expectedSlug}"`);
  }
  if (methodologySlugs.has(frontmatter.slug)) {
    errors.push(`${file.fileName}: duplicate methodology slug "${frontmatter.slug}"`);
  }
  methodologySlugs.add(frontmatter.slug);
}

for (const file of [...reportFiles, ...methodologyFiles]) {
  for (const link of extractInternalLinks(file.source)) {
    if (staticInternalRoutes.has(link)) {
      continue;
    }
    if (link.startsWith("/reports/") && reportSlugs.has(link.replace("/reports/", ""))) {
      continue;
    }
    if (link.startsWith("/methodology/") && methodologySlugs.has(link.replace("/methodology/", ""))) {
      continue;
    }
    if (link.startsWith("/countries/") && allowedCountrySlugs.has(link.replace("/countries/", ""))) {
      continue;
    }
    errors.push(`${file.fileName}: unresolved internal link "${link}"`);
  }
}

if (errors.length > 0) {
  console.error("Content validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`Validated ${reportFiles.length} reports and ${methodologyFiles.length} methodology pages.`);
