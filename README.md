# 🎬 CineScope — Movie & TV Discovery App

> Discover movies and shows you'll love, powered by TMDB.

**Live Demo → [cinescope.streamlit.app](https://movie-recommender-j39lcqbuavwn7ndlblqytc.streamlit.app/)**

[![CI](https://github.com/krzysztofrasala/movie-recommender/actions/workflows/ci.yml/badge.svg)](https://github.com/krzysztofrasala/movie-recommender/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Ruff](https://img.shields.io/badge/lint-ruff-46aef7)](https://github.com/astral-sh/ruff)

---

## ✨ Features

### 🏠 Home & Discovery
- **Film of the Day** — a featured movie every day with a cinematic backdrop banner
- **Now Playing in Cinemas** — live data of what's currently in theatres
- **Trending Today** — popular movies right now, paginated (5 at a time)
- **Recommended For You** — personalized picks based on dense embeddings ($V_{user}$) & star ratings with `🎯 % Match` indicators
- **🍿 VOD Filtering** — filter by Polish streaming availability (**Netflix, Max, Disney+, Prime Video, Apple TV+, SkyShowtime**)

### 👥 Multi-User Profiles & Personalization
- **👥 Profile Switcher** — instant switching between profiles (**"Krzysztof"**, **"Partnerka"**, **"Rodzina"**, or custom user profiles) directly in the sidebar
- **🔒 Isolated Taste & Watchlists** — independent watchlists, star ratings, search history, and ML taste vectors per profile

### 🔍 Search & Discover Pro
- **My Library** — search 5,000+ movies with text filter, genre & year sliders, plus Cards Grid view
- **⚡ Discover Pro** — search specifically by **Actors**, **Directors**, **Original Language** (Polish, Korean, French, Spanish, Japanese, etc.), and minimum rating floors
- **💬 AI Movie Assistant** — chat with a virtual Gemini advisor via Tool Use / Function Calling to get personalized recommendations with interactive cards inside chat
- **🎲 Movie & TV Show Roulette** — instant random recommendation based on runtime (e.g. $\le 90$ mins), minimum rating, and mood
- **👥 Social Matchmaker ("What to Watch Together?")** — joint vector preference matching for two people

### 🎬 Movie & TV Details & Trailers
- Full modal with poster, tagline, runtime, budget, genres
- **Cast photos** — profile pictures with character names for up to 8 actors
- **▶️ YouTube Embedded Video Trailers** — play official YouTube trailers directly inside movie detail modals and roulette wins
- Direct link to JustWatch (streaming availability)

### 🌐 Internationalization & Settings
- **🌐 Language Switcher** — toggle between **Polish (PL 🇵🇱)** and **English (EN 🇬🇧)** for UI and TMDB content
- **⚙️ Settings & Backup** — export and restore multi-profile watchlist & ratings data as a JSON file

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.36+ |
| Recommendation Engine | SentenceTransformers / Dense Embeddings & Cosine Similarity |
| AI Assistant | Gemini API (Google GenAI SDK with Tool Calling) |
| Movie Data (live) | TMDB API (Multilingual `pl-PL` / `en-US`) |
| Containerization | Docker & Docker Compose |
| Language | Python 3.12 |

---

## 🧠 How the Recommendation Engine Works

```
TMDB Discover API (up to 4,000 popular movies)
        │
        ▼
Dense Embeddings (SentenceTransformers all-MiniLM-L6-v2)
        │
        ▼
Dynamic User Preference Vector V_user = Σ (Rating_i × V_i)
        │
        ▼
Cosine Similarity → Pair similarity & match percentage (%)
        │
        ▼
Top picks with match_score & match_reason tooltips
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/krzysztofrasala/movie-recommender.git
cd movie-recommender
```

### 2. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add API Keys
Create `.streamlit/secrets.toml`:
```toml
TMDB_API_KEY = "your_tmdb_api_key_here"
GEMINI_API_KEY = "your_gemini_api_key_here"
```

### 4. Run the app
```bash
streamlit run app.py
```

### 5. Run with Docker 🐳
```bash
docker-compose up --build
```

### 6. Run tests
```bash
pytest              # 78 unit tests covering profiles, i18n, state, assistant, roulette, tmdb, data
```

---

## 📂 Project Structure

```
movie-recommender/
├── app.py                      # Streamlit entry point (page config + layout wiring)
├── Dockerfile                  # Container build instructions
├── docker-compose.yml          # Containerized composition
├── cinescope/                  # Application package
│   ├── config.py               # Constants: moods, decades, genre ids
│   ├── data.py                 # Local dataset & similarity model loading/filtering
│   ├── i18n.py                 # Internationalization (PL/EN dictionary & helpers)
│   ├── nl_query.py             # Natural-language query parsing (zero API cost)
│   ├── recommender.py          # Content-based recommendation & group vector engine
│   ├── state.py                # Multi-profile session state, watchlist, JSON export/import
│   ├── taste.py                # Taste-DNA profiling & personas
│   ├── tmdb.py                 # TMDB API client (all HTTP in one place)
│   └── ui/
│       ├── cards.py            # Movie card / row / grid renderers
│       ├── dialogs.py          # Movie & TV detail modals with YouTube trailer
│       ├── home.py             # Home sections (film of the day, trending, ...)
│       ├── html.py             # Shared HTML snippet builders
│       ├── sidebar.py          # Profile switcher, language toggle, filters, stats, settings backup
│       ├── styles.py           # Global CSS
│       └── tabs/               # Feature tabs:
│           ├── assistant.py    # AI Chat interface with Gemini Tool Calling
│           ├── compare.py      # Compare & Social Matchmaker ("What to Watch Together")
│           ├── library.py      # My Library grid & sorting
│           ├── roulette.py     # Movie & TV Show Roulette (Mood Picker)
│           ├── search.py       # Search & Discover Pro (Actors, Directors, Language)
│           ├── taste_dna.py    # Taste DNA radar chart & metrics
│           └── top10.py        # Top 10 charts
├── tests/                      # pytest suite (78 tests including test_profiles.py)
└── fetch_dataset.py            # Rebuilds recommendation model vectors
```

---

## 📸 Screenshots

### Film of the Day
Every day a different movie takes over the top of the page with a cinematic backdrop banner.

![Film of the Day](docs/screenshots/01-film-of-the-day.png)

### Recommendations
Ten content-based picks in a 2×5 grid — genre chips, streaming-provider logos and star ratings on every card.

![Recommendations](docs/screenshots/02-recommendations.png)

### Movie Details
A full modal with tagline, cast photos, embedded trailer and a direct JustWatch link.

![Movie Details](docs/screenshots/03-movie-details.png)

### Taste DNA
Genre radar and era-preference chart built from your ratings — plus a matching "movie persona" for fun.

![Taste DNA](docs/screenshots/04-taste-dna.png)

---

## 📄 License

Released under the [MIT License](LICENSE) — feel free to fork, modify and build on top of this project.

---

*Data provided by [TMDB](https://www.themoviedb.org) · Streaming info via [JustWatch](https://www.justwatch.com)*
