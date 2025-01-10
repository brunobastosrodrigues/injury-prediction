import pandas as pd
import os
from datetime import datetime

class GarminDataProcessor:
    def __init__(self, save_dir="processed_data"):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)


    def process_daily_summaries(self, daily_summaries):

        # Define the fields to extract
        selected_fields = [
            "calendarDate",
            "startTimeInSeconds",
            "moderateIntensityDurationInSeconds",
            "vigorousIntensityDurationInSeconds",
            "minHeartRateInBeatsPerMinute",
            "maxHeartRateInBeatsPerMinute",
            "averageHeartRateInBeatsPerMinute",
            "restingHeartRateInBeatsPerMinute",
            "averageStressLevel",
            "maxStressLevel",
            "stressDurationInSeconds",
            "restStressDurationInSeconds",
            "activityStressDurationInSeconds",
            "lowStressDurationInSeconds",
            "mediumStressDurationInSeconds",
            "highStressDurationInSeconds",
            "stressQualifier"
        ]

        # Extract the selected fields from each daily summary
        processed_data = []
        for summary in daily_summaries:
            processed_data.append({field: summary.get(field, None) for field in selected_fields})
        # Convert the processed data into a pandas DataFrame
        df = pd.DataFrame(processed_data)
         # Get the latest (maximum) calendarDate
        max_date = df['calendarDate'].max()

        # Filter the dataframe to keep only the rows with the maximum calendarDate
        df_latest = df[df['calendarDate'] == max_date]

        # Sort values by 'calendarDate' and 'startTimeInSeconds'
        df_latest = df_latest.sort_values(by=['calendarDate', 'startTimeInSeconds'], ascending=[True, True])

        # Keep only the last entry of the latest date (in case there are multiple entries for the same date)
        df_last_entry = df_latest.groupby('calendarDate').last().reset_index()

        # Drop the 'startTimeInSeconds' column
        df_last_entry = df_last_entry.drop(columns=['startTimeInSeconds'])

        return df_last_entry
    

    
    def process_sleep(self, sleep_data):
        # Define the fields to extract
        selected_fields = [
            "calendarDate",
            "durationInSeconds",
            "overallSleepScore",
            "sleepScores"
        ]

        # Extract the selected fields from each sleep record
        processed_data = []
        for record in sleep_data:
            processed_data.append({field: record.get(field, None) for field in selected_fields})
        # Convert the processed data into a pandas DataFrame
        df = pd.DataFrame(processed_data)

        return df
    
    def process_activities(self, activities):
        selected_fields = [
            "activityType",
            "durationInSeconds",
            "averageHeartRateInBeatsPerMinute",
            "maxHeartRateInBeatsPerMinute",
            "averageBikeCadenceInRoundsPerMinute",
            "averageRunCadenceInStepsPerMinute",
            "activeKilocalories",
            "distanceInMeters"
        ]

        processed_data = []
        for activity in activities:
            # Convert start time to a human-readable date format
            start_time_in_seconds = activity.get("startTimeInSeconds")
            if start_time_in_seconds:
                date = datetime.fromtimestamp(start_time_in_seconds).strftime('%Y-%m-%d')  # Date in YYYY-MM-DD format
            else:
                date = None  # If there's no start time, set as None

            activity_data = {field: activity.get(field, None) for field in selected_fields}
            activity_data["calendarDate"] = date  # Add the date to the activity data
            
            
            processed_data.append(activity_data)
        # Convert the processed data into a pandas DataFrame
        df = pd.DataFrame(processed_data)
        columns = ['calendarDate'] + [col for col in df.columns if col != 'calendarDate']
        df = df[columns]
        return df
    
    def combine_daily_data(self, daily_df, sleep_df, activities_df):
        # Make copies to avoid modifying original dataframes
        daily = daily_df.copy()
        sleep = sleep_df.copy()
        activities = activities_df.copy()
        
        # Group activities by date
        activities_grouped = activities.groupby('calendarDate').apply(
            lambda x: x.drop('calendarDate', axis=1).to_dict('records')
        ).reset_index()
        activities_grouped.columns = ['calendarDate', 'activities']
        # Prepare sleep data
        # Convert sleep scores from string to dict if they're stored as strings
        if sleep['sleepScores'].dtype == 'object':
            sleep['sleepScores'] = sleep['sleepScores'].apply(
                lambda x: eval(x) if isinstance(x, str) else x
            )
        if sleep['overallSleepScore'].dtype == 'object':
            sleep['overallSleepScore'] = sleep['overallSleepScore'].apply(
                lambda x: eval(x) if isinstance(x, str) else x
            )
        
        # Create sleep data dictionary
        sleep['sleep_data'] = sleep.apply(
            lambda row: {
                'durationInSeconds': row['durationInSeconds'],
                'overallSleepScore': row['overallSleepScore'],
                'sleepScores': row['sleepScores']
            }, axis=1
        )
        sleep_grouped = sleep[['calendarDate', 'sleep_data']]
        
        # Merge all dataframes
        # First merge daily with activities
        merged_df = pd.merge(
            daily,
            activities_grouped,
            on='calendarDate',
            how='left'
        )
        
        # Then merge with sleep data
        final_df = pd.merge(
            merged_df,
            sleep_grouped,
            on='calendarDate',
            how='left'
        )
        
        # Handle NaN values properly
        def handle_activities(x):
            if isinstance(x, list):
                return x
            return []
        
        def handle_sleep(x):
            if isinstance(x, dict):
                return x
            return {}
        
        final_df['activities'] = final_df['activities'].apply(handle_activities)
        final_df['sleep_data'] = final_df['sleep_data'].apply(handle_sleep)
        
        return final_df
    
    def combine_all_days(self, final_dfs):
        """
        Combines all daily `final_df` dataframes into a single dataframe.

        Parameters:
            final_dfs (list): A list of daily `final_df` dataframes.

        Returns:
            pd.DataFrame: A single dataframe with all days' data combined.
        """
        # Combine all dataframes using pd.concat
        combined_df = pd.concat(final_dfs, ignore_index=True)
        
        # Optional: Sort by calendarDate to ensure chronological order
        combined_df = combined_df.sort_values(by='calendarDate').reset_index(drop=True)
        
        return combined_df
    
    def save_to_csv(self, df, filename):
        """
        Save the processed DataFrame to a CSV file.
        :param df: pandas DataFrame to save.
        :param filename: Name of the CSV file (without directory path).
        """
        filepath = os.path.join(self.save_dir, filename)
        df.to_csv(filepath, index=False)
        print(f"Processed data saved to {filepath}")

    def calculate_tss(duration_seconds, avg_metric, threshold_metric, activity_type):
        """
        Calculate Training Stress Score (TSS).
        :param duration_seconds: Duration of the activity in seconds.
        :param avg_metric: Average effort metric (heart rate, power, etc.).
        :param threshold_metric: Threshold effort metric (threshold heart rate, FTP, etc.).
        :param activity_type: Type of activity (e.g., 'running', 'cycling', 'swimming').
        :return: Training Stress Score (TSS).
        """
        if threshold_metric == 0:
            return None  # Avoid division by zero

        # Determine intensity factor based on activity type
        intensity_factor = avg_metric / threshold_metric

        # Calculate TSS
        tss = (duration_seconds * intensity_factor ** 2) / 3600 * 100

        return tss

    def calculate_acwr(acute_load, chronic_load):
        """
        Calculate Acute-to-Chronic Workload Ratio (ACWR).
        :param acute_load: Total load over the past 7 days.
        :param chronic_load: Average load over the past 28 days.
        :return: Acute-to-Chronic Workload Ratio (ACWR).
        """
        if chronic_load == 0:
            return None  # Avoid division by zero

        return acute_load / chronic_load

    def calculate_trimp(duration_minutes, avg_hr, hr_rest, hr_max):
        """
        Calculate Training Impulse (TRIMP) based on heart rate.
        :param duration_minutes: Duration of the activity in minutes.
        :param avg_hr: Average heart rate during the activity.
        :param hr_rest: Resting heart rate.
        :param hr_max: Maximum heart rate.
        :return: TRIMP score.
        """
        if hr_max == hr_rest:
            return None  # Avoid division by zero

        hr_reserve = (avg_hr - hr_rest) / (hr_max - hr_rest)
        trimp = duration_minutes * hr_reserve * 10
        return trimp

    def calculate_hrr(avg_hr, max_hr, rest_hr):
        """
        Calculate Heart Rate Reserve (HRR).
        :param avg_hr: Average heart rate.
        :param max_hr: Maximum heart rate.
        :param rest_hr: Resting heart rate.
        :return: Heart Rate Reserve (HRR).
        """
        return (avg_hr - rest_hr) / (max_hr - rest_hr)

    