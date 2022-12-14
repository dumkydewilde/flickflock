import sys
from flickflock.tmdb import TMDB
from flickflock.flock import Flock

tmdb = TMDB()

def get_tmdb_people_from_query(n=50):

    query = str(input("Search for a movie, show or person: "))

    search = tmdb.search(query)

    if len(search) == 1:
        selected_item = search[0]
        if "original_title" in selected_item:
            name_key = "original_title"
        else:
            name_key = "name"

        print(f"One result, selected '{selected_item[name_key]}'")

    else:
        for i, s in enumerate(search[:10]):
            if "original_title" in s:
                name_key = "original_title"
            else:
                name_key = "name"
            if not "overview" in s:
                s["overview"] = ""
            
            print_string = f"[{i+1}] {s[name_key]}"
            if len(s["overview"]) > 0:
                print_string += f": {s['overview']}"
            print(print_string)
            #

        selection_id = int(input("Select the search result you want to add: "))
        selected_item = search[selection_id-1]

    if selected_item["media_type"] == "person":
        people = [selected_item]
        works = tmdb.get_person_by_id(selected_item["id"])
        for work in [*works.get("cast",[]), *works.get("crew",[])]:
            people.extend(tmdb.get_people_by_media_id(
                work["id"], 
                work["media_type"]
                ))

    else:
        people = tmdb.get_people_by_media_id(selected_item["id"], selected_item["media_type"])

    print(f"\n\n### {tmdb.tmdb_requests} tmdb requests / {tmdb.cached_requests} cached ###")

    return (people[:n], selected_item["id"])

def show_current_flock(flock):
    print("\n## Current flock ##\n")
    def details_func(id):
        keys = ["name", "biography", "birthday", "known_for_department", "popularity"]
        details = tmdb.get_person_by_id(id)
        return {k: details[k] for k in keys}

    flock_details = flock.get_flock(details_function=details_func, most_common=5)
    [print(f"{i['count']} — {i['name']} ({i['known_for_department']})") for i in flock_details.values()]
    print(f"\n\n### {tmdb.tmdb_requests} tmdb requests / {tmdb.cached_requests} cached ###")
    print("\n")

def show_flock_results(flock):
    print("Getting flock results...")
    works = list(flock.get_flock_works(tmdb_movies_from_person, most_common=10))
    works = sorted(works,key=lambda d: d["count"], reverse=True)
    [print(f"{w['count']} — {w['title']} ({w['media_type']}) — https://www.themoviedb.org/{w['media_type']}/{w['id']}: \n {w['overview']}\n") for w in works[:10]]
    print(f"\n\n### {tmdb.tmdb_requests} tmdb requests / {tmdb.cached_requests} cached ###")

def tmdb_movies_from_person(id):
    results = []

    person_details = tmdb.get_person_by_id(id)
    

    for i in [*person_details.get("cast",[]), *person_details.get("crew",[])]:
        if "title" in i:
            name_key = "title"
        else:
            name_key = "name"
            
        results.append({
            "title" : i[name_key],
            "overview": i["overview"],
            "media_type": i["media_type"],
            "id": i["id"]
            })
    
    return results
    

if __name__ == "__main__":
    if len(sys.argv) > 1:
        flock = Flock(flock_id=str(sys.argv[1]))
        show_current_flock(flock)        
    else:
        flock = Flock("flockie")
    add_works = True
    while add_works == True:
        people = get_tmdb_people_from_query()
        flock.add_to_flock([p["id"] for p in people[0]], primary_id=people[1])

        show_current_flock(flock)

        cont = input("\nWould you like to add another work or person to the flock? (Y/n)")
        if cont.lower() == "n" or cont.lower() == "no":
            add_works = False

    show_flock_results(flock)

    
        
