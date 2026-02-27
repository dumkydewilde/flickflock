import pytest
from flickflock.bookmarks import BookmarkList


def test_create_bookmark_list():
    bl = BookmarkList(user_id="test-user-1")
    assert bl.user_id == "test-user-1"
    assert bl.list_id
    assert bl.items == []


def test_add_bookmark():
    bl = BookmarkList(user_id="test-user-2")
    bl.add({"id": 27205, "title": "Inception", "media_type": "movie", "poster_path": "/abc.jpg"})
    assert len(bl.items) == 1
    assert bl.items[0]["id"] == 27205


def test_add_duplicate_bookmark():
    bl = BookmarkList(user_id="test-user-3")
    item = {"id": 27205, "title": "Inception", "media_type": "movie"}
    bl.add(item)
    bl.add(item)
    assert len(bl.items) == 1


def test_remove_bookmark():
    bl = BookmarkList(user_id="test-user-4")
    bl.add({"id": 27205, "title": "Inception", "media_type": "movie"})
    bl.add({"id": 4608, "title": "30 Rock", "media_type": "tv"})
    assert len(bl.items) == 2

    bl.remove(27205, "movie")
    assert len(bl.items) == 1
    assert bl.items[0]["id"] == 4608


def test_remove_nonexistent_bookmark():
    bl = BookmarkList(user_id="test-user-5")
    bl.add({"id": 27205, "title": "Inception", "media_type": "movie"})
    bl.remove(99999, "movie")
    assert len(bl.items) == 1


def test_persistence_round_trip():
    bl = BookmarkList(user_id="test-user-persist")
    bl.add({"id": 27205, "title": "Inception", "media_type": "movie"})
    bl.add({"id": 4608, "title": "30 Rock", "media_type": "tv"})
    saved_list_id = bl.list_id

    # Reload by list_id
    loaded = BookmarkList(list_id=saved_list_id)
    assert loaded.list_id == saved_list_id
    assert loaded.user_id == "test-user-persist"
    assert len(loaded.items) == 2


def test_load_by_user_id():
    bl = BookmarkList(user_id="test-user-load")
    bl.add({"id": 100, "title": "Film A", "media_type": "movie"})

    # Load by user_id (no list_id)
    loaded = BookmarkList(user_id="test-user-load")
    assert loaded.list_id == bl.list_id
    assert len(loaded.items) == 1


def test_to_dict():
    bl = BookmarkList(user_id="test-user-dict")
    bl.add({"id": 1, "title": "Test", "media_type": "movie"})
    d = bl.to_dict()
    assert d["list_id"] == bl.list_id
    assert d["user_id"] == "test-user-dict"
    assert len(d["items"]) == 1


def test_different_media_types_same_id():
    """Movie and TV with the same numeric ID should be treated as different items."""
    bl = BookmarkList(user_id="test-user-media-types")
    bl.add({"id": 100, "title": "Movie 100", "media_type": "movie"})
    bl.add({"id": 100, "title": "Show 100", "media_type": "tv"})
    assert len(bl.items) == 2

    bl.remove(100, "movie")
    assert len(bl.items) == 1
    assert bl.items[0]["media_type"] == "tv"
