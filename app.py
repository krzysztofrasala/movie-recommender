import streamlit as st
import pickle
import pandas as pd
import requests
import urllib.parse
import ast
import datetime
from concurrent.futures import ThreadPoolExecutor

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if 'trending_index' not in st.session_state:
    st.session_state.trending_index = 0
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = []
if 'rec_source' not in st.session_state:
    st.session_state.rec_source = None
if 'user_ratings' not in st.session_state:
    st.session_state.user_ratings = {}
if 'rated_movies_info' not in st.session_state:
    st.session_state.rated_movies_info = {}
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'selected_person_id' not in st.session_state:
    st.session_state.selected_person_id = None
if 'selected_person_name' not in st.session_state:
    st.session_state.selected_person_name = None

MOODS = {
    "😂 Comedy": 35, "😱 Horror": 27, "❤️ Romance": 10749,
    "🦸 Action": 28, "🔍 Thriller": 53, "🚀 Sci-Fi": 878,
    "🎭 Drama": 18,  "🎬 Animation": 16,
}
DECADES = {
    "2020s": (2020, 2029), "2010s": (2010, 2019),
    "2000s": (2000, 2009), "1990s": (1990, 1999), "1980s": (1980, 1989),
}

# ── HELPERS ────────────────────────────────────────────────────────────────────
def get_safe_poster(path):
    if path and isinstance(path, str):
        return "https://image.tmdb.org/t/p/w500" + path
    return "https://via.placeholder.com/500x750/1a1a1a/666666?text=No+Poster"

def parse_genres(genres_str):
    try:
        return [g['name'] for g in ast.literal_eval(genres_str)]
    except:
        return []

def format_runtime(minutes):
    if not minutes:
        return ""
    h, m = divmod(int(minutes), 60)
    return f"{h}h {m}m" if h else f"{m}m"

def rating_color(rating):
    if rating >= 7.5:
        return "#2ECC71"
    if rating >= 6.0:
        return "#F39C12"
    return "#E74C3C"

def poster_html(poster_url, rating, is_hot=False, year=None):
    hot_badge = '<div style="position:absolute;top:8px;left:8px;background:#E50914;color:#fff;padding:2px 8px;border-radius:12px;font-size:0.62rem;font-weight:800;letter-spacing:1px;">🔥 HOT</div>' if is_hot else ""
    year_tag = f'<div style="position:absolute;top:8px;right:8px;background:rgba(0,0,0,0.75);color:#ccc;padding:2px 7px;border-radius:10px;font-size:0.65rem;">{year}</div>' if year else ""
    rc = rating_color(rating)
    return f"""
    <div style="position:relative;border-radius:10px;overflow:hidden;margin-bottom:6px;box-shadow:0 4px 15px rgba(0,0,0,0.5);">
        <img src="{poster_url}" style="width:100%;display:block;">
        <div style="position:absolute;bottom:8px;right:8px;background:rgba(0,0,0,0.85);color:{rc};padding:3px 9px;border-radius:12px;font-size:0.75rem;font-weight:800;">⭐ {rating}</div>
        {hot_badge}{year_tag}
    </div>"""

def genre_chips_html(genres):
    if not genres:
        return ""
    palette = ["#1a3a5c","#1a4a2a","#4a1a3a","#3a2a0a","#0a3a4a"]
    chips = "".join(
        f'<span style="background:{palette[i%len(palette)]};color:#bbb;padding:2px 9px;border-radius:12px;font-size:0.65rem;margin-right:4px;white-space:nowrap;">{g}</span>'
        for i, g in enumerate(genres[:3])
    )
    return f'<div style="margin:4px 0 8px 0;overflow:hidden;">{chips}</div>'

def get_local_genres(title):
    match = movies[movies['title'] == title]
    if not match.empty:
        g = match.iloc[0].get('genres_list', [])
        return g[:3] if isinstance(g, list) else []
    return []

def add_to_watchlist(title, poster, rating):
    if not any(m['title'] == title for m in st.session_state.watchlist):
        st.session_state.watchlist.append({'title': title, 'poster': poster, 'rating': rating})
        return True
    return False

def remove_from_watchlist(title):
    st.session_state.watchlist = [m for m in st.session_state.watchlist if m['title'] != title]

def set_recommendations(recs, source_title):
    st.session_state.recommendations = recs
    st.session_state.rec_source = source_title
    history = [h for h in st.session_state.search_history if h != source_title]
    history.insert(0, source_title)
    st.session_state.search_history = history[:10]

# ── API FUNCTIONS ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=86400)
def fetch_movie_details(movie_id):
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US", timeout=5)
        r.raise_for_status()
        d = r.json()
        return {"poster": get_safe_poster(d.get('poster_path')), "rating": round(d.get('vote_average', 0), 1),
                "overview": d.get('overview', ''), "id": movie_id}
    except:
        return None

@st.cache_data(ttl=86400)
def fetch_movie_extended(movie_id):
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US&append_to_response=credits", timeout=5)
        r.raise_for_status()
        d = r.json()
        director = next((c['name'] for c in d.get('credits', {}).get('crew', []) if c['job'] == 'Director'), 'Unknown')
        cast_raw = d.get('credits', {}).get('cast', [])[:8]
        return {
            'director': director,
            'cast': [c['name'] for c in cast_raw[:6]],
            'cast_details': [{'name': c['name'], 'character': c.get('character', ''), 'photo': get_safe_poster(c.get('profile_path'))} for c in cast_raw],
            'genres': [g['name'] for g in d.get('genres', [])],
            'runtime': d.get('runtime') or 0,
            'budget': d.get('budget') or 0,
            'tagline': d.get('tagline', ''),
        }
    except:
        return None

@st.cache_data(ttl=86400)
def fetch_movie_trailer(movie_id):
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}&language=en-US", timeout=5)
        for v in r.json().get('results', []):
            if v['site'] == 'YouTube' and v['type'] == 'Trailer':
                return f"https://www.youtube.com/watch?v={v['key']}"
        return None
    except:
        return None

@st.cache_data(ttl=3600)
def get_trending_movies():
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/trending/movie/day?api_key={api_key}", timeout=5)
        return r.json().get('results', [])[:20]
    except:
        return []

@st.cache_data(ttl=3600)
def get_now_playing():
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/movie/now_playing?api_key={api_key}&language=en-US", timeout=5)
        return r.json().get('results', [])[:5]
    except:
        return []

@st.cache_data(ttl=86400)
def fetch_tmdb_recommendations(movie_id):
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations?api_key={api_key}&language=en-US", timeout=5)
        return [{'id': m['id'], 'title': m['title'], 'poster': get_safe_poster(m.get('poster_path')),
                 'rating': round(m.get('vote_average', 0), 1), 'overview': m.get('overview', '')}
                for m in r.json().get('results', [])[:10]]
    except:
        return []

@st.cache_data(ttl=3600)
def search_tmdb(query):
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={urllib.parse.quote(query)}&language=en-US", timeout=5)
        return [{'id': m['id'], 'title': m['title'], 'year': m.get('release_date', '')[:4],
                 'rating': round(m.get('vote_average', 0), 1), 'poster': get_safe_poster(m.get('poster_path')),
                 'overview': m.get('overview', '')} for m in r.json().get('results', [])[:10]]
    except:
        return []

@st.cache_data(ttl=3600)
def search_tv(query):
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/search/tv?api_key={api_key}&query={urllib.parse.quote(query)}&language=en-US", timeout=5)
        return [{'id': m['id'], 'title': m.get('name', ''), 'year': m.get('first_air_date', '')[:4],
                 'rating': round(m.get('vote_average', 0), 1), 'poster': get_safe_poster(m.get('poster_path')),
                 'overview': m.get('overview', '')} for m in r.json().get('results', [])[:10]]
    except:
        return []

@st.cache_data(ttl=86400)
def fetch_tv_extended(tv_id):
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/tv/{tv_id}?api_key={api_key}&language=en-US&append_to_response=credits", timeout=5)
        d = r.json()
        creator = ', '.join([c['name'] for c in d.get('created_by', [])]) or 'Unknown'
        cast_raw = d.get('credits', {}).get('cast', [])[:8]
        ep_rt = d.get('episode_run_time', [])
        return {
            'creator': creator,
            'cast': [c['name'] for c in cast_raw[:6]],
            'cast_details': [{'name': c['name'], 'character': c.get('character', ''), 'photo': get_safe_poster(c.get('profile_path'))} for c in cast_raw],
            'genres': [g['name'] for g in d.get('genres', [])],
            'seasons': d.get('number_of_seasons', 0),
            'episodes': d.get('number_of_episodes', 0),
            'runtime': ep_rt[0] if ep_rt else 0,
            'tagline': d.get('tagline', ''),
            'status': d.get('status', ''),
        }
    except:
        return None

@st.cache_data(ttl=86400)
def fetch_tv_trailer(tv_id):
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/tv/{tv_id}/videos?api_key={api_key}&language=en-US", timeout=5)
        for v in r.json().get('results', []):
            if v['site'] == 'YouTube' and v['type'] == 'Trailer':
                return f"https://www.youtube.com/watch?v={v['key']}"
        return None
    except:
        return None

@st.cache_data(ttl=86400)
def fetch_tv_recommendations(tv_id):
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/tv/{tv_id}/recommendations?api_key={api_key}&language=en-US", timeout=5)
        return [{'id': m['id'], 'title': m.get('name', ''), 'year': m.get('first_air_date', '')[:4],
                 'rating': round(m.get('vote_average', 0), 1), 'poster': get_safe_poster(m.get('poster_path')),
                 'overview': m.get('overview', '')} for m in r.json().get('results', [])[:10]]
    except:
        return []

@st.cache_data(ttl=86400)
def get_movie_of_the_day():
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=en-US&page=1", timeout=5)
        results = r.json().get('results', [])
        m = results[datetime.date.today().timetuple().tm_yday % len(results)]
        return {'id': m['id'], 'title': m['title'], 'poster': get_safe_poster(m.get('poster_path')),
                'backdrop': f"https://image.tmdb.org/t/p/w1280{m['backdrop_path']}" if m.get('backdrop_path') else None,
                'rating': round(m.get('vote_average', 0), 1), 'overview': m.get('overview', '')}
    except:
        return None

@st.cache_data(ttl=3600)
def get_top_movies(category='popular'):
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/movie/{category}?api_key={api_key}&language=en-US", timeout=5)
        return [{'id': m['id'], 'title': m['title'], 'poster': get_safe_poster(m.get('poster_path')),
                 'rating': round(m.get('vote_average', 0), 1), 'overview': m.get('overview', '')}
                for m in r.json().get('results', [])[:10]]
    except:
        return []

@st.cache_data(ttl=3600)
def search_person(query):
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/search/person?api_key={api_key}&query={urllib.parse.quote(query)}&language=en-US", timeout=5)
        return [{'id': p['id'], 'name': p['name'], 'role': p.get('known_for_department', 'Acting'),
                 'photo': get_safe_poster(p.get('profile_path')),
                 'known_for': [k.get('title', k.get('name', '')) for k in p.get('known_for', [])[:3]]}
                for p in r.json().get('results', [])[:5]]
    except:
        return []

@st.cache_data(ttl=86400)
def fetch_person_credits(person_id):
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/person/{person_id}/combined_credits?api_key={api_key}&language=en-US", timeout=5)
        cast = sorted(r.json().get('cast', []), key=lambda x: x.get('popularity', 0), reverse=True)[:10]
        return [{'id': m['id'], 'title': m.get('title', m.get('name', '')), 'media_type': m.get('media_type', 'movie'),
                 'year': (m.get('release_date', '') or m.get('first_air_date', ''))[:4],
                 'poster': get_safe_poster(m.get('poster_path')), 'rating': round(m.get('vote_average', 0), 1),
                 'overview': m.get('overview', '')} for m in cast]
    except:
        return []

@st.cache_data(ttl=3600)
def discover_by_mood(genre_id):
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&with_genres={genre_id}&sort_by=popularity.desc&language=en-US", timeout=5)
        return [{'id': m['id'], 'title': m['title'], 'poster': get_safe_poster(m.get('poster_path')),
                 'rating': round(m.get('vote_average', 0), 1), 'overview': m.get('overview', '')}
                for m in r.json().get('results', [])[:10]]
    except:
        return []

@st.cache_data(ttl=3600)
def discover_by_decade(start_year, end_year):
    api_key = st.secrets["TMDB_API_KEY"]
    try:
        r = requests.get(f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&primary_release_date.gte={start_year}-01-01&primary_release_date.lte={end_year}-12-31&sort_by=popularity.desc&language=en-US", timeout=5)
        return [{'id': m['id'], 'title': m['title'], 'poster': get_safe_poster(m.get('poster_path')),
                 'rating': round(m.get('vote_average', 0), 1), 'overview': m.get('overview', '')}
                for m in r.json().get('results', [])[:10]]
    except:
        return []

# ── DATA LOADING ───────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    raw = pd.read_csv('movies.csv')[['id', 'genres', 'release_date']]
    raw['year'] = pd.to_datetime(raw['release_date'], errors='coerce').dt.year.astype('Int64')
    raw['genres_list'] = raw['genres'].apply(parse_genres)
    raw = raw.rename(columns={'id': 'movie_id'})
    movies = movies.merge(raw[['movie_id', 'year', 'genres_list']], on='movie_id', how='left')
    return movies, similarity

try:
    movies, similarity = load_model()
except:
    st.error("Model files not found!")
    st.stop()

# ── RECOMMENDATION LOGIC ───────────────────────────────────────────────────────
def recommend(movie):
    idx = movies[movies['title'] == movie].index[0]
    top = sorted(list(enumerate(similarity[idx])), reverse=True, key=lambda x: x[1])[1:11]
    candidates = [(movies.iloc[i[0]].movie_id, movies.iloc[i[0]].title) for i in top]

    def fetch_one(args):
        m_id, m_title = args
        d = fetch_movie_details(m_id)
        if d:
            d['title'] = m_title
        return d

    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(fetch_one, candidates))
    return [r for r in results if r]

def more_like_this(movie_id, movie_title):
    local = movies[movies['title'].str.lower() == movie_title.lower()]
    return recommend(local.iloc[0]['title']) if not local.empty else fetch_tmdb_recommendations(movie_id)

def recommend_for_you():
    good = {mid: info for mid, info in st.session_state.rated_movies_info.items()
            if st.session_state.user_ratings.get(mid, 0) >= 3}
    if not good:
        return []
    seen, combined = set(good.keys()), []
    for movie_id, info in list(good.items())[:3]:
        local = movies[movies['title'].str.lower() == info['title'].lower()]
        if local.empty:
            continue
        for rec in recommend(local.iloc[0]['title']):
            if rec['id'] not in seen:
                seen.add(rec['id'])
                combined.append(rec)
    return combined[:10]

# ── DIALOGS ────────────────────────────────────────────────────────────────────
@st.dialog("🎬 Movie Details", width="large")
def show_movie_details(movie_id, title, poster, rating, overview):
    ext = fetch_movie_extended(movie_id)
    trailer = fetch_movie_trailer(movie_id)
    rc = rating_color(rating)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(poster_html(poster, rating, rating >= 8.0), unsafe_allow_html=True)
    with col2:
        st.subheader(title)
        if ext and ext['tagline']:
            st.caption(f"*{ext['tagline']}*")
        st.markdown(f'<span style="color:{rc};font-size:1.2rem;font-weight:800;">⭐ {rating}/10</span>', unsafe_allow_html=True)
        if ext:
            if ext['genres']:
                st.markdown(genre_chips_html(ext['genres']), unsafe_allow_html=True)
            cols_meta = st.columns(2)
            if ext['runtime']:
                cols_meta[0].write(f"⏱️ {format_runtime(ext['runtime'])}")
            if ext['director']:
                cols_meta[1].write(f"🎬 {ext['director']}")
            if ext['budget'] > 0:
                st.write(f"💰 Budget: ${ext['budget']:,}")
        st.markdown("---")
        st.write(overview)

    if ext and ext.get('cast_details'):
        st.markdown("**Cast**")
        cast_cols = st.columns(min(len(ext['cast_details']), 8))
        for i, actor in enumerate(ext['cast_details'][:8]):
            with cast_cols[i]:
                st.image(actor['photo'], use_container_width=True)
                st.caption(f"**{actor['name']}**")
                if actor['character']:
                    st.caption(f"*{actor['character']}*")

    if trailer:
        with st.expander("▶️ Watch Trailer"):
            st.video(trailer)

    st.link_button("Find where to watch 📺", f"https://www.justwatch.com/pl/search?q={urllib.parse.quote(title)}", use_container_width=True)

@st.dialog("📺 TV Show Details", width="large")
def show_tv_details(tv_id, title, poster, rating, overview):
    ext = fetch_tv_extended(tv_id)
    trailer = fetch_tv_trailer(tv_id)
    rc = rating_color(rating)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(poster_html(poster, rating, rating >= 8.0), unsafe_allow_html=True)
    with col2:
        st.subheader(title)
        if ext and ext['tagline']:
            st.caption(f"*{ext['tagline']}*")
        st.markdown(f'<span style="color:{rc};font-size:1.2rem;font-weight:800;">⭐ {rating}/10</span>', unsafe_allow_html=True)
        if ext:
            if ext['genres']:
                st.markdown(genre_chips_html(ext['genres']), unsafe_allow_html=True)
            if ext['seasons']:
                st.write(f"📺 {ext['seasons']} season{'s' if ext['seasons'] != 1 else ''} · {ext['episodes']} episodes")
            if ext['runtime']:
                st.write(f"⏱️ ~{format_runtime(ext['runtime'])} / episode")
            if ext['status']:
                status_color = "#2ECC71" if ext['status'] == "Returning Series" else "#888"
                st.markdown(f'<span style="color:{status_color};">● {ext["status"]}</span>', unsafe_allow_html=True)
            if ext['creator']:
                st.write(f"🎬 Created by: **{ext['creator']}**")
        st.markdown("---")
        st.write(overview)

    if ext and ext.get('cast_details'):
        st.markdown("**Cast**")
        cast_cols = st.columns(min(len(ext['cast_details']), 8))
        for i, actor in enumerate(ext['cast_details'][:8]):
            with cast_cols[i]:
                st.image(actor['photo'], use_container_width=True)
                st.caption(f"**{actor['name']}**")
                if actor['character']:
                    st.caption(f"*{actor['character']}*")

    if trailer:
        with st.expander("▶️ Watch Trailer"):
            st.video(trailer)

    st.link_button("Find where to watch 📺", f"https://www.justwatch.com/pl/search?q={urllib.parse.quote(title)}", use_container_width=True)

# ── RENDER HELPERS ─────────────────────────────────────────────────────────────
def render_rec_card(col, item):
    with col:
        genres = get_local_genres(item['title'])
        st.markdown(poster_html(item['poster'], item['rating'], item['rating'] >= 8.0), unsafe_allow_html=True)
        st.markdown(f"**{item['title']}**")
        if genres:
            st.markdown(genre_chips_html(genres), unsafe_allow_html=True)

        if st.button("ℹ️ Details", key=f"rd_{item['id']}", use_container_width=True):
            show_movie_details(item['id'], item['title'], item['poster'], item['rating'], item['overview'])
        st.link_button("Watch 📺", f"https://www.justwatch.com/pl/search?q={urllib.parse.quote(item['title'])}", use_container_width=True)

        in_wl = any(m['title'] == item['title'] for m in st.session_state.watchlist)
        if in_wl:
            st.button("❤️ In Watchlist", key=f"wl_{item['id']}", disabled=True, use_container_width=True)
        else:
            if st.button("🤍 Add to Watchlist", key=f"wl_{item['id']}", use_container_width=True):
                if add_to_watchlist(item['title'], item['poster'], item['rating']):
                    st.toast(f"❤️ **{item['title']}** added to watchlist!")
                st.rerun()

        saved = st.session_state.user_ratings.get(item['id'])
        new_r = st.feedback("stars", key=f"fb_{item['id']}")
        if new_r is not None and new_r != saved:
            st.session_state.user_ratings[item['id']] = new_r
            st.session_state.rated_movies_info[item['id']] = {'title': item['title'], 'poster': item['poster']}

def render_recommendations(recs):
    if not recs:
        return
    rows = [recs[:5], recs[5:10]] if len(recs) >= 6 else [recs]
    for row in rows:
        cols = st.columns(5)
        for i, item in enumerate(row):
            render_rec_card(cols[i], item)

def render_movie_row(movie_list, key_prefix):
    cols = st.columns(5)
    for idx, m in enumerate(movie_list):
        m_id = m.get('id')
        m_title = m.get('title', m.get('name', ''))
        m_poster = get_safe_poster(m.get('poster_path'))
        m_rating = round(m.get('vote_average', 0), 1)
        m_overview = m.get('overview', '')
        m_year = m.get('release_date', m.get('first_air_date', ''))[:4]
        with cols[idx]:
            st.markdown(poster_html(m_poster, m_rating, m_rating >= 8.0, m_year), unsafe_allow_html=True)
            st.markdown(f"**{m_title}**")
            if st.button("ℹ️ Details", key=f"{key_prefix}_d_{m_id}", use_container_width=True):
                show_movie_details(m_id, m_title, m_poster, m_rating, m_overview)
            if st.button("🎬 More like this", key=f"{key_prefix}_m_{m_id}", use_container_width=True):
                with st.spinner("Loading..."):
                    set_recommendations(more_like_this(m_id, m_title), m_title)
                st.rerun()
            st.link_button("Watch 📺", f"https://www.justwatch.com/pl/search?q={urllib.parse.quote(m_title)}", use_container_width=True)

# ── PAGE CONFIG & CSS ──────────────────────────────────────────────────────────
st.set_page_config(page_title="CineScope", layout="wide", page_icon="🎬")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

h1 {
    font-size: 2.8rem !important;
    font-weight: 800 !important;
    background: linear-gradient(90deg, #F5C518 0%, #FF6B35 60%, #E50914 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
}
h2, h3 {
    border-left: 4px solid #F5C518;
    padding-left: 12px;
    margin-top: 0.4rem !important;
    font-weight: 700 !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px !important;
    border: 1px solid #2a2a2a !important;
    background: linear-gradient(135deg, #1e1e1e, #161616) !important;
    color: #ddd !important;
    transition: all 0.18s ease !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
}
.stButton > button:hover {
    border-color: #F5C518 !important;
    color: #F5C518 !important;
    background: linear-gradient(135deg, #252518, #1a1a12) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(245,197,24,0.2) !important;
}
.stButton > button:active { transform: translateY(0px) !important; }

/* ── Link buttons (Watch 📺) ── */
.stLinkButton a {
    border-radius: 8px !important;
    border: none !important;
    background: linear-gradient(135deg, #E50914, #b0060f) !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    transition: all 0.18s ease !important;
    box-shadow: 0 2px 8px rgba(229,9,20,0.3) !important;
}
.stLinkButton a:hover {
    background: linear-gradient(135deg, #ff1a25, #E50914) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(229,9,20,0.45) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #222; }
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 22px !important;
    color: #777 !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}
.stTabs [aria-selected="true"] {
    background: #181818 !important;
    color: #F5C518 !important;
    border-bottom: 2px solid #F5C518 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0A0A0A !important;
    border-right: 1px solid #1e1e1e !important;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    border-left: 3px solid #F5C518 !important;
    padding-left: 8px;
    font-size: 0.9rem !important;
}

/* ── Inputs ── */
[data-testid="stTextInput"] input {
    border-radius: 8px !important;
    background: #181818 !important;
    border-color: #2a2a2a !important;
    color: #fff !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #F5C518 !important;
    box-shadow: 0 0 0 1px #F5C518 !important;
}

/* ── Metric ── */
[data-testid="stMetric"] {
    background: #181818;
    border-radius: 10px;
    padding: 12px;
    border: 1px solid #2a2a2a;
}
[data-testid="stMetricValue"] { color: #F5C518 !important; font-weight: 800 !important; }

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 8px !important; border-left: 4px solid #F5C518 !important; }

/* ── Divider ── */
hr { border-color: #1e1e1e !important; margin: 1.5rem 0 !important; }

/* ── Expander ── */
[data-testid="stExpander"] { border: 1px solid #222 !important; border-radius: 10px !important; background: #181818 !important; }

/* ── Radio ── */
[data-testid="stRadio"] label { font-size: 0.85rem !important; }

/* ── Toast ── */
[data-testid="stToast"] {
    background: #1a1a1a !important;
    border: 1px solid #F5C518 !important;
    border-radius: 10px !important;
    color: #fff !important;
}

/* ── Caption ── */
.stCaption { color: #888 !important; font-size: 0.78rem !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #111; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #F5C518; }
</style>
""", unsafe_allow_html=True)

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.title('🎬 CineScope')
st.caption("Discover movies & shows you'll love · Powered by TMDB")

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 Filters")
    all_genres = sorted(set(g for genres in movies['genres_list'].dropna() for g in genres))
    selected_genres = st.multiselect("Genre", all_genres)
    valid_years = movies['year'].dropna()
    min_year, max_year = int(valid_years.min()), int(valid_years.max())
    year_range = st.slider("Release Year", min_year, max_year, (min_year, max_year))

    total_wl = len(st.session_state.watchlist)
    total_rated = len(st.session_state.rated_movies_info)
    if total_wl > 0 or total_rated > 0:
        st.markdown("---")
        st.header("📊 Your Stats")
        c1, c2 = st.columns(2)
        c1.metric("Watchlist", total_wl)
        c2.metric("Rated", total_rated)
        if total_rated > 0:
            avg = sum(st.session_state.user_ratings.values()) / total_rated
            stars = round(avg + 1)
            st.caption(f"Your avg: {'★' * stars}{'☆' * (5-stars)}")

    if st.session_state.search_history:
        st.markdown("---")
        st.header("🕐 Recent Searches")
        for title in st.session_state.search_history:
            if st.button(f"↩ {title}", key=f"hist_{title}", use_container_width=True):
                local = movies[movies['title'] == title]
                if not local.empty:
                    with st.spinner("Loading..."):
                        set_recommendations(recommend(title), title)
                    st.rerun()

    st.markdown("---")
    st.header("❤️ My Watchlist")
    if not st.session_state.watchlist:
        st.markdown('<div style="color:#555;font-size:0.85rem;text-align:center;padding:20px 0;">No movies yet.<br>Add some from recommendations!</div>', unsafe_allow_html=True)
    else:
        for item in st.session_state.watchlist:
            wc1, wc2, wc3 = st.columns([1, 4, 1])
            with wc1:
                st.image(item['poster'], use_container_width=True)
            with wc2:
                st.markdown(f"<div style='font-size:0.8rem;font-weight:600;line-height:1.3;'>{item['title']}</div>", unsafe_allow_html=True)
                rc = rating_color(item['rating'])
                st.markdown(f"<div style='color:{rc};font-size:0.75rem;'>⭐ {item['rating']}/10</div>", unsafe_allow_html=True)
            with wc3:
                if st.button("✕", key=f"rm_{item['title']}"):
                    remove_from_watchlist(item['title'])
                    st.toast(f"Removed **{item['title']}** from watchlist.")
                    st.rerun()

    if st.session_state.rated_movies_info:
        st.markdown("---")
        st.header("⭐ Your Ratings")
        for mid, info in st.session_state.rated_movies_info.items():
            r = st.session_state.user_ratings.get(mid, 0)
            rc = rating_color(r * 2)
            st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;"><img src="{info["poster"]}" style="width:28px;height:42px;border-radius:4px;object-fit:cover;"><div><div style="font-size:0.72rem;font-weight:600;color:#ddd;">{info["title"]}</div><div style="color:{rc};font-size:0.68rem;">{"★"*(r+1)}{"☆"*(4-r)}</div></div></div>', unsafe_allow_html=True)

# ── FILTERS ────────────────────────────────────────────────────────────────────
filtered = movies.copy()
if selected_genres:
    filtered = filtered[filtered['genres_list'].apply(lambda g: isinstance(g, list) and any(x in g for x in selected_genres))]
filtered = filtered[filtered['year'].notna() & (filtered['year'] >= year_range[0]) & (filtered['year'] <= year_range[1])]

# ── FILM OF THE DAY ────────────────────────────────────────────────────────────
motd = get_movie_of_the_day()
if motd and motd['backdrop']:
    st.markdown(f"""
    <div style="
        background-image: linear-gradient(to right, rgba(5,5,5,0.97) 30%, rgba(5,5,5,0.55) 70%, rgba(5,5,5,0.1)),
                          url({motd['backdrop']});
        background-size: cover; background-position: center top;
        border-radius: 16px; padding: 50px 60px; margin-bottom: 6px; min-height: 230px;
        border: 1px solid #222;
    ">
        <div style="color:#F5C518;font-size:0.72rem;font-weight:700;letter-spacing:3px;margin-bottom:12px;opacity:0.9;">
            🎬 &nbsp; FILM OF THE DAY
        </div>
        <div style="color:#fff;font-size:2.2rem;font-weight:800;margin-bottom:6px;letter-spacing:-0.5px;text-shadow:0 2px 10px rgba(0,0,0,0.5);">
            {motd['title']}
        </div>
        <div style="color:#F5C518;font-size:0.95rem;margin-bottom:16px;font-weight:700;">⭐ {motd['rating']}/10</div>
        <div style="color:#bbb;font-size:0.88rem;max-width:500px;line-height:1.65;">
            {motd['overview'][:240]}{'...' if len(motd['overview']) > 240 else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)
    mc1, mc2, _ = st.columns([1, 1, 6])
    with mc1:
        if st.button("🎯 Find Similar", key="motd_rec", use_container_width=True):
            with st.spinner("Loading..."):
                set_recommendations(more_like_this(motd['id'], motd['title']), motd['title'])
            st.rerun()
    with mc2:
        if st.button("ℹ️ Details", key="motd_det", use_container_width=True):
            show_movie_details(motd['id'], motd['title'], motd['poster'], motd['rating'], motd['overview'])

st.markdown("---")

# ── NOW PLAYING ────────────────────────────────────────────────────────────────
now_playing = get_now_playing()
if now_playing:
    st.subheader("🎭 Now Playing in Cinemas")
    render_movie_row(now_playing, "np")
    st.markdown("---")

# ── TRENDING ───────────────────────────────────────────────────────────────────
all_trending = get_trending_movies()
st.subheader(f"🔥 Trending Today")
if all_trending:
    cp, _, cn = st.columns([1, 8, 1])
    with cp:
        if st.button("⬅️", use_container_width=True):
            if st.session_state.trending_index > 0:
                st.session_state.trending_index -= 5
    with cn:
        if st.button("➡️", use_container_width=True):
            if st.session_state.trending_index < 15:
                st.session_state.trending_index += 5
    render_movie_row(all_trending[st.session_state.trending_index:st.session_state.trending_index + 5], "tr")

st.markdown("---")

# ── FOR YOU ────────────────────────────────────────────────────────────────────
for_you = recommend_for_you()
if for_you:
    st.subheader("💡 Recommended For You")
    st.caption("Based on movies you rated 4–5 stars")
    render_recommendations(for_you)
    st.markdown("---")

# ── RECOMMENDATIONS ────────────────────────────────────────────────────────────
if st.session_state.recommendations:
    st.subheader(f"🎯 Similar to: *{st.session_state.rec_source}*")
    render_recommendations(st.session_state.recommendations)
    st.markdown("---")

# ── TABS ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📽️ My Library", "🔍 Search Movies, TV & People", "🏆 Top 10", "⚖️ Compare"])

# TAB 1 — MY LIBRARY
with tab1:
    if filtered.empty:
        st.markdown('<div style="text-align:center;padding:40px;color:#555;"><div style="font-size:3rem;">🎬</div><div style="font-size:1.1rem;margin-top:10px;">No movies match your filters.</div><div style="font-size:0.85rem;margin-top:6px;">Try adjusting the genre or year range.</div></div>', unsafe_allow_html=True)
    else:
        col_in, col_btn = st.columns([4, 1])
        with col_in:
            sq = st.text_input("Search", placeholder="Search your library...", label_visibility="collapsed")
        with col_btn:
            if st.button("🎲 Surprise Me!", use_container_width=True):
                rand = filtered.sample(1).iloc[0]['title']
                with st.spinner(f"Picking {rand}..."):
                    set_recommendations(recommend(rand), f"{rand} 🎲")
                st.rerun()

        st.markdown("**Pick a mood:**")
        mc = st.columns(len(MOODS))
        for i, (label, gid) in enumerate(MOODS.items()):
            with mc[i]:
                if st.button(label, use_container_width=True, key=f"mood_{gid}"):
                    with st.spinner("Loading..."):
                        set_recommendations(discover_by_mood(gid), label)
                    st.rerun()

        st.markdown("**Browse by decade:**")
        dc = st.columns(len(DECADES))
        for i, (label, (s, e)) in enumerate(DECADES.items()):
            with dc[i]:
                if st.button(label, use_container_width=True, key=f"dec_{label}"):
                    with st.spinner("Loading..."):
                        set_recommendations(discover_by_decade(s, e), f"Best of {label}")
                    st.rerun()

        st.markdown("---")
        res = filtered[filtered['title'].str.contains(sq, case=False, na=False)] if sq else filtered
        if res.empty:
            st.warning(f'No movies found for "{sq}".')
        else:
            sel = st.selectbox(f"Select a movie ({len(res)} results)", res['title'].values)
            if st.button("Get 10 Recommendations", use_container_width=True):
                with st.spinner("Finding recommendations..."):
                    set_recommendations(recommend(sel), sel)
                st.rerun()

# TAB 2 — SEARCH
with tab2:
    stype = st.radio("Search for:", ["🎬 Movies", "📺 TV Shows", "🎭 People (Actors & Directors)"], horizontal=True)
    is_tv = stype == "📺 TV Shows"
    is_people = stype == "🎭 People (Actors & Directors)"

    ph = {"🎬 Movies": "e.g. Dune, Oppenheimer...", "📺 TV Shows": "e.g. Breaking Bad, The Bear...", "🎭 People (Actors & Directors)": "e.g. Christopher Nolan, Meryl Streep..."}
    q2 = st.text_input("Search", placeholder=ph[stype], label_visibility="collapsed", key="tab2q")

    if q2:
        if is_people:
            with st.spinner("Searching..."):
                persons = search_person(q2)
            if not persons:
                st.markdown('<div style="text-align:center;padding:30px;color:#555;"><div style="font-size:2rem;">🔍</div><div>No people found.</div></div>', unsafe_allow_html=True)
            else:
                for p in persons:
                    pc1, pc2 = st.columns([1, 6])
                    with pc1:
                        st.image(p['photo'])
                    with pc2:
                        st.subheader(p['name'])
                        st.caption(f"Known for: **{p['role']}**")
                        if p['known_for']:
                            st.caption("🎬 " + " · ".join(p['known_for']))
                        if st.button(f"View filmography", key=f"pf_{p['id']}"):
                            st.session_state.selected_person_id = p['id']
                            st.session_state.selected_person_name = p['name']
                            st.rerun()
                    st.divider()

            if st.session_state.selected_person_id:
                with st.spinner("Loading filmography..."):
                    credits = fetch_person_credits(st.session_state.selected_person_id)
                st.subheader(f"🎬 {st.session_state.selected_person_name} — Filmography")
                if credits:
                    rows = [credits[:5], credits[5:]]
                    for row in rows:
                        if not row:
                            break
                        cols = st.columns(5)
                        for i, m in enumerate(row):
                            with cols[i]:
                                st.markdown(poster_html(m['poster'], m['rating'], m['rating'] >= 8.0, m['year']), unsafe_allow_html=True)
                                st.markdown(f"**{m['title']}**")
                                is_tv_credit = m['media_type'] == 'tv'
                                if st.button("ℹ️ Details", key=f"pd_{m['id']}", use_container_width=True):
                                    (show_tv_details if is_tv_credit else show_movie_details)(m['id'], m['title'], m['poster'], m['rating'], m['overview'])
                                if st.button("🎬 Similar", key=f"ps_{m['id']}", use_container_width=True):
                                    with st.spinner("Loading..."):
                                        recs = fetch_tv_recommendations(m['id']) if is_tv_credit else more_like_this(m['id'], m['title'])
                                        set_recommendations(recs, m['title'])
                                    st.rerun()
        else:
            with st.spinner("Searching..."):
                results2 = search_tv(q2) if is_tv else search_tmdb(q2)
            if not results2:
                st.markdown('<div style="text-align:center;padding:30px;color:#555;"><div style="font-size:2rem;">🎬</div><div>No results found.</div></div>', unsafe_allow_html=True)
            else:
                for rs in [0, 5]:
                    row = results2[rs:rs+5]
                    if not row:
                        break
                    cols = st.columns(5)
                    for i, m in enumerate(row):
                        with cols[i]:
                            st.markdown(poster_html(m['poster'], m['rating'], m['rating'] >= 8.0, m.get('year')), unsafe_allow_html=True)
                            st.markdown(f"**{m['title']}**")
                            if is_tv:
                                if st.button("ℹ️ Details", key=f"sr_d_{rs}_{m['id']}", use_container_width=True):
                                    show_tv_details(m['id'], m['title'], m['poster'], m['rating'], m['overview'])
                                if st.button("📺 Similar shows", key=f"sr_s_{rs}_{m['id']}", use_container_width=True):
                                    with st.spinner("Loading..."):
                                        set_recommendations(fetch_tv_recommendations(m['id']), m['title'])
                                    st.rerun()
                            else:
                                if st.button("ℹ️ Details", key=f"sr_d_{rs}_{m['id']}", use_container_width=True):
                                    show_movie_details(m['id'], m['title'], m['poster'], m['rating'], m['overview'])
                                if st.button("🎬 Similar movies", key=f"sr_s_{rs}_{m['id']}", use_container_width=True):
                                    with st.spinner("Loading..."):
                                        set_recommendations(more_like_this(m['id'], m['title']), m['title'])
                                    st.rerun()

# TAB 3 — TOP 10
with tab3:
    ttype = st.radio("", ["🔥 Most Popular", "⭐ Top Rated"], horizontal=True, key="top_type")
    top_movies = get_top_movies('popular' if '🔥' in ttype else 'top_rated')
    for rank, m in enumerate(top_movies, 1):
        cr, cp2, ci = st.columns([1, 2, 6])
        with cr:
            st.markdown(f"<div style='font-size:3.5rem;font-weight:900;color:#F5C518;text-align:center;padding-top:16px;line-height:1;text-shadow:0 0 20px rgba(245,197,24,0.4);'>{rank}</div>", unsafe_allow_html=True)
        with cp2:
            st.markdown(poster_html(m['poster'], m['rating'], m['rating'] >= 8.0), unsafe_allow_html=True)
        with ci:
            rc = rating_color(m['rating'])
            st.subheader(m['title'])
            st.markdown(f'<span style="color:{rc};font-size:1rem;font-weight:700;">⭐ {m["rating"]}/10</span>', unsafe_allow_html=True)
            st.write(m['overview'][:220] + ('...' if len(m['overview']) > 220 else ''))
            ca, cb = st.columns(2)
            with ca:
                if st.button("ℹ️ Details", key=f"td_{rank}_{m['id']}", use_container_width=True):
                    show_movie_details(m['id'], m['title'], m['poster'], m['rating'], m['overview'])
            with cb:
                if st.button("🎬 Similar", key=f"ts_{rank}_{m['id']}", use_container_width=True):
                    with st.spinner("Loading..."):
                        set_recommendations(more_like_this(m['id'], m['title']), m['title'])
                    st.rerun()
        st.divider()

# TAB 4 — COMPARE
with tab4:
    st.caption("Pick two movies to compare side by side.")
    col1, col2 = st.columns(2)
    with col1:
        movie1 = st.selectbox("First movie", movies['title'].values, key="cmp1")
    with col2:
        movie2 = st.selectbox("Second movie", movies['title'].values, key="cmp2", index=1)

    if st.button("⚖️ Compare", use_container_width=True):
        m1_id = int(movies[movies['title'] == movie1].iloc[0]['movie_id'])
        m2_id = int(movies[movies['title'] == movie2].iloc[0]['movie_id'])
        with st.spinner("Loading..."):
            det1, det2 = fetch_movie_details(m1_id), fetch_movie_details(m2_id)
            ext1, ext2 = fetch_movie_extended(m1_id), fetch_movie_extended(m2_id)
        if det1 and det2 and ext1 and ext2:
            idx1 = movies[movies['title'] == movie1].index[0]
            idx2 = movies[movies['title'] == movie2].index[0]
            sim = round(float(similarity[idx1][idx2]) * 100, 1)
            sim_color = rating_color(sim / 10)
            st.markdown(f'<div style="text-align:center;padding:20px;"><div style="font-size:0.8rem;color:#888;letter-spacing:2px;margin-bottom:4px;">CONTENT SIMILARITY</div><div style="font-size:3rem;font-weight:900;color:{sim_color};">{sim}%</div><div style="font-size:0.8rem;color:#666;">based on genre, cast, director & keywords</div></div>', unsafe_allow_html=True)
            st.markdown("---")
            c1, c2 = st.columns(2)
            for col, title, det, ext in [(c1, movie1, det1, ext1), (c2, movie2, det2, ext2)]:
                with col:
                    st.markdown(poster_html(det['poster'], det['rating'], det['rating'] >= 8.0), unsafe_allow_html=True)
                    st.subheader(title)
                    if ext['tagline']:
                        st.caption(f"*{ext['tagline']}*")
                    rc = rating_color(det['rating'])
                    st.markdown(f'<span style="color:{rc};font-weight:800;font-size:1.1rem;">⭐ {det["rating"]}/10</span>', unsafe_allow_html=True)
                    if ext['genres']:
                        st.markdown(genre_chips_html(ext['genres']), unsafe_allow_html=True)
                    if ext['runtime']:
                        st.write(f"⏱️ {format_runtime(ext['runtime'])}")
                    if ext['director']:
                        st.write(f"🎬 {ext['director']}")
                    if ext['budget'] > 0:
                        st.write(f"💰 ${ext['budget']:,}")
                    if ext.get('cast_details'):
                        st.markdown("**Cast:**")
                        for actor in ext['cast_details'][:4]:
                            st.caption(f"• {actor['name']}" + (f" *({actor['character']})*" if actor['character'] else ""))
            common_cast = set(ext1['cast']) & set(ext2['cast'])
            common_genres = set(ext1['genres']) & set(ext2['genres'])
            same_dir = ext1['director'] == ext2['director'] and ext1['director'] != 'Unknown'
            if common_cast or common_genres or same_dir:
                st.markdown("---")
                st.subheader("🔗 What they share")
                if same_dir:
                    st.success(f"Same director: **{ext1['director']}**")
                if common_genres:
                    st.info(f"Common genres: **{', '.join(common_genres)}**")
                if common_cast:
                    st.info(f"Same actors: **{', '.join(common_cast)}**")

# ── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;padding:30px 0 10px;color:#444;font-size:0.78rem;line-height:2;">
    <div style="font-size:1.1rem;font-weight:700;color:#F5C518;margin-bottom:6px;">🎬 CineScope</div>
    Discover movies & shows you'll love<br>
    Movie data & images provided by <a href="https://www.themoviedb.org" target="_blank" style="color:#F5C518;text-decoration:none;">TMDB</a>
    &nbsp;·&nbsp; Where to watch via <a href="https://www.justwatch.com" target="_blank" style="color:#F5C518;text-decoration:none;">JustWatch</a><br>
    <span style="color:#333;font-size:0.72rem;">© 2026 CineScope · Built with Streamlit</span>
</div>
""", unsafe_allow_html=True)
