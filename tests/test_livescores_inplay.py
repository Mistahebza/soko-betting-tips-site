import os
import sys
import json

sys.path.insert(0, os.getcwd())

from app import create_app


class MockResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_livescores_inplay_basic():
    path = os.path.join(os.getcwd(), 'tests', 'fixtures', 'livescores_sample.json')
    with open(path, 'r', encoding='utf-8') as fh:
        payload = json.load(fh)

    app = create_app({'SPORTMONKS_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        assert 'include' in params or params == {}
        # verify Authorization header is set
        assert headers and 'Authorization' in headers
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/livescores/inplay?include=participants;scores;events;league.country;round')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'data' in data
    assert len(data['data']) == 1


def test_livescores_inplay_filters_forwarded():
    path = os.path.join(os.getcwd(), 'tests', 'fixtures', 'livescores_sample.json')
    with open(path, 'r', encoding='utf-8') as fh:
        payload = json.load(fh)

    app = create_app({'SPORTMONKS_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        # ensure custom params are forwarded
        assert params.get('team') == '14'
        assert params.get('include') == 'participants;scores'
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/livescores/inplay?team=14&include=participants;scores')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'data' in data
