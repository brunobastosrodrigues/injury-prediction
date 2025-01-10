import requests
from requests_oauthlib import OAuth1
from flask import Flask, request, redirect, session, url_for
import os
from urllib.parse import parse_qs
from access_data import DataCollector

# Garmin API credentials
CONSUMER_KEY = "6d993b8f-15f9-4fd0-bd8e-4208fe376f18"
CONSUMER_SECRET = "yNKjmCecC6DW7mSS3P34NKrvq5MLEnvLr8j"

# Garmin OAuth endpoints
REQUEST_TOKEN_URL = "https://connectapi.garmin.com/oauth-service/oauth/request_token"
AUTHORIZATION_URL = "https://connect.garmin.com/oauthConfirm"
ACCESS_TOKEN_URL = "https://connectapi.garmin.com/oauth-service/oauth/access_token"
USER_ID_URL = "https://apis.garmin.com/wellness-api/rest/user/id"

# Flask app setup
app = Flask(__name__)
app.secret_key = os.urandom(24)  


@app.route("/")
def home():
    """Landing page with auth start button"""
    return '''
        <h1>Garmin OAuth Example</h1>
        <a href="/start_auth">Start Authentication</a>
    '''

@app.route("/start_auth")
def start_auth():
    """Step 1: Acquire Unauthorized Request Token and Token Secret"""
    try:
        # Create OAuth1 object for getting request token
        oauth = OAuth1(
            CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
            callback_uri=url_for('callback', _external=True)
        )

        # Request temporary token
        response = requests.post(REQUEST_TOKEN_URL, auth=oauth)
        
        if response.status_code != 200:
            return f"Failed to get request token. Status: {response.status_code}, Response: {response.text}", 500

        # Parse response using parse_qs instead of manual splitting
        token_data = parse_qs(response.text)
        
        # Store tokens in session (get first value from lists)
        session['request_token'] = token_data["oauth_token"][0]
        session['request_token_secret'] = token_data["oauth_token_secret"][0]

        # Redirect user to Garmin's authorization page
        auth_url = f"{AUTHORIZATION_URL}?oauth_token={session['request_token']}"
        return redirect(auth_url)

    except Exception as e:
        return f"Error during authorization initialization: {str(e)}", 500

@app.route("/callback")
def callback():
    """Step 2 & 3: Handle callback and acquire Access Token"""
    try:
        oauth_verifier = request.args.get("oauth_verifier")
        if not oauth_verifier:
            return "Authorization failed. No verifier received.", 400

        # Get tokens from session
        request_token = session.get('request_token')
        request_token_secret = session.get('request_token_secret')

        if not request_token or not request_token_secret:
            return "No request token found in session.", 400

        # Create OAuth1 object for getting access token
        oauth = OAuth1(
            CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
            resource_owner_key=request_token,
            resource_owner_secret=request_token_secret,
            verifier=oauth_verifier
        )

        # Exchange request token for access token
        response = requests.post(ACCESS_TOKEN_URL, auth=oauth)
        
        if response.status_code != 200:
            return f"Failed to get access token. Status: {response.status_code}, Response: {response.text}", 500

        # Parse response
        token_data = dict(x.split("=") for x in response.text.split("&"))
        
        # Store access tokens in session
        session['access_token'] = token_data["oauth_token"]
        session['access_token_secret'] = token_data["oauth_token_secret"]

        
        return redirect(url_for('get_user_id'))
    
    except Exception as e:
        return f"Error during callback: {str(e)}", 500

@app.route("/get_user_id")
def get_user_id():
    """Step 4: Fetch the User ID using Access Token"""
    try:
        # Get tokens from session
        access_token = session.get('access_token')
        access_token_secret = session.get('access_token_secret')

        if not access_token or not access_token_secret:
            return "No access token found in session.", 400

        # Create OAuth1 object for API request
        oauth = OAuth1(
            CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )

        # Make request to get user ID
        response = requests.get(USER_ID_URL, auth=oauth)
        
        if response.status_code != 200:
            return f"Failed to get user ID. Status: {response.status_code}, Response: {response.text}", 500

        user_id = response.json().get("userId")
        # Initialize data collector and start collection
        collector = DataCollector(oauth, user_id)
        
        # Collect historical data first
        historical_result = collector.collect_historical_data()
        
        # Store collection status in session
        session['collection_status'] = historical_result
        
        return f"Thank you for your submission! Your data has been received and is being processed."

    except Exception as e:
        return f"Error fetching user ID: {str(e)}", 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)