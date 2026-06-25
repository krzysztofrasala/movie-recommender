"""
Fetches top movies from TMDB API and rebuilds the recommendation model.
Usage: python fetch_dataset.py
"""

import os
import requests
import pandas as pd
import pickle
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

API_KEY = os.environ.get("TMDB_API_KEY")
if not API_KEY:
    raise ValueError("Set TMDB_API_KEY environment variable before running this script.")
BASE = "https://api.themoviedb.org/3"
MAX_PAGES = 200  # 20 movies/page → up to 4000 movies (keeps similarity.pkl < 100MB)


def get(url, params={}):
    params["api_key"] = API_KEY
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 429:
                time.sleep(2)
                continue
            r.raise_for_status()
            return r.json()
        except Exception:
            time.sleep(1)
    return None


def fetch_movie_ids():
    ids = []
    for page in range(1, MAX_PAGES + 1):
        data = get(f"{BASE}/discover/movie", {
            "sort_by": "popularity.desc",
            "vote_count.gte": 50,
            "page": page,
        })
        if not data or not data.get("results"):
            break
        ids.extend(m["id"] for m in data["results"])
        if page % 50 == 0:
            print(f"  Fetched page {page}/{MAX_PAGES} — {len(ids)} IDs so far")
    return list(set(ids))


def fetch_details(movie_id):
    data = get(f"{BASE}/movie/{movie_id}", {"append_to_response": "keywords,credits"})
    if not data or not data.get("title"):
        return None

    genres = [g["name"].replace(" ", "") for g in data.get("genres", [])]
    keywords = [k["name"].replace(" ", "") for k in data.get("keywords", {}).get("keywords", [])]
    cast = [c["name"].replace(" ", "") for c in data.get("credits", {}).get("cast", [])[:3]]
    director = next(
        (p["name"].replace(" ", "") for p in data.get("credits", {}).get("crew", []) if p["job"] == "Director"),
        ""
    )
    overview = data.get("overview", "").split()
    tags = overview + genres + keywords + cast + ([director] if director else [])

    return {
        "movie_id": movie_id,
        "title": data["title"],
        "release_date": data.get("release_date", ""),
        "tags": " ".join(tags).lower(),
        "genres": str([{"name": g["name"]} for g in data.get("genres", [])]),
    }


def main():
    print("Step 1: Fetching movie IDs from TMDB...")
    ids = fetch_movie_ids()
    print(f"  Total unique IDs: {len(ids)}")

    print("Step 2: Fetching details for each movie (parallel)...")
    rows = []
    failed = 0
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(fetch_details, mid): mid for mid in ids}
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result:
                rows.append(result)
            else:
                failed += 1
            if i % 500 == 0:
                print(f"  Processed {i}/{len(ids)} — {len(rows)} OK, {failed} failed")

    print(f"  Done: {len(rows)} movies fetched, {failed} failed")

    df = pd.DataFrame(rows).drop_duplicates("movie_id")
    df = df[df["tags"].str.strip() != ""].reset_index(drop=True)
    print(f"  After dedup/cleanup: {df.shape[0]} movies")

    print("Step 3: Building similarity matrix...")
    cv = CountVectorizer(max_features=5000, stop_words="english")
    vectors = cv.fit_transform(df["tags"]).toarray()
    sim = cosine_similarity(vectors).astype("float32")  # float32 halves file size vs float64

    print("Step 4: Saving model files...")
    model_df = df[["movie_id", "title", "tags"]]
    pickle.dump(model_df.to_dict(), open("movie_dict.pkl", "wb"))
    pickle.dump(sim, open("similarity.pkl", "wb"))

    # Save a minimal movies.csv so app.py can read release_date and genres
    csv_df = df[["movie_id", "title", "release_date", "genres"]].rename(columns={"movie_id": "id"})
    csv_df.to_csv("movies.csv", index=False)

    years = pd.to_datetime(df["release_date"], errors="coerce").dt.year
    print(f"\nDone! {len(df)} movies saved.")
    print(f"Year range: {int(years.min())} – {int(years.max())}")


if __name__ == "__main__":
    main()
