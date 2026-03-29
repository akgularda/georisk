# Website Publishing Layer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first production-ready website and report publishing layer for EarlyPredict using the visual direction in `C:\Users\akgul\Downloads\codex_prompts_georisk\design.md`.

**Architecture:** The website will live in a separate `web/` Next.js app inside `georisk` so publishing stays isolated from forecasting and data pipelines. It will use file-based MDX content, a thin static-data integration layer, and reusable editorial components for homepage, forecasts, country pages, reports, and methodology pages.

**Tech Stack:** Next.js App Router, TypeScript, Tailwind CSS, MDX, npm, GitHub Actions

---

### Task 1: Scaffold the web app

**Files:**
- Create: `web/*`
- Modify: `README.md`

**Step 1:** Generate a Next.js App Router project with TypeScript, ESLint, Tailwind CSS, and `src/` layout under `georisk/web`.

**Step 2:** Install MDX and any small runtime dependencies required for local content rendering and charts.

### Task 2: Add content and sample data contracts

**Files:**
- Create: `web/content/reports/*.mdx`
- Create: `web/content/methodology/*.mdx`
- Create: `web/src/data/*.ts`
- Create: `web/src/lib/content.ts`
- Create: `web/src/lib/site-data.ts`

**Step 1:** Define frontmatter/content loaders for reports and methodology pages.

**Step 2:** Add sample forecast, country, and report data aligned to the existing platform artifacts and the `design.md` tone.

### Task 3: Build the editorial component system

**Files:**
- Create: `web/src/components/**/*`
- Modify: `web/src/app/globals.css`
- Modify: `web/src/app/layout.tsx`

**Step 1:** Implement the homepage visual language from `design.md`: restrained header, country-shape hero, risk strip, drivers, scenario block, timeline, report preview, and secondary global context.

**Step 2:** Add reusable components for risk cards, forecast tables, report layout, metadata badges, timelines, and mini charts.

### Task 4: Wire the required routes

**Files:**
- Create: `web/src/app/page.tsx`
- Create: `web/src/app/forecasts/page.tsx`
- Create: `web/src/app/countries/[slug]/page.tsx`
- Create: `web/src/app/reports/page.tsx`
- Create: `web/src/app/reports/[slug]/page.tsx`
- Create: `web/src/app/methodology/**/*.tsx`
- Create: `web/src/app/about/page.tsx`

**Step 1:** Build the homepage, forecast explorer, country page, report index/detail, methodology pages, and about page.

**Step 2:** Add metadata, print styles, and static-generation-friendly data access.

### Task 5: Add editorial tooling and verification

**Files:**
- Create: `web/scripts/validate-content.mjs`
- Create: `.github/workflows/web-publishing.yml`
- Modify: `docs/data_platform.md`
- Modify: `README.md`

**Step 1:** Add content validation and a GitHub Actions workflow for install, lint, build, and scheduled publishing.

**Step 2:** Run lint/build and document local run/publish instructions.
