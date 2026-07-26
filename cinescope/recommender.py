"""Content-based recommendation logic on top of the local similarity model."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from cinescope import data, tmdb

TOP_N = 10
MIN_STARS_FOR_PROFILE = 3  # st.feedback stars are 0-4; >=3 means a 4-5 star rating


import numpy as np
import streamlit as st

from cinescope import data, tmdb

TOP_N = 10
MIN_STARS_FOR_PROFILE = 3  # st.feedback stars are 0-4; >=3 means a 4-5 star rating


def recommend(title: str) -> list[dict]:
    """Top-N most similar local movies to ``title``, enriched with TMDB details and match scores."""
    movies = data.get_movies()
    local = movies[movies["title"] == title]
    if local.empty:
        return []
    idx = local.index[0]
    neighbors_data = data.get_neighbors()
    neighbor_indices = neighbors_data["indices"][idx][:TOP_N]
    neighbor_scores = neighbors_data["scores"][idx][:TOP_N]

    candidates = [
        (movies.iloc[i].movie_id, movies.iloc[i].title, float(neighbor_scores[j]))
        for j, i in enumerate(neighbor_indices)
    ]

    source_genres = set(data.get_local_genres(title))

    def fetch_one(candidate: tuple) -> dict | None:
        movie_id, movie_title, score = candidate
        details = tmdb.fetch_movie_details(movie_id)
        if details:
            details["title"] = movie_title
            details["match_score"] = int(round(max(0.0, min(1.0, score)) * 100))
            cand_genres = set(data.get_local_genres(movie_title))
            shared = source_genres.intersection(cand_genres)
            if shared:
                details["match_reason"] = f"Shared genres: {', '.join(sorted(shared)[:2])}"
            else:
                details["match_reason"] = "High semantic story match"
        return details

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_one, candidates))
    return [r for r in results if r]


def more_like_this(movie_id: int, movie_title: str) -> list[dict]:
    """Local content-based recs when the title is in the dataset, TMDB fallback otherwise."""
    movies = data.get_movies()
    local = movies[movies["title"].str.lower() == movie_title.lower()]
    if local.empty:
        return tmdb.fetch_movie_recommendations(movie_id)
    return recommend(local.iloc[0]["title"])


def recommend_for_you() -> list[dict]:
    """Blend recommendations using a dynamic User Preference Vector (V_user) weighted by user star ratings."""
    rated_info = st.session_state.get("rated_movies_info", {})
    user_ratings = st.session_state.get("user_ratings", {})

    good_ratings = {
        movie_id: info
        for movie_id, info in rated_info.items()
        if user_ratings.get(movie_id, 0) >= MIN_STARS_FOR_PROFILE
    }
    if not good_ratings:
        return []

    movies = data.get_movies()
    vectors, is_dense = data.get_vectors()

    # Construct User Preference Vector V_user
    user_vector = None
    rated_indices = set()
    user_top_genres = set()

    for movie_id, info in good_ratings.items():
        stars = user_ratings.get(movie_id, 3) + 1  # 0-4 -> 1-5
        weight = float(stars) / 5.0

        local = movies[movies["title"].str.lower() == info["title"].lower()]
        if local.empty:
            continue
        idx = local.index[0]
        rated_indices.add(idx)

        genres = data.get_local_genres(info["title"])
        user_top_genres.update(genres)

        vec = vectors[idx]
        if is_dense:
            norm = np.linalg.norm(vec)
            vec_norm = vec / norm if norm > 0 else vec
            if user_vector is None:
                user_vector = weight * vec_norm
            else:
                user_vector += weight * vec_norm
        else:
            vec_dense = vec.toarray().ravel()
            norm = np.linalg.norm(vec_dense)
            vec_norm = vec_dense / norm if norm > 0 else vec_dense
            if user_vector is None:
                user_vector = weight * vec_norm
            else:
                user_vector += weight * vec_norm

    if user_vector is None:
        return []

    # Normalize V_user
    u_norm = np.linalg.norm(user_vector)
    if u_norm > 0:
        user_vector /= u_norm

    # Compute similarity between user_vector and all movie vectors
    if is_dense:
        vec_norms = np.linalg.norm(vectors, axis=1)
        vec_norms[vec_norms == 0] = 1.0
        sim_scores = np.dot(vectors, user_vector) / vec_norms
    else:
        sim_scores = vectors.dot(user_vector)
        row_norms = np.sqrt(vectors.multiply(vectors).sum(axis=1)).A1
        row_norms[row_norms == 0] = 1.0
        sim_scores = sim_scores / row_norms

    # Zero out already rated movies
    for idx in rated_indices:
        sim_scores[idx] = -1.0

    # Get top-N candidate indices
    top_indices = np.argsort(-sim_scores)[:TOP_N]

    candidates = [
        (movies.iloc[i].movie_id, movies.iloc[i].title, float(sim_scores[i]))
        for i in top_indices if sim_scores[i] > 0
    ]

    def fetch_one(candidate: tuple) -> dict | None:
        movie_id, movie_title, score = candidate
        details = tmdb.fetch_movie_details(movie_id)
        if details:
            details["title"] = movie_title
            details["match_score"] = int(round(max(0.0, min(1.0, score)) * 100))
            cand_genres = set(data.get_local_genres(movie_title))
            shared = user_top_genres.intersection(cand_genres)
            if shared:
                details["match_reason"] = f"Matches your taste in {', '.join(sorted(shared)[:2])}"
            else:
                details["match_reason"] = "Matches your overall film profile"
        return details

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_one, candidates))
    return [r for r in results if r]


def recommend_for_group(favorite_titles_person1: list[str], favorite_titles_person2: list[str]) -> list[dict]:
    """Find recommendations that best match the joint taste vector of two persons."""
    movies = data.get_movies()
    vectors, is_dense = data.get_vectors()

    def build_user_vec(titles: list[str]):
        u_vec = None
        seen_indices = set()
        user_genres = set()
        for t in titles:
            local = movies[movies["title"].str.lower() == t.lower()]
            if local.empty:
                continue
            idx = local.index[0]
            seen_indices.add(idx)
            user_genres.update(data.get_local_genres(t))
            v = vectors[idx]
            if is_dense:
                norm = np.linalg.norm(v)
                v_norm = v / norm if norm > 0 else v
                u_vec = v_norm if u_vec is None else u_vec + v_norm
            else:
                v_dense = v.toarray().ravel()
                norm = np.linalg.norm(v_dense)
                v_norm = v_dense / norm if norm > 0 else v_dense
                u_vec = v_norm if u_vec is None else u_vec + v_norm
        if u_vec is not None and np.linalg.norm(u_vec) > 0:
            u_vec /= np.linalg.norm(u_vec)
        return u_vec, seen_indices, user_genres

    v1, seen1, g1 = build_user_vec(favorite_titles_person1)
    v2, seen2, g2 = build_user_vec(favorite_titles_person2)

    if v1 is None and v2 is None:
        return []
    elif v1 is None:
        joint_vector = v2
    elif v2 is None:
        joint_vector = v1
    else:
        joint_vector = v1 + v2
        j_norm = np.linalg.norm(joint_vector)
        if j_norm > 0:
            joint_vector /= j_norm

    if is_dense:
        vec_norms = np.linalg.norm(vectors, axis=1)
        vec_norms[vec_norms == 0] = 1.0
        sim_scores = np.dot(vectors, joint_vector) / vec_norms
    else:
        sim_scores = vectors.dot(joint_vector)
        row_norms = np.sqrt(vectors.multiply(vectors).sum(axis=1)).A1
        row_norms[row_norms == 0] = 1.0
        sim_scores = sim_scores / row_norms

    all_seen = seen1.union(seen2)
    for idx in all_seen:
        sim_scores[idx] = -1.0

    top_indices = np.argsort(-sim_scores)[:TOP_N]

    joint_top_genres = g1.intersection(g2) if (g1 and g2) else g1.union(g2)

    candidates = [
        (movies.iloc[i].movie_id, movies.iloc[i].title, float(sim_scores[i]))
        for i in top_indices if sim_scores[i] > 0
    ]

    def fetch_one(candidate: tuple) -> dict | None:
        movie_id, movie_title, score = candidate
        details = tmdb.fetch_movie_details(movie_id)
        if details:
            details["title"] = movie_title
            details["match_score"] = int(round(max(0.0, min(1.0, score)) * 100))
            cand_genres = set(data.get_local_genres(movie_title))
            shared = joint_top_genres.intersection(cand_genres)
            if shared:
                details["match_reason"] = f"Matches both tastes: {', '.join(sorted(shared)[:2])}"
            else:
                details["match_reason"] = "Optimal balance for both tastes"
        return details

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_one, candidates))
    return [r for r in results if r]


