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

## CI

A GitHub Actions workflow is included at `.github/workflows/ci.yml` which runs tests on push and PRs.

## Notes

- For local development, run `pip install flake8` if you want to lint locally to match CI.
- This project uses RapidAPI's API-Football. Be mindful of rate limits on free plans; the app limits to 30 matches per run and caches results in-memory for a configurable TTL.
- For production, consider using a shared cache (Redis) and better secrets management.
