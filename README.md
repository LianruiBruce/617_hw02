# HW02 — Data Story Remix: The New-Look Utah Jazz

## Original Story

**"Why I'm Obsessed With the New-Look Utah Jazz"**
by Michael Pina, The Ringer, February 3, 2026.
[Read the original article →](https://www.theringer.com/2026/02/03/nba/jaren-jackson-jr-trade-utah-jazz-lauri-markkanen-2026-nba-draft)

## Remix Summary

The original article is an optimistic narrative about how the Jaren Jackson Jr. trade transforms the Jazz into a compelling team with a projected starting five of **Walker Kessler, Keyonte George, Lauri Markkanen, Jaren Jackson Jr., and Ace Bailey**. Pina argues that the pieces fit together spatially and functionally, with enough youth and draft capital to keep building.

My remix retains the optimism but restructures the argument into **three testable layers**, each supported by a different visualization:

1. **Space** — Do the five players actually occupy different zones on the court?
2. **Roles** — Do their functional profiles complement each other, or do they overlap?
3. **Risks** — What structural weaknesses does the data reveal that the narrative glosses over?

This three-act structure turns the original essay-style argument into a data-driven narrative where the reader can interact with the evidence and form their own conclusions, rather than passively absorbing the author's enthusiasm.

## Visualizations

### Viz 1: Shot Map (D3, Interactive)

A half-court scatter plot of every recorded field-goal attempt for the five projected starters in the 2025-26 season.

- **Design purpose**: Give readers an immediate spatial intuition for why the original article is optimistic — you can *see* that these five players tend to occupy different areas.
- **Interactions**: Click player chips to filter; click individual dots to inspect shot details (action type, zone, distance, make/miss); density and filter controls; cross-chart focusing from Viz 2.
- **Trade-offs**: With 2300+ shots, density is a problem. I added a sampling control (Sparse / Medium / Dense / All) so the user can balance readability vs. completeness. Stats in the legend always use the full dataset.

### Viz 2: Role Fit Matrix (D3, Interactive)

A player × role-dimension heatmap using six functional metrics: floor spacing, rim pressure, shot creation, scoring load, rim protection proxy, and shot versatility.

- **Design purpose**: Move beyond spatial intuition to structural analysis. The matrix makes it immediately visible that, e.g., Kessler dominates rim pressure while George dominates shot creation — the roles don't redundantly overlap.
- **Interactions**: Hover shows the metric description and raw score. **Click any cell** to trigger view coordination — the shot map above automatically filters to show only that player in the zones most relevant to that metric.
- **Trade-offs**: The scores are min-max normalized proxies, not ground-truth advanced stats. Rim protection uses blocks/game as an approximation. I document this in the method notes and the story text.

### Viz 3: Risk Audit (D3, Interactive Bar Charts)

Three side-by-side bar chart cards, each addressing a specific structural risk:

1. **Sample size imbalance**: Kessler (37 shots) and JJJ (49 shots) have drastically fewer logged attempts than George (839), Markkanen (805), and Bailey (628).
2. **Creation burden**: George accounts for ~42% of the group's assists, making the ball-handling hierarchy narrow.
3. **Spacing concentration**: Markkanen and George produce ~56% of the lineup's three-point volume.

- **Design purpose**: Provide the counterargument that the original article largely omits. This is the "remix" turn — I'm not just restating Pina's optimism, I'm testing it.
- **Interactions**: Hover on any bar to cross-highlight that player on the shot map (view coordination). Bars animate in on load.
- **Trade-offs**: I kept these as simple horizontal bars rather than more complex charts because the point is immediate visual comparison, not deep exploration. The narrative text below each card provides context.

## View Coordination

Clicking a cell in the Role Matrix (Viz 2) or hovering a bar in Risk Audit (Viz 3) triggers the Shot Map (Viz 1) to focus on the relevant player and zone subset. A "Clear focus" button resets the view. This bridges the three sections into a single interactive reading experience.

## Data Pipeline

The data is collected via `hw02_getScoreData.py`, which:

1. Fetches shot chart data from `nba_api.ShotChartDetail` for all five players
2. Fetches per-game stats from `nba_api.LeagueDashPlayerStats`
3. Classifies each shot into zones (At Rim, Paint/Floater, Midrange, Corner 3, Above Break 3) and action buckets (Spot-Up, Self-Created, Paint Finish, Drive/Floater, Post Touch)
4. Computes role proxy scores by combining shot distribution with per-game stats
5. Generates risk card data (sample size, creation burden, spacing load)
6. Outputs everything as both `.json` and `.js` files for offline browser compatibility

## Design Process

1. **Story selection**: I chose this article because it makes a strong spatial argument ("imagine these five on a court together") that is directly testable with shot chart data.
2. **Angle development**: Rather than simply illustrating the original argument, I restructured it as a three-part test: space → roles → risks. This gives the remix an independent editorial voice.
3. **Viz sketching**: I started with the shot map (which I had as a prototype), then designed the role matrix as a deliberately different visual form (heatmap vs. scatter) to satisfy the "noticeably different designs" requirement. The risk bars are a third distinct form.
4. **View coordination**: I connected Viz 2 → Viz 1 clicks and Viz 3 → Viz 1 hovers so the three sections feel like one integrated story rather than three separate charts.
5. **Counterargument**: Section 3 explicitly challenges the original article's optimism using the same data, satisfying the remix requirement that the story not simply restate the source material.

## AI Usage

- **Model**: Claude (Anthropic)
- **How it was used**:
  - Debugging Python data pipeline issues (nba_api parameter names, column availability)
  - Code scaffolding for D3 court drawing and data binding patterns
  - Copy-editing and proofreading narrative text
  - Background research on NBA shot chart coordinate systems
- **What is my own work**:
  - Story angle and three-section narrative structure
  - Choice of visualizations and their design rationale
  - Data pipeline logic (zone classification, role proxy formulas, risk card generation)
  - View coordination architecture
  - All editorial decisions about what to include, emphasize, or challenge

## Running Locally

```bash
cd hw02
pip install nba_api pandas
python hw02_getScoreData.py
# Then open index.html in a browser (works offline via .js data files)
```

## Author

**Lianrui Geng** — COMP 617, Spring 2026
