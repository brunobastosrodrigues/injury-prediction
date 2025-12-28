import datetime, random
import numpy as np
from logistics.training_plan import generate_annual_training_plan
from training_response.fitness_fatigue_form import initialize_tss_history, initialize_hrv_history, calculate_training_metrics, update_history, calculate_max_daily_tss
from training_response.injury_simulation import inject_realistic_injury_patterns, create_false_alarm_patterns
from sensor_data.daily_metrics_simulation import simulate_morning_sensor_data, simulate_evening_sensor_data
from logistics.athlete_profiles import generate_athlete_cohort
from sensor_data.simulate_activities import simulate_training_day_with_wearables
from sensor_data.sensor_noise import SensorNoiseModel
from physiological.menstrual_cycle import MenstrualCycleModel
import pandas as pd
from datetime import timedelta

# Random seed for reproducibility
np.random.seed(42)
random.seed(42)


def calculate_injury_probability(day_data, athlete, fatigue, form, acwr=1.0):
    """
    Calculate injury probability based on ACWR (Gabbett model) + wellness vulnerability.

    ACWR-Based Injury Model (Gabbett, 2016 - validated on PMData):
    - ACWR < 0.8:  Undertrained zone (detraining risk, moderate injury risk)
    - ACWR 0.8-1.3: Sweet spot (optimal training, lowest injury risk)
    - ACWR 1.3-1.5: Danger zone (elevated injury risk)
    - ACWR > 1.5:  High risk zone (highest injury probability)

    PMData Results:
    - ACWR >1.5 zone has 33.7% injury rate (vs 28.5% in optimal zone)
    - Load features (acute_load, chronic_load, acwr) dominate prediction
    - Wellness features act as vulnerability modifiers

    The model: Injury_Risk = ACWR_Risk × Wellness_Vulnerability

    Returns probability in range [0, 0.06] per day
    """
    # ========================================
    # PART 1: ACWR-BASED RISK (PRIMARY TRIGGER)
    # ========================================
    # Gabbett injury zones - this is the main driver
    if acwr < 0.8:
        # Undertrained: moderate risk from detraining/sudden load increases
        acwr_risk = 0.4 + (0.8 - acwr) * 0.5  # 0.4-0.9 range
    elif acwr <= 1.3:
        # Sweet spot: lowest risk
        # Risk is lowest around ACWR=1.0, slightly higher at edges
        deviation = abs(acwr - 1.0) / 0.3  # 0-1 range within sweet spot
        acwr_risk = 0.2 + deviation * 0.15  # 0.2-0.35 range
    elif acwr <= 1.5:
        # Danger zone: elevated risk
        progress = (acwr - 1.3) / 0.2  # 0-1 within danger zone
        acwr_risk = 0.5 + progress * 0.3  # 0.5-0.8 range
    else:
        # High risk zone: highest probability
        excess = min(1.0, (acwr - 1.5) / 0.5)  # Cap at ACWR=2.0
        acwr_risk = 0.8 + excess * 0.2  # 0.8-1.0 range

    # ========================================
    # PART 2: WELLNESS VULNERABILITY MODIFIER
    # ========================================
    # Wellness doesn't cause injuries, but makes athletes more susceptible
    # when combined with high ACWR

    # Extract wellness features (normalized 0-1)
    sleep_hours = day_data.get('sleep_hours', 7.5)
    sleep_deficit = max(0, (7.0 - sleep_hours) / 3.0)  # Deficit below 7 hours

    sleep_quality = day_data.get('sleep_quality', 0.7)
    poor_sleep_quality = 1.0 - sleep_quality

    stress = day_data.get('stress', 40)
    high_stress = stress / 100.0

    body_battery = day_data.get('body_battery_morning', 75)
    low_recovery = 1.0 - (body_battery / 100.0)

    # Fatigue from training
    fatigue_norm = min(1.0, max(0.0, fatigue / 100.0))

    # Form (TSB) - negative form means accumulated fatigue
    form_risk = max(0.0, min(1.0, -form / 30.0))

    # Wellness vulnerability score (0-1)
    # These don't trigger injuries alone, but amplify ACWR risk
    vulnerability = (
        0.25 * sleep_deficit +           # Sleep debt
        0.15 * poor_sleep_quality +       # Poor sleep quality
        0.20 * high_stress +              # High stress
        0.15 * low_recovery +             # Poor recovery
        0.15 * fatigue_norm +             # Training fatigue
        0.10 * form_risk                  # Negative form
    )

    # Clamp vulnerability to reasonable range
    vulnerability = min(1.0, max(0.0, vulnerability))

    # ========================================
    # PART 3: COMBINED INJURY PROBABILITY
    # ========================================
    # Base probability varies by ACWR zone
    # Vulnerability acts as a multiplier (1.0 to 2.0x)

    # Base probabilities calibrated to PMData injury rates:
    # - Optimal zone: ~28% 3-day injury rate → ~0.01/day
    # - High risk zone: ~34% 3-day injury rate → ~0.015/day
    base_prob = 0.003  # Minimum (perfect conditions, optimal ACWR)
    max_prob = 0.05    # Maximum (high ACWR + poor wellness)

    # Calculate base injury probability from ACWR
    acwr_prob = base_prob + (max_prob * 0.6) * acwr_risk

    # Apply vulnerability modifier (1.0x to 2.0x multiplier)
    vulnerability_multiplier = 1.0 + vulnerability

    injury_prob = acwr_prob * vulnerability_multiplier

    # Add stochastic variation (±20%)
    injury_prob *= random.uniform(0.8, 1.2)

    # Clamp to valid range
    return min(max_prob, max(base_prob * 0.3, injury_prob))


def generate_load_spike_schedule(year=2024):
    """
    Generate a schedule of training load spikes throughout the year.

    These represent realistic scenarios that cause ACWR to spike:
    - Training camps (5-10 days of high volume)
    - Race preparation blocks (increased intensity)
    - Return from illness/vacation (sudden load increase)
    - Overreaching periods (intentional overload)
    - Acute spikes (single high-intensity days)

    Calibrated to PMData: ~12% of days should have ACWR > 1.5

    Returns list of (start_day, duration, multiplier) tuples
    """
    spikes = []

    # Training camps (3-4 per year, 5-10 days each, 1.6-2.2x load)
    num_camps = random.randint(3, 4)
    camp_months = random.sample([2, 3, 4, 5, 6, 7, 8, 9], num_camps)
    for month in camp_months:
        start_day = (month - 1) * 30 + random.randint(5, 20)
        duration = random.randint(5, 10)
        multiplier = random.uniform(1.6, 2.2)  # Higher intensity
        spikes.append((start_day, duration, multiplier, 'camp'))

    # Return from rest periods (sudden load after deload, 1.5-2.0x)
    num_returns = random.randint(4, 6)
    for _ in range(num_returns):
        start_day = random.randint(30, 330)
        duration = random.randint(3, 7)
        multiplier = random.uniform(1.5, 2.0)  # Higher intensity
        spikes.append((start_day, duration, multiplier, 'return'))

    # Overreaching blocks (intentional, 5-10 days, 1.4-1.8x)
    num_overreach = random.randint(3, 5)
    for _ in range(num_overreach):
        start_day = random.randint(60, 300)
        duration = random.randint(5, 10)
        multiplier = random.uniform(1.4, 1.8)
        spikes.append((start_day, duration, multiplier, 'overreach'))

    # Acute spikes (single or 2-3 day very high load events - races, tests)
    num_acute = random.randint(6, 10)
    for _ in range(num_acute):
        start_day = random.randint(30, 340)
        duration = random.randint(1, 3)
        multiplier = random.uniform(1.8, 2.5)  # Very high intensity
        spikes.append((start_day, duration, multiplier, 'acute'))

    # Reduced load periods (illness, vacation, life stress - causes undertrained ACWR)
    num_reduced = random.randint(3, 5)
    for _ in range(num_reduced):
        start_day = random.randint(30, 330)
        duration = random.randint(7, 14)
        multiplier = random.uniform(0.2, 0.5)  # Lower load
        spikes.append((start_day, duration, multiplier, 'reduced'))

    return spikes


def get_load_multiplier(day_of_year, load_spikes):
    """
    Check if current day falls within a load spike period.
    Returns the multiplier if in a spike, 1.0 otherwise.
    """
    for start_day, duration, multiplier, spike_type in load_spikes:
        if start_day <= day_of_year < start_day + duration:
            return multiplier, spike_type
    return 1.0, None


def simulate_full_year(athlete, year=2024):
    # Set starting date
    start_date = datetime.datetime(year, 1, 1)
    
    # Generate annual plan
    annual_plan, race_dates = generate_annual_training_plan(athlete, start_date)
    try:
        annual_plan.to_parquet('athlete_annual_training_plan.parquet', index=False)
    except:
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

    # Generate load spike schedule for realistic ACWR variability
    load_spikes = generate_load_spike_schedule(year)

    sensor_profile = athlete.get('sensor_profile', 'garmin')

    # Menstrual cycle state
    cycle_config = athlete.get('menstrual_cycle_config')
    day_in_cycle = random.randint(1, cycle_config['cycle_length']) if cycle_config else None

    for index, day in annual_plan.iterrows():
        # Get physiological modulations (e.g. Menstrual Cycle)
        modulations = None
        if cycle_config:
            phase = MenstrualCycleModel.get_phase(day_in_cycle, cycle_config['cycle_length'], cycle_config['luteal_phase_length'])
            modulations = MenstrualCycleModel.calculate_modulations(phase, day_in_cycle)
            # Increment day in cycle
            day_in_cycle = (day_in_cycle % cycle_config['cycle_length']) + 1

        # Step 1: Simulate morning sensor data
        day_data = simulate_morning_sensor_data(athlete, day['date'], prev_day, recovery_days_remaining, max_daily_tss, tss_history, acwr, modulations)
        
        # Apply daily noise (RHR, HRV, sleep)
        day_data = SensorNoiseModel.apply_daily_noise(day_data)
        
        sleep_quality = day_data['sleep_quality']
        hrv = day_data['hrv']

        # Step 2: Execute training plan (potentially with deviations)
        wearable_activity_data = simulate_training_day_with_wearables(athlete, day, day_data, fatigue)
        
        # Apply device-specific activity noise
        if wearable_activity_data:
            for sport in wearable_activity_data:
                if sensor_profile == 'garmin':
                    wearable_activity_data[sport] = SensorNoiseModel.apply_garmin_profile(wearable_activity_data[sport])
                else:
                    wearable_activity_data[sport] = SensorNoiseModel.apply_optical_profile(wearable_activity_data[sport])
        
        activity_data.append(wearable_activity_data)

        # Apply load spike multiplier for realistic ACWR variability
        day_of_year = (day['date'] - start_date).days + 1
        load_multiplier, spike_type = get_load_multiplier(day_of_year, load_spikes)

        # Modify TSS based on load spike (training camp, overreaching, rest period, etc.)
        original_tss = day_data['actual_tss']
        day_data['actual_tss'] = original_tss * load_multiplier

        # Also add some daily random variation (±15%) to increase ACWR variability
        daily_variation = random.uniform(0.85, 1.15)
        day_data['actual_tss'] *= daily_variation

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
                # Calculate injury probability using ACWR-based Gabbett model
                # ACWR is the primary trigger, wellness acts as vulnerability modifier
                feature_based_prob = calculate_injury_probability(day_data, athlete, fatigue, form, acwr)

                # Apply modulations (Menstrual)
                if modulations and 'injury_risk_modifier' in modulations:
                    feature_based_prob *= modulations['injury_risk_modifier']

                # Apply modulations (Circadian)
                if 'circadian_injury_modifier' in day_data:
                    feature_based_prob *= day_data['circadian_injury_modifier']

                # Small chance of truly random injury (unexplained, no patterns)
                random_injury_prob = 0.001  # ~0.4 per year
                if random.random() < random_injury_prob:
                    day_data['injury'] = 1
                    recovery_days_remaining = np.random.randint(3, 7)
                # HIGH ACWR immediate injury (acute overload mechanism)
                # This creates direct ACWR-injury correlation
                elif acwr > 1.5 and random.random() < 0.08:  # ~8% chance when high ACWR
                    day_data['injury'] = 1
                    recovery_days_remaining = np.random.randint(3, 7)
                # DANGER zone ACWR - elevated but not immediate
                elif acwr > 1.3 and random.random() < 0.04:  # ~4% chance in danger zone
                    day_data['injury'] = 1
                    recovery_days_remaining = np.random.randint(3, 5)
                # UNDERTRAINED zone - also risky (coming back too fast)
                elif acwr < 0.8 and random.random() < 0.03:  # ~3% chance when undertrained
                    day_data['injury'] = 1
                    recovery_days_remaining = np.random.randint(2, 5)
                # Wellness-triggered injury (vulnerability in optimal ACWR zone)
                elif len(daily_data) > 30 and random.random() < feature_based_prob * 0.5:
                    # Lower probability for pure wellness injuries
                    day_data['injury'] = 1
                    recovery_days_remaining = np.random.randint(3, 7)
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
            'drinking_factor': athlete['drinking_factor'],
            'sensor_profile': athlete['sensor_profile'],
            'chronotype': athlete.get('chronotype', 'intermediate')
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

    # Save DataFrames (prefer Parquet)
    try:
        df_athletes.to_parquet(f"{output_folder}/athletes.parquet", index=False)
        df_daily_data.to_parquet(f"{output_folder}/daily_data.parquet", index=False)
        df_activity_data.to_parquet(f"{output_folder}/activity_data.parquet", index=False)
    except Exception as e:
        print(f"Warning: Could not save as Parquet ({e}). Falling back to CSV.")
        df_athletes.to_csv(f"{output_folder}/athletes.csv", index=False)
        df_daily_data.to_csv(f"{output_folder}/daily_data.csv", index=False)
        df_activity_data.to_csv(f"{output_folder}/activity_data.csv", index=False)

    print("Simulation data saved successfully!")
