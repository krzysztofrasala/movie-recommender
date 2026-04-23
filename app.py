import streamlit as st
import pickle
import pandas as pd
import requests
import urllib.parse

# Function to fetch movie poster from TMDB API
def fetch_poster(movie_id):
    api_key = st.secrets["TMDB_API_KEY"]
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        
        if poster_path:
            # Correcting URL concatenation (no double slash)
            return "https://image.tmdb.org/t/p/w500" + poster_path
        return "https://via.placeholder.com/500x750?text=No+Poster+Found"
    except Exception:
        return "https://via.placeholder.com/500x750?text=Error+Loading+Image"

# Data Loading with Error Handling
try:
    movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
except FileNotFoundError:
    st.error("Model files not found. Please upload movie_dict.pkl and similarity.pkl to GitHub.")
    st.stop() # Prevents NameError if files are missing

# Core recommendation logic
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    # Get top 5 recommendations excluding the searched movie
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
    
    recommended_movies = []
    recommended_posters = []

    for i in movies_list:
        current_movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_posters.append(fetch_poster(current_movie_id))
        
    return recommended_movies, recommended_posters

# Streamlit UI Configuration
st.set_page_config(page_title="Movie Recommender", layout="wide")
st.title('Movie Recommender System 🎬')

selected_movie = st.selectbox(
    'Search for a movie to get recommendations:',
    movies['title'].values
)

if st.button('Recommend'):
    names, posters = recommend(selected_movie)
    
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            st.image(posters[i])
            st.write(f"**{names[i]}**")
            
            # JustWatch deep link
            encoded_title = urllib.parse.quote(names[i])
            justwatch_url = f"https://www.justwatch.com/pl/search?q={encoded_title}"
            st.markdown(f"[Where to watch? 📺]({justwatch_url})")