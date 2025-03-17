import requests
from requests_oauthlib import OAuth1
from flask import Flask, request, redirect, session, url_for, render_template, jsonify
import os
from urllib.parse import parse_qs
from access_data import DataCollector
from threading import Thread

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
    return render_template('home.html')

@app.route("/about")
def about():
    """About page"""
    return render_template('about.html')

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
        session[access_token] = access_token
        session[access_token_secret] = access_token_secret

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
        # Save the user_id to the session
        session['user_id'] = user_id
        
        return redirect(url_for('authentification_success'))

    except Exception as e:
        return f"Error fetching user ID: {str(e)}", 500
    
@app.route('/authentification-success')
def authentification_success():
    """Page to show the user that the authentication was successful."""
    return render_template('authentification_successful.html')
    
@app.route('/thank-you')
def thank_you():
    """Thank you page after sharing data."""
    # Get the session data
    access_token = session.get('access_token')
    access_token_secret = session.get('access_token_secret')
    user_id = session.get('user_id')
    injuries = session.get('injury_dates', [])

    # Create OAuth object
    oauth = OAuth1(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret
    )
    
    # Start data collection in background
    Thread(target=collect_data_async, args=(oauth, user_id, injuries)).start()
    
    # Return the page immediately
    return render_template('thank_you.html')

def collect_data_async(oauth, user_id, injuries):
    collector = DataCollector(oauth, user_id)
    collector.collect_historical_data(injuries)

@app.route('/report-injuries', methods=['GET'])
def show_injury_form():
    return render_template('report_injuries.html')

# Route to handle form submission
@app.route('/report-injuries', methods=['POST'])
def report_injury():
    try:
        data = request.get_json()
        injury_dates = data.get('injuryDates', [])
        
        if not injury_dates:
            return jsonify({'error': 'No injury dates provided'}), 400
            
        session['injury_dates'] = injury_dates
        return jsonify({'message': 'Injury dates received successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == "__main__":
    app.run(port=5000, debug=True)