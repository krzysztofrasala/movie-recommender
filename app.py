import streamlit as st
import pickle
import pandas as pd
import requests
import urllib.parse

# 1. Function to fetch movie details (Poster, Rating, Overview)
def fetch_movie_details(movie_id):
    api_key = st.secrets["TMDB_API_KEY"]
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        return {
            "poster": "https://image.tmdb.org/t/p/w500" + data.get('poster_path', ''),
            "rating": round(data.get('vote_average', 0), 1),
            "overview": data.get('overview', 'No description available.'),
            "id": movie_id
        }
    except Exception:
        return None

# 2. Function to fetch YouTube Trailer Link
def fetch_movie_trailer(movie_id):
    api_key = st.secrets["TMDB_API_KEY"]
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}&language=en-US"
    
    try:
        response = requests.get(url)
        data = response.json()
        # Look for a YouTube video of type 'Trailer'
        for video in data.get('results', []):
            if video['site'] == 'YouTube' and video['type'] == 'Trailer':
                return f"https://www.youtube.com/watch?v={video['key']}"
        return None
    except Exception:
        return None

# 3. Function to fetch trending movies
def get_trending_movies():
    api_key = st.secrets["TMDB_API_KEY"]
    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={api_key}"
    try:
        response = requests.get(url)
        return response.json().get('results', [])[:5]
    except Exception:
        return []

# --- Data Loading ---
try:
    movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
except FileNotFoundError:
    st.error("Model files not found. Please upload pkl files to GitHub.")
    st.stop()

# --- Recommendation Logic ---
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
    
    recommended_data = []
    for i in movies_list:
        m_id = movies.iloc[i[0]].movie_id
        m_title = movies.iloc[i[0]].title
        details = fetch_movie_details(m_id)
        if details:
            details['title'] = m_title
            recommended_data.append(details)
    return recommended_data

# --- UI Configuration ---
st.set_page_config(page_title="Movie Master Recommender", layout="wide")
st.title('🎬 Movie Master Recommender')

# Trending Section
st.subheader("🔥 Trending Today")
trending_movies = get_trending_movies()
if trending_movies:
    t_cols = st.columns(5)
    for idx, movie in enumerate(trending_movies):
        with t_cols[idx]:
            p_path = "https://image.tmdb.org/t/p/w500" + movie.get('poster_path', '')
            st.image(p_path)
            st.write(f"**{movie.get('title')}**")
            st.write(f"⭐ {movie.get('vote_average')}")

st.markdown("---")

# Search Section
st.subheader("🔍 Find Your Next Movie")
selected_movie = st.selectbox('Select a movie you enjoyed:', movies['title'].values)

if st.button('Get Recommendations'):
    recommendations = recommend(selected_movie)
    
    r_cols = st.columns(5)
    for i, item in enumerate(recommendations):
        with r_cols[i]:
            st.image(item['poster'])
            st.write(f"**{item['title']}**")
            st.write(f"⭐ {item['rating']}/10")
            
            # Trailer and Plot in Expanders
            trailer_url = fetch_movie_trailer(item['id'])
            if trailer_url:
                with st.expander("📺 Watch Trailer"):
                    st.video(trailer_url)
            
            with st.expander("📖 Read Plot"):
                st.write(item['overview'])
            
            # External Link
            encoded_title = urllib.parse.quote(item['title'])
            st.markdown(f"[Where to watch? 📺](https://www.justwatch.com/pl/search?q={encoded_title})")