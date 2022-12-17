import os
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from flickflock.tmdb import TMDB
from flickflock.flock import Flock

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

tmdb = TMDB(api_key=os.environ.get("TMDB_API_KEY"))

@app.route("/api/search", methods=["GET"])
def search():
    query = request.args.get("q", None)
    if query:        
        return jsonify(tmdb.search(query))
    else:
        return "Invalid search query."

@app.route("/api/person/<int:id>", methods=["GET"])
def get_person_details(id):
    return tmdb.get_person_by_id(id)

@app.route("/api/<media_type>/<int:id>", methods=["GET"])
def get_content_details(id, media_type):
    if media_type and id > 0:
        return tmdb.get_people_by_media_id(id, media_type)
    else:
        return "Invalid request", 400

@app.route("/api/flock/create", methods=["POST"])
def create_flock():
    return

@app.route("/api/flock", methods=["POST"], defaults={"flock_id" : None}, strict_slashes=False)
@app.route("/api/flock/<flock_id>", methods=["GET", "POST"])
def flock(flock_id):
    if not flock_id:
        flock = Flock()
    else:
        flock = Flock(flock_id=flock_id)
    
    if request.method == "GET" and flock_id:
        return jsonify({
            "flock_id": flock.flock_id,
            "selection": flock.get_selection(),
            "flock": flock.get_flock(most_common=25)
        })
    
    if request.method == "POST":
        data = request.get_json()
        
        for item in data.get("data", []):
            flock.update_selection(item)
            if item.get("media_type", None) == "person":
                # if person, add person and find related persons
                flock.add_to_flock(item["id"])
                flock.add_to_flock([p["id"] for p in tmdb.get_person_relations(item["id"]) if p["id"] is not item["id"]], item["id"])
            if item.get("media_type", None) and item.get("media_type") != "person":
                # if work, find people from that work
                flock.add_to_flock([p["id"] for p in tmdb.get_people_by_media_id(item["id"], item["media_type"])], item["id"])

        return jsonify({
                    "flock_id": flock.flock_id,
                    "selection": flock.get_selection(),
                    "flock": flock.get_flock(most_common=25)
                })

@app.route("/api/flock/<flock_id>/details", methods=["GET"])
def flock_details(flock_id):
    if not flock_id:
        flock = Flock(flock_id=flock_id)
    else:
        flock = Flock(flock_id=flock_id)
    
    if request.method == "GET" and flock_id:
        return jsonify({
            "flock_id": flock.flock_id,
            "selection": flock.get_selection(),
            "flock": flock.get_flock(details_function=person_details_func, most_common=25)
        })



@app.route("/api/flock/<flock_id>/results", methods=["GET"])
def flock_results(flock_id):
    if not flock_id:
        return None
    else:
        flock = Flock(flock_id=flock_id)
    
    if request.method == "GET" and flock.flock_id:
        works = list(flock.get_flock_works(tmdb_movies_from_person, most_common=10))
        
        return jsonify({
            "flock_id": flock.flock_id,
            "selection": flock.get_selection(),
            "flock_works": sorted(works,key=lambda d: d["count"], reverse=True)[:50]
        })

            

def person_details_func(id):
    keys = ["id", "name", "biography", "birthday", "known_for_department", "popularity", "profile_path"]
    details = tmdb.get_person_by_id(id)
    return {k: details.get(k, "") for k in keys}

def tmdb_movies_from_person(id):
    keys = ["id", "overview", "media_type", "poster_path", "popularity", "first_air_date", "release_date", "original_language"]
    results = []
    person_details = tmdb.get_person_by_id(id)
    for i in [*person_details.get("cast",[]), *person_details.get("crew",[])]:
        if "title" in i:
            name_key = "title"
        else:
            name_key = "name"
            
        results.append({
            "title" : i[name_key],
            **{k: i.get(k, "") for k in keys}
            })
    
    return results


if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 8080)),host="0.0.0.0", debug=True)