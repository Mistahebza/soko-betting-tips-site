import os
import sys

sys.path.insert(0, os.getcwd())

from app import create_app


def test_fixtures_success():
    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    payload = {"response": [{"id": 1, "name": "Test Match"}]}

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/fixtures')
    assert resp.status_code == 200
    assert b'Test Match' in resp.data


def test_fixtures_with_filters():
    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    payload = {"response": [{"id": 2, "name": "Filtered Match"}]}

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        assert params.get('league') == 8
        assert params.get('date') == '2025-10-25'
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/fixtures?league=8&date=2025-10-25')
    assert resp.status_code == 200
    assert b'Filtered Match' in resp.data


def test_fixtures_non_200():
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

    resp = client.get('/fixtures')
    assert resp.status_code == 503
    assert b'API Error: 500' in resp.data


def test_fixtures_network_error():
    import requests as req

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        raise req.RequestException('conn')

    session.get = fake_get

    resp = client.get('/fixtures')
    assert resp.status_code == 503
    assert b'Network error while fetching fixtures' in resp.data
