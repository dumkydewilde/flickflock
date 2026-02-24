import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flickflock.tmdb import TMDB
from flickflock.flock import Flock

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)
origins_list = [
    "http://localhost:8080",
    "http://localhost:5173",
    "http://localhost:4173",
    "https://flickflock.pages.dev",
    r"https://.*\.flickflock\.pages\.dev",
]
cors = CORS(app, origins=origins_list)

tmdb = TMDB(api_key=os.environ.get("TMDB_API_KEY"))


def error_response(message, status_code):
    return jsonify({"error": message}), status_code


@app.route("/api/search", methods=["GET"])
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return error_response("Missing search query parameter 'q'", 400)
    try:
        return jsonify(tmdb.search(query))
    except Exception as e:
        log.exception("Search failed for query: %s", query)
        return error_response("Search failed", 500)


@app.route("/api/person/<int:id>", methods=["GET"])
def get_person_details(id):
    try:
        return jsonify(tmdb.get_person_by_id(id))
    except Exception as e:
        log.exception("Failed to get person %d", id)
        return error_response("Person not found", 404)


@app.route("/api/<media_type>/<int:id>", methods=["GET"])
def get_content_details(id, media_type):
    if media_type not in ("movie", "tv"):
        return error_response("media_type must be 'movie' or 'tv'", 400)
    try:
        return jsonify(tmdb.get_people_by_media_id(id, media_type))
    except Exception as e:
        log.exception("Failed to get %s/%d", media_type, id)
        return error_response("Content not found", 404)


@app.route("/api/flock", methods=["GET", "POST"], strict_slashes=False)
@app.route("/api/flock/<flock_id>", methods=["GET", "POST"], strict_slashes=False)
def flock(flock_id=None):
    if request.method == "GET":
        if flock_id in ("", None, "None"):
            return error_response("Invalid Flock ID", 400)
        try:
            f = Flock(flock_id=flock_id)
            return jsonify({
                "flock_id": f.flock_id,
                "selection": f.get_selection(),
                "flock": f.get_flock(most_common=25),
            })
        except Exception as e:
            log.exception("Failed to get flock %s", flock_id)
            return error_response("Failed to load flock", 500)

    if request.method == "POST":
        try:
            f = Flock(flock_id=flock_id)
            data = request.get_json()
            if not data or "data" not in data:
                return error_response("Request body must include 'data' array", 400)

            for item in data["data"]:
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

            return jsonify({
                "flock_id": f.flock_id,
                "selection": f.get_selection(),
                "flock": f.get_flock(most_common=25),
            })
        except Exception as e:
            log.exception("Failed to update flock %s", flock_id)
            return error_response("Failed to update flock", 500)

    return error_response("Method not allowed", 405)


@app.route("/api/flock/<flock_id>/details", methods=["GET"])
def flock_details(flock_id):
    if not flock_id:
        return error_response("Invalid Flock ID", 400)
    try:
        f = Flock(flock_id=flock_id)
        return jsonify({
            "flock_id": f.flock_id,
            "selection": f.get_selection(),
            "flock": f.get_flock(details_function=person_details_func, most_common=25),
        })
    except Exception as e:
        log.exception("Failed to get flock details %s", flock_id)
        return error_response("Failed to load flock details", 500)


@app.route("/api/flock/<flock_id>/results", methods=["GET"])
def flock_results(flock_id):
    if not flock_id:
        return error_response("Invalid Flock ID", 400)
    try:
        f = Flock(flock_id=flock_id)
        works = f.get_flock_works(tmdb_movies_from_person, most_common=10)
        return jsonify({
            "flock_id": f.flock_id,
            "selection": f.get_selection(),
            "flock_works": works[:50],
        })
    except Exception as e:
        log.exception("Failed to get flock results %s", flock_id)
        return error_response("Failed to load results", 500)


@app.route("/api/flock/<flock_id>/remove", methods=["POST"])
def flock_remove(flock_id):
    if not flock_id:
        return error_response("Invalid Flock ID", 400)

    data = request.get_json()
    selection_id = data.get("selection_id") if data else None
    if not selection_id:
        return error_response("Missing selection_id", 400)

    try:
        f = Flock(flock_id=flock_id)
        f.remove_selection(selection_id)
        f.sync_flock()
        return jsonify({
            "flock_id": f.flock_id,
            "selection": f.get_selection(),
            "flock": f.get_flock(most_common=25),
        })
    except Exception as e:
        log.exception("Failed to remove selection from flock %s", flock_id)
        return error_response("Failed to remove selection", 500)


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
    app.run(port=int(os.environ.get("PORT", 8080)), host="0.0.0.0", debug=True)
