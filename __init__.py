from flask_oauthlib.client import OAuth
from flask import Flask, render_template, url_for, session, flash, redirect, jsonify, request
from functools import wraps
import requests
import json

from models import Character, Party, Player
from health_utils import get_character_health, ThrottlingException
import random

from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()

app = Flask(__name__)
app.secret_key = "development"

TWITCH_CLIENTID = 'qt4d7c961m6qsoq7jma6yzuj2ntgh5'
TWITCH_SECRET = 'ujlk4ohct1cqsyu7xhjz233o6twnnz'

# Create table if it doesnt exist already.
if not Player.exists():
    Player.create_table(wait=True)

oauth = OAuth()
twitch = oauth.remote_app(
  'twitch',
  consumer_key=TWITCH_CLIENTID, # get at: https://www.twitch.tv/kraken/oauth2/clients/new
  consumer_secret=TWITCH_SECRET,
  base_url='https://api.twitch.tv/kraken/',
  request_token_url=None,
  request_token_params={'scope': ["user_read", "channel_check_subscription"]},
  access_token_method='POST',
  access_token_url='https://api.twitch.tv/kraken/oauth2/token',
  authorize_url='https://api.twitch.tv/kraken/oauth2/authorize'
  )



#########################
# Public routes
#########################

@app.route('/')
def index():
    party = Party(name='Dungeons and Databases')
    characters = [2342595, 2266180, 2790689, 5304380, 6448988, 2278224, 4657425, 2271732]
    members = []
    for character in characters:
      try:
        data = get_character_health(character_id=character)
        members.append(Character(character, data['name'], 0, 0, data['current_hp'], data['health_status']))
        cache.set(character, data, timeout=100 * 60)
      except ThrottlingException as e:
        data = cache.get(character)
        if data is None:
          flash("D&D Beyond throttled us and charcter_id {} was not already cached.".format(character), 'danger')
        else:
          members.append(Character(character, data['name'], 0, 0, data['current_hp'], data['health_status']))
          flash("ThrottlingException from D&D Beyond, retrieving {} from cache".format(data['name']), 'warning')
    for char in sorted(members, key=lambda x: x.name):
      party.add(char)
    return render_template('main.html', entries=party) 


#########################
# Authorization routes
#########################

@twitch.tokengetter
def get_twitch_token():
    if 'twitch_oauth' in session:
        return session.get('twitch_oauth')


def change_twitch_header(uri, headers, body):
    """
    Modifies the request header before the request is made to the Twitch api.
    """
    # todo: Does the new twitch api still require this? It seems to work.
    auth = headers.get('Authorization')
    if auth:
        auth = auth.replace('Bearer', 'OAuth')
        headers['Authorization'] = auth

    # Append the client id to the end of the url.
    # todo: can this be done as part of the configuration
    url = uri + "?client_id=" + app.config['TWITCH_KEY']

    return url, headers, body

twitch.pre_request = change_twitch_header


def validate_token():
    """
    Required by twitch: https://dev.twitch.tv/docs/authentication#if-you-use-twitch-for-login-to-your-app-you-must-validate-every-request
    Submits a request to the Twitch root URL. Response should include status of token.
    Usage:
    returns None on fail, user name on success
    """
    r = twitch.get(twitch.base_url)
    #assert app.debug == False

    if(r.data['token']['valid'] == True):
        return jsonify(r.data['token']['user_name'])


def authorized(fn):
    """
    Decorator that checks if the user is authenticated.
    Usage:
    @app.route("/")
    @authorized
    def secured_root(userid=None):
        pass
    """
    @wraps(fn)
    def decorated_function(*args, **kwargs):
        if 'twitch_oauth' not in session:
            # Access token was not found in the session
            flash('Please log in to continue')
            return render_template('index.html', title="Unauthorized", content=""), 401

        userid = validate_token()
        if userid is None:
            # Token is no longer valid
            flash('Please log in to continue')
            return render_template('index.html', title="Unauthorized"), 401

        return fn(*args, **kwargs)
    return decorated_function
    

@app.route('/login')
def login():
    callback_url = url_for('oauthorized', _external=True) 
    return twitch.authorize(callback=callback_url or None)


@app.route('/logout')
def logout():
    session.pop('twitch_oauth', None)
    flash('You are now logged out')
    return redirect(url_for('index'))


@app.route('/login/authorized')
def oauthorized():
    resp = twitch.authorized_response()
    if resp is None:
        flash('You denied the request to sign in.')
    else:
        session['twitch_oauth'] = resp
        flash('Successfully logged in.')
    return redirect(url_for('index'))


#########################
# Secured Routes
#########################

@app.route('/me')
@authorized
def getme():
    url = twitch.base_url
    r = twitch.get(url)
    return jsonify(r.data)


@app.route('/test')
@authorized
def test():
    return render_template('index.html', title="Test")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
