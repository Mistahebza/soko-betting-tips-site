import os
import sys

sys.path.insert(0, os.getcwd())

from app import create_app


def test_team_statistics_success():
    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    payload = {"response": {"team": {"id": 33, "name": "Team X"}, "league": {"id": 39}, "fixtures": {}}}

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        assert params.get('league') == 39
        assert params.get('team') == 33
        assert params.get('season') == 2019
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/teams/statistics?league=39&team=33&season=2019')
    assert resp.status_code == 200
    assert b'Team X' in resp.data


def test_team_statistics_with_date_filter():
    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    payload = {"response": {"team": {"id": 33, "name": "Team X"}, "league": {"id": 39}, "fixtures": {}}}

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        assert params.get('date') == '2019-10-08'
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/teams/statistics?league=39&team=33&season=2019&date=2019-10-08')
    assert resp.status_code == 200
    assert b'Team X' in resp.data


def test_team_statistics_api_non_200():
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

    resp = client.get('/teams/statistics?league=39&team=33&season=2019')
    assert resp.status_code == 503
    assert b'API Error: 500' in resp.data


def test_team_statistics_network_error():
    import requests as req

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        raise req.RequestException('connection error')

    session.get = fake_get

    resp = client.get('/teams/statistics?league=39&team=33&season=2019')
    assert resp.status_code == 503
    assert b'Network error while fetching team statistics' in resp.data
