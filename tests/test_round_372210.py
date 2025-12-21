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


def test_round_372210_forwarded_and_response():
    path = os.path.join(os.getcwd(), 'tests', 'fixtures', 'round_372210.json')
    with open(path, 'r', encoding='utf-8') as fh:
        payload = json.load(fh)

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        # ensure round is forwarded
        assert params is not None
        assert str(params.get('round')) == '372210'
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/fixtures?round=372210')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('id') == 372210
    assert 'fixtures' in data
    assert any(f.get('id') == 19427612 for f in data['fixtures'])
