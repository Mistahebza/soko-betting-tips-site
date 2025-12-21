import json
from datetime import datetime

import os
import sys
import pytest

# Ensure the project root is on sys.path so tests can import application code
sys.path.insert(0, os.getcwd())

from app import create_app, BASE_URL


def test_missing_api_key_shows_error():
    app = create_app({'API_KEY': None})
    client = app.test_client()

    resp = client.get('/')
    assert resp.status_code == 503
    assert b'API key for API-Football is not configured' in resp.data


def test_predictions_rendering():
    # Prepare fake fixture and prediction responses
    today = datetime.today().strftime('%Y-%m-%d')

    fixtures_payload = {
        "response": [
            {
                "fixture": {"id": 123},
                "teams": {"home": {"name": "Team A"}, "away": {"name": "Team B"}},
                "league": {"name": "Premier League", "country": "England"}
            }
        ]
    }

    prediction_payload = {
        "response": [
            {
                "predictions": {
                    "winner": {"name": "Team A"},
                    "advice": "Bet on Team A",
                    "goals": "2-1",
                    "under_over": "Over",
                    "percent": {"home": "60%", "draw": "25%", "away": "15%"}
                },
                "prediction": {"correct_score": "2-1"}
            }
        ]
    }

    # Create app and patch the session.get to return predictable mock responses
    app = create_app({'API_KEY': 'fake-key', 'CACHE_TTL': 3600})
    client = app.test_client()
    session = app.config['SESSION']

    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    fixtures_resp = MockResponse(200, fixtures_payload)
    prediction_resp = MockResponse(200, prediction_payload)

    def fake_get(url, headers=None, params=None, timeout=None):
        if url.endswith('/fixtures'):
            return fixtures_resp
        if url.endswith('/predictions'):
            return prediction_resp
        return MockResponse(404, {})

    session.get = fake_get

    resp = client.get('/')
    assert resp.status_code == 200
    body = resp.data.decode('utf-8')
    assert 'Team A vs Team B' in body
    assert 'Team A' in body
    assert '60% – 25% – 15%' in body
    assert 'Bet on Team A' in body


def test_fixtures_api_non_200_returns_error():
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
        if url.endswith('/fixtures'):
            return MockResponse(500, {})
        return MockResponse(404, {})

    session.get = fake_get

    resp = client.get('/')
    assert resp.status_code == 503
    assert b'API Error: 500' in resp.data


def test_predictions_empty_response_shows_no_predictions():
    fixtures_payload = {
        "response": [
            {
                "fixture": {"id": 222},
                "teams": {"home": {"name": "X"}, "away": {"name": "Y"}},
                "league": {"name": "Test League", "country": "Nowhere"}
            }
        ]
    }

    prediction_payload = {"response": []}

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    def fake_get(url, headers=None, params=None, timeout=None):
        if url.endswith('/fixtures'):
            return MockResponse(200, fixtures_payload)
        if url.endswith('/predictions'):
            return MockResponse(200, prediction_payload)
        return MockResponse(404, {})

    session.get = fake_get

    resp = client.get('/')
    assert resp.status_code == 200
    assert b'No predictions available today' in resp.data


def test_network_exception_returns_error():
    import requests as req

    app = create_app({'API_KEY': 'fake-key'})
    client = app.test_client()
    session = app.config['SESSION']

    def fake_get(url, headers=None, params=None, timeout=None):
        raise req.RequestException('connection error')

    session.get = fake_get

    resp = client.get('/')
    assert resp.status_code == 503
    assert b'Network error while fetching fixtures' in resp.data


def test_cache_expires_and_refetches():
    fixtures_payload_a = {
        "response": [
            {"fixture": {"id": 1}, "teams": {"home": {"name": "A"}, "away": {"name": "B"}}, "league": {"name": "L", "country": "C"}}
        ]
    }
    prediction_payload_a = {"response": [{"predictions": {"winner": {"name": "A"}, "advice": "A adv", "percent": {"home": "70%", "draw": "20%", "away": "10%"}}, "prediction": {"correct_score": "1-0"}}]}

    fixtures_payload_b = {
        "response": [
            {"fixture": {"id": 2}, "teams": {"home": {"name": "C"}, "away": {"name": "D"}}, "league": {"name": "L2", "country": "C2"}}
        ]
    }
    prediction_payload_b = {"response": [{"predictions": {"winner": {"name": "C"}, "advice": "C adv", "percent": {"home": "40%", "draw": "30%", "away": "30%"}}, "prediction": {"correct_score": "2-1"}}]}

    app = create_app({'API_KEY': 'fake-key', 'CACHE_TTL': 1})
    client = app.test_client()
    session = app.config['SESSION']

    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    # First responses
    def fake_get_first(url, headers=None, params=None, timeout=None):
        if url.endswith('/fixtures'):
            return MockResponse(200, fixtures_payload_a)
        if url.endswith('/predictions'):
            return MockResponse(200, prediction_payload_a)
        return MockResponse(404, {})

    session.get = fake_get_first
    r1 = client.get('/')
    assert r1.status_code == 200
    assert b'A vs B' in r1.data

    # Wait for TTL to expire
    import time
    time.sleep(1.1)

    # Now change session to return B responses
    def fake_get_second(url, headers=None, params=None, timeout=None):
        if url.endswith('/fixtures'):
            return MockResponse(200, fixtures_payload_b)
        if url.endswith('/predictions'):
            return MockResponse(200, prediction_payload_b)
        return MockResponse(404, {})

    session.get = fake_get_second
    r2 = client.get('/')
    assert r2.status_code == 200
    assert b'C vs D' in r2.data
