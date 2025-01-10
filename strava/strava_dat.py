import requests
import pandas as pd
import time
import os

# Strava API credentials
CLIENT_ID = "144607"
CLIENT_SECRET = "5103b9d299464cde9b0ec9ba1b289dcbe18efb48"
REDIRECT_URI = "http://localhost:8080/exchange_token"

# Step 1: Obtain access token
def get_access_token():
    print(f"Go to the following URL and authorize the app:")
    print(f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=activity:read")
    
    # Get the authorization code from the redirect URL
    authorization_code = input("Enter the code from the URL: ").strip()
    
    # Exchange authorization code for access token
    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": authorization_code,
            "grant_type": "authorization_code"
        }
    )
    response_json = response.json()
    if "access_token" in response_json:
        return response_json["access_token"]
    else:
        raise Exception(f"Error fetching access token: {response_json}")

# Step 2: Fetch activities
def fetch_activities(access_token):
    activities = []
    page = 1
    while True:
        response = requests.get(
            f"https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"per_page": 50, "page": page}
        )
        data = response.json()
        if len(data) == 0:  # Break if no more activities
            break
        activities.extend(data)
        page += 1
        time.sleep(1)  # Rate limiting: Avoid hitting API limits
    return activities



def check_injury(description):
    injury_keywords = ["injury", "hurt", "pain", "strain", "broken", "twisted", "cramp", "fracture", "sore", "tear", "bruise"]
    if description:
        description_lower = description.lower()
        return any(keyword in description_lower for keyword in injury_keywords)
    return False
# Step 3: Save to CSV
def save_to_csv(activities, output_file="strava_activities.csv"):
    if not activities:
        print("No activities found!")
        return
    # Extract relevant fields
    df = pd.DataFrame([
        {
            "id": activity["id"],
            "start_date": activity["start_date"],
            "name": activity["name"],
            "distance_meters": activity["distance"],
            "moving_time_seconds": activity["moving_time"],
            "elapsed_time_seconds": activity["elapsed_time"],
            "elevation_gain_meters": activity["total_elevation_gain"],
            "type": activity["type"],
            "sport_type": activity.get("sport_type", None),
            "average_speed_mps": activity["average_speed"],
            "max_speed_mps": activity.get("max_speed", None),
            "average_heart_rate_bpm": activity.get("average_heartrate", None),
            "max_heart_rate_bpm": activity.get("max_heartrate", None),
            "injury_occurred": check_injury(activity.get("name", ""))
        }
        for activity in activities
    ])
    df.to_csv(output_file, index=False)
    print(f"Saved {len(activities)} activities to {output_file}")

# Main workflow
def main():
    if not os.path.exists("access_token.txt"):
        access_token = get_access_token()
        with open("access_token.txt", "w") as f:
            f.write(access_token)
    else:
        with open("access_token.txt", "r") as f:
            access_token = f.read().strip()

    try:
        activities = fetch_activities(access_token)
        save_to_csv(activities)
    except Exception as e:
        print(f"Error: {e}")
        os.remove("access_token.txt")  # Remove token if it fails, forcing re-authentication

if __name__ == "__main__":
    main()
