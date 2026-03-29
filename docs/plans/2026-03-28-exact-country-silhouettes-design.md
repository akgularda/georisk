# Exact Country Silhouettes Approved Design

## Goal

Replace the current hand-drawn country silhouette placeholders with exact source-based outlines for every supported `shapeKey` country, while shifting the visual treatment away from generic AI-dashboard glow and toward a harder emergency / breaking-news red presentation.

The result should feel like an urgent geopolitical command panel:

- exact country geometry
- severe editorial framing
- visible alert pressure
- no synthetic blob-art feeling

## Scope

This design applies to every currently supported silhouette country:

- `iran`
- `israel`
- `sudan`
- `ukraine`
- `syria`
- `colombia`
- `taiwan`
- `lebanon`

It covers:

- the shared silhouette source pipeline
- the runtime shape registry
- the `CountryPulseGraphic` rendering system
- the silhouette presentation used on the homepage theater and dossier pages

## Architecture

- keep one authoritative boundary source in the repo under `web/`
- generate normalized SVG path data from that source for all supported `shapeKey` countries
- store the generated runtime registry in source control so the app does not perform geometry work at render time
- keep `CountryPulseGraphic` as the single rendering component
- preserve the existing component API so pages do not need structural rewrites

The only allowed geometry transformations are:

- projection
- uniform scaling
- centering
- stable numeric serialization

No manual redrawing, no hand-tuned control points, and no per-country bespoke SVG art.

## Shape Source

The silhouettes should come from one admin-0 country boundary dataset. The source file must live in the repo so the site build never depends on a runtime network request.

Generation rules:

- match countries by ISO3
- preserve `Polygon` and `MultiPolygon` geometry from the source
- normalize each country into the existing silhouette canvas with consistent padding
- emit a stable SVG path string for runtime use

“Exact” means exact to the chosen boundary source and consistent across all supported countries.

## Visual Direction

The existing silhouette cards feel too much like AI-generated hero art because they treat the country as a glowing central object. That should change.

The new rendering should feel like a cartographic emergency plate:

- exact outline is the primary visual fact
- the frame stays rectilinear and severe
- red feels operational, not decorative
- the silhouette sits inside a controlled alert field, not a soft halo cloud
- the texture should be subtle, technical, and editorial

## Emergency / Breaking-News Red Treatment

The silhouette panels should read as urgent and live:

- stronger red signal field behind the country
- sharper contrast between outline, plate, and alert background
- reduced decorative softness
- visible pressure around the country boundary

But the effect should still be restrained:

- not neon
- not sci-fi bloom
- not posterized propaganda art
- not a generic AI heat-glow

The reference mood is “breaking-news command surface,” not “AI startup hero illustration.”

## Runtime Behavior

At runtime:

- `CountryPulseGraphic` reads from a generated path registry
- each country keeps its true aspect ratio
- silhouettes are fit and centered consistently
- the same component supports both `theater` and `dossier` sizes

No page should need to know where the geometry came from.

## Validation

The implementation should include a repeatable generator/validation path so the registry cannot silently drift.

Validation should confirm:

- every `CountryShapeKey` has a generated path
- every path is non-empty
- the generator fails if a supported ISO3 is missing from the source geometry

## Acceptance Criteria

- all supported `shapeKey` countries render from the single source-backed registry
- Lebanon and Israel visibly match their real outlines instead of the current placeholders
- the silhouette treatment feels more like emergency / breaking-news red than generic AI glow
- `CountryPulseGraphic` retains its current call sites
- `npm run lint` passes
- `npm run build` passes
- affected homepage and dossier panels render cleanly in browser verification
