import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import Flask, render_template, current_app

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _create_session(retries=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504)):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(["GET", "POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def create_app(test_config=None):
    app = Flask(__name__, static_folder='static')

    # Configuration
    api_key = None
    if test_config and 'API_KEY' in test_config:
        api_key = test_config['API_KEY']
    else:
        api_key = os.getenv('API_FOOTBALL_KEY')

    app.config['API_KEY'] = api_key
    app.config['BASE_URL'] = BASE_URL
    app.config['SESSION'] = _create_session()
    # simple in-memory cache with a timestamp; TTL is configurable via CACHE_TTL (seconds)
    app.config['CACHE'] = {"data": None, "timestamp": None}
    # default TTL (seconds) for cache; can be overridden via env or test_config
    app.config['CACHE_TTL'] = int(os.getenv('CACHE_TTL', '3600'))
    if test_config and 'CACHE_TTL' in test_config:
        app.config['CACHE_TTL'] = int(test_config['CACHE_TTL'])

    @app.context_processor
    def inject_today():
        today_str = datetime.today().strftime('%A, %B %d, %Y')
        return {'today_str': today_str}

    def get_predictions():
        api_key = current_app.config.get('API_KEY')
        if not api_key:
            return {'error': 'API key for API-Football is not configured. Please set API_FOOTBALL_KEY.'}

        cache = current_app.config['CACHE']
        cached = cache.get('data')
        ts = cache.get('timestamp')
        ttl = current_app.config.get('CACHE_TTL', 3600)
        if cached and ts and (datetime.now() - ts).total_seconds() < ttl:
            return cached

        session = current_app.config['SESSION']
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }

        today = datetime.today().strftime('%Y-%m-%d')
        fixtures_url = f"{current_app.config['BASE_URL']}/fixtures"
        params = {"date": today}

        try:
            resp = session.get(fixtures_url, headers=headers, params=params, timeout=10)
        except requests.RequestException as e:
            logger.exception("Error fetching fixtures")
            return {'error': f'Network error while fetching fixtures: {e}'}

        if resp.status_code != 200:
            logger.warning('Fixtures API responded with status %s', resp.status_code)
            return {'error': f'API Error: {resp.status_code} - Unable to fetch fixtures'}

        fixtures = resp.json().get('response', [])
        league_predictions = defaultdict(list)

        # Limit to 30 matches to stay safe on free tier
        for fixture in fixtures[:30]:
            fixture_id = fixture['fixture']['id']
            home = fixture['teams']['home']['name']
            away = fixture['teams']['away']['name']
            league_name = fixture['league']['name']
            country = fixture['league']['country']
            league_key = f"{country} - {league_name}"

            # Fetch prediction for this match
            pred_url = f"{current_app.config['BASE_URL']}/predictions"
            pred_params = {"fixture": fixture_id}

            try:
                pred_resp = session.get(pred_url, headers=headers, params=pred_params, timeout=10)
            except requests.RequestException:
                logger.exception("Failed to fetch prediction for fixture %s", fixture_id)
                continue

            if pred_resp.status_code == 200 and pred_resp.json().get('response'):
                data = pred_resp.json()['response'][0]
                pred = data.get('predictions', {})

                winner = pred.get('winner', {}).get('name', 'N/A')
                advice = pred.get('advice', 'Check both teams')
                goals_pred = pred.get('goals', 'N/A')
                under_over = pred.get('under_over', 'N/A')
                correct_score = data.get('prediction', {}).get('correct_score', 'N/A')

                probs = pred.get('percent', {})
                win_home = probs.get('home', 'N/A')
                win_draw = probs.get('draw', 'N/A')
                win_away = probs.get('away', 'N/A')

                league_predictions[league_key].append({
                    "match": f"{home} vs {away}",
                    "winner": winner,
                    "advice": advice,
                    "win_probs": f"{win_home} – {win_draw} – {win_away}",
                    "correct_score": correct_score,
                    "goals": goals_pred,
                    "under_over": under_over
                })

        cache['data'] = league_predictions
        cache['timestamp'] = datetime.now()
        return league_predictions

    def get_timezone():
        """Fetch timezone information from API-Sports / timezone endpoint.

        Reads `API_SPORTS_KEY` from env; if not set falls back to `API_FOOTBALL_KEY`.
        Uses same session and caching mechanism as predictions.
        Returns dict on success or dict with `error` key on failure.
        """
        key = os.getenv('API_SPORTS_KEY') or current_app.config.get('API_KEY')
        if not key:
            return {'error': 'API key for API-Sports is not configured. Please set API_SPORTS_KEY or API_FOOTBALL_KEY.'}

        cache = current_app.config['CACHE']
        cached = cache.get('timezone')
        ts = cache.get('timestamp')
        ttl = current_app.config.get('CACHE_TTL', 3600)
        if cached and ts and (datetime.now() - ts).total_seconds() < ttl:
            return cached

        session = current_app.config['SESSION']
        headers = {"x-apisports-key": key}
        url = 'https://v3.football.api-sports.io/timezone'

        try:
            resp = session.get(url, headers=headers, timeout=10)
        except requests.RequestException as e:
            logger.exception('Error fetching timezone')
            return {'error': f'Network error while fetching timezone: {e}'}

        if resp.status_code != 200:
            logger.warning('Timezone API responded with status %s', resp.status_code)
            return {'error': f'API Error: {resp.status_code} - Unable to fetch timezone'}

        payload = resp.json()
        cache['timezone'] = payload
        cache['timestamp'] = datetime.now()
        return payload

    @app.route('/timezone')
    def timezone():
        data = get_timezone()
        if isinstance(data, dict) and 'error' in data:
            return render_template('error.html', message=data['error']), 503
        # Return JSON response for API consumers
        from flask import jsonify

        return jsonify(data)

    def get_countries(name=None, code=None, search=None):
        """Fetch countries from API-Sports /countries endpoint.

        Accepts optional filters: `name`, `code`, `search`.
        Returns dict or dict with `error` key on failure.
        """
        key = os.getenv('API_SPORTS_KEY') or current_app.config.get('API_KEY')
        if not key:
            return {'error': 'API key for API-Sports is not configured. Please set API_SPORTS_KEY or API_FOOTBALL_KEY.'}

        cache = current_app.config['CACHE']
        # create a cache key for countries queries
        query_key = f"countries:{name or ''}:{code or ''}:{search or ''}"
        cached = cache.get(query_key)
        ts = cache.get('timestamp')
        ttl = current_app.config.get('CACHE_TTL', 3600)
        if cached and ts and (datetime.now() - ts).total_seconds() < ttl:
            return cached

        session = current_app.config['SESSION']
        headers = {"x-apisports-key": key}
        url = 'https://v3.football.api-sports.io/countries'
        params = {}
        if name:
            params['name'] = name
        if code:
            params['code'] = code
        if search:
            params['search'] = search

        try:
            resp = session.get(url, headers=headers, params=params, timeout=10)
        except requests.RequestException as e:
            logger.exception('Error fetching countries')
            return {'error': f'Network error while fetching countries: {e}'}

        if resp.status_code != 200:
            logger.warning('Countries API responded with status %s', resp.status_code)
            return {'error': f'API Error: {resp.status_code} - Unable to fetch countries'}

        payload = resp.json()
        cache[query_key] = payload
        cache['timestamp'] = datetime.now()
        return payload

    @app.route('/countries')
    def countries():
        # Read query params
        from flask import request, jsonify

        name = request.args.get('name')
        code = request.args.get('code')
        search = request.args.get('search')

        data = get_countries(name=name, code=code, search=search)
        if isinstance(data, dict) and 'error' in data:
            return render_template('error.html', message=data['error']), 503
        return jsonify(data)

    def get_leagues(id=None, name=None, country=None, code=None, season=None, team=None, search=None, type=None, current=None, last=None):
        """Fetch leagues from API-Sports /leagues endpoint supporting multiple filters.

        Accepts optional params: id, name, country, code, season, team, search, type, current, last.
        Returns dict payload or dict with `error` key on failure.
        """
        key = os.getenv('API_SPORTS_KEY') or current_app.config.get('API_KEY')
        if not key:
            return {'error': 'API key for API-Sports is not configured. Please set API_SPORTS_KEY or API_FOOTBALL_KEY.'}

        cache = current_app.config['CACHE']
        query_key = f"leagues:{id or ''}:{name or ''}:{country or ''}:{code or ''}:{season or ''}:{team or ''}:{search or ''}:{type or ''}:{current or ''}:{last or ''}"
        cached = cache.get(query_key)
        ts = cache.get('timestamp')
        ttl = current_app.config.get('CACHE_TTL', 3600)
        if cached and ts and (datetime.now() - ts).total_seconds() < ttl:
            return cached

        session = current_app.config['SESSION']
        headers = {"x-apisports-key": key}
        url = 'https://v3.football.api-sports.io/leagues'
        params = {}
        if id is not None:
            params['id'] = id
        if name:
            params['name'] = name
        if country:
            params['country'] = country
        if code:
            params['code'] = code
        if season is not None:
            params['season'] = season
        if team is not None:
            params['team'] = team
        if search:
            params['search'] = search
        if type:
            params['type'] = type
        if current is not None:
            # expect true/false or string 'true'
            params['current'] = str(current).lower()
        if last is not None:
            params['last'] = last

        try:
            resp = session.get(url, headers=headers, params=params, timeout=10)
        except requests.RequestException as e:
            logger.exception('Error fetching leagues')
            return {'error': f'Network error while fetching leagues: {e}'}

        if resp.status_code != 200:
            logger.warning('Leagues API responded with status %s', resp.status_code)
            return {'error': f'API Error: {resp.status_code} - Unable to fetch leagues'}

        payload = resp.json()
        cache[query_key] = payload
        cache['timestamp'] = datetime.now()
        return payload

    @app.route('/leagues')
    def leagues():
        from flask import request, jsonify

        id = request.args.get('id')
        name = request.args.get('name')
        country = request.args.get('country')
        code = request.args.get('code')
        season = request.args.get('season')
        team = request.args.get('team')
        search = request.args.get('search')
        typ = request.args.get('type')
        current = request.args.get('current')
        last = request.args.get('last')

        # normalize types
        if season is not None:
            try:
                season = int(season)
            except ValueError:
                season = season
        if id is not None:
            try:
                id = int(id)
            except ValueError:
                id = id
        if team is not None:
            try:
                team = int(team)
            except ValueError:
                team = team
        if last is not None:
            try:
                last = int(last)
            except ValueError:
                last = last
        if current is not None:
            current = current.lower() in ('1', 'true', 'yes')

        data = get_leagues(id=id, name=name, country=country, code=code, season=season, team=team, search=search, type=typ, current=current, last=last)
        if isinstance(data, dict) and 'error' in data:
            return render_template('error.html', message=data['error']), 503
        return jsonify(data)

    @app.route('/')
    def home():
        predictions = get_predictions()
        if isinstance(predictions, dict) and 'error' in predictions:
            return render_template('error.html', message=predictions['error']), 503

        return render_template('index.html', predictions=predictions)

    return app


# Expose a WSGI application callable so servers like gunicorn can import it
application = create_app()

if __name__ == '__main__':
    application.run(debug=True)