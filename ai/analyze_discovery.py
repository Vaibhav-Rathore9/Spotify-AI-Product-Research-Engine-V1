"""
Music Discovery Analysis Engine

Filters reviews for music-discovery relevance and extracts structured insights:
pain points, listening goals, behaviors, discovery barriers, recommendation
frustrations, emotions, user segments, and product hypotheses.

This is a deterministic, keyword-based engine — no LLM required.
"""

from collections import Counter
from typing import List, Dict, Any


# ═══════════════════════════════════════════════════════════════
# 1. RELEVANCE FILTER — keywords that indicate music discovery
# ═══════════════════════════════════════════════════════════════

DISCOVERY_KEYWORDS = [
    # ── Core Discovery ──
    "discover", "recommend", "suggestion", "algorithm", "new music",
    "explore", "finding", "find new", "find music",
    # ── Spotify Discovery Features ──
    "daily mix", "discover weekly", "release radar", "daylist",
    # ── Playlists & Radio ──
    "playlist", "radio", "enhanced", "blend",
    # ── Shuffle & Repeat ──
    "shuffle", "repeat", "same song", "same artist", "same playlist",
    "stuck", "loop", "echo chamber", "repetitive", "recycling",
    "over and over", "always plays", "keeps playing",
    # ── Mood & Context ──
    "mood", "workout", "study", "focus", "relax", "commute",
    "energy", "tempo", "genre", "vibe",
    # ── Taste & Preference ──
    "taste", "taste profile", "liked songs", "preference",
    "variety", "diverse", "diversity", "mainstream", "niche",
    # ── New & Novel ──
    "new artist", "new album", "new release", "hidden gem",
    "indie", "underground", "deep cut",
    # ── Negative Discovery Signals ──
    "not like", "don't listen", "not interested", "already heard",
    "same songs", "same artists", "similar artists",
    "skip", "ignore", "dislike", "blocked",
    # ── Smart Shuffle ──
    "smart shuffle", "enhance",
]


def is_discovery_relevant(review: Dict[str, Any]) -> bool:
    """Return True if the review is about music discovery / recommendations."""
    text = (review.get("title", "") + " " + review.get("text", "")).lower()
    return any(kw in text for kw in DISCOVERY_KEYWORDS)


def filter_relevant(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return only discovery-relevant reviews."""
    return [r for r in reviews if is_discovery_relevant(r)]


# ═══════════════════════════════════════════════════════════════
# 2. CATEGORIZATION RULES — pattern-match into structured buckets
# ═══════════════════════════════════════════════════════════════

def _classify_pain_points(text: str) -> List[str]:
    """Extract pain point labels from review text."""
    hits = []
    t = text.lower()
    if any(w in t for w in ["same songs", "same artist", "same playlist", "over and over",
                            "always plays", "keeps playing", "recycling", "repetitive",
                            "repeat the same"]):
        hits.append("Recommendations feel repetitive / same content")
    if any(w in t for w in ["mainstream", "popular", "generic", "only popular"]):
        hits.append("Recommendations too mainstream")
    if any(w in t for w in ["discover weekly", "release radar", "daylist"]):
        if any(w in t for w in ["disappointing", "bad", "wrong", "stale", "recycling",
                                "same", "worse"]):
            hits.append("Discover features (Weekly/Radar/Daylist) declining quality")
        else:
            hits.append("Discover features (Weekly/Radar/Daylist) discussed")
    if any(w in t for w in ["shuffle", "smart shuffle"]):
        if any(w in t for w in ["not random", "not actually", "weighted", "favors"]):
            hits.append("Shuffle algorithm is not truly random")
        elif any(w in t for w in ["annoying", "on by default", "turn it off"]):
            hits.append("Smart Shuffle is intrusive / hard to disable")
        else:
            hits.append("Shuffle behavior issues")
    if any(w in t for w in ["mood", "energy", "tempo", "vibe", "context"]):
        hits.append("Recommendations lack context/mood awareness")
    if any(w in t for w in ["niche", "indie", "underground", "deep cut", "hidden gem"]):
        hits.append("Algorithm ignores niche/underground music")
    if any(w in t for w in ["diversity", "diverse", "variety", "echo chamber"]):
        hits.append("Lack of variety / echo chamber")
    if any(w in t for w in ["taste profile", "doesn't understand", "doesn't know my taste"]):
        hits.append("Algorithm doesn't understand personal taste")
    if any(w in t for w in ["podcast", "podcasts"]) and any(
        w in t for w in ["recommend", "suggestion", "home", "push", "shoved"]
    ):
        hits.append("Podcast recommendations pollute music discovery")
    if any(w in t for w in ["radio"]) and any(
        w in t for w in ["same", "worse", "stale", "repeat"]
    ):
        hits.append("Artist/Song radio is repetitive")
    return hits


def _classify_listening_goal(text: str) -> List[str]:
    """Extract listening goals from review text."""
    t = text.lower()
    goals = []
    if any(w in t for w in ["workout", "gym", "exercise", "running"]):
        goals.append("Workout / Exercise")
    if any(w in t for w in ["study", "focus", "concentrate"]):
        goals.append("Study / Focus")
    if any(w in t for w in ["relax", "chill", "sleep", "calm"]):
        goals.append("Relaxation")
    if any(w in t for w in ["commute", "driving", "car"]):
        goals.append("Commute")
    if any(w in t for w in ["party", "social", "friends"]):
        goals.append("Social / Party")
    if any(w in t for w in ["discover", "new music", "explore", "find new"]):
        goals.append("Music exploration")
    if any(w in t for w in ["background", "passive"]):
        goals.append("Background listening")
    return goals


def _classify_behavior(text: str) -> List[str]:
    """Extract current listening behaviors from review text."""
    t = text.lower()
    behaviors = []
    if any(w in t for w in ["same playlist", "liked songs only", "replays same",
                            "listen to same"]):
        behaviors.append("Replays same playlists")
    if any(w in t for w in ["search manually", "searches", "manual search"]):
        behaviors.append("Searches manually")
    if any(w in t for w in ["skip", "skipping", "skips"]):
        behaviors.append("Skips recommendations frequently")
    if any(w in t for w in ["ignore", "ignoring"]):
        behaviors.append("Ignores recommendation features")
    if any(w in t for w in ["personal playlist", "creates playlist", "curate"]):
        behaviors.append("Creates personal playlists")
    if any(w in t for w in ["unfollow", "block", "dislike"]):
        behaviors.append("Actively blocks/dislikes unwanted content")
    return behaviors


def _classify_barrier(text: str) -> List[str]:
    """Extract behavioral discovery barriers."""
    t = text.lower()
    barriers = []
    if any(w in t for w in ["echo chamber", "filter bubble", "stuck in"]):
        barriers.append("Algorithm echo chamber / filter bubble")
    if any(w in t for w in ["trust", "doesn't understand", "doesn't know"]):
        barriers.append("Doesn't trust the algorithm")
    if any(w in t for w in ["effort", "time", "too much work", "pain"]):
        barriers.append("Discovery requires too much effort")
    if any(w in t for w in ["habit", "comfort", "familiar", "always the same"]):
        barriers.append("Existing habits are easier")
    if any(w in t for w in ["too many", "overwhelm", "clutter", "noise"]):
        barriers.append("Too much choice / noise")
    if any(w in t for w in ["wrong", "irrelevant", "doesn't match", "not interested",
                            "not like"]):
        barriers.append("Recommendations are irrelevant")
    if any(w in t for w in ["afraid", "don't want", "ruin"]):
        barriers.append("Fear of ruining current mood")
    return barriers


def _classify_frustration(text: str) -> List[str]:
    """Extract recommendation frustrations."""
    t = text.lower()
    frust = []
    if any(w in t for w in ["same artist", "same songs", "same music", "recycling",
                            "repetitive"]):
        frust.append("Same artists/songs repeatedly")
    if any(w in t for w in ["mainstream", "popular", "generic", "top 50"]):
        frust.append("Too mainstream / not diverse enough")
    if any(w in t for w in ["doesn't adapt", "stale", "stuck", "worse over time"]):
        frust.append("Algorithm doesn't adapt / evolves poorly")
    if any(w in t for w in ["podcast", "podcasts"]):
        frust.append("Pushes podcast content")
    if any(w in t for w in ["smart shuffle", "enhance", "interruption"]):
        frust.append("Smart Shuffle interrupts intentional listening")
    if any(w in t for w in ["no explanation", "why", "black box"]):
        frust.append("No transparency in why songs are recommended")
    if any(w in t for w in ["mood", "context", "activity", "time of day"]):
        frust.append("Doesn't understand mood/activity context")
    return frust


def _classify_emotion(text: str) -> str:
    """Return the dominant emotion label."""
    t = text.lower()
    if any(w in t for w in ["frustrat", "annoy", "hate", "terrible", "awful",
                            "worst", "angry", "infuriat"]):
        return "Frustrated"
    if any(w in t for w in ["love", "great", "amazing", "perfect", "best", "good"]):
        return "Satisfied"
    if any(w in t for w in ["disappoint", "letdown", "miss", "used to"]):
        return "Disappointed"
    if any(w in t for w in ["wish", "hope", "want", "need"]):
        return "Curious"
    if any(w in t for w in ["overwhelm", "confus", "too much"]):
        return "Overwhelmed"
    if any(w in t for w in ["comfort", "familiar", "cozy"]):
        return "Comfort"
    return "Frustrated"   # default for discovery complaints


def _classify_segment(text: str) -> str:
    """Assign a user segment label."""
    t = text.lower()
    if any(w in t for w in ["workout", "gym", "exercise", "running"]):
        return "Gym User"
    if any(w in t for w in ["study", "focus", "college", "university"]):
        return "Student"
    if any(w in t for w in ["commute", "driving", "car"]):
        return "Daily Commuter"
    if any(w in t for w in ["curate", "curated", "playlist", "organized"]):
        return "Playlist Curator"
    if any(w in t for w in ["audiophile", "quality", "lossless", "hi-fi", "hifi"]):
        return "Music Enthusiast"
    if any(w in t for w in ["discover", "explore", "new artist", "new music",
                            "indie", "niche"]):
        return "Music Enthusiast"
    if any(w in t for w in ["background", "passive", "ambient"]):
        return "Passive Listener"
    return "Casual Listener"


# ═══════════════════════════════════════════════════════════════
# 3. PRODUCT HYPOTHESIS GENERATOR
# ═══════════════════════════════════════════════════════════════

HYPOTHESIS_TEMPLATES = [
    {
        "id": 1,
        "title": "Context-Aware Discovery Engine",
        "claim": (
            "A recommendation system that incorporates current context (time of day, "
            "activity detected from usage patterns, user-stated mood) will reduce skip "
            "rates by 20%+ and increase discovery engagement."
        ),
        "mvp": (
            "Let users set a 'listening context' (mood, activity, energy level) via a "
            "simple UI, then re-rank recommendations using this signal alongside "
            "existing collaborative filtering."
        ),
        "signal_keywords": ["mood", "energy", "tempo", "vibe", "context", "workout",
                            "study", "focus", "relax", "commute"],
    },
    {
        "id": 2,
        "title": "Discovery Transparency & Control Dashboard",
        "claim": (
            "Giving users visibility into why songs are recommended and simple controls "
            "to steer the algorithm will increase trust and reduce 'give up and skip' "
            "behavior."
        ),
        "mvp": (
            "'Why this song?' tooltip on every recommendation + a 'Discovery Preferences' "
            "panel where users can set exploration breadth, genre preferences, and "
            "exclude lists."
        ),
        "signal_keywords": ["algorithm", "doesn't understand", "taste profile",
                            "block", "dislike", "exclude"],
    },
    {
        "id": 3,
        "title": "Echo Chamber Breaker — Serendipity Injection",
        "claim": (
            "Intentionally injecting 15-20% 'serendipity' tracks (from adjacent genres, "
            "emerging artists, or neglected library segments) into algorithmic playlists "
            "will increase perceived variety without decreasing overall satisfaction."
        ),
        "mvp": (
            "'Adventure Mode' toggle on any playlist that increases novelty from 0% to "
            "20%, with a 'How was this?' feedback loop to learn in real-time."
        ),
        "signal_keywords": ["echo chamber", "repetitive", "same", "mainstream", "niche",
                            "indie", "underground", "diversity", "variety", "deep cut"],
    },
    {
        "id": 4,
        "title": "Podcast-Free Discovery Path",
        "claim": (
            "Separating podcast recommendations from music discovery (or giving users a "
            "clean toggle) will measurably improve music discovery satisfaction."
        ),
        "mvp": (
            "A 'Music Only' toggle in discovery settings that suppresses all "
            "podcast/audio-book content from recommendations, search results, and "
            "home page."
        ),
        "signal_keywords": ["podcast"],
    },
    {
        "id": 5,
        "title": "Personalized Music Genome Explorer",
        "claim": (
            "Exposing a visual 'music DNA' profile to users (showing listening patterns "
            "across energy, novelty, genre diversity, artist diversity) will create a "
            "feedback loop where users self-curate, leading to better algorithmic "
            "signals and more satisfying discovery."
        ),
        "mvp": (
            "'My Music DNA' page showing radar chart of listening patterns with sliders "
            "that directly adjust recommendation parameters."
        ),
        "signal_keywords": ["taste", "taste profile", "preference", "discover",
                            "explore", "new artist", "niche"],
    },
]


# ═══════════════════════════════════════════════════════════════
# 4. MAIN ANALYSIS FUNCTION
# ═══════════════════════════════════════════════════════════════

def analyze_discovery(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run the full music-discovery analysis on a list of reviews.

    Returns a dict with:
      - total_reviews
      - relevant_reviews
      - filtered_count
      - source_breakdown  (source → count)
      - pain_points       (label → count, sorted)
      - listening_goals   (label → count, sorted)
      - behaviors         (label → count, sorted)
      - barriers          (label → count, sorted)
      - frustrations      (label → count, sorted)
      - emotions          (label → count, sorted)
      - segments          (label → count, sorted)
      - behavioral_barriers (label → count, sorted)
      - representative_quotes (list of dicts)
      - product_hypotheses (list of dicts with evidence + confidence)
      - per_review_tags   (list of per-review structured tags)
    """
    relevant = filter_relevant(reviews)

    # ── Counters ─────────────────────────────────────────────
    pain_counts: Counter = Counter()
    goal_counts: Counter = Counter()
    beh_counts: Counter = Counter()
    barrier_counts: Counter = Counter()
    frust_counts: Counter = Counter()
    emotion_counts: Counter = Counter()
    segment_counts: Counter = Counter()
    source_counts: Counter = Counter()

    quotes: List[Dict[str, str]] = []
    per_review_tags: List[Dict[str, Any]] = []

    for r in relevant:
        raw = (r.get("title", "") + " " + r.get("text", "")).lower()
        source = r.get("source", "Unknown")
        source_counts[source] += 1

        pp = _classify_pain_points(raw)
        lg = _classify_listening_goal(raw)
        bh = _classify_behavior(raw)
        ba = _classify_barrier(raw)
        fr = _classify_frustration(raw)
        em = _classify_emotion(raw)
        sg = _classify_segment(raw)

        for p in pp:
            pain_counts[p] += 1
        for g in lg:
            goal_counts[g] += 1
        for b in bh:
            beh_counts[b] += 1
        for b in ba:
            barrier_counts[b] += 1
        for f in fr:
            frust_counts[f] += 1
        emotion_counts[em] += 1
        segment_counts[sg] += 1

        # Representative quote
        title = r.get("title", "")
        text_raw = r.get("text", "")
        quote = title if len(title) < 100 else text_raw[:100]
        quotes.append({"quote": quote, "source": source, "full_text": text_raw[:200]})

        per_review_tags.append({
            "title": title,
            "source": source,
            "author": r.get("author", ""),
            "pain_points": pp,
            "listening_goals": lg,
            "behaviors": bh,
            "barriers": ba,
            "frustrations": fr,
            "emotion": em,
            "segment": sg,
        })

    # ── Rank quotes by diagnostic strength ───────────────────
    diag_kw = ["discover", "recommend", "algorithm", "shuffle", "same",
               "mainstream", "echo", "repetitive", "stuck", "variety",
               "diverse", "niche", "radio", "daily mix"]
    scored = []
    for q in quotes:
        score = sum(1 for kw in diag_kw if kw in (q["quote"] + q["full_text"]).lower())
        scored.append((score, q))
    scored.sort(key=lambda x: -x[0])
    top_quotes = []
    seen = set()
    for _, q in scored:
        short = q["quote"][:120]
        if short not in seen:
            seen.add(short)
            top_quotes.append({"quote": short, "source": q["source"]})
        if len(top_quotes) >= 15:
            break

    # ── Product Hypotheses — score by relevance to this dataset ──
    hypotheses = []
    for h in HYPOTHESIS_TEMPLATES:
        mentions = 0
        support_quotes = []
        for r in relevant:
            raw = (r.get("title", "") + " " + r.get("text", "")).lower()
            if any(kw in raw for kw in h["signal_keywords"]):
                mentions += 1
                if len(support_quotes) < 3:
                    support_quotes.append(r.get("title", "")[:100])
        confidence = "Low"
        if mentions >= 15:
            confidence = "High"
        elif mentions >= 8:
            confidence = "Medium-High"
        elif mentions >= 4:
            confidence = "Medium"
        hypotheses.append({
            "id": h["id"],
            "title": h["title"],
            "claim": h["claim"],
            "mvp": h["mvp"],
            "evidence_mentions": mentions,
            "evidence_pct": round(100 * mentions / max(len(relevant), 1), 1),
            "supporting_quotes": support_quotes,
            "confidence": confidence,
        })
    hypotheses.sort(key=lambda x: -x["evidence_mentions"])

    return {
        "total_reviews": len(reviews),
        "relevant_reviews": len(relevant),
        "filtered_count": len(reviews) - len(relevant),
        "source_breakdown": dict(source_counts),
        "pain_points": dict(pain_counts.most_common(15)),
        "listening_goals": dict(goal_counts.most_common(10)),
        "behaviors": dict(beh_counts.most_common(10)),
        "barriers": dict(barrier_counts.most_common(10)),
        "frustrations": dict(frust_counts.most_common(10)),
        "emotions": dict(emotion_counts.most_common()),
        "segments": dict(segment_counts.most_common(10)),
        "representative_quotes": top_quotes,
        "product_hypotheses": hypotheses,
        "per_review_tags": per_review_tags,
    }
