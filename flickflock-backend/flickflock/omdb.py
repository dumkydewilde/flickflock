import logging
import os
import re
import requests
import xxhash
from diskcache import Cache

log = logging.getLogger(__name__)


class OMDb:
    """Lightweight OMDb API client with disk caching."""

    cache = Cache('.requests', statistics=True)

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OMDB_API_KEY")
        if not self.api_key:
            log.warning("No OMDB_API_KEY configured; OMDb enrichment disabled")
        self.base_url = "https://www.omdbapi.com/"

    def get_by_imdb_id(self, imdb_id: str) -> dict | None:
        """Fetch movie/show data from OMDb by IMDB ID. Returns None on failure."""
        if not self.api_key or not imdb_id:
            return None

        url = f"{self.base_url}?i={imdb_id}&apikey={self.api_key}"
        request_id = xxhash.xxh3_64_hexdigest(url)

        # Check cache
        cached = self.cache.get(request_id)
        if cached:
            return cached.get("data")

        try:
            resp = requests.get(url, timeout=5)
            data = resp.json()
            if data.get("Response") == "False":
                log.debug("OMDb returned no result for %s", imdb_id)
                return None
            self.cache.set(request_id, {"data": data}, expire=7 * 24 * 3600)
            return data
        except Exception:
            log.warning("OMDb request failed for %s", imdb_id, exc_info=True)
            return None

    @staticmethod
    def parse_awards(awards_str: str) -> dict:
        """Parse the OMDb Awards string into structured data.

        Examples:
            "Won 3 Oscars. 54 wins & 78 nominations total"
            "Nominated for 1 Oscar. 15 wins & 60 nominations total"
            "2 wins & 3 nominations"
        """
        if not awards_str or awards_str == "N/A":
            return {"text": None, "oscar_wins": 0, "oscar_noms": 0, "wins": 0, "nominations": 0}

        result = {"text": awards_str, "oscar_wins": 0, "oscar_noms": 0, "wins": 0, "nominations": 0}

        oscar_won = re.search(r"Won (\d+) Oscar", awards_str)
        if oscar_won:
            result["oscar_wins"] = int(oscar_won.group(1))

        oscar_nom = re.search(r"Nominated for (\d+) Oscar", awards_str)
        if oscar_nom:
            result["oscar_noms"] = int(oscar_nom.group(1))

        wins = re.search(r"(\d+) win", awards_str)
        if wins:
            result["wins"] = int(wins.group(1))

        noms = re.search(r"(\d+) nomination", awards_str)
        if noms:
            result["nominations"] = int(noms.group(1))

        return result
