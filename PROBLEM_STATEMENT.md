# Spotify Review Discovery Engine

## Objective

Build an AI-powered Product Research Engine that transforms user feedback into actionable product insights and product opportunities.

This project is intended for product research and customer insight discovery.

---

# MVP Scope (V1)

The application should allow a user to:

1. Select review sources.
2. Fetch live reviews.
3. Cache reviews locally.
4. Analyze every review individually using an LLM.
5. Aggregate all analyses.
6. Cluster similar insights into themes.
7. Display findings on a dashboard.

---

# Data Sources

The engine should support three sources.

## Source 1
Google Play Store Reviews

## Source 2
Spotify Community

## Source 3
Reddit

Every scraper must return data using the exact same schema.

```python
{
    "id": "",
    "source": "",
    "title": "",
    "text": "",
    "url": "",
    "date": "",
    "author": ""
}
```

No source-specific schema is allowed.

---

# Pipeline

Frontend

↓

Source Selection

↓

Scrapers

↓

Cache

↓

Merge Reviews

↓

AI Tagging

↓

Structured Dataset

↓

Theme Clustering

↓

Dashboard

---

# Scraper Requirements

Each source must expose a function.

```python
scrape_reddit()

scrape_playstore()

scrape_spotify_community()
```

Each function returns

```python
List[dict]
```

using the shared schema.

No analysis happens inside scrapers.

---

# Cache Layer

Every scraper should cache results.

reddit.json

playstore.json

community.json

Behavior

If scraping succeeds

↓

Overwrite cache.

If scraping fails

↓

Load cached data.

---

# AI Tagging

Every review is processed independently.

Prompt

Analyze this review.

Return ONLY JSON.

Output schema

{
    "pain_point":"",
    "user_goal":"",
    "behavior":"",
    "emotion":"",
    "discovery_barrier":""
}

No markdown.

No explanations.

One review at a time.

---

# Aggregation

After tagging

Convert reviews into structured rows.

Example

Review

↓

Pain Point

↓

Behavior

↓

Emotion

↓

Barrier

---

# Clustering

Cluster tagged reviews into themes.

Return

Theme

Frequency

Supporting Quotes

Summary

---

# Dashboard

Dashboard contains only six sections.

1 Discovery Barriers

2 Recommendation Frustrations

3 Listening Behaviors

4 User Segments

5 Representative Quotes

6 Unmet Needs

No additional analytics required.

---

# Tech Stack

Frontend

Streamlit

Backend

Python

Caching

JSON

LLM

OpenAI Compatible API

Deployment

Streamlit Cloud

---

# Folder Structure

spotify-review-engine/

app.py

requirements.txt

README.md

scrapers/
reddit.py
playstore.py
spotify_community.py

cache/

ai/
tag_reviews.py
cluster_reviews.py

utils/
cache.py
helpers.py

prompts/
tagging_prompt.txt
clustering_prompt.txt

data/

---

# Development Order

Milestone 1

Google Play scraper

Milestone 2

Spotify Community scraper

Milestone 3

Reddit scraper

Milestone 4

Caching

Milestone 5

AI tagging

Milestone 6

Theme clustering

Milestone 7

Dashboard

Milestone 8

Product Opportunity Generation

Do not implement future milestones until the current milestone works.

---

# Design Principles

Keep functions modular.

Avoid duplicate code.

Separate scraping, AI, caching and UI.

All scrapers must produce identical output schema.

Avoid business logic inside Streamlit.

The application should be easy to extend by adding future data sources.

---

## Milestone 8 – Product Opportunity Generation

### Objective

Transform discovered user themes into actionable product opportunities.

### Input

Clustered insights generated from the review analysis pipeline.

### Process

For each theme:

- Identify the likely root cause.
- Explain why users experience this problem.
- Generate 2–3 potential product opportunities.
- Estimate expected user impact.
- Assign a confidence score based on supporting evidence.

### Output

Each theme should contain:

- Theme Name
- Frequency
- Supporting Quotes
- Root Cause
- Product Opportunity
- Expected User Impact
- Confidence Score

### Example

Theme:
Discovery Fatigue

Frequency:
63 mentions

Root Cause:
Recommendation algorithm prioritizes familiar listening patterns over exploration.

Opportunity:
Introduce a "Discovery Radius" control allowing users to adjust how adventurous recommendations should be.

Expected Impact:
Increase satisfaction among long-term users seeking new music.

Confidence:
91%