import os
import sys
import json

sys.path.insert(0, os.getcwd())

from app import create_app


def test_fixtures_sample_payload_and_filters():
    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    # Load sample payload from test fixtures
    path = os.path.join(os.getcwd(), 'tests', 'fixtures', 'fixtures_sample.json')
    with open(path, 'r', encoding='utf-8') as fh:
        payload = json.load(fh)

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    # Basic full-response test
    def fake_get(url, headers=None, params=None, timeout=None):
        return MockResponse(200, payload)

    session.get = fake_get

    resp = client.get('/fixtures')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'response' in data
    assert len(data['response']) >= 3

    names = [f.get('name', '') for f in data['response']]
    assert any('Manchester United' in n for n in names)
    assert any('Brentford vs Liverpool' in n for n in names)

    # Filter by team id (Manchester United id: 14)
    def fake_get_filter(url, headers=None, params=None, timeout=None):
        # The fixtures implementation should pass the numeric team param
        assert params.get('team') == 14
        # Return only the Manchester United fixture as a realistic filtered response
        filtered = [f for f in payload['response'] if any(p.get('id') == 14 for p in f.get('participants', []))]
        return MockResponse(200, {'response': filtered})

    session.get = fake_get_filter
    resp2 = client.get('/fixtures?team=14')
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert len(data2['response']) >= 1
    assert any('Manchester United' in f.get('name', '') for f in data2['response'])
