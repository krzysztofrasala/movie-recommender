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
        
        details = {
            "poster": "https://image.tmdb.org/t/p/w500" + data.get('poster_path', ''),
            "rating": round(data.get('vote_average', 0), 1),
            "overview": data.get('overview', 'No description available.')
        }
        return details
    except Exception:
        return {
            "poster": "https://via.placeholder.com/500x750?text=Error",
            "rating": "N/A",
            "overview": "Could not load data."
        }

# 2. Function to fetch trending movies of the day
def get_trending_movies():
    api_key = st.secrets["TMDB_API_KEY"]
    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        return data.get('results', [])[:5] # Get top 5
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
        recommended_data.append({"title": m_title, "details": details})
        
    return recommended_data

# --- UI Configuration ---
st.set_page_config(page_title="Pro Movie Recommender", layout="wide")
st.title('🎬 Pro Movie Recommender')

# 3. Trending Section
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

# 4. Search & Recommendation Section
st.subheader("🔍 Find Your Next Movie")
selected_movie = st.selectbox('Select a movie you enjoyed:', movies['title'].values)

if st.button('Get Recommendations'):
    recommendations = recommend(selected_movie)
    
    r_cols = st.columns(5)
    for i, item in enumerate(recommendations):
        with r_cols[i]:
            st.image(item['details']['poster'])
            st.write(f"**{item['title']}**")
            st.write(f"⭐ {item['details']['rating']}/10")
            
            with st.expander("Read Plot"):
                st.write(item['details']['overview'])
            
            # Streaming link
            encoded_title = urllib.parse.quote(item['title'])
            url = f"https://www.justwatch.com/pl/search?q={encoded_title}"
            st.markdown(f"[Watch Here 📺]({url})")