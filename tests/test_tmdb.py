import pytest, requests
from flickflock.tmdb import TMDB

class MockTMDBResponse:
    @staticmethod
    def json():
        return {"results": []}

@pytest.fixture
def tmdb_os_settings(monkeypatch):
    monkeypatch.setenv("TMDB_API_KEY", "123abc_env")
    return TMDB()

@pytest.fixture
def tmdb_init_settings():
    return TMDB(api_key="123abc", base_url="test_url")

def test_tmdb(tmdb_os_settings):
    assert tmdb_os_settings

def test_tmdb_set_api_key(tmdb_init_settings):
    assert tmdb_init_settings.api_key == "123abc"

def test_tmdb_set_base_url(tmdb_init_settings):
    assert tmdb_init_settings.base_url == "test_url"

def test_tmdb_authenticate_init_api_key(tmdb_init_settings):
    assert tmdb_init_settings.api_key == "123abc"
    assert tmdb_init_settings.is_authenticated == True

def test_tmdb_authenticate_env_api_key(tmdb_os_settings):
    assert tmdb_os_settings.api_key == "123abc_env"
    assert tmdb_os_settings.is_authenticated == True

def test_tmdb_request(monkeypatch):
    def mock_request(*args, **kwargs):
        return MockTMDBResponse()

    monkeypatch.setattr(requests, "request", mock_request)
    
    tmdb = TMDB()
    result = tmdb.request("path/test")
    assert "results" in result.keys()
    assert isinstance(result["results"], list)