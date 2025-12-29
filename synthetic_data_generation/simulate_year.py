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
from config import SimConfig as cfg
import pandas as pd
from datetime import timedelta

# Random seed for reproducibility
np.random.seed(42)
random.seed(42)


def calculate_injury_probability_asymmetric(day_data, athlete, fatigue, form, acwr=1.0, daily_load=0):
    """
    Asymmetric ACWR Injury Model - Based on PMData Exposure Analysis.

    KEY SCIENTIFIC INSIGHT:
    The ACWR-injury relationship is NOT symmetric. Our analysis reveals:

    1. UNDERTRAINED (ACWR < threshold): TRUE PHYSIOLOGICAL MECHANISM
       - Higher injury rate PER LOAD UNIT than optimal
       - Mechanism: Detraining → tissue fragility → vulnerability on return

    2. OPTIMAL (within threshold): BASELINE RISK
       - Lowest injury rate per load unit
       - Tissue adapted to current training demands

    3. HIGH ACWR (>threshold): STOCHASTIC EXPOSURE MECHANISM
       - Similar injury rate per load unit as optimal
       - Higher raw injury rate is explained by MORE TRAINING TIME

    Configuration loaded from: config/simulation_config.yaml

    Returns: (total_probability, injury_type) where injury_type is
             'physiological', 'exposure', or 'baseline'
    """
    # Load configuration
    thresholds = cfg.acwr_thresholds()
    physio_cfg = cfg.get('injury_model.physiological', {})
    exposure_cfg = cfg.get('injury_model.exposure', {})
    baseline_cfg = cfg.get('injury_model.baseline', {})
    bounds = cfg.get('injury_model.bounds', {})

    undertrained_threshold = thresholds.get('undertrained', 0.8)
    optimal_upper = thresholds.get('optimal_upper', 1.3)

    # ========================================
    # MECHANISM 1: PHYSIOLOGICAL DETRAINING
    # ========================================
    physiological_risk = 0.0
    if acwr < undertrained_threshold:
        detraining_severity = (undertrained_threshold - acwr) / undertrained_threshold

        base_physio_risk = physio_cfg.get('base_daily_risk', 0.008)
        max_multiplier = physio_cfg.get('max_detraining_multiplier', 2.66)
        wellness_amp = physio_cfg.get('wellness_amplification', 0.5)

        physio_multiplier = 1.0 + ((max_multiplier - 1.0) * detraining_severity)
        physiological_risk = base_physio_risk * physio_multiplier

        wellness_vulnerability = _calculate_wellness_vulnerability(day_data, fatigue, form)
        physiological_risk *= (1.0 + wellness_vulnerability * wellness_amp)

    # ========================================
    # MECHANISM 2: STOCHASTIC EXPOSURE
    # ========================================
    exposure_risk = 0.0
    if daily_load > 0:
        accident_rate = exposure_cfg.get('accident_rate_per_load_unit', 0.0001)
        variation_range = exposure_cfg.get('random_variation_range', [0.7, 1.3])

        exposure_risk = accident_rate * daily_load
        exposure_risk *= random.uniform(variation_range[0], variation_range[1])

    # ========================================
    # MECHANISM 3: BASELINE RISK
    # ========================================
    baseline_risk = baseline_cfg.get('daily_risk', 0.002)
    baseline_wellness_amp = baseline_cfg.get('wellness_amplification', 0.3)

    if undertrained_threshold <= acwr <= optimal_upper:
        wellness_vulnerability = _calculate_wellness_vulnerability(day_data, fatigue, form)
        baseline_risk *= (1.0 + wellness_vulnerability * baseline_wellness_amp)

    # ========================================
    # COMBINE MECHANISMS
    # ========================================
    total_risk = physiological_risk + exposure_risk + baseline_risk

    # ========================================
    # DETERMINE INJURY TYPE BY ACWR ZONE
    # ========================================
    # The injury_type reflects the PRIMARY causal mechanism based on ACWR zone,
    # not which risk component happened to be numerically highest.
    # This is critical for proving the asymmetry hypothesis in validation.

    high_risk_threshold = thresholds.get('danger_zone', thresholds.get('high_risk', 1.5))

    if acwr < undertrained_threshold:
        # UNDERTRAINED ZONE: Primary mechanism is physiological detraining
        # Even if exposure_risk is higher (from some residual training),
        # the root cause is the undertrained state causing tissue vulnerability
        injury_type = 'physiological'
    elif acwr > high_risk_threshold:
        # HIGH RISK ZONE: Primary mechanism is exposure/overload
        # The athlete is doing too much too fast, leading to overuse injuries
        injury_type = 'exposure'
    elif acwr > optimal_upper:
        # DANGER ZONE (1.3-1.5): Transitional - could be either mechanism
        # Use the higher risk component to decide
        if exposure_risk > baseline_risk:
            injury_type = 'exposure'
        else:
            injury_type = 'baseline'
    else:
        # OPTIMAL ZONE (0.8-1.3): Primary mechanism is baseline/random
        # These are the "inevitable" injuries that occur even with perfect load management
        injury_type = 'baseline'

    min_prob = bounds.get('min_probability', 0.001)
    max_prob = bounds.get('max_probability', 0.08)
    total_risk = min(max_prob, max(min_prob, total_risk))

    return total_risk, injury_type


def _calculate_wellness_vulnerability(day_data, fatigue, form):
    """
    Calculate wellness vulnerability score (0-1).
    This modifies injury risk but doesn't cause injuries alone.

    Configuration loaded from: config/simulation_config.yaml
    """
    # Load configuration
    weights = cfg.wellness_weights()
    sleep_cfg = cfg.get('wellness_vulnerability.sleep', {})
    stress_cfg = cfg.get('wellness_vulnerability.stress', {})

    target_sleep = sleep_cfg.get('target_hours', 7.0)
    deficit_scale = sleep_cfg.get('deficit_scale', 3.0)

    sleep_hours = day_data.get('sleep_hours', 7.5)
    sleep_deficit = max(0, (target_sleep - sleep_hours) / deficit_scale)

    sleep_quality = day_data.get('sleep_quality', 0.7)
    poor_sleep_quality = 1.0 - sleep_quality

    # === ENHANCED STRESS SENSITIVITY ===
    stress = day_data.get('stress', 40)
    stress_norm = stress / 100.0

    boost_threshold = stress_cfg.get('boost_threshold', 50)
    boost_exponent = stress_cfg.get('boost_exponent', 1.5)
    max_boost = stress_cfg.get('max_boost_multiplier', 3.0)

    if stress > boost_threshold:
        stress_excess = (stress - boost_threshold) / (100 - boost_threshold)
        stress_boost = 1.0 + (stress_excess ** boost_exponent) * (max_boost - 1.0)
        high_stress = stress_norm * stress_boost
    else:
        high_stress = stress_norm

    body_battery = day_data.get('body_battery_morning', 75)
    low_recovery = 1.0 - (body_battery / 100.0)

    fatigue_norm = min(1.0, max(0.0, fatigue / 100.0))
    form_risk = max(0.0, min(1.0, -form / 30.0))

    vulnerability = (
        weights.get('sleep_deficit', 0.25) * sleep_deficit +
        weights.get('poor_sleep_quality', 0.15) * poor_sleep_quality +
        weights.get('high_stress', 0.20) * high_stress +
        weights.get('low_recovery', 0.15) * low_recovery +
        weights.get('fatigue', 0.15) * fatigue_norm +
        weights.get('negative_form', 0.10) * form_risk
    )

    return min(1.0, max(0.0, vulnerability))


# Keep old function for backwards compatibility
def calculate_injury_probability(day_data, athlete, fatigue, form, acwr=1.0):
    """Legacy wrapper - calls the new asymmetric model."""
    daily_load = day_data.get('actual_tss', 50)
    prob, _ = calculate_injury_probability_asymmetric(
        day_data, athlete, fatigue, form, acwr, daily_load
    )
    return prob


def generate_load_spike_schedule(year=2024):
    """
    Generate a schedule of training load spikes throughout the year.

    Configuration loaded from: config/simulation_config.yaml

    Returns list of (start_day, duration, multiplier, spike_type) tuples
    """
    spikes = []

    # Training camps
    camps_cfg = cfg.load_spike_config('camps')
    count_range = camps_cfg.get('count_range', [3, 4])
    duration_range = camps_cfg.get('duration_range', [5, 10])
    multiplier_range = camps_cfg.get('multiplier_range', [1.6, 2.2])
    allowed_months = camps_cfg.get('allowed_months', [2, 3, 4, 5, 6, 7, 8, 9])

    num_camps = random.randint(count_range[0], count_range[1])
    camp_months = random.sample(allowed_months, min(num_camps, len(allowed_months)))
    for month in camp_months:
        start_day = (month - 1) * 30 + random.randint(5, 20)
        duration = random.randint(duration_range[0], duration_range[1])
        multiplier = random.uniform(multiplier_range[0], multiplier_range[1])
        spikes.append((start_day, duration, multiplier, 'camp'))

    # Return from rest periods
    returns_cfg = cfg.load_spike_config('returns')
    count_range = returns_cfg.get('count_range', [4, 6])
    duration_range = returns_cfg.get('duration_range', [3, 7])
    multiplier_range = returns_cfg.get('multiplier_range', [1.5, 2.0])

    num_returns = random.randint(count_range[0], count_range[1])
    for _ in range(num_returns):
        start_day = random.randint(30, 330)
        duration = random.randint(duration_range[0], duration_range[1])
        multiplier = random.uniform(multiplier_range[0], multiplier_range[1])
        spikes.append((start_day, duration, multiplier, 'return'))

    # Overreaching blocks
    overreach_cfg = cfg.load_spike_config('overreach')
    count_range = overreach_cfg.get('count_range', [3, 5])
    duration_range = overreach_cfg.get('duration_range', [5, 10])
    multiplier_range = overreach_cfg.get('multiplier_range', [1.4, 1.8])

    num_overreach = random.randint(count_range[0], count_range[1])
    for _ in range(num_overreach):
        start_day = random.randint(60, 300)
        duration = random.randint(duration_range[0], duration_range[1])
        multiplier = random.uniform(multiplier_range[0], multiplier_range[1])
        spikes.append((start_day, duration, multiplier, 'overreach'))

    # Acute spikes
    acute_cfg = cfg.load_spike_config('acute')
    count_range = acute_cfg.get('count_range', [6, 10])
    duration_range = acute_cfg.get('duration_range', [1, 3])
    multiplier_range = acute_cfg.get('multiplier_range', [1.8, 2.5])

    num_acute = random.randint(count_range[0], count_range[1])
    for _ in range(num_acute):
        start_day = random.randint(30, 340)
        duration = random.randint(duration_range[0], duration_range[1])
        multiplier = random.uniform(multiplier_range[0], multiplier_range[1])
        spikes.append((start_day, duration, multiplier, 'acute'))

    # Reduced load periods
    reduced_cfg = cfg.load_spike_config('reduced')
    count_range = reduced_cfg.get('count_range', [3, 5])
    duration_range = reduced_cfg.get('duration_range', [7, 14])
    multiplier_range = reduced_cfg.get('multiplier_range', [0.2, 0.5])

    num_reduced = random.randint(count_range[0], count_range[1])
    for _ in range(num_reduced):
        start_day = random.randint(30, 330)
        duration = random.randint(duration_range[0], duration_range[1])
        multiplier = random.uniform(multiplier_range[0], multiplier_range[1])
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
    except (ImportError, OSError, ValueError):
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
    false_alarm_cfg = cfg.get('false_alarms', {})
    first_alarm_range = false_alarm_cfg.get('first_alarm_days', [30, 60])
    days_to_next_false_alarm = random.randint(first_alarm_range[0], first_alarm_range[1])

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

        # === GLASS-BOX: Save training context for explainability ===
        day_data['load_scenario'] = spike_type if spike_type else 'normal_training'
        day_data['load_multiplier'] = round(load_multiplier, 2)

        # Modify TSS based on load spike (training camp, overreaching, rest period, etc.)
        original_tss = day_data['actual_tss']
        day_data['actual_tss'] = original_tss * load_multiplier

        # Also add some daily random variation to increase ACWR variability
        daily_var_range = cfg.get('load_spikes.daily_variation_range', [0.85, 1.15])
        daily_variation = random.uniform(daily_var_range[0], daily_var_range[1])
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
                preinjury_cfg = cfg.get('preinjury_patterns', {})
                lookback_days = preinjury_cfg.get('lookback_days', 14)
                daily_data = inject_realistic_injury_patterns(
                    athlete,
                    daily_data,
                    len(daily_data) - 1,  # Current day index
                    lookback_days
                )
                day_data['injury'] = 1
                recovery_cfg = cfg.get('injury_model.recovery_days', {})
                recovery_range = recovery_cfg.get('baseline', [3, 10])
                recovery_days_remaining = np.random.randint(recovery_range[0], recovery_range[1])
                pending_injury_date = None
            else:
                # ==========================================================
                # ASYMMETRIC ACWR INJURY MODEL
                # Two separate mechanisms based on PMData analysis:
                # 1. Physiological (undertrained): 2.66x risk per load unit
                # 2. Stochastic Exposure (high load): constant risk per load unit
                # ==========================================================

                daily_load = day_data.get('actual_tss', 50)

                # === GLASS-BOX: Calculate and save wellness vulnerability ===
                wellness_vuln = _calculate_wellness_vulnerability(day_data, fatigue, form)
                day_data['wellness_vulnerability'] = round(wellness_vuln, 3)

                injury_prob, injury_type = calculate_injury_probability_asymmetric(
                    day_data, athlete, fatigue, form, acwr, daily_load
                )

                # === GLASS-BOX: Save computed injury probability for analysis ===
                day_data['injury_probability'] = round(injury_prob, 4)

                # Apply modulations (Menstrual)
                if modulations and 'injury_risk_modifier' in modulations:
                    injury_prob *= modulations['injury_risk_modifier']

                # Apply modulations (Circadian)
                if 'circadian_injury_modifier' in day_data:
                    injury_prob *= day_data['circadian_injury_modifier']

                # Roll for injury
                if random.random() < injury_prob:
                    day_data['injury'] = 1
                    day_data['injury_type'] = injury_type  # Track mechanism for analysis

                    # Recovery time varies by injury type (from config)
                    recovery_cfg = cfg.get('injury_model.recovery_days', {})
                    if injury_type == 'physiological':
                        # Physiological injuries (tissue damage) take longer to heal
                        recovery_range = recovery_cfg.get('physiological', [5, 12])
                        recovery_days_remaining = np.random.randint(recovery_range[0], recovery_range[1])
                    elif injury_type == 'exposure':
                        # Exposure injuries (accidents) vary widely
                        recovery_range = recovery_cfg.get('exposure', [2, 10])
                        recovery_days_remaining = np.random.randint(recovery_range[0], recovery_range[1])
                    else:
                        # Baseline injuries
                        recovery_range = recovery_cfg.get('baseline', [3, 7])
                        recovery_days_remaining = np.random.randint(recovery_range[0], recovery_range[1])
                else:
                    day_data['injury'] = 0
                    day_data['injury_type'] = None
        else:
            # Still in recovery period
            day_data['injury'] = 1
            day_data['injury_type'] = 'recovery'  # Mark as recovery period
            day_data['wellness_vulnerability'] = None
            day_data['injury_probability'] = None
            recovery_days_remaining -= 1

        # === GLASS-BOX: Always save ACWR for time-series analysis ===
        day_data['acwr'] = round(acwr, 3) if acwr else None

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
            # Insert a false alarm pattern (from config)
            duration_range = false_alarm_cfg.get('duration_days', [7, 12])
            false_alarm_days = random.randint(duration_range[0], duration_range[1])
            create_false_alarm_patterns(athlete, daily_data, len(daily_data) - 1, false_alarm_days)
            # Schedule next false alarm (from config)
            interval_range = false_alarm_cfg.get('interval_days', [20, 35])
            days_to_next_false_alarm = random.randint(interval_range[0], interval_range[1])

    
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
                'injury': daily_entry['injury'],
                # === GLASS-BOX COLUMNS (Explainability) ===
                'injury_type': daily_entry.get('injury_type'),  # physiological, exposure, baseline, recovery
                'acwr': daily_entry.get('acwr'),  # Acute:Chronic Workload Ratio
                'load_scenario': daily_entry.get('load_scenario'),  # camp, return, overreach, acute, reduced, normal_training
                'load_multiplier': daily_entry.get('load_multiplier'),  # Training load multiplier applied
                'wellness_vulnerability': daily_entry.get('wellness_vulnerability'),  # 0-1 vulnerability score
                'injury_probability': daily_entry.get('injury_probability')  # Computed injury probability
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
