import uuid, itertools, time, math, json, sqlite3, os
from collections import Counter, defaultdict

# Department weights: how much creative influence does this role have
DEPARTMENT_WEIGHTS = {
    "Directing": 5.0,
    "Writing": 4.0,
    "Acting": 3.0,
    "Production": 2.0,
    "Sound": 1.5,
    "Camera": 1.0,
    "Editing": 1.0,
    "Art": 0.5,
    "Crew": 0.3,
}
DEFAULT_DEPARTMENT_WEIGHT = 0.5

_DB_PATH = os.environ.get("FLOCK_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "flock.db"))


def _get_db():
    db_dir = os.path.dirname(_DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS flocks (
            flock_id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    conn.commit()
    return conn


def cast_order_weight(order):
    """Lead actors matter more than background cast."""
    if order is None:
        return 0.5
    if order <= 2:
        return 1.0
    elif order <= 5:
        return 0.8
    elif order <= 10:
        return 0.5
    elif order <= 20:
        return 0.3
    else:
        return 0.1


def compute_entity_weight(entity):
    """Compute importance weight for a person based on their role."""
    department = entity.get("department", entity.get("known_for_department", ""))
    base_weight = DEPARTMENT_WEIGHTS.get(department, DEFAULT_DEPARTMENT_WEIGHT)

    if department == "Acting" or "order" in entity:
        base_weight *= cast_order_weight(entity.get("order"))

    return base_weight


class Flock:
    def __init__(self, name=None, flock_id=None, db_type=None):
        self.flock = {}
        self.direct_person_ids = set()

        if flock_id:
            flock_data = self._get_from_db(flock_id)
        else:
            flock_data = None

        if flock_data:
            self.flock_id = flock_data["flock_id"]
            self.flock_name = flock_data.get("flock_name", "")
            self.flock_entries = flock_data["flock_entries"]
            self.selection = flock_data.get("selection", [])
            self.direct_person_ids = set(flock_data.get("direct_person_ids", []))
        else:
            self.flock_id = str(uuid.uuid4())
            self.flock_name = name
            self.flock_entries = []
            self.selection = []

    def _get_from_db(self, key):
        conn = _get_db()
        try:
            row = conn.execute("SELECT data FROM flocks WHERE flock_id = ?", (key,)).fetchone()
            return json.loads(row[0]) if row else {}
        finally:
            conn.close()

    def _set_in_db(self, key, value):
        conn = _get_db()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO flocks (flock_id, data, updated_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), time.time()),
            )
            conn.commit()
        finally:
            conn.close()

    def set_flock_name(self, name):
        self.flock_name = name

    def get_flock_id(self):
        return self.flock_id

    def update_selection(self, selection):
        self.selection.append(selection)

    def get_selection(self):
        return self.selection

    def remove_selection(self, selection_id):
        self.selection = [s for s in self.selection if s.get("id") != selection_id]
        self.flock_entries = [
            e for e in self.flock_entries if e.get("primary_id") != selection_id
        ]
        self.direct_person_ids.discard(selection_id)

    def add_to_flock(self, entities, primary_id="", source_type="movie"):
        """Add entities to the flock.

        entities: list of dicts with 'id' and optionally 'department', 'order',
                  'known_for_department' — OR list of plain IDs (backward compat)
        primary_id: the selection that led to this entry
        source_type: "movie", "tv", "person_direct", "person_transitive"
        """
        if not isinstance(entities, list):
            entities = [entities]

        # Normalize to weighted entity dicts
        weighted = []
        for e in entities:
            if isinstance(e, dict):
                weighted.append({
                    "id": e["id"],
                    "weight": compute_entity_weight(e),
                    "department": e.get("department", e.get("known_for_department", "")),
                })
            else:
                weighted.append({
                    "id": e,
                    "weight": DEFAULT_DEPARTMENT_WEIGHT,
                    "department": "",
                })

        if source_type == "person_direct":
            for e in weighted:
                self.direct_person_ids.add(e["id"])

        self.flock_entries.append({
            "entities": weighted,
            "timestamp": time.time(),
            "primary_id": primary_id,
            "source_type": source_type,
        })

    def remove_from_flock(self, index):
        self.flock_entries.pop(index)

    def sync_flock(self):
        if self.flock_id:
            flock_current = {
                "flock_id": self.flock_id,
                "flock_entries": self.flock_entries,
                "flock_name": self.flock_name,
                "selection": self.selection,
                "direct_person_ids": list(self.direct_person_ids),
            }
            self._set_in_db(self.flock_id, flock_current)

    def score_flock(self):
        """Score flock members using weighted, normalized scoring with TF-IDF."""
        self.sync_flock()

        person_scores = defaultdict(float)
        person_entry_count = defaultdict(int)

        for entry in self.flock_entries:
            entities = entry.get("entities", [])

            # Backward compat: old entries stored plain ID lists
            if entities and not isinstance(entities[0], dict):
                entities = [{"id": e, "weight": DEFAULT_DEPARTMENT_WEIGHT} for e in entities]

            # Normalize: each selection contributes a budget of 1.0
            total_weight = sum(e.get("weight", DEFAULT_DEPARTMENT_WEIGHT) for e in entities)
            if total_weight == 0:
                continue

            for e in entities:
                person_id = e["id"] if isinstance(e, dict) else e
                raw_weight = e.get("weight", DEFAULT_DEPARTMENT_WEIGHT)
                normalized = raw_weight / total_weight
                person_scores[person_id] += normalized
                person_entry_count[person_id] += 1

        # TF-IDF: penalize people who appear in everything
        num_entries = max(len(self.flock_entries), 1)
        for person_id in list(person_scores.keys()):
            tf = person_entry_count[person_id] / num_entries
            idf = math.log(1 + num_entries / person_entry_count[person_id])
            person_scores[person_id] *= (tf * idf)

        self.flock = dict(
            sorted(person_scores.items(), key=lambda x: x[1], reverse=True)
        )
        return self.flock

    def get_flock(self, details_function=None, most_common=None):
        """Retrieve flock and scores with optional details."""
        self.score_flock()

        items = list(self.flock.items())
        if most_common:
            items = items[:most_common]

        if details_function:
            flock_with_details = {}
            for person_id, score in items:
                flock_with_details[person_id] = {
                    "count": round(score, 4),
                    **details_function(person_id),
                }
            return flock_with_details
        else:
            return {pid: round(score, 4) for pid, score in items}

    def get_flock_works(self, get_works_function, unique_work_key="id", most_common=None):
        """Score works by weighted flock member collaboration with direct-selection boost."""
        flock_scores = self.get_flock(most_common=most_common)

        works_by_id = {}
        works_member_scores = defaultdict(dict)  # {work_id: {person_id: score}}
        works_direct_boost = defaultdict(float)

        selected_work_ids = set()
        for sel in self.selection:
            if sel.get("media_type") != "person":
                selected_work_ids.add(sel.get("id"))

        for person_id, score in flock_scores.items():
            works = get_works_function(person_id)
            for w in works:
                wid = w[unique_work_key]
                if wid not in works_by_id:
                    works_by_id[wid] = w
                works_member_scores[wid][person_id] = score

                if person_id in self.direct_person_ids:
                    works_direct_boost[wid] += 0.5

        results = []
        for wid, work_data in works_by_id.items():
            weighted_score = sum(works_member_scores[wid].values())
            direct_boost = works_direct_boost.get(wid, 0)
            penalty = 0.1 if wid in selected_work_ids else 1.0

            score = (weighted_score + direct_boost) * penalty

            # Top connected members sorted by their flock score
            connected = sorted(
                works_member_scores[wid].keys(),
                key=lambda pid: works_member_scores[wid][pid],
                reverse=True,
            )

            results.append({
                "count": round(score, 2),
                "connected_member_ids": connected[:5],
                **work_data,
            })

        return sorted(results, key=lambda x: x["count"], reverse=True)
