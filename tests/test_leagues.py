import os
import sys

sys.path.insert(0, os.getcwd())

from app import create_app


def test_leagues_by_id_and_season():
    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    payload = {"response": [{"league": {"id": 39, "name": "Premier League"}, "season": 2019}]}

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        assert params.get('id') == 39 or params.get('season') == 2019
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/leagues?id=39&season=2019')
    assert resp.status_code == 200
    assert b'Premier League' in resp.data


def test_leagues_by_name_and_country():
    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    payload = {"response": [{"league": {"id": 61, "name": "Ligue 1"}, "country": "France"}]}

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        assert params.get('name') == 'premier league' or params.get('country') == 'england'
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/leagues?name=premier%20league')
    assert resp.status_code == 200

    resp = client.get('/leagues?country=england')
    assert resp.status_code == 200


def test_leagues_search_and_type_and_current():
    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    payload = {"response": [{"league": {"id": 100, "name": "Some League"}}]}

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        assert params.get('search') == 'premier league' or params.get('type') == 'league' or params.get('current') in ('true', '1', 'True')
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/leagues?search=premier%20league')
    assert resp.status_code == 200

    resp = client.get('/leagues?type=league')
    assert resp.status_code == 200

    resp = client.get('/leagues?current=true')
    assert resp.status_code == 200


def test_leagues_team_and_last_and_non_200():
    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get_ok(url, headers=None, params=None, timeout=None):
        assert params.get('team') == 33 or params.get('last') == 99
        return MockResponse(200, {"response": [{"league": {"id": 10, "name": "Team League"}}]})

    def fake_get_err(url, headers=None, params=None, timeout=None):
        return MockResponse(500, {})

    session.get = fake_get_ok
    resp = client.get('/leagues?team=33')
    assert resp.status_code == 200

    session.get = fake_get_ok
    resp = client.get('/leagues?last=99')
    assert resp.status_code == 200

    session.get = fake_get_err
    resp = client.get('/leagues')
    assert resp.status_code == 503
    assert b'API Error: 500' in resp.data
