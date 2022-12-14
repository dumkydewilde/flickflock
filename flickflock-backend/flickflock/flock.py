import uuid, itertools
from collections import Counter
from diskcache import Cache 



class Flock:
    def __init__(self, name=None, flock_id=None):
        self.db = Cache('.flock', statistics=True)
        self.flock = Counter()
        
        if flock_id:
            flock_data = self.db.get(flock_id)
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
        

    def set_flock_name(self, name):
        self.flock_name = name

    def get_flock_id(self):
        return self.flock_id

    def add_to_flock(self, entities):
        if isinstance(entities, list):
            self.flock_entries.append(entities)
        else:
            self.flock_entries.append([entities])

        return None

    def remove_from_flock(self, index):
        self.flock_entries.pop(index)

    def sync_flock(self):
        if self.flock_id:
            flock_db = self.db.get(self.flock_id, {})
            flock_current = {
                "flock_id" : self.flock_id,
                "flock_entries" : self.flock_entries,
                "flock_name" : self.flock_name
            }
            self.db[self.flock_id] ={
                **flock_db,
                **flock_current
            }

    def order_flock(self):
        """Order flock from history"""
        self.flock_entries = [list(e) for e in set(tuple(e) for e in self.flock_entries)] # only unique entries
        self.sync_flock()
        self.flock = Counter(list(itertools.chain(*self.flock_entries)))
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