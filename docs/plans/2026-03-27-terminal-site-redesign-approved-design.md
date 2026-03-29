# Terminal Site Redesign Approved Design

## Goal

Redesign the entire `web/` app into a hard-edged geopolitical intelligence terminal with one dominant visual idea:

> the homepage is a dual-theater command surface centered on Iran and Israel, each rendered as a country silhouette on a restrained red danger field.

The site must stop reading like a soft editorial AI product. It should read like a severe intelligence system with a database spine and a clear sense of operational urgency.

## Product Position

This redesign should not look like:
- a startup landing page
- a generic AI dashboard
- a rounded card wall
- a glassmorphism or glow-heavy interface

It should feel like:
- a terminal-grade intelligence product
- a compact command surface
- a country-first geopolitical monitor
- a research system with visible structure and restraint

## Visual System

### Palette

- background: near-black graphite
- panel: muted steel / dark charcoal
- text: off-white
- secondary text: steel gray
- red: restrained alert color and danger-field anchor
- amber: caution / uncertainty / neutral stress
- green: positive directional movement or system-health only

### Shape language

- square or near-square corners
- strong horizontal and vertical dividers
- hard panel boundaries
- no soft floating cards
- no blob gradients
- no big rounded hero shells

The only deliberate curved form is the danger halo behind country silhouettes.

### Typography

- keep `Inter`
- use tighter uppercase metadata labels
- emphasize numbers more aggressively than prose
- keep body copy concise and analyst-like
- favor compact hierarchy over airy editorial spacing

### Motion

- minimal
- danger halos can drift or pulse slowly
- subtle scan-line or grid movement is acceptable
- no glow-bloom softness
- no bouncy card hover behavior

## Site Architecture

The site should behave like one coherent system.

- `/` becomes the `Theater Desk`
- `/countries` becomes the `Country Monitor`
- `/countries/[slug]` becomes the `Country Dossier`
- `/forecasts` becomes the `Forecast Board`
- `/reports/[slug]` keeps long-form reading inside the same shell
- `/methodology` becomes the `System Manual`
- `/about` stays minimal

## Homepage

### Structure

The homepage uses a three-part hero and then drops directly into database-first monitoring.

- top frame
  - brand left
  - model, feed, status, update metadata right
  - thin live strip beneath
- hero
  - left rail: lead brief, drivers, 72h changes, chronology excerpt
  - center: Iran and Israel silhouettes on separate red danger circles, slight overlap or visible tension seam
  - right rail: 7d / 30d / 90d ladder, confidence, freshness, signal agreement, flagship report, scenario framing
- database slice directly under hero
  - dense country monitor table
  - region / risk / movement / freshness filters
  - one-line summaries
- lower intelligence band
  - chronology
  - one flagship report
  - other rising theaters

### Homepage principles

- the hero is the only atmospheric area on the page
- the site should be glanceable before it is readable
- the dual-theater object must be unforgettable
- no long marketing-style explanation blocks

## Country Dossiers

Country pages are working surfaces, not articles with cards attached.

- one silhouette hero with smaller controlled danger field
- left rail for situation reading, drivers, triggers, 72h changes
- center for score, horizons, scenario framing, chronology, evidence
- right rail for confidence, freshness, source coverage, scenario and report links
- chronology must read like a case file
- reports and references stay inside the same system shell

## Country Monitor

The monitor should borrow the seriousness of CrisisWatch while remaining more visually distinctive.

- dense sortable/filterable table
- severity lives in edges, chips, or narrow markers
- no oversized cards or decorative maps
- optional preview pane on larger screens
- one-line situation summaries are required

## Forecast Board

The forecast board is more model-facing than the monitor.

- table-first layout
- compact top metrics
- filters for horizon, region, confidence, freshness
- ranked rows for score, delta, confidence, freshness, strongest driver
- only minimal secondary panels

## Reports

Reports should read like intelligence briefs.

- strong metadata row
- hard dividers
- one-sentence thesis near the top
- visible "what changed" block
- evidence callouts and scenario framing
- no soft magazine treatment

## Methodology And Tone

Methodology should read like a manual, not a trust-marketing page.

- explicit sections for what exists vs what is planned
- direct wording about data, scoring, confidence, and failure modes
- short claims, visible timestamps, visible caveats

Tone rules:
- analyst brief
- terse
- operational
- restrained
- never startup-brand language
- never melodramatic language

## Data Requirements For The UI

The design requires presentational support for:
- two featured homepage countries instead of one featured flag
- `iran` and `israel` country silhouettes
- denser country rows with short summaries and freshness metadata
- explicit model/feed/status text in the global shell

These can be implemented as structured demo content now and later swapped to real forecast artifacts without changing the shell.

## Non-Negotiables

- the site-wide shell is dark, rectilinear, and severe
- Iran and Israel both appear in the homepage hero
- the country shape remains primary, not a map, not a chart
- the red danger circle is intentional and restrained
- the homepage contains an actual country-monitor slice, not just storytelling modules
- the current soft editorial system is treated as replaceable first-pass work
