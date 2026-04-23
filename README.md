# Movie Recommendation System 🎬

A machine learning-based movie recommender system using Content-Based Filtering. The system suggests movies similar to the one selected by the user based on tags, genres, and cast.

## How it works
The system uses **Natural Language Processing (NLP)** to create tags for each movie. We then use **Cosine Similarity** to calculate the mathematical distance between movies in a multi-dimensional vector space.



## Tech Stack
- **Python** (Pandas, NumPy, Scikit-learn)
- **Jupyter Notebook** (Data Preprocessing & Modeling)
- **Streamlit** (Web Interface)

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/krzysztofrasala/movie-recommender.git](https://github.com/krzysztofrasala/movie-recommender.git)
   cd movie-recommender

2. **2. Create and activate virtual environment:**
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate


3. **2. Install dependecies:**
   pip install -r requirements.txt

4. **Generate the Model:**
   Open recommender.ipynb in VS Code and Run All cells. This will generate the necessary movie_dict.pkl and similarity.pkl files (which are too large to be stored on GitHub).

5. **Run the Web App:**
   streamlit run app.py

