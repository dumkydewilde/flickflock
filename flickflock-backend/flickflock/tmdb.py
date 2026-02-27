import logging, os, requests, xxhash
from datetime import date
from diskcache import Cache

log = logging.getLogger(__name__)

class TMDB:    
    api_key_name = "TMDB_API_KEY"
    tmdb_requests = 0
    cached_requests = 0
    cache = Cache('.requests', statistics=True)

    def __init__(self, base_url="https://api.themoviedb.org/3", api_key=None, use_cache=True):
        self.base_url = base_url
        self.api_key = api_key
        self.is_authenticated = False
        self.use_cache = use_cache

        self.authenticate()

    def reset_cache(self):
        self.cache_db.truncate()

    def get_cached_request(self, request_id):
        try:
            cache = self.cache.get(request_id)
        except Exception as e:
            print(f"Exception when fetching from cache ({request_id}): {e}")
            print("resetting cache...")
            
            cache = None
        
        if cache:
            return cache["data"]
        else:
            return False

    def set_cached_request(self, request_id, data):
        self.cache.set(request_id, {
            "date": str(date.today()),
            "data": data
        }, expire=7 * 24 * 3600)  # 7-day TTL

    def authenticate(self):
        if self.api_key:
            self.is_authenticated = True
            return
        elif self.api_key_name in os.environ:
            self.api_key = os.environ.get(self.api_key_name)
            self.is_authenticated = True
            return
        else:
            raise Exception("Unable to authenticate")   
        
        # TODO: check authentication
        

    def request(self, path: str, method="GET", params={}) -> dict:
        """Make a request to the TMDB api and return the result as a dict."""
        params = "&".join([f"{k}={params[k]}" for k in params])
        query_string = f"api_key={self.api_key}&{params}"
        request_url = f"{self.base_url}/{path}?{query_string}"

        if self.use_cache and method == "GET":
            request_id = xxhash.xxh3_64_hexdigest(request_url)
            res = self.get_cached_request(request_id)
            if res is False:
                res = requests.request(method, request_url).json()
                self.tmdb_requests += 1
                self.set_cached_request(request_id, res)
            
        else:
            res = requests.request(method, request_url).json()
            self.tmdb_requests += 1

        if "status_message" in res:
            log.error("TMDB API error: %s", res["status_message"])
            raise RuntimeError(f"TMDB API error: {res['status_message']}")

        return res


    def search(self, search_query: str, type="multi") -> list:
        """Provide a search query to search the TMDB database and return a dict with the first page of results."""
        print(f"searching for: {search_query}")

        results = self.request(f"search/{type}", params={"query": search_query})["results"]
        return self._rank_search_results(results, search_query)

    _ARTICLES = {"the ", "a ", "an "}

    @staticmethod
    def _strip_article(title: str) -> str:
        for art in TMDB._ARTICLES:
            if title.startswith(art):
                return title[len(art):]
        return title

    @staticmethod
    def _rank_search_results(results: list, query: str) -> list:
        """Re-rank search results to boost exact and prefix title matches."""
        q = query.lower().strip()
        q_no_article = TMDB._strip_article(q)

        def sort_key(item):
            title = (item.get("title") or item.get("name") or "").lower()
            title_no_article = TMDB._strip_article(title)
            popularity = item.get("popularity", 0)

            if title == q or title_no_article == q_no_article:
                boost = 3
            elif title.startswith(q) or title_no_article.startswith(q_no_article):
                boost = 2
            elif q in title:
                boost = 1
            else:
                boost = 0
            return (-boost, -popularity)

        return sorted(results, key=sort_key)

    def get_details(self, media_type: str, id: int) -> dict:
        """Get details for a movie or TV show."""
        return self.request(f"{media_type}/{id}")

    def get_credits(self, media_type: str, id: int) -> list:
        return self.request(f"{media_type}/{id}/credits")

    def get_people_by_media_id(
        self,
        id: int,
        media_type: str,
        ) -> list:
        """Get the people who have contributed to a type of media"""
        credits = self.get_credits(media_type, id)
        return [*credits["cast"], *credits["crew"]]
        

    def get_person_by_id(self, id):
        person_details = self.request(f"person/{id}")
        person_credits = self.request(f"person/{id}/combined_credits")
        return {
            **person_details, 
            **person_credits
            }

    # Departments worth including in filtered/transitive expansion
    KEY_CREW_DEPARTMENTS = {"Directing", "Writing", "Production", "Sound"}

    # TMDB TV genre IDs to exclude — these create noisy connections
    # (talk show hosts "work with" every guest, polluting recommendations)
    EXCLUDED_TV_GENRE_IDS = {
        10767,  # Talk (late night shows, talk shows)
        10763,  # News
    }

    def get_people_by_media_id_filtered(self, id, media_type, max_cast=15):
        """Get filtered people from a work: top-billed cast + key crew only."""
        credits = self.get_credits(media_type, id)
        cast = credits.get("cast", [])[:max_cast]
        crew = [c for c in credits.get("crew", [])
                if c.get("department") in self.KEY_CREW_DEPARTMENTS]
        return [*cast, *crew]

    def get_person_relations(self, person_id):
        """Original unfiltered expansion (kept for backward compat)."""
        relations = []
        works = self.get_person_by_id(person_id)
        for work in [*works.get("cast", []), *works.get("crew", [])]:
            relations.extend(self.get_people_by_media_id(
                work["id"],
                work["media_type"]
            ))
        return relations

    def get_person_relations_filtered(self, person_id, max_works=10, max_cast_per_work=15):
        """Get collaborators from a person's top works only (filtered expansion).

        Used for transitive connections: limits to top N works by popularity,
        and only top-billed cast + key crew per work.
        """
        person = self.get_person_by_id(person_id)
        all_works = [*person.get("cast", []), *person.get("crew", [])]

        # Deduplicate, skip excluded genres, and take top N by popularity
        seen = set()
        top_works = []
        for w in sorted(all_works, key=lambda w: w.get("popularity", 0), reverse=True):
            if w["id"] in seen:
                continue
            seen.add(w["id"])
            # Skip talk shows, news, etc. — they create noisy connections
            genre_ids = set(w.get("genre_ids", []))
            if genre_ids & self.EXCLUDED_TV_GENRE_IDS:
                continue
            top_works.append(w)
            if len(top_works) >= max_works:
                break

        relations = []
        for work in top_works:
            relations.extend(self.get_people_by_media_id_filtered(
                work["id"], work["media_type"], max_cast=max_cast_per_work
            ))
        return relations