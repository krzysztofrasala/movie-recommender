# 🎬 Movie Recommendation System

A machine learning-based movie recommender system that uses **Content-Based Filtering** to suggest movies similar to a user's selection based on tags, genres, cast, and crew.

## 🚀 Features
- **Smart Recommendations**: Suggests the top 5 most similar movies.
- **Streamlit Web UI**: An interactive and user-friendly interface.
- **NLP-Powered**: Utilizes Natural Language Processing (Stemming & CountVectorizer) to analyze movie metadata.
- **Data-Driven**: Features a robust preprocessing pipeline using Pandas and Scikit-learn.

## 🛠️ Tech Stack
- **Python**: Core logic and data processing.
- **Pandas & NumPy**: Data manipulation and cleaning.
- **Scikit-learn**: Vectorization and Cosine Similarity calculation.
- **Streamlit**: Web application framework for the UI.
- **NLTK**: Text preprocessing (Stemming).

## 🧠 How It Works
1. **Data Integration**: Merges `movies.csv` and `credits.csv` into a single dataset.
2. **Tag Creation**: Combines movie overviews, genres, keywords, cast, and directors into a unified "tags" column.
3. **Vectorization**: Converts text tags into numerical vectors using the **Bag of Words** (CountVectorizer) technique.
4. **Similarity Calculation**: Uses **Cosine Similarity** to calculate the mathematical distance between movie vectors.

## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/krzysztofrasala/movie-recommender.git
cd movie-recommender
```

### 2. Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Generate the Model (Important)
The model files (`.pkl`) are too large for GitHub storage. You must generate them locally:
1. Open `recommender.ipynb` in your code editor (VS Code or Jupyter).
2. **Run All Cells** to process the data and export the models.
3. Verify that `movie_dict.pkl` and `similarity.pkl` have been created in the root directory.

## 🏃 Usage
Run the following command to start the web interface:
```bash
streamlit run app.py
```

## 📂 Project Structure
- `app.py`: The main Streamlit web application.
- `recommender.ipynb`: Data cleaning, feature engineering, and model building.
- `requirements.txt`: Project dependencies.
- `movies.csv / credits.csv`: Raw movie datasets.

---
*Created as a portfolio project to demonstrate NLP and Machine Learning Recommendation Systems.*
