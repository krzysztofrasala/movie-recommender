import streamlit as st
import pickle
import pandas as pd
import urllib.parse # Required for safe URL encoding

# Load the data
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
    
    recommended_movies = []
    for i in movies_list:
        recommended_movies.append(movies.iloc[i[0]].title)
    return recommended_movies

# UI Header
st.set_page_config(page_title="Movie Recommender", page_icon="🎬")
st.title('Movie Recommender System 🎬')

selected_movie_name = st.selectbox(
    'Search for a movie you like:',
    movies['title'].values
)

if st.button('Recommend'):
    recommendations = recommend(selected_movie_name)
    st.write("### You might also like:")
    
    # Displaying recommendations with JustWatch links
    for title in recommendations:
        # Create a safe URL for JustWatch search (Polish version)
        encoded_title = urllib.parse.quote(title)
        justwatch_url = f"https://www.justwatch.com/pl/search?q={encoded_title}"
        
        # Display title and a clickable link
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(title)
        with col2:
            st.markdown(f"[![JustWatch](https://img.shields.io/badge/Check-JustWatch-orange)]({justwatch_url})")