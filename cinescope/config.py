"""App-wide constants: mood shortcuts, decade ranges and TMDB genre ids."""

# Mood button label → TMDB genre id.
MOODS = {
    "😂 Comedy": 35, "😱 Horror": 27, "❤️ Romance": 10749,
    "🦸 Action": 28, "🔍 Thriller": 53, "🚀 Sci-Fi": 878,
    "🎭 Drama": 18,  "🎬 Animation": 16,
}

# Decade label → (start year, end year) inclusive.
DECADES = {
    "2020s": (2020, 2029), "2010s": (2010, 2019),
    "2000s": (2000, 2009), "1990s": (1990, 1999), "1980s": (1980, 1989),
}

# Official TMDB movie genre names → genre ids.
GENRE_NAME_TO_ID = {
    "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35,
    "Crime": 80, "Drama": 18, "Family": 10751, "Fantasy": 14,
    "History": 36, "Horror": 27, "Music": 10402, "Mystery": 9648,
    "Romance": 10749, "Science Fiction": 878, "Thriller": 53,
    "War": 10752, "Western": 37,
}
