# Exact Country Silhouettes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace all supported country silhouette placeholders with exact source-based outlines and restyle the silhouette panels so they read as urgent breaking-news red instead of generic AI glow.

**Architecture:** Vendor one repo-local boundary source under `web/`, generate a checked-in runtime path registry from that source, then switch `CountryPulseGraphic` to the generated paths and a stricter emergency plate visual treatment. Keep runtime simple: no projection logic in React, no page-level API changes, and no hand-drawn SVG maintenance.

**Tech Stack:** Next.js App Router, React, Tailwind CSS v4 theme variables, repo-local GeoJSON, Node scripts, TypeScript.

---

### Task 1: Add The Source Geometry And Failing Validation

**Files:**
- Create: `web/data/country-boundaries.geojson`
- Create: `web/scripts/validate-country-shapes.mjs`
- Modify: `web/package.json`

**Step 1: Write the failing test**

Create `web/scripts/validate-country-shapes.mjs` that:
- imports the generated runtime registry if present
- knows the supported shape keys and expected ISO3 coverage
- exits non-zero if any shape key is missing or mapped to an empty path

**Step 2: Run it to verify it fails**

Run: `node scripts/validate-country-shapes.mjs`
Expected: FAIL because no generated exact-shape registry exists yet.

**Step 3: Add the source geometry**

- vendor one repo-local GeoJSON file containing the supported countries only
- keep the file under `web/data/`
- ensure the geometry source is sufficient for:
  - `iran`
  - `israel`
  - `sudan`
  - `ukraine`
  - `syria`
  - `colombia`
  - `taiwan`
  - `lebanon`

**Step 4: Add npm script wiring**

- add `shapes:validate` to `web/package.json`

**Step 5: Re-run the failing validation**

Run: `npm run shapes:validate`
Expected: still FAIL because the runtime registry has not been generated yet.

### Task 2: Generate The Runtime Shape Registry

**Files:**
- Create: `web/scripts/generate-country-shapes.mjs`
- Create: `web/src/lib/country-shapes.ts`

**Step 1: Write the failing generation expectation**

Use the validation script from Task 1 as the failure harness.

**Step 2: Implement the generator**

`generate-country-shapes.mjs` should:
- read `web/data/country-boundaries.geojson`
- map supported `shapeKey` values to ISO3
- select the matching source feature
- project coordinates into a fixed SVG coordinate space
- preserve aspect ratio
- fit each outline into the existing `360 x 360` canvas with consistent padding
- emit a checked-in `web/src/lib/country-shapes.ts`

`country-shapes.ts` should export:
- `COUNTRY_SHAPE_KEYS`
- shape metadata if needed
- `countryShapes: Record<CountryShapeKey, string>`

**Step 3: Run generator**

Run: `node scripts/generate-country-shapes.mjs`
Expected: PASS and write `src/lib/country-shapes.ts`.

**Step 4: Run validation**

Run: `npm run shapes:validate`
Expected: PASS

### Task 3: Switch The Component To Exact Shapes

**Files:**
- Modify: `web/src/components/country-pulse-graphic.tsx`
- Modify: `web/src/lib/types.ts`

**Step 1: Write the failing test**

The current component still renders hardcoded placeholder paths.

Use:
- `npm run shapes:validate`
- `npm run build`

Expected: PASS before code changes, but component still ignores the generated registry and therefore fails the approved design.

**Step 2: Implement the minimal runtime change**

- remove the inline hardcoded shape path table from `country-pulse-graphic.tsx`
- import the generated runtime registry from `src/lib/country-shapes.ts`
- keep the `CountryPulseGraphic` props stable
- keep `CountryShapeKey` aligned with the generated registry

**Step 3: Verify**

Run: `npm run lint`
Expected: PASS

Run: `npm run build`
Expected: PASS

### Task 4: Restyle The Silhouette Panels Away From AI Glow

**Files:**
- Modify: `web/src/components/country-pulse-graphic.tsx`
- Modify: `web/src/app/globals.css`

**Step 1: Write the failing visual contract**

Current problems:
- oversized floating halo
- object-in-space composition
- too much decorative softness
- not enough emergency / breaking-news red pressure

**Step 2: Implement the new treatment**

- reduce or remove the generic soft halo behavior
- introduce a flatter alert-field plate behind the country
- make the red treatment sharper and more urgent
- keep technical texture subtle and rectilinear
- preserve a calm, exact silhouette fit that respects true country aspect ratio
- make theater mode feel more urgent than dossier mode without changing the component API

**Step 3: Verify**

Run: `npm run lint`
Expected: PASS

Run: `npm run build`
Expected: PASS

### Task 5: Browser Verification Of The Affected Surfaces

**Files:**
- No additional source files required unless verification exposes regressions

**Step 1: Run the web checks**

Run: `npm run shapes:validate`
Expected: PASS

Run: `npm run lint`
Expected: PASS

Run: `npm run build`
Expected: PASS

**Step 2: Preview affected routes**

Inspect:
- `/`
- `/countries/lebanon`
- `/countries/israel`
- `/countries/iran`
- `/countries/ukraine`

Expected:
- exact source-based outlines
- no placeholder geometry
- Lebanon and Israel clearly read as real country shapes
- silhouette cards feel urgent and breaking-news red, not AI-glow generic
- layout remains stable on desktop and mobile

### Task 6: Final Cleanup

**Files:**
- Update only if verification reveals gaps

**Step 1: Re-run generator**

Run: `node scripts/generate-country-shapes.mjs`
Expected: no unexpected diff after the final implementation.

**Step 2: Re-run validation**

Run: `npm run shapes:validate`
Expected: PASS

**Step 3: Re-run lint/build**

Run: `npm run lint`
Expected: PASS

Run: `npm run build`
Expected: PASS
