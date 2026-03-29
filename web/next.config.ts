import createMDX from "@next/mdx";
import type { NextConfig } from "next";

function normalizeBasePath(value: string | undefined): string {
  if (!value) {
    return "";
  }
  const trimmed = value.trim();
  if (!trimmed || trimmed === "/") {
    return "";
  }
  return trimmed.startsWith("/") ? trimmed.replace(/\/+$/, "") : `/${trimmed.replace(/\/+$/, "")}`;
}

const isGithubPages = process.env.GITHUB_PAGES === "true";
const repositoryName = process.env.GITHUB_REPOSITORY?.split("/")[1];
const configuredPagesBasePath = process.env.PAGES_BASE_PATH?.trim();
const basePath = isGithubPages
  ? normalizeBasePath(configuredPagesBasePath || (repositoryName ? `/${repositoryName}` : ""))
  : "";

const nextConfig: NextConfig = {
  pageExtensions: ["ts", "tsx", "md", "mdx"],
  output: isGithubPages ? "export" : undefined,
  trailingSlash: isGithubPages,
  images: {
    unoptimized: isGithubPages,
  },
  basePath,
  assetPrefix: basePath || undefined,
};

const withMDX = createMDX({
  options: {
    remarkPlugins: ["remark-gfm"],
  },
});

export default withMDX(nextConfig);
