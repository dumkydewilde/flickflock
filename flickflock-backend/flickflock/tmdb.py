import os, requests, xxhash
from datetime import date
from diskcache import Cache 

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

        if self.cache and method == "GET":
            request_id = xxhash.xxh3_64_hexdigest(request_url)
            res = self.get_cached_request(request_id)
            if res == False:
                res = requests.request(method, request_url).json()
                self.tmdb_requests += 1
                self.set_cached_request(request_id, res)
            
        else:
            res = requests.request(method, request_url).json()
            self.tmdb_requests += 1

        return res


    def search(self, search_query: str, type="multi") -> list:
        """Provide a search query to search the TMDB database and return a dict with the first page of results."""
        print(f"searching for: {search_query}")

        return self.request(f"search/{type}", params={"query" :  search_query})["results"]

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

    def get_person_relations(self, person_id):
        relations = []
        works = self.get_person_by_id(person_id)
        for work in [*works.get("cast",[]), *works.get("crew",[])]:
            relations.extend(self.get_people_by_media_id(
                work["id"], 
                work["media_type"]
                ))

        return relations