# HW02: Data Story Remix - A New Geometry in Salt Lake

**Author**: Lianrui Geng  
**Original Story**: ["Why I’m Obsessed With the New-Look Utah Jazz"](https://www.theringer.com/2026/02/03/nba/jaren-jackson-jr-trade-utah-jazz-lauri-markkanen-2026-nba-draft) by Michael Pina (The Ringer)  
**Live Deployment**: [GitHub Pages Link Here] (Please update after pushing)

---

## 1. Overview and Remix Intent

For this assignment, I chose to remix a recent sports journalism piece from *The Ringer* that enthusiastically praised the Utah Jazz's newly constructed starting five (Walker Kessler, Keyonte George, Lauri Markkanen, Jaren Jackson Jr., and Ace Bailey). The original article relied heavily on basketball theory, eye-test narratives, and isolated stats to argue that this lineup is a perfect modern basketball puzzle.

**My Remix Strategy:**
Instead of just reiterating the original praise, I wanted to subject this "paper puzzle" to a rigorous data check. My remix transitions the piece from a purely enthusiastic op-ed into an analytical **Data Story**. I kept the core narrative regarding "spatial distribution" but challenged the optimism by visualizing the actual shot distributions, comparing the players' functional roles, and finally exposing the structural vulnerabilities (risks) of the roster using the latest 2025-26 season data.

The resulting standalone webpage features three distinct, D3.js-powered interactive visualizations that guide the reader from the theoretical "geometry" of the court to the practical overlap of roles, and finally to the underlying risks of the lineup.

---

## 2. Design Process and "Making Of"

### Step 1: Data Acquisition and Processing
I started by writing a Python script (`hw02_getScoreData.py`) utilizing the `nba_api` package to fetch real-time, granular data for the 2025-26 regular season. 
- I pulled every single shot attempt (`ShotChartDetail`) for the five players to understand their spatial tendencies.
- I pulled basic season stats (`LeagueDashPlayerStats`) to build proxy metrics for their roles (e.g., scoring load, playmaking).
- The python script processes this raw JSON data and outputs cleaned summaries (`jazz_story_summary.js` and `jazz_shots_data.js`) that are immediately readable by the frontend D3 script.

### Step 2: Storyboarding the Visual Narrative
I structured the webpage into three progressive sections:
1.  **Section 1 / Space (The Optimism):** Visualizing the court geometry. I chose a **Shot Map (Scatter Plot)** overlaying a basketball court. I wanted the user to physically see if the players are crowding each other or spreading the floor.
2.  **Section 2 / Roles (The Division of Labor):** Analyzing how the players' skills overlap. I designed a **Grouped Horizontal Bar Chart** comparing the five starters across six calculated metrics (Floor spacing, Rim pressure, Shot creation, etc.).
3.  **Section 3 / Risks (The Blind Spots):** Providing the counter-argument. I designed **Small Multiples of Horizontal Bar Charts (Risk Cards)** to immediately highlight massive imbalances in sample size, playmaking burden, and spacing dependency.

### Step 3: Visual Design & Color Palette
I aimed for a premium, cinematic "Dark Mode" aesthetic common in modern data journalism (like *The New York Times* or *The Pudding*). 
-   **Background**: Deep navy/slate (`#0a0f18`) with glassmorphism (backdrop-blur) effects for the cards.
-   **Color Coding**: Each of the five players was assigned a distinct, vibrant color (Green, Purple, Yellow, Blue, Orange) that remains strictly consistent across all three visualizations. This allows the reader's brain to quickly track a player without constantly referring to the legend.
-   **Imagery**: I generated thematic, people-free images of Utah/basketball arenas to visually anchor each section without tying the piece to specific photographs that might age poorly.

---

## 3. Visualization Details & Interactivity (D3.js)

All three visualizations were custom-built using **D3.js v7**.

### Viz 1: Interactive Court Shot Map (Scatter Plot)
- **Design**: A scaled SVG drawing of a half-court, plotting individual shots as coordinates. Makes are solid circles; misses are semi-transparent outlines.
- **Interactivity**: 
  - **Filters**: Users can filter by shot density (sampling), and toggle between "All shots", "Makes only", or "Misses only".
  - **Legend Toggles**: Clicking a player's chip in the legend toggles their shots on/off.
  - **Tooltips/Drill-down**: Hovering over a dot shows basic info. Clicking a dot isolates that shot and populates a detailed "Shot Slice" dashboard UI on the right side.

### Viz 2: Role Comparison Matrix (Grouped Horizontal Bars)
- **Design**: A normalized (0-100) horizontal bar chart comparing the 5 players across 6 distinct basketball roles. The background track ensures players with a score of "0" are still visually represented as lacking in that area.
- **Interactivity & View Coordination (Bells & Whistles)**: 
  - Hovering over a bar reveals the exact score and the methodology (proxy description) for that metric.
  - **View Coordination**: Clicking any bar triggers two actions: 
    1. It filters the top Shot Map (Viz 1) to only show the relevant player and the court zones associated with that specific metric (e.g., clicking Kessler's "Rim Protection" focuses the map on Kessler's shots "At Rim").
    2. It smoothly scrolls the user back up to the Shot Map to see the effect immediately.

### Viz 3: Structural Risk Cards (Small Multiples)
- **Design**: Three isolated horizontal bar charts acting as "warning cards." By removing the normalization used in Viz 2 and showing raw values, the stark disparity between the players (e.g., George having 800+ shots vs. JJJ having 49) becomes jarringly obvious.
- **Interactivity & View Coordination**:
  - Hovering over these bars applies a brightness filter and coordinates with the Shot Map above.
  - Clicking the bars also smoothly scrolls the page back up to the connected map view.

---

## 4. Bells & Whistles Attempted

1.  **View Coordination (2 pts)**: Heavily implemented. Both Viz 2 and Viz 3 act as interactive controllers for Viz 1. Clicking a specific role or risk metric automatically filters the Shot Map to the relevant player and zones, bridging the abstract role data with the physical court geometry. Smooth scrolling was added to ensure the user notices the linked interaction.
2.  **Multiple Views / Counter-Argument (3 pts)**: The original story is purely optimistic about the trade. My remix deliberately dedicates Section 3 to forming a **counter-argument**. I use the data to explicitly highlight "blind spots" (Spacing Fragility, Playmaking Bottleneck, Chemistry/Sample Size) that could cause the lineup to fail, directly refuting the idea that it's a flawless "paper puzzle."

---

## 5. AI Usage Disclosure
- **Tool**: Claude 3.5 Sonnet / Gemini 3.1 Pro (via Cursor IDE).
- **Usage**: AI was utilized to scaffold the initial D3.js boilerplate, assist with the complex SVG math for drawing the basketball court arcs, and debug JavaScript event listeners (specifically fixing a bug with the smooth scrolling logic). AI was also used to generate the thematic background images (via DALL-E/Midjourney APIs) and copy-edit the narrative prose for a more journalistic tone. The overall narrative structure, data pipeline design, visualization concepts, and view coordination logic are my original work.

---

## Running Locally

```bash
cd hw02
pip install nba_api pandas
python hw02_getScoreData.py
# Then open index.html in a browser (works offline via .js data files)
```
