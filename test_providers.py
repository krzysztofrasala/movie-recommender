import os
from cinescope.tmdb import fetch_movie_providers, _get, search_movies
print(search_movies("The Devil Wears Prada"))
res = _get("search/movie", {"query": "The Devil Wears Prada", "language": "en-US"})
if res and res.get("results"):
    mid = res["results"][0]["id"]
    print("ID:", mid)
    print("Providers:", _get(f"movie/{mid}/watch/providers"))
