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


def test_head_to_head_basic():
    path = os.path.join(os.getcwd(), 'tests', 'fixtures', 'head_to_head_14_52.json')
    with open(path, 'r', encoding='utf-8') as fh:
        payload = json.load(fh)

    app = create_app({'SPORTMONKS_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        assert 'head-to-head/14/52' in url
        assert headers and 'Authorization' in headers
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/fixtures/head-to-head/14/52')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'data' in data
    assert len(data['data']) == 1


def test_head_to_head_with_include_and_params():
    path = os.path.join(os.getcwd(), 'tests', 'fixtures', 'head_to_head_14_52.json')
    with open(path, 'r', encoding='utf-8') as fh:
        payload = json.load(fh)

    app = create_app({'SPORTMONKS_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        assert params.get('include') == 'participants;league;scores;state;venue;events'
        assert params.get('limit') == '5'
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/fixtures/head-to-head/14/52?include=participants;league;scores;state;venue;events&limit=5')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'data' in data
