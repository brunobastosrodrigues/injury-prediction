import os
import datetime
from auth import get_access_token
from fetcher import fetch_activities, fetch_time_in_hr_zones
import pandas as pd

def save_to_csv(activities, heart_rate_zones, access_token, output_file="strava_activities.csv"):
    injury_keywords = ["injury", "hurt", "pain", "strain", "broken", "twisted", "cramp", "fracture", "sore", "tear", "bruise"]

    def check_injury(description):
        if description:
            description_lower = description.lower()
            return any(keyword in description_lower for keyword in injury_keywords)
        return False

    df = pd.DataFrame([
        {
            "id": activity["id"],
            "name": activity["name"],
            "distance_meters": activity["distance"],
            "moving_time_seconds": activity["moving_time"],
            "elapsed_time_seconds": activity["elapsed_time"],
            "elevation_gain_meters": activity["total_elevation_gain"],
            "type": activity["type"],
            "sport_type": activity.get("sport_type", None),
            "start_date": activity["start_date"],
            "average_speed_mps": activity["average_speed"],
            "max_speed_mps": activity.get("max_speed", None),
            "average_heart_rate_bpm": activity.get("average_heartrate", None),
            "max_heart_rate_bpm": activity.get("max_heartrate", None),
            "hr_zones": fetch_time_in_hr_zones(access_token, activity["id"], heart_rate_zones) if activity["type"] == "Run" and activity.get("average_heartrate") else None,
            "injury_occurred": check_injury(activity.get("name", ""))
        }
        for activity in activities
    ])
    df.to_csv(output_file, index=False)
    print(f"Saved {len(activities)} activities to {output_file}")

def main():
    if not os.path.exists("access_token.txt"):
        access_token = get_access_token()
        with open("access_token.txt", "w") as f:
            f.write(access_token)
    else:
        with open("access_token.txt", "r") as f:
            access_token = f.read().strip()

    try:
        heart_rate_zones = {
            "zone_1": (86, 113), 
            "zone_2": (114, 147),
            "zone_3": (148, 168),
            "zone_4": (169, 176),
            "zone_5": (177, 183),
            "zone_6": (184, 202),
        }
        activities = fetch_activities(access_token)
        save_to_csv(activities, heart_rate_zones, access_token)
    except Exception as e:
        print(f"Error: {e}")
        if os.path.exists("access_token.txt"):
            os.remove("access_token.txt")

if __name__ == "__main__":
    main()
