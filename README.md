# Georisk

Implementation workspace for a geopolitical early-warning platform.

Read first:
- [final.md](C:/Users/akgul/Downloads/codex_prompts_georisk/final.md)

Current scope:
- real-source weekly data platform with `ACLED`, `FAO`, `GDELT`, `IDEA`, `IMF`, `NASA Black Marble`, `NOAA`, `SIPRI`, `UN Comtrade`, `UNCTAD`, `UCDP GED`, `UNHCR`, `WGI`, and `World Bank WDI`
- real `country_week` forecasting pipeline
- implemented backtesting package and CLI
- publishing app in [web](C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/web) using Next.js App Router, TypeScript, Tailwind CSS, and MDX
- tests for data-platform contracts, forecasting, and backtesting

Current gaps:
- no implemented social publishing subsystem yet
- no dense downstream serving table set yet

Current priority:
- densify the weekly data layer and downstream serving tables
- strengthen the real forecasting path on that denser history
- wire publication layers to generated forecast and backtest artifacts

Read next:
- canonical checkpoint: [final.md](C:/Users/akgul/Downloads/codex_prompts_georisk/final.md)
- current repo status: [current_state.md](C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/docs/current_state.md)
- prompt-aligned roadmap: [2026-03-26-prompt-aligned-roadmap.md](C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/docs/plans/2026-03-26-prompt-aligned-roadmap.md)

Prompt-pack source material remains in the sibling [codex_prompts](C:/Users/akgul/Downloads/codex_prompts_georisk/codex_prompts) directory.
