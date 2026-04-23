import streamlit as st
import pickle
import pandas as pd
import requests
import urllib.parse

# --- 1. SESSION STATE FOR CAROUSEL ---
if 'trending_index' not in st.session_state:
    st.session_state.trending_index = 0

# --- 2. API FUNCTIONS ---
def get_safe_poster(path):
    """Returns a valid TMDB poster URL or a placeholder if path is missing."""
    if path and isinstance(path, str):
        return "https://image.tmdb.org/t/p/w500" + path
    return "https://via.placeholder.com/500x750?text=No+Poster+Available"

def fetch_movie_details(movie_id):
    api_key = st.secrets["TMDB_API_KEY"]
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return {
            "poster": get_safe_poster(data.get('poster_path')),
            "rating": round(data.get('vote_average', 0), 1),
            "overview": data.get('overview', 'No description available.'),
            "id": movie_id
        }
    except:
        return None

def fetch_movie_trailer(movie_id):
    api_key = st.secrets["TMDB_API_KEY"]
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}&language=en-US"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        for video in data.get('results', []):
            if video['site'] == 'YouTube' and video['type'] == 'Trailer':
                return f"https://www.youtube.com/watch?v={video['key']}"
        return None
    except:
        return None

def get_trending_movies():
    api_key = st.secrets["TMDB_API_KEY"]
    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={api_key}"
    try:
        response = requests.get(url, timeout=5)
        return response.json().get('results', [])[:20]
    except:
        return []

# --- 3. DATA LOADING ---
try:
    movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
except:
    st.error("Model files not found! Please ensure movie_dict.pkl and similarity.pkl are in the project folder.")
    st.stop()

# --- 4. RECOMMENDATION LOGIC ---
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    # Fetch top 10 results
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:11]
    
    recommended_data = []
    for i in movies_list:
        m_id = movies.iloc[i[0]].movie_id
        m_title = movies.iloc[i[0]].title
        details = fetch_movie_details(m_id)
        if details:
            details['title'] = m_title
            recommended_data.append(details)
    return recommended_data

# --- 5. UI CONFIGURATION ---
st.set_page_config(page_title="Movie Master Pro", layout="wide")
st.title('🎬 Movie Master Recommender')

# --- SECTION: Trending Today (With Pagination) ---
st.subheader("🔥 Trending Today")

all_trending = get_trending_movies()

if all_trending:
    col_prev, col_page, col_next = st.columns([1, 8, 1])
    
    with col_prev:
        if st.button("⬅️ Prev"):
            if st.session_state.trending_index > 0:
                st.session_state.trending_index -= 5
    
    with col_next:
        if st.button("Next ➡️"):
            if st.session_state.trending_index < 15:
                st.session_state.trending_index += 5
    
    start_idx = st.session_state.trending_index
    current_trending = all_trending[start_idx : start_idx + 5]
    
    t_cols = st.columns(5)
    for idx, movie in enumerate(current_trending):
        with t_cols[idx]:
            m_id = movie.get('id')
            m_title = movie.get('title')
            
            st.image(get_safe_poster(movie.get('poster_path')))
            st.write(f"**{m_title}**")
            st.write(f"⭐ {round(movie.get('vote_average', 0), 1)}/10")
            
            t_trailer = fetch_movie_trailer(m_id)
            if t_trailer:
                with st.expander("📺 Watch Trailer"):
                    st.video(t_trailer)
            
            with st.expander("📖 Plot"):
                st.write(movie.get('overview', 'No summary available.'))
            
            t_encoded = urllib.parse.quote(m_title)
            st.link_button("Watch 📺", f"https://www.justwatch.com/pl/search?q={t_encoded}", use_container_width=True)

st.markdown("---")

# --- SECTION: Search & Recommendations (10 movies in 2 rows) ---
st.subheader("🔍 Find Your Next Movie")
selected_movie = st.selectbox('Select a movie you enjoyed:', movies['title'].values)

if st.button('Get 10 Recommendations', use_container_width=True):
    recommendations = recommend(selected_movie)
    
    if len(recommendations) >= 10:
        # Row 1
        r_cols1 = st.columns(5)
        for i in range(5):
            item = recommendations[i]
            with r_cols1[i]:
                st.image(item['poster'])
                st.write(f"**{item['title']}**")
                st.write(f"⭐ {item['rating']}/10")
                r_trailer = fetch_movie_trailer(item['id'])
                if r_trailer:
                    with st.expander("📺 Watch Trailer"):
                        st.video(r_trailer)
                st.link_button("Watch 📺", f"https://www.justwatch.com/pl/search?q={urllib.parse.quote(item['title'])}", use_container_width=True)

        # Row 2
        r_cols2 = st.columns(5)
        for i in range(5, 10):
            item = recommendations[i]
            with r_cols2[i-5]:
                st.image(item['poster'])
                st.write(f"**{item['title']}**")
                st.write(f"⭐ {item['rating']}/10")
                r_trailer = fetch_movie_trailer(item['id'])
                if r_trailer:
                    with st.expander("📺 Watch Trailer"):
                        st.video(r_trailer)
                st.link_button("Watch 📺", f"https://www.justwatch.com/pl/search?q={urllib.parse.quote(item['title'])}", use_container_width=True)