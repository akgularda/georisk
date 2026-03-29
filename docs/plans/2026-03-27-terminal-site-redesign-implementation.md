# Terminal Site Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current soft editorial website with a site-wide hard-edged intelligence terminal centered on a dual Iran/Israel homepage theater, a database-first monitor, and dossier-style country pages.

**Architecture:** Introduce a new terminal theme layer in `app/globals.css`, refactor the global shell in `app/layout.tsx` plus `site-header.tsx` and `site-footer.tsx`, then replace single-country homepage logic with dual-theater data structures and new homepage modules. After the shell and homepage are stable, move the same component language into the country monitor and dossier routes so the redesign is coherent across the site.

**Tech Stack:** Next.js App Router, React server components, Tailwind CSS v4 theme variables, existing content loader and local demo data.

---

### Task 1: Lock The New Theme Tokens

**Files:**
- Modify: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\app\globals.css`

**Step 1: Write the failing test**

There is no CSS test harness in this app, so use a visual contract check instead.

**Step 2: Run a current build snapshot**

Run: `npm run build`
Expected: PASS with the old editorial shell still intact.

**Step 3: Write minimal implementation**

- replace light background tokens with graphite / steel terminal tokens
- add reusable classes for:
  - system shell
  - hard panels
  - rail panels
  - data tables
  - alert halo
  - metadata labels
- keep report prose readable under the darker palette

**Step 4: Run build to verify it still passes**

Run: `npm run build`
Expected: PASS

### Task 2: Replace The Global Shell

**Files:**
- Modify: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\app\layout.tsx`
- Modify: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\components\site-header.tsx`
- Modify: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\components\site-footer.tsx`
- Modify: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\lib\site.ts`

**Step 1: Write the failing test**

Visual contract only. The current shell is wrong by design: light translucent header, soft footer, no system bar.

**Step 2: Run current preview**

Run: `npm run dev -- --hostname localhost --port 3000`
Expected: current site loads with the old soft header/footer.

**Step 3: Write minimal implementation**

- create a hard-edged header with:
  - compact brand block
  - terminal-grade nav
  - model/feed/system status metadata
  - thin live strip
- replace the layout background with dark grid / scan texture
- harden the footer into a restrained system footer
- update site copy in `site.ts` so the shell language matches the redesign

**Step 4: Run lint/build**

Run: `npm run lint`
Expected: PASS

Run: `npm run build`
Expected: PASS

### Task 3: Add Dual-Theater Data And Shape Support

**Files:**
- Modify: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\lib\types.ts`
- Modify: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\data\countries.ts`
- Modify: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\lib\site-data.ts`
- Modify: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\components\country-pulse-graphic.tsx`

**Step 1: Write the failing test**

The current homepage cannot render Iran and Israel because:
- no `iran` or `israel` shape keys exist
- no Iran or Israel demo profiles exist
- homepage helpers only expose a single featured country

**Step 2: Verify current limitation**

Run: `npm run build`
Expected: PASS, but there is still no dual-theater data path.

**Step 3: Write minimal implementation**

- extend `CountryShapeKey` with `iran` and `israel`
- add Iran and Israel profiles with homepage-quality summary, drivers, signals, and outlooks
- remove or stop depending on the single `featured` homepage flag
- expose helpers such as:
  - `getFeaturedTheaters()`
  - `getMonitorCountries()`
  - `getRisingCountries()`
- rework the silhouette component so it supports darker fills and danger halos

**Step 4: Run lint/build**

Run: `npm run lint`
Expected: PASS

Run: `npm run build`
Expected: PASS

### Task 4: Rebuild The Homepage As The Theater Desk

**Files:**
- Modify: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\app\page.tsx`
- Create: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\components\theater-hero.tsx`
- Create: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\components\monitor-table.tsx`
- Create: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\components\signal-rail.tsx`
- Create: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\components\chronology-strip.tsx`
- Create: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\components\featured-report-panel.tsx`

**Step 1: Write the failing test**

Visual contract only. The current homepage fails the approved design because it is:
- single-country
- centered on Sudan
- too soft
- too sectioned
- not table-first enough

**Step 2: Verify current state**

Run: `http://localhost:3000`
Expected: old editorial homepage with Sudan hero.

**Step 3: Write minimal implementation**

- replace the current hero with:
  - left rail brief
  - center dual-theater hero
  - right rail operational ladder
- insert a real homepage monitor table directly beneath the hero
- reduce explanatory prose
- keep one chronology block, one flagship report block, and one rising-theaters block
- ensure Iran and Israel dominate the visual hierarchy

**Step 4: Run lint/build and inspect**

Run: `npm run lint`
Expected: PASS

Run: `npm run build`
Expected: PASS

Preview:
- open `/`
- confirm dark shell, dual-theater hero, and database slice render correctly

### Task 5: Rebuild The Country Monitor

**Files:**
- Modify: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\app\countries\page.tsx`
- Reuse or extend: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\components\monitor-table.tsx`

**Step 1: Write the failing test**

The current countries page is a card wall and does not behave like a country monitor.

**Step 2: Verify current state**

Preview `/countries`
Expected: soft multi-card grid.

**Step 3: Write minimal implementation**

- replace the card wall with a dense table-first monitor
- add a compact utility/filter bar
- surface one-line summaries, bands, deltas, confidence, and freshness
- align row styling with the homepage monitor slice

**Step 4: Run lint/build and inspect**

Run: `npm run lint`
Expected: PASS

Run: `npm run build`
Expected: PASS

Preview `/countries`
Expected: table-first monitor surface

### Task 6: Rebuild The Country Dossier Page

**Files:**
- Modify: `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\app\countries\[slug]\page.tsx`
- Modify as needed:
  - `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\components\country-outlook-header.tsx`
  - `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\components\driver-list.tsx`
  - `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\components\timeline-list.tsx`
  - `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\components\scenario-grid.tsx`

**Step 1: Write the failing test**

The current dossier is still laid out like stacked editorial sections instead of left/right intelligence rails.

**Step 2: Verify current state**

Preview one country page such as `/countries/iran`
Expected after Task 3: page exists, but layout still reflects the older editorial composition until rewritten.

**Step 3: Write minimal implementation**

- create a dossier hero with silhouette and controlled halo
- shift the page into rail-based composition
- tighten chronology, drivers, and related-report modules
- keep evidence and report surfaces consistent with the terminal shell

**Step 4: Run lint/build and inspect**

Run: `npm run lint`
Expected: PASS

Run: `npm run build`
Expected: PASS

Preview `/countries/iran` and `/countries/israel`
Expected: dossier-style pages with strong shell consistency

### Task 7: Apply The Shell To Forecast, Reports, And Methodology

**Files:**
- Modify as needed:
  - `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\app\forecasts\page.tsx`
  - `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\components\forecast-explorer.tsx`
  - `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\app\reports\*.tsx`
  - `C:\Users\akgul\Downloads\codex_prompts_georisk\georisk\web\src\app\methodology\*.tsx`
  - related report and prose components

**Step 1: Write the failing test**

Those routes still inherit too much of the soft first-pass styling.

**Step 2: Verify current state**

Preview affected routes and note mismatched shell elements.

**Step 3: Write minimal implementation**

- port the same terminal tokens and panel rules to forecast, report, and methodology surfaces
- keep reports readable while hardening metadata and supporting blocks
- ensure methodology copy clearly separates implemented vs planned system pieces

**Step 4: Run lint/build and inspect**

Run: `npm run lint`
Expected: PASS

Run: `npm run build`
Expected: PASS

### Task 8: Final Verification

**Files:**
- No new files required unless verification uncovers regressions

**Step 1: Run lint**

Run: `npm run lint`
Expected: PASS

**Step 2: Run build**

Run: `npm run build`
Expected: PASS

**Step 3: Manual preview**

Open and inspect:
- `/`
- `/countries`
- `/countries/iran`
- `/countries/israel`
- `/forecasts`
- one report page
- `/methodology`

Expected:
- dark rectilinear shell
- dual-theater homepage
- no soft-card regression
- no broken layout on mobile/desktop widths

**Step 4: Commit**

```bash
git add web/src docs/plans
git commit -m "feat: redesign site as terminal intelligence interface"
```
