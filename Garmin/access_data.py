import pandas as pd
from datetime import datetime, timedelta, timezone
from process_data import GarminDataProcessor
import os
import requests

# Additional API endpoints for injury-relevant data
ACTIVITIES_URL = "https://apis.garmin.com/wellness-api/rest/activities"
DAILY_SUMMARIES_URL = "https://apis.garmin.com/wellness-api/rest/dailies"
SLEEP_URL = "https://apis.garmin.com/wellness-api/rest/sleeps"

class DataCollector:
    def __init__(self, oauth, user_id):
        self.oauth = oauth
        self.user_id = user_id
        self.data_dir = f"user_data/{user_id}"
        os.makedirs(self.data_dir, exist_ok=True)
        
    def collect_historical_data(self, days_back=2):
        """Collect historical data for each day of the past year"""
        all_daily_data = []
        # Get the current time in UTC
        end_date = datetime.now(timezone.utc)
        end_date = end_date.replace(hour=0, minute=59, second=59, microsecond=999999)
        
        # Collect data day-by-day for the past year
        for i in range(days_back):
            # Calculate the specific day in the past year
            start = end_date - timedelta(days=1+i)
            end = start.replace(hour=23, minute=59, second=59, microsecond=999999)
            daily_df = self._collect_data(start, end)
            all_daily_data.append(daily_df)
        data_processor = GarminDataProcessor()
        user_combined_df = data_processor.combine_all_days(all_daily_data)
        data_processor.save_to_csv(user_combined_df, f"{self.user_id}_all_data.csv")

            



    def _collect_data(self, start_date, end_date):
        """Core data collection logic"""
        start_str = int(start_date.timestamp())
        end_str = int(end_date.timestamp())
        
        data_points = {
            "activities": self._get_activities(start_str, end_str),
            "daily_summaries": self._get_daily_summaries(start_str, end_str),
            "sleep": self._get_sleep(start_str, end_str)
        }
        data_processor = GarminDataProcessor()

        # Process and save combined data
        daily_summary_df = data_processor.process_daily_summaries(data_points["daily_summaries"])
        sleep_df = data_processor.process_sleep(data_points["sleep"])
        activities_df = data_processor.process_activities(data_points["activities"])
        combined_data = data_processor.combine_daily_data(daily_summary_df, sleep_df, activities_df)

        data_processor.save_to_csv(combined_data, start_date.strftime('%Y-%m-%d')+ "_data.csv")

        data_processing_tasks = [
            ("daily_summaries", data_processor.process_daily_summaries, start_date.strftime('%Y-%m-%d') + "_daily_summaries.csv"),
            ("sleep", data_processor.process_sleep, start_date.strftime('%Y-%m-%d') + "_sleep.csv"),
            ("activities", data_processor.process_activities, start_date.strftime('%Y-%m-%d') + "_activities.csv")
        ]

        # Process and save each data category
        for category, process_function, output_filename in data_processing_tasks:
            processed_data = process_function(data_points[category])
            data_processor.save_to_csv(processed_data, output_filename)
        
        return combined_data


    def _make_request(self, url, params):
        """Make authenticated request to Garmin API with error handling"""
        try:
            response = requests.get(url, auth=self.oauth, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching data from {url}: {response.status_code}")
                print(f"Response: {response.text}")
                return []
        except Exception as e:
            print(f"Exception making request to {url}: {str(e)}")
            return []

    # Individual data collection methods
    def _get_activities(self, start_date, end_date):
        return self._make_request(ACTIVITIES_URL, {'uploadStartTimeInSeconds': start_date, 'uploadEndTimeInSeconds': end_date})

    def _get_daily_summaries(self, start_date, end_date):
        return self._make_request(DAILY_SUMMARIES_URL, {'uploadStartTimeInSeconds': start_date, 'uploadEndTimeInSeconds': end_date})

    def _get_sleep(self, start_date, end_date):
        return self._make_request(SLEEP_URL, {'uploadStartTimeInSeconds': start_date, 'uploadEndTimeInSeconds': end_date})