# Current Sprint

## Goal

Build the Google Play scraper (Milestone 1), Spotify Community scraper (Milestone 2), and Reddit scraper (Milestone 3).

## Deliverables

### Milestone 1: Google Play Scraper
- [x] Create project structure.
- [x] Implement scrape_playstore().
- [x] Fetch live Spotify reviews.
- [x] Return standardized schema.
- [x] Display reviews in Streamlit.

### Milestone 2: Spotify Community Scraper
- [x] Implement scrape_spotify_community() using RSS feeds.
- [x] Fetch live Spotify Community posts.
- [x] Standardize schema (including cleaning HTML).
- [x] Support multi-source selection in Streamlit.
- [x] Display Spotify Community posts alongside Play Store reviews.

### Milestone 3: Reddit Scraper
- [x] Implement scrape_reddit() using Reddit's RSS feed format.
- [x] Clean Reddit HTML tags and specific artifacts like "submitted by...".
- [x] Implement User-Agent rotation to mitigate Reddit's 429 Rate Limiting errors.
- [x] Provide a solid fallback local list of seed posts just in case of hard blocks.
- [x] Integrate "Reddit" as a source in the Streamlit frontend.

### Milestone 4: Cache Layer
- [x] Create cache utility (`utils/cache.py`).
- [x] Save scraper results to JSON files (e.g., `reddit.json`).
- [x] Implement fallback logic: load from cache if live scraping fails.
- [x] Integrate cache layer into the Streamlit app's fetch loop.

### Milestone 5: AI Tagging
- [x] Load prompt template from `prompts/tagging_prompt.txt`.
- [x] Configure LLM call (Gemini `gemini-1.5-flash`) returning structured JSON output.
- [x] Implement robust keyword-based regex/dictionary fallback tagger.
- [x] Integrate AI batch tagging into the Streamlit app with card badge layout.

### Future Milestones
### Milestone 6: Theme Clustering
- [x] Create clustering logic (`ai/cluster_reviews.py`) with Gemini LLM.
- [x] Add robust deterministic mock clustering engine as a fallback.
- [x] Group AI-tagged reviews into distinct themes with supporting quotes and summaries.
- [x] Display clusters visually inside Streamlit via neat expander components.

### Milestone 7: Dashboard
- [x] Create prompts and dashboard analysis script (`ai/generate_dashboard.py`).
- [x] Structure the Streamlit output view into exactly six designated sections.
- [x] Add tab navigation to separate structured insights from raw reviews cleanly.
- [x] Integrate mock analysis support for a fully functional offline layout.

### Milestone 8: Product Opportunity Generation
- [x] Integrate product opportunity prompts (`prompts/clustering_prompt.txt`).
- [x] Extract root causes, product opportunities, impacts, and confidence scores from review themes.
- [x] Build robust fallback mappings for offline opportunities analysis.
- [x] Create a dedicated "Product Opportunities" tab in Streamlit showing structured root-cause and opportunity breakdowns.

## Status: ✅ ALL MILESTONES (1 TO 8) FULLY COMPLETE