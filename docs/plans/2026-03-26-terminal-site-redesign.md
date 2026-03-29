# Terminal Site Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign the entire `web/` app into a hard-edged intelligence terminal with Iran as the featured country while preserving the product’s core country-shape-first identity.

**Architecture:** The redesign should reuse the existing Next.js route structure and MDX content system, but replace the soft editorial theme with a unified terminal-style design system. The work should update tokens, layout primitives, page shells, and content data together so the site looks coherent at every route instead of mixing the old and new visual languages.

**Tech Stack:** Next.js App Router, TypeScript, Tailwind CSS, MDX, Recharts, Playwright/browser verification

---

### Task 1: Replace the global visual system

**Files:**
- Modify: `web/src/app/globals.css`
- Modify: `web/src/app/layout.tsx`
- Modify: `web/src/components/site-header.tsx`
- Modify: `web/src/components/site-footer.tsx`
- Modify: `web/src/lib/site.ts`

**Step 1:** Replace the warm editorial palette with the approved terminal palette:
- near-black graphite background
- dark steel panels
- off-white text
- restrained red / amber / green semantic accents

**Step 2:** Replace soft card language with hard-edged panel rules:
- near-square corners
- straight dividers
- stronger border grid
- denser spacing defaults

**Step 3:** Remove soft halo and bloom effects from the shell-level theme.

### Task 2: Add Iran and rework featured-country data

**Files:**
- Modify: `web/src/lib/types.ts`
- Modify: `web/src/data/countries.ts`
- Modify: `web/src/lib/site-data.ts`
- Modify: `web/content/reports/*.mdx`

**Step 1:** Add `iran` to `CountryShapeKey`.

**Step 2:** Add an Iran profile with:
- featured status
- risk summary
- timeline
- scenarios
- market / logistics / political signals

**Step 3:** Make Iran the homepage default hero case.

**Step 4:** Replace or supplement the current featured report content so the homepage no longer defaults to Sudan.

### Task 3: Rebuild the silhouette and hero system

**Files:**
- Modify: `web/src/components/country-pulse-graphic.tsx`
- Modify: `web/src/components/country-outlook-header.tsx`
- Modify: `web/src/components/risk-badge.tsx`
- Modify: `web/src/components/confidence-badge.tsx`
- Modify: `web/src/components/data-freshness-badge.tsx`
- Modify: `web/src/app/page.tsx`

**Step 1:** Replace the current soft silhouette presentation with a harder technical frame:
- rectangular stage
- scan/grid treatment
- restrained edge glow or line emphasis
- no soft circular bloom

**Step 2:** Rebuild the homepage hero into a denser terminal layout with:
- center-stage Iran silhouette
- hard metrics strip
- left and right supporting rails

**Step 3:** Keep the country itself visually primary over the trend chart and over any global context.

### Task 4: Redesign the explorer and country dossier views

**Files:**
- Modify: `web/src/components/forecast-explorer.tsx`
- Modify: `web/src/components/driver-list.tsx`
- Modify: `web/src/components/scenario-grid.tsx`
- Modify: `web/src/components/timeline-list.tsx`
- Modify: `web/src/components/global-context-strip.tsx`
- Modify: `web/src/app/forecasts/page.tsx`
- Modify: `web/src/app/countries/[slug]/page.tsx`
- Modify: `web/src/app/countries/page.tsx`

**Step 1:** Turn the forecast explorer into a stricter operational grid with denser ranking presentation and less soft spacing.

**Step 2:** Convert country pages into hard-edged dossier layouts with stronger section separation and more compact signal panels.

**Step 3:** Preserve readability while increasing information density and reducing decorative whitespace.

### Task 5: Redesign reports, methodology, and secondary pages

**Files:**
- Modify: `web/src/components/report-card.tsx`
- Modify: `web/src/components/methodology-note.tsx`
- Modify: `web/src/components/report-toc.tsx`
- Modify: `web/src/mdx-components.tsx`
- Modify: `web/src/app/reports/page.tsx`
- Modify: `web/src/app/reports/[slug]/page.tsx`
- Modify: `web/src/app/methodology/page.tsx`
- Modify: `web/src/app/methodology/[slug]/page.tsx`
- Modify: `web/src/app/about/page.tsx`
- Modify: `web/src/app/not-found.tsx`

**Step 1:** Move long-form pages into the same dark terminal shell without sacrificing line length and readability.

**Step 2:** Rebuild cards, callouts, and TOC modules to match the new hard-edged system.

**Step 3:** Make the whole site feel like one product, not a redesigned homepage with legacy internals.

### Task 6: Verify the redesign across the full site

**Files:**
- Modify if needed: `web/README.md`
- Modify if needed: `.github/workflows/web-publishing.yml`

**Step 1:** Run content validation, lint, and build.

**Step 2:** Browser-check at minimum:
- `/`
- `/forecasts`
- `/countries/iran`
- `/reports/<featured-report>`
- `/methodology/model`

**Step 3:** Verify:
- no console warnings
- no remaining soft visual language
- Iran is the featured hero case
- silhouette remains visually dominant

Run:
- `npm run content:validate`
- `npm run lint`
- `npm run build`

## Scheduling Note

This redesign is planned site-wide.

But according to the current repo priority, implementation should start only after:
1. complete data layer
2. real-data forecasting
3. backtesting

If project priority changes, this plan is ready to execute as a separate frontend track.
