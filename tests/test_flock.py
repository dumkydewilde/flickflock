import pytest
from flickflock.flock import Flock, compute_entity_weight, cast_order_weight


def test_flock():
    flock = Flock(db_type="local")
    assert flock


def test_set_flock_name():
    flock = Flock(db_type="local")
    flock.set_flock_name("test_flock")
    assert flock.flock_name == "test_flock"


def test_cast_order_weight():
    assert cast_order_weight(0) == 1.0
    assert cast_order_weight(2) == 1.0
    assert cast_order_weight(5) == 0.8
    assert cast_order_weight(10) == 0.5
    assert cast_order_weight(20) == 0.3
    assert cast_order_weight(50) == 0.1
    assert cast_order_weight(None) == 0.5


def test_compute_entity_weight_directing():
    w = compute_entity_weight({"department": "Directing"})
    assert w == 5.0


def test_compute_entity_weight_lead_actor():
    w = compute_entity_weight({"department": "Acting", "order": 0})
    assert w == 3.0 * 1.0  # Acting weight * lead order


def test_compute_entity_weight_supporting_actor():
    w = compute_entity_weight({"department": "Acting", "order": 8})
    assert w == 3.0 * 0.5


def test_compute_entity_weight_unknown():
    w = compute_entity_weight({"department": "Catering"})
    assert w == 0.5  # default


def test_department_weights_directors_outrank_crew():
    director = compute_entity_weight({"department": "Directing"})
    crew = compute_entity_weight({"department": "Crew"})
    assert director > crew


def test_add_to_flock_weighted():
    flock = Flock(db_type="local")
    flock.add_to_flock([
        {"id": 1, "department": "Directing"},
        {"id": 2, "department": "Acting", "order": 0},
        {"id": 3, "department": "Crew"},
    ], primary_id="movie_1", source_type="movie")

    assert len(flock.flock_entries) == 1
    entities = flock.flock_entries[0]["entities"]
    assert len(entities) == 3
    # Director should have highest weight
    assert entities[0]["weight"] > entities[2]["weight"]


def test_add_to_flock_backward_compat():
    """Plain ID lists should still work."""
    flock = Flock(db_type="local")
    flock.add_to_flock([100, 200, 300], primary_id="test")

    entities = flock.flock_entries[0]["entities"]
    assert len(entities) == 3
    assert entities[0]["id"] == 100


def test_direct_person_ids_tracked():
    flock = Flock(db_type="local")
    flock.add_to_flock(
        [{"id": 42, "department": "Acting", "order": 0}],
        primary_id=42,
        source_type="person_direct",
    )
    assert 42 in flock.direct_person_ids


def test_score_flock_normalization():
    """A movie with many people shouldn't dominate one with few."""
    flock = Flock(db_type="local")

    # Movie A: 2 people
    flock.add_to_flock([
        {"id": 1, "department": "Directing"},
        {"id": 2, "department": "Acting", "order": 0},
    ], primary_id="A", source_type="movie")

    # Movie B: 100 people (all crew)
    big_cast = [{"id": i, "department": "Crew"} for i in range(100, 200)]
    flock.add_to_flock(big_cast, primary_id="B", source_type="movie")

    scores = flock.score_flock()
    # Person 1 (director of movie A) should still be competitive
    # despite movie B having 100 entries
    assert scores[1] > 0


def test_score_flock_directors_rank_higher():
    flock = Flock(db_type="local")
    flock.add_to_flock([
        {"id": 1, "department": "Directing"},
        {"id": 2, "department": "Crew"},
    ], primary_id="movie_1", source_type="movie")

    scores = flock.score_flock()
    assert scores[1] > scores[2]


def test_remove_selection():
    flock = Flock(db_type="local")
    flock.update_selection({"id": 10, "media_type": "movie"})
    flock.add_to_flock([{"id": 1, "department": "Acting", "order": 0}],
                       primary_id=10, source_type="movie")
    flock.update_selection({"id": 20, "media_type": "movie"})
    flock.add_to_flock([{"id": 2, "department": "Directing"}],
                       primary_id=20, source_type="movie")

    assert len(flock.selection) == 2
    assert len(flock.flock_entries) == 2

    flock.remove_selection(10)
    assert len(flock.selection) == 1
    assert flock.selection[0]["id"] == 20
    assert len(flock.flock_entries) == 1


def test_get_flock_works_penalizes_selected():
    """Works already in the selection should be penalized."""
    flock = Flock(db_type="local")
    flock.update_selection({"id": 99, "media_type": "movie"})
    flock.add_to_flock([
        {"id": 1, "department": "Directing"},
    ], primary_id=99, source_type="movie")

    def mock_works(person_id):
        return [
            {"id": 99, "title": "Already Selected Movie"},
            {"id": 100, "title": "New Discovery"},
        ]

    results = flock.get_flock_works(mock_works)
    # The new discovery should rank higher
    assert results[0]["id"] == 100
    assert results[1]["id"] == 99


def test_get_flock_works_direct_boost():
    """Directly selected people should boost their works."""
    flock = Flock(db_type="local")
    flock.add_to_flock(
        [{"id": 1, "department": "Acting", "order": 0}],
        primary_id=1,
        source_type="person_direct",
    )
    flock.add_to_flock(
        [{"id": 2, "department": "Acting", "order": 0}],
        primary_id="movie_X",
        source_type="movie",
    )

    def mock_works(person_id):
        if person_id == 1:
            return [{"id": 50, "title": "Direct Person's Obscure Film"}]
        return [{"id": 60, "title": "Other Film"}]

    results = flock.get_flock_works(mock_works)
    direct_work = next(w for w in results if w["id"] == 50)
    other_work = next(w for w in results if w["id"] == 60)
    # Direct person's work gets the 0.5 trust boost
    assert direct_work["count"] > other_work["count"]
