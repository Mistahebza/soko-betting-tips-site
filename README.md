# Soko Betting Tips Site

[![CI](https://github.com/Mistahebza/soko-betting-tips-site/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Mistahebza/soko-betting-tips-site/actions/workflows/ci.yml)

A minimal Flask app that fetches football predictions from API-Football and displays daily tips.

## Features

- Fetches fixtures and predictions from API-Football (via RapidAPI)
- Lightweight in-memory cache to reduce API calls
- Simple responsive UI
- Tests and CI

## Getting started

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Export your API key (get one at https://dashboard.api-football.com/register):

```bash
export API_FOOTBALL_KEY="your_api_key_here"
```

(Optional) set cache TTL in seconds (default 3600):

```bash
export CACHE_TTL=3600
```

3. Run the app locally:

```bash
python -m app
# then open http://127.0.0.1:5000
```

## Tests

Run tests with pytest:

```bash
pytest
```

## Usage

After starting the app locally (`python -m app`), you can query the small API endpoints:

- List countries (no filters):

```bash
curl -s "http://127.0.0.1:5000/countries" | jq .
```

- Filter countries by name:

```bash
curl -s "http://127.0.0.1:5000/countries?name=england" | jq .
```

- Filter countries by code:

```bash
curl -s "http://127.0.0.1:5000/countries?code=fr" | jq .
```

- Search countries (partial name):

```bash
curl -s "http://127.0.0.1:5000/countries?search=engl" | jq .
```

- Get timezone info (API-Sports):

```bash
curl -s "http://127.0.0.1:5000/timezone" | jq .
```

- List available seasons:

```bash
curl -s "http://127.0.0.1:5000/seasons" | jq .
```

- Get team statistics for league/team/season:

```bash
curl -s "http://127.0.0.1:5000/teams/statistics?league=39&team=33&season=2019" | jq .
```

- Get team statistics filtered by end date:

```bash
curl -s "http://127.0.0.1:5000/teams/statistics?league=39&team=33&season=2019&date=2019-10-08" | jq .
```

- List fixtures (unfiltered):

```bash
curl -s "http://127.0.0.1:5000/fixtures" | jq .
```

- Filter fixtures by league and date:

```bash
curl -s "http://127.0.0.1:5000/fixtures?league=8&date=2025-10-25" | jq .
```

- Filter fixtures by team or date range:

```bash
curl -s "http://127.0.0.1:5000/fixtures?team=14&from=2025-10-01&to=2025-10-31" | jq .
```

- Live inplay scores (SportMonks):

```bash
curl -s "http://127.0.0.1:5000/livescores/inplay?include=participants;scores;periods;events;league.country;round" \
  -H "Authorization: Bearer $SPORTMONKS_KEY" | jq .
```

- Head-to-head fixtures (SportMonks):

```bash
curl -s "http://127.0.0.1:5000/fixtures/head-to-head/14/52?include=participants;league;scores;state;venue;events&limit=5" \
  -H "Authorization: Bearer $SPORTMONKS_KEY" | jq .
```

Note: provide a SportMonks API key via `export SPORTMONKS_KEY=...` for these endpoints.

### Test fixtures sample 🧪

A sample fixtures payload used by the unit tests is included at `tests/fixtures/fixtures_sample.json`.
You can run the test that uses this sample with:

```bash
pytest tests/test_fixtures_payload.py -q
```

This test verifies the `/fixtures` endpoint handles the sample payload and that filtering (e.g., `?team=14`) is forwarded to the upstream request.

## CI

A GitHub Actions workflow is included at `.github/workflows/ci.yml` which runs tests on push and PRs.

## Notes

- For local development, run `pip install flake8` if you want to lint locally to match CI.
- This project uses RapidAPI's API-Football. Be mindful of rate limits on free plans; the app limits to 30 matches per run and caches results in-memory for a configurable TTL.
- For production, consider using a shared cache (Redis) and better secrets management.
