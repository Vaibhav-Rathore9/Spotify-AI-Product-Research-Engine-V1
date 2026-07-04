"""
Spotify Review Discovery Engine — Streamlit Frontend

Milestone 2: Fetch and display live reviews from
Google Play Store and Spotify Community.
"""

import streamlit as st
import logging
from scrapers.playstore import scrape_playstore
from scrapers.spotify_community import scrape_spotify_community
from scrapers.reddit import scrape_reddit
from utils.cache import fetch_with_cache
from ai.tag_reviews import tag_reviews_batch
from ai.cluster_reviews import cluster_reviews
from ai.generate_dashboard import generate_dashboard_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Spotify Review Discovery Engine",
    page_icon="🎵",
    layout="wide",
)

# ── Custom Styling ───────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Header gradient */
    .main-header {
        background: linear-gradient(135deg, #1DB954 0%, #1ed760 50%, #191414 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .main-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        font-size: 1.05rem;
        opacity: 0.85;
        margin-top: 0.5rem;
    }

    /* Stats bar */
    .stats-bar {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }
    .stat-chip {
        background: rgba(29, 185, 84, 0.1);
        border: 1px solid rgba(29, 185, 84, 0.2);
        border-radius: 10px;
        padding: 0.75rem 1.25rem;
        text-align: center;
        flex: 1;
        min-width: 120px;
    }
    .stat-chip .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1DB954;
    }
    .stat-chip .stat-label {
        font-size: 0.8rem;
        opacity: 0.6;
        margin-top: 0.25rem;
    }

    /* Button override */
    .stButton > button {
        background: linear-gradient(135deg, #1DB954, #1ed760) !important;
        color: #000 !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.75rem 2.5rem !important;
        border-radius: 50px !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        letter-spacing: 0.3px;
    }
    .stButton > button:hover {
        transform: scale(1.03) !important;
        box-shadow: 0 6px 20px rgba(29, 185, 84, 0.4) !important;
    }

    /* Divider */
    .section-divider {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.06);
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🎵 Spotify Review Discovery Engine</h1>
    <p>Fetch and explore live user reviews from multiple sources</p>
</div>
""", unsafe_allow_html=True)

# ── Source Selection & Controls ──────────────────────────────
col_source, col_count = st.columns([1, 1])

with col_source:
    sources = st.multiselect(
        "Select review sources",
        options=["Google Play Store", "Spotify Community", "Reddit"],
        default=["Google Play Store"],
        help="Choose one or more sources to fetch reviews from.",
    )

with col_count:
    review_count = st.slider(
        "Number of reviews per source",
        min_value=10,
        max_value=200,
        value=50,
        step=10,
    )

# ── Caching & Refresh Controls ──────────────────────────────
col_cache, col_refresh = st.columns([1, 1])

with col_cache:
    use_cache = st.checkbox(
        "☑ Use Cached Data",
        value=False,
        help="When checked, will use cached data if available. Unchecked always attempts fresh scraping."
    )

with col_refresh:
    refresh_clicked = st.button(
        "🔄 Refresh Live Reviews",
        use_container_width=True,
        help="Ignore cache completely and fetch fresh data from all sources."
    )

fetch_clicked = st.button("🔍  Analyze Live Reviews", use_container_width=True)

# ── Scraper registry ─────────────────────────────────────────
SCRAPERS = {
    "Google Play Store": scrape_playstore,
    "Spotify Community": scrape_spotify_community,
    "Reddit": scrape_reddit,
}

# ── Fetch & Display ──────────────────────────────────────────
if fetch_clicked or refresh_clicked:
    if not sources:
        st.warning("Please select at least one review source.")
    else:
        all_reviews = []
        scraper_results = []
        
        # If refresh clicked, always ignore cache
        if refresh_clicked:
            use_cache = False
            logger.info("Refresh requested - ignoring cache")

        for source_name in sources:
            scraper_fn = SCRAPERS[source_name]
            with st.spinner(f"Fetching reviews from {source_name}..."):
                result = fetch_with_cache(source_name, scraper_fn, count=review_count, use_cache=use_cache)
                scraper_results.append(result)
                all_reviews.extend(result.reviews)
                
                # Print diagnostics to terminal
                if result.success:
                    logger.info(f"✓ {source_name}: {result.review_count} reviews")
                else:
                    logger.error(f"✗ {source_name}: {result.error}")

        # ── Display Scraping Diagnostics ──────────────────────
        if scraper_results:
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            st.subheader("📋 Scraping Diagnostics")
            
            diag_cols = st.columns(len(scraper_results))
            
            for idx, result in enumerate(scraper_results):
                with diag_cols[idx]:
                    if result.success and result.review_count > 0:
                        st.success(f"✓ {result.source}")
                        source_text = "Live Data" if not result.used_cache else "Loaded From Cache"
                        st.caption(f"{result.review_count} reviews — {source_text}")
                    elif result.success and result.review_count == 0:
                        st.warning(f"⚠ {result.source}")
                        st.caption("0 reviews returned")
                        if result.error:
                            st.caption(f"Reason: {result.error}")
                    else:
                        st.error(f"⚠ {result.source}")
                        st.caption("0 reviews")
                        if result.error:
                            st.caption(f"Reason: {result.error}")
                        if result.used_cache:
                            st.info("Loaded From Cache")
            
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        if all_reviews:
            # ── AI Tagging & Clustering ──────────────────────
            with st.spinner("Analyzing & tagging reviews with AI..."):
                try:
                    all_reviews = tag_reviews_batch(all_reviews)
                except Exception as e:
                    st.error(f"Failed to tag reviews: {e}")
            
            themes = []
            with st.spinner("Clustering themes..."):
                try:
                    themes = cluster_reviews(all_reviews)
                except Exception as e:
                    st.error(f"Failed to cluster reviews: {e}")

            # ── Stats ────────────────────────────────────────
            source_counts = {}
            for r in all_reviews:
                src = r.get("source", "Unknown")
                source_counts[src] = source_counts.get(src, 0) + 1

            ratings = []
            for r in all_reviews:
                if r["source"] == "Google Play Store":
                    try:
                        score = int(r["title"].split(":")[1].strip().split("/")[0])
                        ratings.append(score)
                    except (IndexError, ValueError):
                        pass

            avg_rating = sum(ratings) / len(ratings) if ratings else 0

            source_summary = " · ".join(
                f"{name}: {count}" for name, count in source_counts.items()
            )

            stats_html = f"""
            <div class="stats-bar">
                <div class="stat-chip">
                    <div class="stat-value">{len(all_reviews)}</div>
                    <div class="stat-label">Total Reviews</div>
                </div>
                <div class="stat-chip">
                    <div class="stat-value">{len(source_counts)}</div>
                    <div class="stat-label">Sources Active</div>
                </div>
            """
            if avg_rating > 0:
                stats_html += f"""
                <div class="stat-chip">
                    <div class="stat-value">{'⭐ ' + f'{avg_rating:.1f}'}</div>
                    <div class="stat-label">Avg Play Store Rating</div>
                </div>
                """
            stats_html += "</div>"

            st.markdown(stats_html, unsafe_allow_html=True)
            st.markdown(f"**Sources:** {source_summary}")
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

            dashboard_data = {}
            with st.spinner("Compiling product research dashboard..."):
                try:
                    dashboard_data = generate_dashboard_data(all_reviews)
                except Exception as e:
                    st.error(f"Failed to generate dashboard: {e}")

            themes = []
            with st.spinner("Generating product opportunities..."):
                try:
                    themes = cluster_reviews(all_reviews)
                except Exception as e:
                    st.error(f"Failed to generate product opportunities: {e}")

            tab_dashboard, tab_opps, tab_reviews = st.tabs([
                "📊 Product Research Dashboard", 
                "💡 Product Opportunities", 
                "💬 Raw Tagged Reviews"
            ])

            with tab_dashboard:
                st.subheader("Product Research Insights")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # 1. Discovery Barriers
                    st.markdown("### 1. Discovery Barriers")
                    for db in dashboard_data.get("discovery_barriers", []):
                        st.markdown(f"**{db.get('barrier', '')}** (Count: {db.get('count', 0)})")
                        for ex in db.get("examples", []):
                            st.markdown(f"- *{ex}*")
                    st.markdown("---")
                    
                    # 3. Listening Behaviors
                    st.markdown("### 3. Listening Behaviors")
                    for lb in dashboard_data.get("listening_behaviors", []):
                        st.markdown(f"- **{lb.get('behavior', '')}**: {lb.get('context', '')}")
                    st.markdown("---")

                    # 5. Representative Quotes
                    st.markdown("### 5. Representative Quotes")
                    for rq in dashboard_data.get("representative_quotes", []):
                        st.markdown(f"> *\"{rq.get('quote', '')}\"* — **{rq.get('source', '')}** ({rq.get('theme', '')})")

                with col2:
                    # 2. Recommendation Frustrations
                    st.markdown("### 2. Recommendation Frustrations")
                    for rf in dashboard_data.get("recommendation_frustrations", []):
                        st.markdown(f"**{rf.get('frustration', '')}** (Count: {rf.get('count', 0)})")
                        st.markdown(f"- {rf.get('details', '')}")
                    st.markdown("---")

                    # 4. User Segments
                    st.markdown("### 4. User Segments")
                    for us in dashboard_data.get("user_segments", []):
                        st.markdown(f"👤 **{us.get('segment', '')}**")
                        st.markdown(f"*{us.get('description', '')}*")
                    st.markdown("---")

                    # 6. Unmet Needs
                    st.markdown("### 6. Unmet Needs")
                    for un in dashboard_data.get("unmet_needs", []):
                        st.markdown(f"💡 **{un.get('need', '')}**")
                        st.markdown(f"*{un.get('explanation', '')}*")

            with tab_opps:
                st.subheader("💡 Product Opportunity Generation")
                if themes:
                    for t in themes:
                        with st.expander(f"**Theme: {t.get('theme', 'Unknown')}** (Mentions: {t.get('frequency', 0)})"):
                            st.write(f"**Summary:** {t.get('summary', '')}")
                            st.markdown(f"🔍 **Likely Root Cause:** *{t.get('root_cause', 'N/A')}*")
                            
                            st.markdown("**🚀 Potential Product Opportunities:**")
                            for opp in t.get('opportunities', []):
                                st.markdown(f"- {opp}")
                                
                            st.markdown(f"📈 **Expected User Impact:** {t.get('expected_impact', 'N/A')}")
                            st.markdown(f"📊 **Confidence Score:** `{t.get('confidence_score', 'N/A')}`")
                            
                            if t.get('supporting_quotes'):
                                st.markdown("**💬 Supporting Quotes:**")
                                for q in t.get('supporting_quotes', []):
                                    st.markdown(f"> *\"{q}\"*")
                else:
                    st.write("No product opportunities generated. Analyze reviews first.")

            with tab_reviews:
                st.subheader("Raw Tagged Reviews")
                # ── Review Cards ─────────────────────────────────
                for review in all_reviews:
                    # Truncate very long text for display
                    display_text = review["text"]
                    if len(display_text) > 500:
                        display_text = display_text[:500] + "..."

                    source_label = review.get("source", "Unknown")

                    with st.container(border=True):
                        col_author, col_badge = st.columns([3, 1])
                        with col_author:
                            st.markdown(f"**👤 {review['author']}**")
                        with col_badge:
                            if source_label == "Google Play Store":
                                st.markdown(f"`{review.get('title', '')}`")
                            else:
                                st.caption(source_label)

                        if source_label != "Google Play Store":
                            st.markdown(f"**{review.get('title', '')}**")

                        st.markdown(display_text)

                        tag_col1, tag_col2, tag_col3, tag_col4, tag_col5 = st.columns(5)
                        with tag_col1:
                            st.caption(f"⚠️ Pain: {review.get('pain_point', 'N/A')}")
                        with tag_col2:
                            st.caption(f"🎯 Goal: {review.get('user_goal', 'N/A')}")
                        with tag_col3:
                            st.caption(f"🎧 Behavior: {review.get('behavior', 'N/A')}")
                        with tag_col4:
                            st.caption(f"🎭 Emotion: {review.get('emotion', 'N/A')}")
                        with tag_col5:
                            st.caption(f"🛑 Barrier: {review.get('discovery_barrier', 'N/A')}")

                        st.caption(f"📅 {review['date']}  ·  {source_label}")
        else:
            st.warning("No reviews were returned. Try again.")
