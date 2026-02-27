import uuid, json, time, sqlite3, os

_DB_PATH = os.environ.get(
    "FLOCK_DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "flock.db"),
)


def _get_db():
    db_dir = os.path.dirname(_DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookmark_lists (
            list_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            items TEXT NOT NULL DEFAULT '[]',
            updated_at REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_bookmark_lists_user_id
        ON bookmark_lists(user_id)
    """)
    conn.commit()
    return conn


class BookmarkList:
    """A shareable list of bookmarked movies/shows tied to a user_id."""

    def __init__(self, user_id=None, list_id=None):
        self.items = []

        if list_id:
            data = self._load_by_list_id(list_id)
            if data:
                self.list_id = data["list_id"]
                self.user_id = data["user_id"]
                self.items = data["items"]
                return

        # No existing list found by list_id; try to find by user_id
        if user_id:
            data = self._load_by_user_id(user_id)
            if data:
                self.list_id = data["list_id"]
                self.user_id = data["user_id"]
                self.items = data["items"]
                return

        # Create new
        self.list_id = str(uuid.uuid4())
        self.user_id = user_id or str(uuid.uuid4())

    def _load_by_list_id(self, list_id):
        conn = _get_db()
        try:
            row = conn.execute(
                "SELECT list_id, user_id, items FROM bookmark_lists WHERE list_id = ?",
                (list_id,),
            ).fetchone()
            if row:
                return {
                    "list_id": row[0],
                    "user_id": row[1],
                    "items": json.loads(row[2]),
                }
            return None
        finally:
            conn.close()

    def _load_by_user_id(self, user_id):
        conn = _get_db()
        try:
            row = conn.execute(
                "SELECT list_id, user_id, items FROM bookmark_lists WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
                (user_id,),
            ).fetchone()
            if row:
                return {
                    "list_id": row[0],
                    "user_id": row[1],
                    "items": json.loads(row[2]),
                }
            return None
        finally:
            conn.close()

    def add(self, item):
        """Add a bookmark item (dict with id, title, media_type, poster_path, etc.)."""
        if any(b["id"] == item["id"] and b.get("media_type") == item.get("media_type") for b in self.items):
            return  # already bookmarked
        self.items.append(item)
        self._save()

    def remove(self, media_id, media_type):
        """Remove a bookmark by media id and type."""
        self.items = [
            b for b in self.items
            if not (b["id"] == media_id and b.get("media_type") == media_type)
        ]
        self._save()

    def to_dict(self):
        return {
            "list_id": self.list_id,
            "user_id": self.user_id,
            "items": self.items,
        }

    def _save(self):
        conn = _get_db()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO bookmark_lists (list_id, user_id, items, updated_at) VALUES (?, ?, ?, ?)",
                (self.list_id, self.user_id, json.dumps(self.items), time.time()),
            )
            conn.commit()
        finally:
            conn.close()
