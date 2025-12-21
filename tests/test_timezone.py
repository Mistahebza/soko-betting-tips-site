import os
import sys

sys.path.insert(0, os.getcwd())

from app import create_app


def test_timezone_success():
    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    payload = {"response": {"timezone": "Europe/London"}}

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/timezone')
    assert resp.status_code == 200
    assert b'Europe/London' in resp.data


def test_timezone_non_200_returns_error():
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

    resp = client.get('/timezone')
    assert resp.status_code == 503
    assert b'API Error: 500' in resp.data


def test_timezone_network_error():
    import requests as req

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        raise req.RequestException('connection error')

    session.get = fake_get

    resp = client.get('/timezone')
    assert resp.status_code == 503
    assert b'Network error while fetching timezone' in resp.data
