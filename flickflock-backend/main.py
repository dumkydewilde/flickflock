import os
import logging
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from flickflock.tmdb import TMDB
from flickflock.flock import Flock
from flickflock.bookmarks import BookmarkList

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:5173",
        "http://localhost:4173",
        "https://flickflock.pages.dev",
        "null",  # browsers send Origin: null after cross-origin 307 redirect
    ],
    allow_origin_regex=r"https://.*\.flickflock\.pages\.dev",
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

tmdb = TMDB(api_key=os.environ.get("TMDB_API_KEY"))


@app.get("/api/search")
def search(q: str = Query("", min_length=1)):
    try:
        return tmdb.search(q)
    except Exception:
        log.exception("Search failed for query: %s", q)
        raise HTTPException(500, "Search failed")


@app.get("/api/person/{person_id}")
def get_person_details(person_id: int):
    try:
        return tmdb.get_person_by_id(person_id)
    except Exception:
        log.exception("Failed to get person %d", person_id)
        raise HTTPException(404, "Person not found")


# --- Flock routes MUST come before the generic {media_type}/{content_id} routes ---
# FastAPI matches routes in definition order; the generic parameterized routes
# would otherwise swallow /api/flock/... paths and fail parsing the UUID as int.

@app.get("/api/flock/{flock_id}/details")
def flock_details(flock_id: str):
    if not flock_id:
        raise HTTPException(400, "Invalid Flock ID")
    try:
        f = Flock(flock_id=flock_id)
        return {
            "flock_id": f.flock_id,
            "selection": f.get_selection(),
            "flock": f.get_flock(details_function=person_details_func, most_common=25),
        }
    except Exception:
        log.exception("Failed to get flock details %s", flock_id)
        raise HTTPException(500, "Failed to load flock details")


@app.get("/api/flock/{flock_id}/results")
def flock_results(flock_id: str):
    if not flock_id:
        raise HTTPException(400, "Invalid Flock ID")
    try:
        f = Flock(flock_id=flock_id)
        works = f.get_flock_works(tmdb_movies_from_person, most_common=10)
        return {
            "flock_id": f.flock_id,
            "selection": f.get_selection(),
            "flock_works": works[:50],
        }
    except Exception:
        log.exception("Failed to get flock results %s", flock_id)
        raise HTTPException(500, "Failed to load results")


@app.post("/api/flock/{flock_id}/remove")
def flock_remove(flock_id: str, request_body: dict):
    selection_id = request_body.get("selection_id") if request_body else None
    if not selection_id:
        raise HTTPException(400, "Missing selection_id")
    try:
        f = Flock(flock_id=flock_id)
        f.remove_selection(selection_id)
        f.sync_flock()
        return {
            "flock_id": f.flock_id,
            "selection": f.get_selection(),
            "flock": f.get_flock(most_common=25),
        }
    except Exception:
        log.exception("Failed to remove selection from flock %s", flock_id)
        raise HTTPException(500, "Failed to remove selection")


@app.get("/api/flock/{flock_id}")
def get_flock(flock_id: str):
    if flock_id in ("", "None"):
        raise HTTPException(400, "Invalid Flock ID")
    try:
        f = Flock(flock_id=flock_id)
        return {
            "flock_id": f.flock_id,
            "selection": f.get_selection(),
            "flock": f.get_flock(most_common=25),
        }
    except Exception:
        log.exception("Failed to get flock %s", flock_id)
        raise HTTPException(500, "Failed to load flock")


@app.post("/api/flock")
@app.post("/api/flock/{flock_id}")
def update_flock(request_body: dict, flock_id: str | None = None):
    try:
        f = Flock(flock_id=flock_id)
        data_items = request_body.get("data")
        if not data_items:
            raise HTTPException(400, "Request body must include 'data' array")

        for item in data_items:
            if "id" not in item or "media_type" not in item:
                continue

            f.update_selection(item)
            media_type = item["media_type"]

            if media_type == "person":
                person = tmdb.get_person_by_id(item["id"])
                f.add_to_flock(
                    [{"id": item["id"],
                      "department": person.get("known_for_department", "Acting"),
                      "order": 0}],
                    primary_id=item["id"],
                    source_type="person_direct",
                )
                relations = tmdb.get_person_relations_filtered(item["id"])
                f.add_to_flock(
                    [p for p in relations if p.get("id") != item["id"]],
                    primary_id=item["id"],
                    source_type="person_transitive",
                )
            elif media_type in ("movie", "tv"):
                people = tmdb.get_people_by_media_id(item["id"], media_type)
                f.add_to_flock(
                    people,
                    primary_id=item["id"],
                    source_type=media_type,
                )

        return {
            "flock_id": f.flock_id,
            "selection": f.get_selection(),
            "flock": f.get_flock(most_common=25),
        }
    except HTTPException:
        raise
    except Exception:
        log.exception("Failed to update flock %s", flock_id)
        raise HTTPException(500, "Failed to update flock")


# --- Bookmark routes ---

@app.get("/api/bookmarks")
def get_bookmarks(x_user_id: str = Header(None)):
    """Get the current user's bookmark list."""
    if not x_user_id:
        raise HTTPException(400, "X-User-Id header required")
    try:
        bl = BookmarkList(user_id=x_user_id)
        return bl.to_dict()
    except Exception:
        log.exception("Failed to get bookmarks for user %s", x_user_id)
        raise HTTPException(500, "Failed to load bookmarks")


@app.get("/api/bookmarks/{list_id}")
def get_bookmark_list(list_id: str):
    """Get a bookmark list by its public ID (for sharing)."""
    try:
        bl = BookmarkList(list_id=list_id)
        return bl.to_dict()
    except Exception:
        log.exception("Failed to get bookmark list %s", list_id)
        raise HTTPException(500, "Failed to load bookmark list")


@app.post("/api/bookmarks")
def add_bookmark(request_body: dict, x_user_id: str = Header(None)):
    """Add an item to the user's bookmark list."""
    if not x_user_id:
        raise HTTPException(400, "X-User-Id header required")
    item = request_body.get("item")
    if not item or "id" not in item or "media_type" not in item:
        raise HTTPException(400, "Request body must include 'item' with id and media_type")
    try:
        bl = BookmarkList(user_id=x_user_id)
        bl.add(item)
        return bl.to_dict()
    except Exception:
        log.exception("Failed to add bookmark for user %s", x_user_id)
        raise HTTPException(500, "Failed to add bookmark")


@app.delete("/api/bookmarks/{media_type}/{media_id}")
def remove_bookmark(media_type: str, media_id: int, x_user_id: str = Header(None)):
    """Remove an item from the user's bookmark list."""
    if not x_user_id:
        raise HTTPException(400, "X-User-Id header required")
    try:
        bl = BookmarkList(user_id=x_user_id)
        bl.remove(media_id, media_type)
        return bl.to_dict()
    except Exception:
        log.exception("Failed to remove bookmark for user %s", x_user_id)
        raise HTTPException(500, "Failed to remove bookmark")


# --- Generic media routes AFTER flock routes to avoid shadowing ---

@app.get("/api/{media_type}/{content_id}/details")
def get_media_details(content_id: int, media_type: str):
    if media_type not in ("movie", "tv"):
        raise HTTPException(400, "media_type must be 'movie' or 'tv'")
    try:
        details = tmdb.get_details(media_type, content_id)
        credits = tmdb.get_credits(media_type, content_id)
        top_cast = credits.get("cast", [])[:8]
        top_crew = [c for c in credits.get("crew", [])
                    if c.get("job") in ("Director", "Writer", "Screenplay")]

        # Fetch streaming/watch providers
        watch_providers = {}
        try:
            wp_response = tmdb.get_watch_providers(media_type, content_id)
            watch_providers = wp_response.get("results", {})
        except Exception:
            log.warning("Failed to fetch watch providers for %s/%d", media_type, content_id)

        # For TV shows, fetch external IDs to get imdb_id (movies already have it in details)
        imdb_id = details.get("imdb_id")
        if not imdb_id and media_type == "tv":
            try:
                external_ids = tmdb.get_external_ids(media_type, content_id)
                imdb_id = external_ids.get("imdb_id")
            except Exception:
                log.warning("Failed to fetch external IDs for %s/%d", media_type, content_id)

        return {**details, "imdb_id": imdb_id, "top_cast": top_cast, "top_crew": top_crew, "watch_providers": watch_providers}
    except Exception:
        log.exception("Failed to get details for %s/%d", media_type, content_id)
        raise HTTPException(404, "Content not found")


@app.get("/api/{media_type}/{content_id}")
def get_content_details(content_id: int, media_type: str):
    if media_type not in ("movie", "tv"):
        raise HTTPException(400, "media_type must be 'movie' or 'tv'")
    try:
        return tmdb.get_people_by_media_id(content_id, media_type)
    except Exception:
        log.exception("Failed to get %s/%d", media_type, content_id)
        raise HTTPException(404, "Content not found")


def person_details_func(id):
    keys = ["id", "name", "biography", "birthday", "known_for_department", "popularity", "profile_path"]
    details = tmdb.get_person_by_id(id)
    return {k: details.get(k, "") for k in keys}


def tmdb_movies_from_person(id):
    keys = ["id", "overview", "media_type", "poster_path", "popularity", "first_air_date", "release_date", "original_language"]
    excluded = TMDB.EXCLUDED_GENRE_IDS
    results = []
    person_details = tmdb.get_person_by_id(id)
    for i in [*person_details.get("cast", []), *person_details.get("crew", [])]:
        # Skip talk shows, news, etc. — they pollute results
        if set(i.get("genre_ids", [])) & excluded:
            continue
        name_key = "title" if "title" in i else "name"
        results.append({
            "title": i[name_key],
            **{k: i.get(k, "") for k in keys},
        })
    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
