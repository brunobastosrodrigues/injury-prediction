import datetime, random
import numpy as np
from logistics.training_plan import generate_annual_training_plan
from training_response.fitness_fatigue_form import initialize_tss_history, initialize_hrv_history, calculate_training_metrics, update_history, calculate_max_daily_tss
from sensor_data.daily_metrics_simulation import simulate_morning_sensor_data, simulate_evening_sensor_data, inject_realistic_injury_patterns, create_false_alarm_patterns
from logistics.athlete_profiles import generate_athlete_cohort
from sensor_data.simulate_activities import simulate_training_day_with_wearables
import pandas as pd
from datetime import timedelta

# Random seed for reproducibility
np.random.seed(42)
random.seed(42)

def simulate_full_year(athlete, year=2024):
    # Set starting date
    start_date = datetime.datetime(year, 1, 1)
    
    # Generate annual plan
    annual_plan, race_dates = generate_annual_training_plan(athlete, start_date)
    annual_plan.to_csv('athlete_annual_training_plan.csv', index=False)
    max_daily_tss = calculate_max_daily_tss(athlete['weekly_training_hours'], athlete['training_experience'])

    # Initialize injury tracking
    recovery_days_remaining = 0

    tss_history = initialize_tss_history(athlete, start_date)
    hrv_history = initialize_hrv_history(athlete, tss_history)
    acwr_timeline = []

    # Initialize fitness/fatigue/form
    fitness, fatigue, form, acwr = calculate_training_metrics(tss_history, hrv_history, athlete['hrv_baseline'])
    acwr_timeline.append(acwr)
    # Simulate each day
    daily_data = []
    activity_data = []
    sleep_quality = athlete['sleep_quality']
    prev_day = {
        'training_stress': 60,
        'resting_hr': athlete['resting_hr'],
        'hrv': athlete['hrv_baseline'],
        'stress': athlete['stress_factor'] * 100,
        'fatigue': fatigue,
        'form': form,
        'body_battery_evening': 50
    }

    # Track when we should inject injury patterns
    pending_injury_date = None
    days_to_next_false_alarm = random.randint(30, 60)  # Schedule first false alarm

    for index, day in annual_plan.iterrows():
        # Step 1: Simulate morning sensor data
        day_data = simulate_morning_sensor_data(athlete, day['date'], prev_day, recovery_days_remaining, max_daily_tss, tss_history, acwr)
        sleep_quality = day_data['sleep_quality']
        hrv = day_data['hrv']

        # Step 2: Execute training plan (potentially with deviations)
        wearable_activity_data = simulate_training_day_with_wearables(athlete, day, day_data, fatigue)
        activity_data.append(wearable_activity_data)
        tss_today = day_data['actual_tss']
        
        # Update TSS and HRV history
        tss_history, hrv_history = update_history(tss_history, hrv_history, tss_today, hrv)


        # Step 3: Update fitness/fatigue/form after training 
        fitness, fatigue, form, acwr = calculate_training_metrics(tss_history, hrv_history, athlete['hrv_baseline'])
        acwr_timeline.append(acwr)
        # Step 4: Simulate the remaining daily sensor data (stress)
        simulate_evening_sensor_data(athlete, fatigue, day_data)

        # Step 5: Handle injury occurrence with more realism
        if recovery_days_remaining == 0:
            # If there's a pending injury date and we've reached it
            if pending_injury_date and day['date'] == pending_injury_date:
                # Only inject patterns once - right when the injury occurs
                daily_data = inject_realistic_injury_patterns(
                    athlete, 
                    daily_data, 
                    len(daily_data) - 1,  # Current day index 
                    14  # Look back up to 14 days to modify
                )
                day_data['injury'] = 1
                recovery_days_remaining = np.random.randint(3, 10)
                pending_injury_date = None
            else:
                # Add some truly random injuries (unexplained, no patterns)
                if random.random() < 0.003:  # ~1 random injuries per year
                    day_data['injury'] = 1
                    recovery_days_remaining = np.random.randint(3, 7)  # Shorter recovery for sudden injuries
                # Plan future injuries with patterns
                elif len(daily_data) > 30 and random.random() < 0.0135:  # ~4.5-5 pattern-based injuries per year
                    # Variable warning period (longer is more realistic)
                    injury_warning_days = random.randint(7, 14)
                    injury_date = day['date'] + timedelta(days=injury_warning_days)
                    pending_injury_date = injury_date
                else:
                    day_data['injury'] = 0
        else:
            # Still in recovery period
            day_data['injury'] = 1
            recovery_days_remaining -= 1
            
        daily_data.append(day_data)
        
        # Update previous day data
        prev_day['fatigue'] = fatigue
        prev_day['form'] = form
        prev_day['resting_hr'] = day_data['resting_hr']
        prev_day['hrv'] = day_data['hrv']
        prev_day['stress'] = day_data['stress']
        prev_day['training_stress'] = day_data['actual_tss'] 
        prev_day['body_battery_evening'] = day_data['body_battery_evening']
        
        # Handle false alarm pattern injection (patterns that look like injuries but don't result in one)
        days_to_next_false_alarm -= 1
        if days_to_next_false_alarm <= 0 and recovery_days_remaining == 0 and not pending_injury_date:
            # Insert a false alarm pattern
            false_alarm_days = random.randint(7, 12)
            create_false_alarm_patterns(athlete, daily_data, len(daily_data) - 1, false_alarm_days)
            # Schedule next false alarm
            days_to_next_false_alarm = random.randint(20, 35)

    
    result = {
        'athlete': athlete,
        'daily_data': daily_data,
        'activity_data': activity_data
    }
    
    return result


def generate_simulation_dataset(n_athletes):
    # Generate athlete cohort
    athletes = generate_athlete_cohort(n_athletes)
    
    # Simulate each athlete's year
    simulated_data = []
    for i, athlete in enumerate(athletes):
        print(f"Simulating athlete {i+1}/{n_athletes}...")
        athlete_data = simulate_full_year(athlete)
        simulated_data.append(athlete_data)
    
    return simulated_data

def save_simulation_data(simulated_data, output_folder="simulated_data"):
    """Save simulation data into CSV files."""
    
    # Create lists to store data before converting to DataFrame
    athlete_profiles = []
    daily_data_records = []
    activity_data_records = []


    # Loop through each simulated athlete
    for athlete_data in simulated_data:
        athlete = athlete_data['athlete']
        # Save athlete profile
        athlete_profiles.append({
            'athlete_id': athlete['id'],
            'gender': athlete['gender'],
            'age': athlete['age'],
            'height_cm': athlete['height'],
            'weight_kg': round(athlete['weight'], 1),
            'genetic_factor': round(athlete['genetic_factor'], 2),
            'hrv_baseline': athlete['hrv_baseline'],
            'hrv_range': athlete['hrv_range'],
            'max_hr': round(athlete['max_hr'], 1),
            'resting_hr': round(athlete['resting_hr'], 1),
            'lthr': round(athlete['lthr'], 1),
            'hr_zones': athlete['hr_zones'],
            'vo2max': round(athlete['vo2max'], 1),
            'running_threshold_pace': athlete['run_threshold_pace'],
            'ftp': round(athlete['ftp'], 1),
            'css': athlete['css'],
            'training_experience': athlete['training_experience'],
            'weekly_training_hours': round(athlete['weekly_training_hours'], 1),
            'recovery_rate': round(athlete['recovery_rate'], 2),
            'lifestyle': athlete['lifestyle'],
            'sleep_time_norm': athlete['sleep_time_norm'],
            'sleep_quality': athlete['sleep_quality'],
            'nutrition_factor': athlete['nutrition_factor'],
            'stress_factor': athlete['stress_factor'],
            'smoking_factor': athlete['smoking_factor'],
            'drinking_factor': athlete['drinking_factor']
        })

        # Save daily data
        for daily_entry in athlete_data['daily_data']:
            daily_data_records.append({
                'athlete_id': daily_entry['athlete_id'],
                'date': daily_entry['date'],
                'resting_hr': daily_entry['resting_hr'],
                'hrv': daily_entry['hrv'],
                'sleep_hours': daily_entry['sleep_hours'],
                'deep_sleep': daily_entry['deep_sleep'],
                'light_sleep': daily_entry['light_sleep'],
                'rem_sleep': daily_entry['rem_sleep'],
                'sleep_quality': daily_entry['sleep_quality'],
                'body_battery_morning': daily_entry['body_battery_morning'],
                'stress': daily_entry['stress'],
                'body_battery_evening': daily_entry['body_battery_evening'],
                'planned_tss': daily_entry['planned_tss'],
                'actual_tss': daily_entry['actual_tss'],
                'injury': daily_entry['injury']
            })

        # Save activity data
        for activity_entry in athlete_data['activity_data']:
            if not activity_entry:  # Skip empty dictionaries
                continue
            
            for sport_key, workout_data in activity_entry.items():
                activity_data_records.append({
                'athlete_id': workout_data['athlete_id'],
                'date': workout_data['date'],
                'sport': workout_data['sport'],  
                'workout_type': workout_data['workout_type'],
                'duration_minutes': workout_data['duration_minutes'],
                'tss': workout_data['tss'],
                'intensity_factor': workout_data['intensity_factor'],
                'avg_hr': workout_data.get('avg_hr'),
                'max_hr': workout_data.get('max_hr'),
                'hr_zones': workout_data.get('hr_zones'),
                'distance_km': workout_data.get('distance_km'),
                'avg_speed_kph': workout_data.get('avg_speed_kph'),
                'avg_power': workout_data.get('avg_power'),
                'normalized_power': workout_data.get('normalized_power'),
                'power_zones': workout_data.get('power_zones'),
                'intensity_variability': workout_data.get('intensity_variability'),
                'work_kilojoules': workout_data.get('work_kilojoules'),
                'elevation_gain': workout_data.get('elevation_gain'),
                'avg_pace_min_km': workout_data.get('avg_pace_min_km'),
                'training_effect_aerobic': workout_data.get('training_effect_aerobic'),
                'training_effect_anaerobic': workout_data.get('training_effect_anaerobic'),
                'distance_m': workout_data.get('distance_m'),
                'avg_pace_min_100m': workout_data.get('avg_pace_min_100m')
            })
        

    # Convert lists to DataFrames
    df_athletes = pd.DataFrame(athlete_profiles)
    df_daily_data = pd.DataFrame(daily_data_records)
    df_activity_data = pd.DataFrame(activity_data_records)

    # Save DataFrames to CSV files
    df_athletes.to_csv(f"{output_folder}/athletes.csv", index=False)
    df_daily_data.to_csv(f"{output_folder}/daily_data.csv", index=False)
    df_activity_data.to_csv(f"{output_folder}/activity_data.csv", index=False)

    print("Simulation data saved successfully!")
