# Government Emergency Design Brief

## Purpose

This brief turns the emergency-surface research into a concrete design doctrine for the website.

The target is not "more dramatic." The target is a site that feels like an official warning service:

- credible
- urgent
- clear under stress
- usable on first scan
- impossible to confuse with a generic AI dashboard

This brief governs Task 10 of the evergreen website hardening plan.

## Recommended Reference Family

The visual reference family should be:

- U.S. Web Design System for banner, alert, summary, and federal-service credibility
- GOV.UK Design System for layout, warning text, service-problem copy, and typographic discipline
- W3C / WCAG guidance for structure, alert semantics, target size, reflow, and contrast
- official hazard and emergency services for status rhythm and severity communication

The site should not reference:

- sci-fi operations dashboards
- glow-heavy "command center" product pages
- abstract AI hero layouts
- cinematic intelligence UI tropes

## Design Position

Adopt a **government emergency surface** rather than a product dashboard.

The homepage and country pages should read like an emergency briefing issued by a serious institution:

- one dominant situation summary
- one visible status layer
- one clear hierarchy
- direct language
- visible timestamps and provenance

The user should know the top-risk country, forecast freshness, and fallback status within a five-second scan.

## Non-Negotiable Rules

1. One dominant lead only above the fold.
2. One sitewide emergency or status banner only.
3. Red is reserved for elevated states, warnings, and critical numbers, not for ambiance.
4. Freshness, published time, forecast-as-of date, and fallback state must be visible near the main claim.
5. Text-first evidence beats decorative panels.
6. Country graphics are locator artifacts, not visual theater.
7. Operational pages use sentence case for real headings.
8. Mobile and zoomed layouts must preserve reading order and scanning.
9. No critical meaning can rely on color alone.
10. Nothing decorative should remain if it does not help comprehension.

## Page Anatomy

Every operational page should share the same first-screen structure:

1. institutional identity strip
2. sitewide emergency or status banner
3. page heading
4. one lead assessment sentence
5. key-facts strip
6. main evidence area

### Homepage

The homepage should answer:

- which country is highest risk
- what changed
- how fresh the forecast is
- whether fallback is active
- where the user goes next

It should stop behaving like a three-column theatrical hero.

### Country page

The country page should answer:

- why this country is on the board
- what the current forecast says
- what evidence supports that ranking
- how recent the data is

The current country shape can stay, but only as a flat locator graphic.

### Status page

The status page should look like a public service status bulletin:

- current freshness tier
- latest publish time
- forecast-as-of date
- fallback or outage status
- affected surfaces
- next expected update window if known

## Style System

### Typography

Operational typography should feel institutional, not startup-generic.

Recommended stack:

- primary UI sans: `Public Sans`
- secondary mono for technical metadata: `IBM Plex Mono`

Rules:

- remove `Inter` as the visual lead on operational surfaces
- use sentence case for headings
- keep all-caps only for small structural labels
- keep the scale tight: display, heading, body, metadata
- prefer real headings over repeated micro-kickers

### Color

Base palette:

- near-black or graphite background
- flat dark neutral surfaces
- warm off-white foreground
- cool neutral dividers

Signal palette:

- one hard emergency red
- one amber for aging or caution
- one green for healthy system state

Rules:

- red appears in bars, labels, warning frames, and key figures
- red does not wash entire pages
- do not stack multiple hot accent colors in one panel
- no purple, neon, or speculative "AI" color language

### Surfaces

Operational surfaces should be flatter and stricter:

- hard edges or lightly rounded corners
- thin borders
- minimal shadow
- no stacked gradients in reading areas
- no atmospheric grid or scanline background behind primary text

## Component Guidance

### Institutional identity strip

Purpose:

- establish authenticity immediately
- show institution, model, and feed identity in a sober way

Should include:

- organization name
- product name
- model version
- live or stale status text

Should not include:

- decorative brand theatrics
- multiple competing badges

### Sitewide emergency banner

Purpose:

- communicate the highest-priority operational state across the site

Should include:

- short plain-language state
- freshness or outage message
- short action links where needed

Should not include:

- multiple simultaneous banners
- auto-dismiss behavior
- long prose

### Key-facts strip

Purpose:

- expose the facts users need immediately

Should include:

- score
- weekly change
- forecast horizon
- forecast-as-of date
- published time
- freshness tier
- fallback state
- coverage

### Country graphic

Purpose:

- support orientation only

Should include:

- exact shape where available
- direct label
- flat severe treatment

Should not include:

- glow
- crosshair
- fake radar
- decorative overlays
- dramatic framing copy

### Forecast board and monitor table

Purpose:

- support rank comparison under stress

Rules:

- table-first presentation
- clear row priority
- fewer chips, more direct labels
- mobile collapse must remain readable
- critical state should be written out, not implied

## Copy Rules

Operational copy must sound like a government service.

Write:

- short sentences
- active voice
- plain language
- explicit status terms
- direct next steps

Avoid:

- fictional command-center language
- vague system jargon
- hype
- cinematic phrasing

Bad:

- "The desk auto-focuses on the highest-stress dossier countries."

Better:

- "Lebanon has the highest forecast risk in the latest published snapshot."

Every warning should answer:

- what changed
- why it matters
- what the user should do next

## Anti-Pattern Blacklist

Do not ship the following on operational pages:

- glassmorphism
- ambient glow
- oversized gradient atmospherics
- radar or reticle motifs
- stacked hero cards
- giant all-caps headlines
- decorative chips everywhere
- synthetic "terminal" micro-label repetition
- pulse animations
- fictive intelligence copy

## Verification Standard

Task 10 implementation should not be considered complete until:

- the lead country is obvious within a five-second scan
- freshness and fallback are visible without scrolling
- stale and outage states are unmistakable
- keyboard navigation remains clean
- focus states remain visible
- mobile reflow remains readable at `320 CSS px`
- the pages no longer read as a generic AI dashboard

## Source Basis

This brief is based on:

- [2026-03-28-emergency-surface-design-research.md](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/docs/plans/2026-03-28-emergency-surface-design-research.md)
- [U.S. Web Design System](https://designsystem.digital.gov/)
- [GOV.UK Design System](https://design-system.service.gov.uk/)
- [W3C WAI tutorials and WCAG understanding docs](https://www.w3.org/WAI/)
- [CDC CERC guidance](https://www.cdc.gov/cerc/php/about/index.html)
- [Section508.gov typography guidance](https://www.section508.gov/develop/fonts-typography/)
