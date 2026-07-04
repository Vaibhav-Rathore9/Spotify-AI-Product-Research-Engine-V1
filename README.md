# 🎵 Spotify Review Discovery Engine

An AI-powered product research tool that scrapes, analyzes, and visualizes user reviews from multiple sources including Google Play Store, Spotify Community, and Reddit.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 📋 Overview

The Spotify Review Discovery Engine helps product teams understand user sentiment by:

- **Scraping** live reviews from multiple sources
- **Tagging** reviews with AI-powered sentiment analysis
- **Clustering** related feedback into themes
- **Visualizing** insights through an interactive dashboard

## 🚀 Features

### Multi-Source Scraping
- **Google Play Store** - Mobile app reviews
- **Spotify Community** - Forum posts and discussions  
- **Reddit** - r/spotify subreddit posts

### Smart Caching
- Intelligent caching system with user control
- Never silently falls back to cache - always transparent
- Option to force fresh scraping or use cached data

### AI-Powered Analysis
- Automated review tagging (pain points, user goals, behaviors, emotions)
- Theme clustering and opportunity identification
- Product research dashboard generation

### Transparent Diagnostics
- Real-time scraping status display
- Detailed error logging and reporting
- Visual indicators for data source status

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Vaibhav-Rathore9/Spotify-AI-Product-Research-Engine-V1.git
   cd Spotify-AI-Product-Research-Engine-V1
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables (if needed):**
   ```bash
   # Create .env file for any API keys
   echo "OPENAI_API_KEY=your_key_here" > .env
   ```

## 🎯 Usage

### Running the Dashboard
```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Using the Interface

1. **Select Sources** - Choose which review sources to scrape
2. **Set Review Count** - Adjust how many reviews per source (10-200)
3. **Cache Control**:
   - ☑ **Use Cached Data** - Enable to use cached data when available
   - 🔄 **Refresh Live Reviews** - Force fresh scraping, ignoring cache
4. **Analyze** - Click "🔍 Analyze Live Reviews" to start

### Understanding Diagnostics

The dashboard displays scraping diagnostics:
- ✓ **Green checkmark** - Successful scraping
- ⚠ **Red warning** - Scraping failed, using cache or showing error
- **Status indicators** - Shows "Live Data" or "Loaded From Cache"

## 🏗️ Architecture

```
spotify-review-engine/
├── app.py                    # Streamlit frontend
├── scrapers/                 # Data collection layer
│   ├── playstore.py         # Google Play Store scraper
│   ├── reddit.py            # Reddit scraper
│   └── spotify_community.py # Spotify Community scraper
├── ai/                       # AI processing pipeline
│   ├── tag_reviews.py       # Review tagging
│   ├── cluster_reviews.py   # Theme clustering
│   └── generate_dashboard.py # Dashboard generation
├── utils/                    # Utility functions
│   ├── cache.py             # Caching system
│   ├── scraper_result.py    # ScraperResult dataclass
│   └── helpers.py           # Helper functions
├── cache/                    # Cached data storage
├── data/                     # Data storage
└── prompts/                  # AI prompts
```

## 🔧 Configuration

### Caching Behavior

The caching system follows these rules:

1. **Default behavior**: Always attempts fresh scraping
2. **Cache enabled**: Uses cache if scraping fails
3. **Refresh mode**: Ignores cache completely
4. **Transparency**: Always shows whether cache was used

### Logging

INFO-level logging throughout the pipeline shows:
- Which scraper executed
- Whether it succeeded
- Why it failed (if applicable)
- Whether cache was used
- Number of reviews returned

## 🛠️ Development

### Project Structure

- **Scrapers**: Modular scrapers with standardized `ScraperResult` output
- **Cache**: Intelligent caching with user control
- **AI Pipeline**: Unchanged - handles tagging and clustering
- **Frontend**: Streamlit dashboard with diagnostics

### Adding New Sources

1. Create a new scraper in `scrapers/`
2. Implement `scraper_fn(count) -> ScraperResult`
3. Register in `SCRAPERS` dict in `app.py`
4. Add to source selection options

## 📊 Example Output

### Scraping Diagnostics
```
Fetching Google Play Store...
✓ 52 reviews

Fetching Reddit...
✓ 24 reviews

Fetching Spotify Community...
✗ RSS returned HTTP 404

Loading Spotify Community cache...
✓ Loaded 18 cached reviews
```

### Dashboard Display
```
✓ Google Play
52 reviews
Live Data

✓ Reddit
24 reviews
Live Data

⚠ Spotify Community
0 reviews
Loaded From Cache

Reason:
RSS feed returned HTTP 404
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Streamlit for rapid prototyping
- Uses google-play-store for app reviews
- Leverages RSS feeds for community data
- AI analysis powered by OpenAI/GPT models

## 📞 Support

For support, email vr41414@gmail.com or open an issue on GitHub.

---

**Note**: This tool is for research purposes. Always respect the terms of service of data sources and implement appropriate rate limiting.