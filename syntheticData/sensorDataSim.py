import random
import numpy as np

# Random seed for reproducibility
np.random.seed(42)
random.seed(42)

def simulate_morning_sensor_data(athlete, date, prev_day, recovery_days_remaining, max_daily_tss):
    # Basic structure for daily metrics
    daily_data = {
        'athlete_id': athlete['id'],
        'date': date,
        'resting_hr': None,
        'hrv': None,
        'sleep_hours': None,
        'deep_sleep': None,
        'light_sleep': None,
        'rem_sleep': None,
        'sleep_quality': None,
        'body_battery_morning': None,
        'stress': None,
        'body_battery_evening': None,
        'workout_data': None,
        'injury': 0
    }

    baseline_sleep = athlete['sleep_time_norm'] * athlete['sleep_quality']

    training_stress = prev_day['training_stress'] if prev_day else 0
    stress_level_yesterday = prev_day['stress'] if prev_day else 30
    fatigue = prev_day['fatigue'] if prev_day else 30

    # Calculate recovery score (0-1 scale, higher is better recovery)
    recovery_score = max(0, 1 - (fatigue / 150))

    # Calculate injury effect (0-1 scale)
    injury_effect = 0
    if recovery_days_remaining > 0:
        # Stronger effect when recovery_days_remaining is closer to 10 which is the maximum in the model
        injury_effect = recovery_days_remaining / 10
    
    # Simulate resting metrics
    fatigue_factor = min(fatigue / 100, 1)  # Normalize fatigue effect
    stress_factor = min(stress_level_yesterday / 100, 1)  # Normalize stress effect

    # Simulate sleep hours centered around athlete's norm
    sleep_norm = athlete['sleep_time_norm']
    sleep_variation = random.normalvariate(0, 0.5)
    
    # Sleep affected by fatigue (tired athletes may sleep more) and injury
    fatigue_sleep_effect = 0.1 * fatigue_factor - 0.2 * injury_effect
    stress_effect = 0.1 * stress_factor
    sleep_hours = sleep_norm + fatigue_sleep_effect - stress_effect + sleep_variation
    sleep_hours = max(sleep_hours, 4.0)  # Set minimum sleep

    # Sleep stages with more realistic proportions
    # Deep sleep typically 10-25% of total sleep
    # REM sleep typically 20-25% of total sleep
    # Light sleep makes up the rest
    
    # Calculate base proportions
    base_deep_pct = 0.20  # 20% deep sleep baseline
    base_rem_pct = 0.23   # 23% REM sleep baseline
    
    # Adjust proportions based on fatigue, stress and injury
    deep_sleep_pct = base_deep_pct - (0.05 * fatigue_factor) - (0.07 * injury_effect) - (0.03 * stress_factor)
    rem_sleep_pct = base_rem_pct - (0.03 * fatigue_factor) - (0.05 * injury_effect) - (0.02 * stress_factor)
    
    # Ensure percentages remain physiologically plausible
    deep_sleep_pct = max(0.08, min(deep_sleep_pct, 0.25))
    rem_sleep_pct = max(0.15, min(rem_sleep_pct, 0.25))
    light_sleep_pct = 1 - deep_sleep_pct - rem_sleep_pct
    
    # Calculate actual sleep times
    deep_sleep = sleep_hours * deep_sleep_pct
    rem_sleep = sleep_hours * rem_sleep_pct
    light_sleep = sleep_hours * light_sleep_pct

    sleep_quality = calculate_sleep_quality(sleep_hours, deep_sleep, light_sleep, rem_sleep)
    night_sleep = sleep_hours * sleep_quality
    sleep_debt = max(0, baseline_sleep - night_sleep)
    training_stress_surplus = max(0, training_stress - max_daily_tss)

    excessive_fatigue = prev_day['form'] < -20
    high_load = training_stress > max_daily_tss
    overtraining_risk = prev_day['form'] < -20 and training_stress > max_daily_tss
    peaking = 35 > prev_day['form'] > 20
    high_stress = stress_level_yesterday > 50

    rhr_deviation = (
        1.5 * sleep_debt  +                                     # Sleep debt impact
        0.2 * injury_effect * athlete['resting_hr'] +           # Injury impact (scaled to baseline)
        0.1 * fatigue_factor * athlete['resting_hr'] -          # Fatigue impact (scaled to baseline)
        0.03 * recovery_score * athlete['resting_hr'] -         # Recovery benefit (scaled to baseline)
        0.02 * max(0, sleep_quality - 0.7) * athlete['resting_hr']  # Good sleep benefit (scaled to baseline)
    )

    if overtraining_risk:
        rhr_deviation += 0.12 * athlete['resting_hr']  # Significant increase when both fatigued and high load
    elif excessive_fatigue:
        rhr_deviation += 0.08 * athlete['resting_hr']  # Substantial increase when athlete is very fatigued
    elif high_load:
        rhr_deviation += 0.06 * athlete['resting_hr']  # Moderate increase from high training load
    elif peaking:
        rhr_deviation -= 0.02 * athlete['resting_hr']  # Slight decrease during peak form
    elif high_stress:
        rhr_deviation += 0.04 * athlete['resting_hr']  # Modest increase from psychological stress
    else:
        rhr_deviation += random.normalvariate(0, 0.01 * athlete['resting_hr'])  # Small random variation in normal conditions
    
    # Add temporal correlation (if previous day exists)
    if prev_day and 'resting_hr' in prev_day:
        yesterday_rhr_deviation = prev_day['resting_hr'] - athlete['resting_hr']
        rhr_deviation = 0.7 * rhr_deviation + 0.3 * yesterday_rhr_deviation
    
    # Calculate final RHR 
    rhr = athlete['resting_hr'] + rhr_deviation 
    
    # Ensure RHR stays within physiological bounds (±15% of baseline)
    min_rhr = athlete['resting_hr'] * 0.85
    max_rhr = athlete['resting_hr'] * 1.15
    rhr = max(min_rhr, min(rhr, max_rhr))

    # Calculate HRV with bidirectional effects (note: HRV and RHR are generally inversely related)
    hrv_baseline = athlete['hrv_baseline']

    expanded_boundaries = prev_day['form'] < -20 or training_stress > max_daily_tss

    if expanded_boundaries:
        min_hrv = hrv_baseline * 0.6  # Allow wider range when excessively fatigued
        max_hrv = hrv_baseline * 1.4
    else:
        min_hrv = hrv_baseline * 0.85  # Normal range: ±15%
        max_hrv = hrv_baseline * 1.15
    
    hrv_deviation = (
        -3.0 * sleep_debt -                                    # Sleep debt impact (negative)
        0.25 * injury_effect * hrv_baseline -                  # Injury impact (negative, scaled)
        0.15 * fatigue_factor * hrv_baseline +                 # Fatigue impact (negative, scaled)
        0.1 * recovery_score * hrv_baseline +                  # Recovery benefit (positive, scaled)
        0.05 * max(0, sleep_quality - 0.7) * hrv_baseline      # Good sleep benefit (positive, scaled)
    )

    if overtraining_risk:
        hrv_deviation -= 0.15 * hrv_baseline  # Significant decrease when both fatigued and high load
    elif excessive_fatigue:
        hrv_deviation -= 0.1 * hrv_baseline   # Substantial decrease when athlete is very fatigued
    elif high_load:
        hrv_deviation -= 0.08 * hrv_baseline  # Moderate decrease from high training load
    elif peaking:
        hrv_deviation += 0.05 * hrv_baseline  # Slight increase during peak form
    elif high_stress:
        hrv_deviation -= 0.07 * hrv_baseline  # Modest decrease from psychological stress
    else:
        hrv_deviation += random.normalvariate(0, 0.02 * hrv_baseline)  # Small random variation in normal conditions
    
    # Add temporal correlation (if previous day exists)
    if prev_day and 'hrv' in prev_day:
        yesterday_hrv_deviation = prev_day['hrv'] - hrv_baseline
        hrv_deviation = 0.7 * hrv_deviation + 0.3 * yesterday_hrv_deviation
    
    # Calculate final HRV
    hrv = hrv_baseline + hrv_deviation 
    
    # Ensure HRV stays within physiological bounds (±15% of baseline unless excessively fatigued or excessive training)
    hrv = max(min_hrv, min(hrv, max_hrv))
    
    # Calculate body battery (0-100 scale)
    morning_body_battery = calculate_morning_body_battery(athlete, prev_day, sleep_quality, sleep_hours, hrv, rhr, stress_level_yesterday, recovery_score, injury_effect)

    # Morning metrics
    daily_data['resting_hr'] = rhr
    daily_data['hrv'] = hrv
    daily_data['sleep_hours'] = sleep_hours
    daily_data['deep_sleep'] = deep_sleep
    daily_data['light_sleep'] = light_sleep
    daily_data['rem_sleep'] = rem_sleep
    daily_data['sleep_quality'] = sleep_quality
    daily_data['body_battery_morning'] = morning_body_battery

    return daily_data

def simulate_evening_sensor_data(athlete, fatigue, daily_data):
    smoking_factor = athlete['smoking_factor']
    alcohol_factor = athlete['drinking_factor']
    life_stress_factor = athlete['stress_factor']
    hrv = daily_data['hrv']
    base_resting_hr = athlete['resting_hr']
    resting_hr = daily_data['resting_hr']
    sleep_quality = daily_data['sleep_quality']
    body_battery_morning = daily_data['body_battery_morning']
    training_stress = daily_data['actual_tss']

    # Calculate stress factors
    stress_factors = (
        10 * smoking_factor + 10 * alcohol_factor + 10 * life_stress_factor + 
        0.2 * (100 - hrv) + 0.1 * (resting_hr - base_resting_hr) + 0.1 * (100 - sleep_quality) + 
        0.3 * (100 - body_battery_morning) + 0.2 * fatigue
    )

    # Normalize stress factors to 0-100 range
    stress = min(max(stress_factors, 0), 100)

    # Calculate evening body battery
    base_decay = 20  # Natural decay throughout the day

    # Adjust decay based on starting value
    if body_battery_morning > 80:
        decay_modifier = 1.5  # Higher starting values decay faster
    elif body_battery_morning < 40:
        decay_modifier = 1.0  # Lower starting values decay slower
    else:
        decay_modifier = 1.2

    if training_stress < 50:
        decay_modifier *= 2
    elif training_stress > 150:
        decay_modifier *= 0.5

    # Calculate workout drain (non-linear)
    workout_drain = training_stress * (0.085 + (training_stress / 400) * 0.1)  # Increases with intensity

    # Calculate stress drain
    stress_drain = stress * 0.4

    # Calculate fatigue drain
    fatigue_drain = fatigue * 0.1

    # Calculate total drain
    total_drain = (base_decay * decay_modifier) + workout_drain + stress_drain

    # Calculate evening body battery
    body_battery_evening = body_battery_morning - total_drain - fatigue_drain + np.random.normal(0, 2)
    body_battery_evening = round(min(max(body_battery_evening, 5), 100), 1)

    # Update daily data
    daily_data['stress'] = stress
    daily_data['body_battery_evening'] = body_battery_evening



def calculate_sleep_quality(sleep_hours, deep_sleep, light_sleep, rem_sleep):
    """
    Calculate sleep quality score based on sleep duration and stages.
    
    Parameters:
    sleep_hours (float): Total sleep hours
    deep_sleep (float): Hours of deep sleep
    light_sleep (float): Hours of light sleep
    rem_sleep (float): Hours of REM sleep
    
    Returns:
    float: Sleep quality score between 0-1
    """
    # Ideal sleep stage proportions based on research
    # Healthy adults typically need:
    IDEAL_DEEP_PERCENT = 0.25  # ~25% of sleep should be deep sleep
    IDEAL_REM_PERCENT = 0.25   # ~25% of sleep should be REM sleep
    IDEAL_LIGHT_PERCENT = 0.50 # ~50% of sleep should be light sleep
    
    # Base sleep duration factor (optimal is 7-9 hours for adults)
    if sleep_hours >= 7 and sleep_hours <= 9:
        duration_factor = 1.0
    elif sleep_hours >= 6 and sleep_hours < 7:
        duration_factor = 0.85
    elif sleep_hours > 9 and sleep_hours <= 10:
        duration_factor = 0.9
    elif sleep_hours >= 5 and sleep_hours < 6:
        duration_factor = 0.7
    elif sleep_hours > 10:
        duration_factor = 0.8
    else:  # less than 5 hours
        duration_factor = max(0.4, sleep_hours / 10)
    
    # Calculate actual percentages
    total_sleep = max(0.1, sleep_hours)  # Prevent division by zero
    deep_sleep_percent = deep_sleep / total_sleep
    light_sleep_percent = light_sleep / total_sleep
    rem_sleep_percent = rem_sleep / total_sleep
    
    # Calculate how close each sleep stage is to ideal (as a percentage)
    # Using a function that penalizes more for too little than too much
    def stage_quality(actual, ideal):
        if actual >= ideal:
            # Less penalty for excess (diminishing returns)
            return 1.0 - 0.5 * min(1.0, (actual - ideal) / ideal)
        else:
            # Higher penalty for deficiency
            return actual / ideal
    
    deep_quality = stage_quality(deep_sleep_percent, IDEAL_DEEP_PERCENT)
    rem_quality = stage_quality(rem_sleep_percent, IDEAL_REM_PERCENT)
    light_quality = stage_quality(light_sleep_percent, IDEAL_LIGHT_PERCENT)
    
    # Weight the importance of each sleep stage
    # Research suggests deep sleep and REM are more important for recovery
    stage_quality_score = (
        deep_quality * 0.45 +    # Deep sleep most important for physical recovery
        rem_quality * 0.35 +     # REM important for mental recovery
        light_quality * 0.20     # Light sleep least critical but still needed
    )
    
    # Combine duration and quality factors
    # Both are important but poor quality affects recovery more than slightly short duration
    sleep_quality = (duration_factor * 0.4) + (stage_quality_score * 0.6)
    
    # Ensure the result is between 0 and 1
    return min(1.0, max(0.0, sleep_quality))

def calculate_morning_body_battery(athlete, prev_day, sleep_quality, sleep_hours, hrv, rhr, stress_level_yesterday, recovery_score, injury_effect):
    # Start with previous evening's body battery value (if available)
    # Otherwise start at a reasonable default
    last_body_battery = prev_day['body_battery_evening'] if prev_day and 'body_battery_evening' in prev_day else 30
    
    # Calculate recharge amount based on sleep quality and duration
    sleep_norm = athlete['sleep_time_norm']
    
    # Sleep recharge (higher quality and longer duration = more recharge)
    # Maximum recharge of about 50 points with optimal sleep
    max_recharge = 100 - last_body_battery 
    sleep_efficiency = sleep_quality * (min(sleep_hours / sleep_norm, 1.2))  # Cap benefit at 120% of normal
    sleep_recharge = max_recharge * sleep_efficiency
    
    # Recovery adjustments
    hrv_factor = hrv / athlete['hrv_baseline']  # Normalized HRV (1.0 = baseline)
    rhr_factor = athlete['resting_hr'] / rhr    # Inverted RHR factor (higher = better)
    
    # Adjust recharge based on physiological recovery markers
    recovery_multiplier = (0.7 * hrv_factor + 0.3 * rhr_factor) * recovery_score * 2.5
    adjusted_recharge = sleep_recharge * recovery_multiplier
    
    # Drain factors from previous day (if available)
    previous_drain = 0
    if prev_day:
        # Stress drains body battery
        stress_drain = stress_level_yesterday * 0.2
        
        # Training stress drains body battery
        training_drain = prev_day.get('training_stress', 0) * 0.15
        
        previous_drain = stress_drain + training_drain
    
    # Injury reduces body battery
    injury_drain = injury_effect * 15
    
    # Calculate new body battery
    new_body_battery = last_body_battery + adjusted_recharge - previous_drain - injury_drain
    
    # Apply diminishing returns as we approach 100
    if new_body_battery > 80:
        # Dampen recharge as we get closer to 100
        excess = new_body_battery - 80
        new_body_battery = 80 + (excess * 0.6)
    
    # Apply floor and ceiling
    new_body_battery = max(min(new_body_battery, 100), 60)
    
    # Round to nearest whole number
    return round(new_body_battery)