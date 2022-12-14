import uuid, itertools, time
from collections import Counter
from diskcache import Cache 
from google.cloud import firestore

class Flock:
    def __init__(self, name=None, flock_id=None, db_type="cloud"):
        if db_type == "local":
            self.db_type = "local"
            self.db = Cache('.flock', statistics=True)
        else:
            self.db_type = "cloud"
            self.db = firestore.Client().collection('flock')

        
        self.flock = Counter()
        
        if flock_id:
            flock_data = self.get_from_db(flock_id)
        else:
            flock_data = None
            
        if flock_data:
            self.flock_id = flock_data["flock_id"]
            self.flock_name = flock_data.get("flock_name", "")
            self.flock_entries = flock_data["flock_entries"]
        else:
            self.flock_id = str(uuid.uuid4())
            self.flock_name = name
            self.flock_entries = []
        
    def get_from_db(self, key):
        if self.db_type == "local":
            return self.db.get(key, {})
        else:
            doc = self.db.document(key).get()
            if doc.exists:
                return doc.to_dict()
            else: 
                return {}

    def set_in_db(self, key, value):
        if self.db_type == "local":
            self.db[key] = value
            return
        else:
            print(key)
            print(value)
            self.db.document(key).set(value)

    def set_flock_name(self, name):
        self.flock_name = name

    def get_flock_id(self):
        return self.flock_id

    def add_to_flock(self, entities, primary_id=""):
        if not isinstance(entities, list):
            entities = [entities]
            if primary_id == "":
                primary_id = entities

        self.flock_entries.append({
            "entities" : entities,
            "timestamp" : time.time(),
            "primary_id" : primary_id
            })

        return None

    def remove_from_flock(self, index):
        self.flock_entries.pop(index)

    def sync_flock(self):
        if self.flock_id:
            flock_db = self.get_from_db(self.flock_id)
            flock_current = {
                "flock_id" : self.flock_id,
                "flock_entries" : self.flock_entries,
                "flock_name" : self.flock_name
            }
            self.set_in_db(self.flock_id, {
                **flock_db,
                **flock_current
            })

    def order_flock(self):
        """Order flock from history"""
        self.sync_flock()
        self.flock = Counter(list(itertools.chain(*[e["entities"] for e in self.flock_entries])))
        return self.flock

    def get_flock(self, details_function=None, most_common=None):
        """Retrieve flock and occurences with optional details"""
        self.order_flock()
        if details_function:
            flock_with_details = {}
            for id, _ in self.flock.most_common(most_common):
                flock_with_details[id] = {
                    "count" : self.flock[id],
                    **details_function(id)
                }
            return flock_with_details
        else:
            return dict(self.flock.most_common(most_common))

    def get_flock_works(self, get_works_function, unique_work_key="id", most_common=None):
        works = list(itertools.chain(*[get_works_function(id)*count for id, count in self.get_flock(most_common=most_common).items()]))
        works_count = Counter([w[unique_work_key] for w in works])

        return  {w[unique_work_key]: {
            **{"count": works_count[w[unique_work_key]]},
            **w
            } for w in works}.values()