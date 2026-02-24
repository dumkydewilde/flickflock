import os
import logging
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from flickflock.tmdb import TMDB
from flickflock.flock import Flock

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
    ],
    allow_origin_regex=r"https://.*\.flickflock\.pages\.dev",
    allow_methods=["*"],
    allow_headers=["*"],
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
        return {**details, "top_cast": top_cast, "top_crew": top_crew}
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


def person_details_func(id):
    keys = ["id", "name", "biography", "birthday", "known_for_department", "popularity", "profile_path"]
    details = tmdb.get_person_by_id(id)
    return {k: details.get(k, "") for k in keys}


def tmdb_movies_from_person(id):
    keys = ["id", "overview", "media_type", "poster_path", "popularity", "first_air_date", "release_date", "original_language"]
    results = []
    person_details = tmdb.get_person_by_id(id)
    for i in [*person_details.get("cast", []), *person_details.get("crew", [])]:
        name_key = "title" if "title" in i else "name"
        results.append({
            "title": i[name_key],
            **{k: i.get(k, "") for k in keys},
        })
    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
