# Emergency Surface Design Research

## Executive Summary

The current website already communicates severity, but too much of that severity comes from decorative cues: terminal framing, repeated micro-labels, red grid overlays, split-focus hero composition, and synthetic "operations room" styling. That reads closer to an AI-generated dashboard than to a credible public-sector or institutional emergency surface.

The research-backed direction is different:

- urgency should come from priority, placement, and plain language
- trust should come from timestamps, provenance, and evidence rhythm
- usability should come from typography, hierarchy, spacing, and accessible states
- visual identity should be severe and intentional, not theatrical

Recommended direction: **Institutional Emergency Operations**

This keeps the dark operational tone that fits the brand, but replaces sci-fi dashboard styling with a flatter, more official, more legible public-sector system. The site should feel closer to a government emergency bulletin, an official hazards surface, or a serious wire-service briefing than to a startup analytics dashboard.

## Research Questions

1. What makes an emergency or official public-information website feel urgent without becoming sensational?
2. What design rules maximize usability when users need to scan quickly under stress?
3. Which patterns make interfaces look like generic AI dashboards, and what should replace them?
4. How should those findings change this specific website's operational surfaces?

## Methodology

This research combined:

- current-repo review of the existing web presentation in [page.tsx](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/web/src/app/page.tsx), [country-pulse-graphic.tsx](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/web/src/components/country-pulse-graphic.tsx), [monitor-table.tsx](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/web/src/components/monitor-table.tsx), [forecast-explorer.tsx](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/web/src/components/forecast-explorer.tsx), and [globals.css](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/web/src/app/globals.css)
- official public-sector design systems and content guidance
- accessibility standards and W3C usability guidance
- official emergency communication and hazard presentation examples
- editorial trust guidance from a major news institution

## Current Design Diagnosis

The present system's main visual weaknesses are structural, not cosmetic.

### What the current UI gets wrong

- The homepage hero splits attention across three loud columns instead of establishing one dominant emergency briefing.
- The dark gradients, red grid textures, and repeated "terminal" chrome create atmosphere, but they weaken official credibility.
- `Inter` and heavy badge usage make the UI feel like a contemporary SaaS dashboard instead of a state or institutional warning surface.
- Decorative micro-labels like "Lead brief", "Emergency focus", and "Command notes" appear everywhere, which lowers information density while increasing noise.
- The country silhouette panels still rely on a display treatment that reads as designed spectacle rather than as operational evidence.
- Tables use many badges and status chips, but not enough direct labels, clear row priorities, or mobile-first emergency scanning rules.

### What must change

- Move from "dashboard theater" to "official bulletin hierarchy"
- Move from decorative urgency to operational urgency
- Move from many equally loud panels to one dominant lead and a disciplined secondary structure
- Move from style-first widgets to text-first evidence surfaces

## Three Design Approaches

### Approach A: Civic Minimalism

Make the site feel very close to a government service portal.

Pros:

- maximum clarity
- strongest public-sector trust cues
- easiest accessibility path

Cons:

- loses too much brand distinctiveness
- can feel too administrative for a geopolitical forecasting surface

### Approach B: Institutional Emergency Operations

Keep a dark graphite shell, but use public-sector hierarchy, flatter panels, restrained signal red, stronger typography, and text-first alert structure.

Pros:

- preserves the site's intelligence and emergency tone
- removes most AI-dashboard cues
- supports live status and operational scanning well

Cons:

- requires a broad but coherent redesign across multiple operational pages

### Approach C: Editorial Intelligence Briefing

Push the site toward a magazine or wire-service briefing style with stronger editorial typography and less operational UI chrome.

Pros:

- highly credible and serious
- better for longform reports and methodology

Cons:

- weaker for live status and alert-state communication
- less suited to forecast-board and monitor interactions

## Recommendation

Use **Approach B: Institutional Emergency Operations**.

It is the best fit for the product and the research. It preserves a command-surface tone, but grounds it in public-sector usability rules, clear alert semantics, and editorial trust cues.

## Key Findings

### 1. Urgency should come from placement, hierarchy, and update cadence

Official emergency surfaces do not create urgency by making everything loud. They make the highest-priority state dominant and suppress competing signals.

Evidence:

- USWDS says site alerts should be used for critical notifications, should be placed prominently near the top of the page, and should not be stacked across the interface.
- NWS explicitly shows only one event per forecast zone at a time, and displays only the most significant threat to life or property on the map.
- WHO's emergency risk communication guidance emphasizes accurate information delivered early, often, and in trusted language and channels.

Design consequence:

- one global operational alert strip only
- one primary lead country above the fold
- one clearly dominant update timestamp and freshness state
- no multi-alert piles, no equal-volume competing hero cards

### 2. Maximum usability under stress depends on structure, not decoration

Accessibility guidance and government design systems align on the same core pattern: users need strong document structure, readable text measure, consistent headings, and interaction targets that do not force precision.

Evidence:

- W3C says well-structured content allows more efficient navigation and helps users find and prioritize content.
- USWDS recommends left-aligned type and says most lines of text should stay within a readable range, with around 66 characters as a strong target for long text.
- GOV.UK's type scale guidance emphasizes larger small-screen text, tested readability, consistent rhythm, and relative units for zoom.
- WCAG 2.2 target-size guidance sets the minimum size expectation around a 24 by 24 CSS pixel interaction footprint, though the practical UI target here should be larger.

Design consequence:

- stronger heading ladder with fewer decorative sublabels
- tighter max measure on summaries and notes
- simpler mobile layouts with larger controls
- clearer section landmarks and table/cell labeling

### 3. Serious official interfaces use warnings sparingly

Institutional systems do not turn every panel into an alert. They reserve high-attention treatments for actual warnings.

Evidence:

- GOV.UK says notification banners should be used sparingly because people often miss them, and only the highest-priority banner should remain if messages cannot be combined.
- GOV.UK also says if information is directly relevant to the user's task, it should be in the main page content rather than in a banner.
- GOV.UK warning text is for genuinely important consequences, not for general emphasis.

Design consequence:

- use red only for actual risk, stale-critical states, and explicit warning surfaces
- keep most secondary UI in neutral graphite, slate, and paper tones
- replace many accent chips with direct text labels
- do not use "warning" treatments for ordinary metadata

### 4. Decorative imagery is usually a trust leak on serious operational pages

Government guidance is blunt here: decorative imagery rarely helps comprehension, and text remains the primary vehicle for accessible information.

Evidence:

- GOV.UK says not to use images alone to provide information.
- GOV.UK says to use images only if they help users understand information in a different way.
- GOV.UK defines decorative images as generic images that add no information.

Design consequence:

- country silhouettes stay only where they support orientation
- no fake-radar, crosshair, or cinematic glass overlays
- no stock-photo style hero treatments
- every visual on an operational page must either explain or be removed

### 5. Credible emergency communication depends on trust and attribution

The site needs to feel less like it is "performing intelligence" and more like it is issuing a traceable operational brief.

Evidence:

- WHO stresses that people act when information is accurate, early, frequent, and delivered through trusted channels.
- AP's fact-check guidance says: be sure you are right, focus on what matters, keep items short, and support claims with attribution.

Design consequence:

- every major operational panel needs a visible timestamp
- provenance and freshness should appear inline, not be buried
- lead summaries should be short and factual
- the UI should prefer exact labels like `Updated`, `Forecast as of`, `Confidence`, `Baseline fallback`, `Coverage`

### 6. Emergency severity is a taxonomy problem, not just a color problem

Official emergency systems classify severity explicitly.

Evidence:

- NWS uses a severity vocabulary of warnings, watches, advisories, and statements, plus explicit color mapping.
- CISA differentiates `Alert` and `Advisory` based on immediacy and depth.

Design consequence:

- the site should use explicit severity/state language instead of generic mood words
- example operational states: `Normal`, `Aging`, `Stale`, `Critical`, `Fallback`, `Outage`
- example forecast surface labels: `Lead Risk`, `Elevated`, `Monitor`, `Baseline Fallback`

## Visual Heuristics

### What should make the site feel official and urgent

- a single dominant lead story above the fold
- strong timestamping and provenance
- flat panels with hard edges and thin rules
- disciplined use of red for real alerts only
- sober typography with visible hierarchy
- quiet backgrounds and high text contrast
- explicit status language instead of atmospheric cues
- evidence next to claims

### What makes interfaces look like generic AI dashboards

- too many glowing cards
- too many small labels, chips, and decorative status pills
- gradients and background effects carrying the whole emotional load
- split-focus hero sections with multiple equally important cards
- stock "command center" copy
- abstract icons or maps that communicate mood more than meaning
- large numerical displays without nearby interpretation or provenance

## Component-Level Do / Don't

### Global Page Shell

Do:

- use a calm graphite or off-black base
- keep one background treatment for the whole page
- use thin dividers and consistent spacing bands

Do not:

- stack grid, wash, vignette, scanline, and glow effects together
- make every section look like a separate terminal

### Header And Global Alert Strip

Do:

- place one full-width status strip near the top
- expose `Fresh`, `Aging`, `Stale`, `Critical`, `Fallback`, or `Outage` clearly
- keep the strip short and factual

Do not:

- run multiple alert bars simultaneously
- use marketing-style announcement banners

### Homepage Hero

Do:

- lead with one country only
- put the country, score, forecast horizon, freshness, and update time at the top
- follow with a short evidence-based summary
- keep the next-most-important items in a narrow secondary rail

Do not:

- split the hero between two countries as the default operational mode
- use giant decorative subheads or cinematic framing

### Country Silhouette / Locator Graphic

Do:

- keep the exact shape if available
- flatten the treatment so the outline reads as a locator artifact
- pair shape with plain text labels and status metadata

Do not:

- use silhouettes as pure decoration
- add radar overlays, reticles, scan rings, or glossy glass effects

### Monitor Table And Forecast Board

Do:

- sort with one dominant criterion by default
- expose the reason for rank near the number
- reduce chip count and write labels directly in the table
- support mobile collapse into labeled stacked records

Do not:

- make tables depend on color alone
- hide key metadata inside badges
- put too many filters ahead of the actual ranking

### Status And Methodology Panels

Do:

- present system status, freshness, fallback state, coverage, and provenance as plain factual rows
- keep alert language consistent across operational and methodology surfaces

Do not:

- separate trust signals from the pages where users need them
- bury baseline fallback or stale state in explanatory prose

## Short Style System Direction

### Design Character

- institutional
- severe
- evidence-led
- flat
- print-informed
- operational, not cinematic

### Typography

- UI sans: `Public Sans` or `Source Sans 3`
- data mono: `IBM Plex Mono`
- editorial/report serif: `Source Serif 4` where longform needs warmth and authority

Rules:

- remove `Inter` from operational surfaces
- reserve all-caps tracked text for small structural labels only
- use fewer labels, larger actual headings
- default body copy should read like a briefing, not like UI helper text

### Color

Base:

- graphite / near-black backgrounds
- warm paper foreground
- cool gray structural lines

Signals:

- one hard emergency red for alerts and high-risk emphasis
- one amber for caution / aging
- one green for healthy status only

Rules:

- red should be rare and meaningful
- no purple, neon, or gradient-led emotion
- no more than two accent colors active in a single operational panel

### Layout

- single dominant lead column above the fold
- one secondary rail for status and provenance
- max content width around 1200-1280px for operational pages
- tighter measures for explanatory text

### Surfaces

- flat panels
- thin rules
- restrained shadows only where needed for separation
- no floating-glass effect

### Motion

- minimal
- no looping ambient motion
- only state-change emphasis, page-enter fade, and filter/sort continuity

## Design Requirements For The Later Implementation Task

The later visual implementation should satisfy these hard rules:

1. Every operational page must identify one primary action or interpretation above the fold.
2. No operational page may stack more than one top-level warning/banner surface.
3. Red must be reserved for genuinely elevated states, not routine metadata.
4. Operational pages must remain legible and structured at 200% zoom.
5. Interactive controls should exceed the WCAG minimum and target an easier practical size.
6. Every risk claim on the homepage and country pages must have visible freshness or provenance nearby.
7. The design must support artifact-only countries without looking broken or unfinished.
8. Decorative imagery that adds no information must be removed.
9. Motion must remain subordinate to reading and scanning.
10. The design must feel like an official emergency briefing, not a startup analytics product.

## Source Notes

### Primary sources

1. WHO, *Emergencies: Emergency risk communication guidance* (11 January 2018)
   - https://www.who.int/news-room/questions-and-answers/item/emergencies-emergency-risk-communication-guidance
   - Key use: trust, timeliness, clarity, evidence-based emergency communication

2. U.S. Web Design System, *Site alert*
   - https://designsystem.digital.gov/components/site-alert/
   - Key use: alert placement, non-stacking, prominence, ARIA roles

3. U.S. Web Design System, *Typography*
   - https://designsystem.digital.gov/components/typography/
   - Key use: line length, left alignment, line height, readable density

4. GOV.UK Design System, *Notification banner*
   - https://design-system.service.gov.uk/components/notification-banner/
   - Key use: sparing usage, priority handling, page placement

5. GOV.UK Design System, *Warning text*
   - https://design-system.service.gov.uk/components/warning-text/
   - Key use: warning reserved for important consequences

6. GOV.UK Design System, *Type scale*
   - https://design-system.service.gov.uk/styles/type-scale/
   - Key use: responsive legibility, tested readability, consistent rhythm

7. GOV.UK content guidance, *Images*
   - https://www.gov.uk/guidance/content-design/images
   - Key use: no decorative information, text-first communication, color accessibility

8. W3C WAI, *Page Structure Tutorial* (updated 24 March 2026)
   - https://www.w3.org/WAI/tutorials/page-structure/
   - Key use: section landmarks, headings, efficient navigation

9. W3C WAI, *Understanding Success Criterion 2.5.8: Target Size (Minimum)*
   - https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
   - Key use: minimum interaction size and spacing

10. National Weather Service, *Weather.gov Help - Hazards Map*
    - https://www.weather.gov/help-map/
    - Key use: most-significant-threat display logic and explicit update cadence

11. CISA, *Cybersecurity Alerts & Advisories*
    - https://www.cisa.gov/news-events/cybersecurity-advisories
    - Key use: severity taxonomy and clear distinction between alert and advisory

12. The Associated Press, *What we fact-check and why* (1 February 2017)
    - https://www.ap.org/the-definitive-source/behind-the-news/what-we-fact-check-and-why/
    - Key use: concise leads, relevance, attribution, certainty

### Short synthesis

Across public-sector, emergency, accessibility, and editorial guidance, the pattern is consistent:

- make the most important thing obvious
- reduce competition for attention
- prefer words and structure over decorative symbolism
- show freshness, certainty, and provenance near the claim
- keep warning treatments rare so they remain believable
