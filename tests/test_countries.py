import os
import sys

sys.path.insert(0, os.getcwd())

from app import create_app


def test_countries_name_filter():
    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    payload = {"response": [{"name": "England", "code": "ENG"}]}

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        assert params.get('name') == 'england'
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/countries?name=england')
    assert resp.status_code == 200
    assert b'England' in resp.data


def test_countries_code_filter():
    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    payload = {"response": [{"name": "France", "code": "FR"}]}

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        assert params.get('code') == 'fr'
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/countries?code=fr')
    assert resp.status_code == 200
    assert b'France' in resp.data


def test_countries_search_filter():
    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    payload = {"response": [{"name": "England", "code": "ENG"}]}

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        assert params.get('search') == 'engl'
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/countries?search=engl')
    assert resp.status_code == 200
    assert b'England' in resp.data


def test_countries_api_non_200():
    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        return MockResponse(500, {})

    session.get = fake_get

    resp = client.get('/countries')
    assert resp.status_code == 503
    assert b'API Error: 500' in resp.data
