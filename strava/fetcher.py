import requests
import time
from rate_limiter import check_rate_limit
from utils import calculate_time_in_zones

def fetch_activities(access_token):
    activities = []
    page = 1

    while True:
        check_rate_limit()
        response = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"per_page": 50, "page": page},
            timeout=20
        )
        data = response.json()
        if len(data) == 0:
            break
        activities.extend(data)
        page += 1
    return activities

def fetch_time_in_hr_zones(access_token, activity_id, heart_rate_zones):
    global REQUEST_COUNT
    check_rate_limit()

    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        params={"keys": "heartrate", "key_by_type": "true"}
    )
    REQUEST_COUNT += 1

    if response.status_code == 200:
        data = response.json()
        heart_rate_stream = data.get("heartrate", {}).get("data", [])
        return calculate_time_in_zones(heart_rate_stream, heart_rate_zones)
    else:
        print(f"Error fetching heart rate stream for activity {activity_id}: {response.json()}")
        return {
            "time_in_zones_raw": {zone: 0 for zone in heart_rate_zones.keys()},
            "time_in_zones_percentage": {zone: 0.0 for zone in heart_rate_zones.keys()},
        }
