import numpy as np
import pandas as pd
import random
import json
from datetime import datetime, timedelta

# Constants
N_ATHLETES = 5
N_DAYS = 15
INJURY_RATE = 0.12  # 12% of athlete-days should have an injury
TOTAL_ENTRIES = N_ATHLETES * N_DAYS

# Random seed for reproducibility
np.random.seed(42)
random.seed(42)

athlete_profiles = {}

for athlete_id in range(1, N_ATHLETES + 1):
    age = np.random.randint(18, 50)  # Triathletes range from 18 to 50
    gender = np.random.choice(["Male", "Female"])

    # Generate correlated attributes
    base_vo2max = np.random.normal(55, 7)  # Normal distribution, mean 55, std 7
    base_vo2max = np.clip(base_vo2max, 40, 75)  # Limit realistic range

    ftp = base_vo2max * np.random.uniform(4.0, 5.5)  # Strong correlation (FTP ~ 4-5.5x VO2max)
    ftp = round(np.clip(ftp, 160, 400))  # Ensure realistic FTP values

    weekly_training_hours = np.interp(base_vo2max, [40, 75], [7, 20])  # More VO2max = More training
    weekly_training_hours += np.random.uniform(-2, 2)  # Some individual variation
    weekly_training_hours = max(7, weekly_training_hours)  # Ensure min 7h/week

    # Resting HR inverse correlation with fitness
    base_resting_hr = np.interp(base_vo2max, [40, 75], [52, 38])  
    base_resting_hr += np.random.uniform(-3, 3)  # Small variation
    base_resting_hr = round(np.clip(base_resting_hr, 35, 55))  

    # HRV baseline - strongly correlated with fitness level and inversely with age
    base_hrv = np.interp(base_vo2max, [40, 75], [60, 95])
    age_adjustment = np.interp(age, [18, 50], [5, -10])
    base_hrv += age_adjustment
    base_hrv = round(np.clip(base_hrv, 40, 110))

    # Max HR slightly decreases with age
    max_hr = 220 - age + np.random.randint(-5, 5)  

    # Base athlete type: high-volume vs. high-intensity preference
    training_style = np.random.choice(["High Volume", "High Intensity"], p=[0.7, 0.3])

    # Assign altitude preference (some athletes live/train at altitude)
    base_altitude = np.random.choice([0, 500, 1000, 2000], p=[0.7, 0.15, 0.1, 0.05])

    # Recovery capacity (affects injury recovery and fatigue)
    recovery_capacity = np.random.normal(7, 1.5)  # Scale of 1-10, normally distributed
    recovery_capacity = round(np.clip(recovery_capacity, 3, 10), 1)
    # Age-based recovery adjustment
    if age > 40:
        recovery_capacity -= (age - 40) * 0.1

    # Store athlete profile
    athlete_profiles[athlete_id] = {
        "Age": age,
        "Gender": gender,
        "VO2max": round(base_vo2max, 1),
        "FTP": ftp,
        "Weekly_Training_Hours": round(weekly_training_hours, 1),
        "Resting_HR": base_resting_hr,
        "Base_HRV": base_hrv,
        "Max_HR": max_hr,
        "Training_Style": training_style,
        "Base_Altitude": base_altitude,
        "Recovery_Capacity": recovery_capacity
    }

# Convert to DataFrame
df_profiles = pd.DataFrame.from_dict(athlete_profiles, orient="index")

# Save athlete profiles to CSV
df_profiles.to_csv("athlete_profiles.csv", index_label="Athlete_ID")

print(df_profiles.head(10))

# Generate dates for 1 year
start_date = datetime(2024, 1, 1)
dates = [start_date + timedelta(days=i) for i in range(N_DAYS)]

# Training periodization parameters
def generate_training_plan(athlete_id, start_date, n_days):
    """Generate a periodized training plan for an athlete over a year."""
    
    # Define key races/events throughout the year
    # Format: (days from start, importance 1-10)
    athlete = athlete_profiles[athlete_id]
    
    # Each athlete gets 3-5 A/B races throughout the year
    n_races = np.random.randint(3, 6)
    races = []
    
    # Ensure races are reasonably spaced (at least 30 days apart)
    min_race_separation = 30
    available_days = list(range(60, n_days - 30))  # No races in first 2 months or last month
    
    for _ in range(n_races):
        if not available_days:
            break
            
        race_day = random.choice(available_days)
        importance = np.random.choice([10, 8], p=[0.4, 0.6])  # 40% A races, 60% B races
        races.append((race_day, importance))
        
        # Remove nearby days from consideration
        available_days = [d for d in available_days if abs(d - race_day) > min_race_separation]
    
    # Add some C-priority races (shorter/less important)
    n_c_races = np.random.randint(2, 5)
    for _ in range(n_c_races):
        if not available_days:
            break
            
        race_day = random.choice(available_days)
        races.append((race_day, 5))  # C races importance = 5
        
        # Remove nearby days from consideration (15 days for C races)
        available_days = [d for d in available_days if abs(d - race_day) > 15]
    
    # Sort races by date
    races.sort()
    
    # Generate daily training load targets based on periodization
    daily_load_targets = np.zeros(n_days)
    acute_load_targets = np.zeros(n_days)
    
    # Base training load parameters
    if athlete["Training_Style"] == "High Volume":
        base_load = 0.7
        peak_load = 0.9
    else:  # High Intensity
        base_load = 0.65
        peak_load = 0.95
    
    # Weekly undulation pattern (harder/easier days)
    weekly_pattern = [0.9, 0.7, 1.0, 0.5, 0.8, 1.0, 0.3]  # Su,M,T,W,Th,F,Sa
    
    # Apply base load pattern first
    for day in range(n_days):
        weekday = (day + start_date.weekday()) % 7
        daily_load_targets[day] = base_load * weekly_pattern[weekday]
    
    # Now apply periodization for each race
    for race_day, importance in races:
        # Race day itself is recovery or very light
        daily_load_targets[race_day] = 0.1 if importance > 8 else 0.2
        
        # Taper period (length depends on race importance)
        taper_length = 14 if importance > 8 else 7
        for i in range(1, taper_length + 1):
            if race_day - i >= 0:
                taper_factor = i / taper_length
                daily_load_targets[race_day - i] = max(0.3, daily_load_targets[race_day - i] * taper_factor)
        
        # Build period (3-4 weeks depending on race importance)
        build_length = 28 if importance > 8 else 21
        for i in range(taper_length + 1, taper_length + build_length + 1):
            if race_day - i >= 0:
                # Progressive overload during build
                build_intensity = min(peak_load, base_load + (peak_load - base_load) * 
                                     (1 - (i - taper_length) / build_length))
                daily_load_targets[race_day - i] = build_intensity * weekly_pattern[(race_day - i + start_date.weekday()) % 7]
        
        # Recovery after race (proportional to race importance)
        recovery_days = 7 if importance > 8 else 3
        for i in range(1, recovery_days + 1):
            if race_day + i < n_days:
                daily_load_targets[race_day + i] = 0.3 + (0.2 * i / recovery_days)
    
    # Calculate acute training load (7-day rolling average) for CTL/ATL calculation
    for day in range(n_days):
        if day < 7:
            acute_load_targets[day] = np.mean(daily_load_targets[:day+1])
        else:
            acute_load_targets[day] = np.mean(daily_load_targets[day-7:day+1])
    
    # Add some random variation (life happens)
    random_factors = np.random.normal(1, 0.15, n_days)
    random_factors = np.clip(random_factors, 0.7, 1.3)
    daily_load_targets = daily_load_targets * random_factors
    
    # Ensure load is between 0 and 1
    daily_load_targets = np.clip(daily_load_targets, 0, 1)
    
    return daily_load_targets, races

# Generate training plans for all athletes
athlete_training_plans = {}
athlete_races = {}

for athlete_id in range(1, N_ATHLETES + 1):
    plan, races = generate_training_plan(athlete_id, start_date, N_DAYS)
    athlete_training_plans[athlete_id] = plan
    athlete_races[athlete_id] = races

def calculate_sleep_quality(light, deep, rem, awake, total_in_bed_min=None):
    """
    Calculate sleep score based on multiple factors similar to commercial wearables.
    
    Parameters:
    - light, deep, rem: minutes in each sleep stage
    - awake: minutes awake during sleep period
    - total_in_bed_min: total time in bed (if None, calculated from other parameters)
    
    Returns: Sleep score from 0-100
    """
    # Calculate total time in bed if not provided
    if total_in_bed_min is None:
        total_in_bed_min = light + deep + rem + awake
    
    # Calculate actual sleep time
    total_sleep_min = light + deep + rem
    
    # 1. Duration component (30% of score)
    # Optimal sleep is between 7-9 hours (420-540 min)
    if total_sleep_min >= 480:
        duration_score = 30
    elif total_sleep_min >= 420:
        duration_score = 25 + (total_sleep_min - 420) * (5 / 60)
    elif total_sleep_min >= 360:
        duration_score = 20 + (total_sleep_min - 360) * (5 / 60)
    elif total_sleep_min >= 300:
        duration_score = 15 + (total_sleep_min - 300) * (5 / 60)
    else:
        duration_score = max(0, total_sleep_min / 300 * 15)
    
    # 2. Sleep efficiency component (25% of score)
    sleep_efficiency = total_sleep_min / total_in_bed_min if total_in_bed_min > 0 else 0
    efficiency_score = min(25, sleep_efficiency * 25)
    
    # 3. Sleep composition component (30% of score)
    # Ideal sleep composition: ~15-20% deep, ~20-25% REM, ~55-65% light
    if total_sleep_min > 0:
        deep_percent = deep / total_sleep_min * 100
        rem_percent = rem / total_sleep_min * 100
        
        # Score deep sleep (optimal around 15-20%)
        if deep_percent >= 15 and deep_percent <= 20:
            deep_score = 15
        elif deep_percent > 20:
            deep_score = 15 - min(5, (deep_percent - 20) * 0.5)
        else:  # deep_percent < 15
            deep_score = deep_percent / 15 * 15
        
        # Score REM sleep (optimal around 20-25%)
        if rem_percent >= 20 and rem_percent <= 25:
            rem_score = 15
        elif rem_percent > 25:
            rem_score = 15 - min(5, (rem_percent - 25) * 0.5)
        else:  # rem_percent < 20
            rem_score = rem_percent / 20 * 15
    else:
        deep_score = rem_score = 0
    
    composition_score = deep_score + rem_score
    
    # 4. Continuity/fragmentation component (15% of score)
    # Fragmentation is measured by awake time relative to total sleep time
    if total_sleep_min > 0:
        fragmentation_ratio = awake / total_sleep_min
        if fragmentation_ratio <= 0.05:
            continuity_score = 15
        elif fragmentation_ratio <= 0.10:
            continuity_score = 12
        elif fragmentation_ratio <= 0.15:
            continuity_score = 9
        elif fragmentation_ratio <= 0.25:
            continuity_score = 5
        else:
            continuity_score = max(0, 5 - (fragmentation_ratio - 0.25) * 10)
    else:
        continuity_score = 0
    
    # Calculate total score
    total_score = duration_score + efficiency_score + composition_score + continuity_score
    
    # Add minor random variation to simulate device differences
    variation = np.random.uniform(-2, 2)
    final_score = np.clip(total_score + variation, 0, 100)
    
    return round(final_score, 1)

# Function to adjust resting heart rate based on fatigue factors
def adjust_resting_hr(base_hr, sleep_quality, stress, training_load):
    # Scale sleep impact (Max ~2 bpm)
    sleep_penalty = (100 - sleep_quality) * 0.02  

    # Scale stress impact (Max ~2 bpm)
    stress_penalty = stress * 0.02  

    # Scale training load impact (Max ~2 bpm)
    training_penalty = training_load * 2  

    # Total HR variation (capped for realism)
    hr_variation = min(5, sleep_penalty + stress_penalty + training_penalty)

    return round(base_hr + hr_variation, 1)

# Function to calculate HRV based on multiple factors
def calculate_hrv(base_hrv, sleep_quality, chronic_load, acute_load, stress, recovery_capacity):
    """
    Calculate heart rate variability based on various physiological factors.
    HRV decreases with fatigue and increases with recovery.
    """
    # Calculate acute:chronic workload ratio (ACWR)
    if chronic_load > 0:
        acwr = acute_load / chronic_load
    else:
        acwr = 1.0
        
    # ACWR impacts:
    # 0.8-1.3: optimal range
    # <0.8: undertraining
    # >1.3: overtraining risk
    if 0.8 <= acwr <= 1.3:
        acwr_impact = 5  # Positive impact on HRV
    elif acwr > 1.3:
        acwr_impact = -10 * (acwr - 1.3)  # Negative impact increases with ACWR
    else:  # acwr < 0.8
        acwr_impact = 0  # Neutral impact
    
    # Sleep quality impact (poor sleep lowers HRV)
    sleep_impact = (sleep_quality - 70) * 0.2
    
    # Stress impact (high stress lowers HRV)
    stress_impact = -stress / 1000
    
    # Calculate daily HRV
    daily_hrv = base_hrv + acwr_impact + sleep_impact + stress_impact
    
    # Add recovery capacity influence
    recovery_factor = recovery_capacity / 7  # Normalize to ~1
    daily_hrv *= recovery_factor
    
    # Add realistic day-to-day variation
    daily_hrv += np.random.normal(0, 3)
    
    return round(np.clip(daily_hrv, 20, 120), 1)

# Function to assign seasonal temperature and humidity
def get_environmental_factors(date, base_altitude):
    month = date.month
    if month in [12, 1, 2]:  # Winter
        temp = np.random.uniform(-5, 10) if base_altitude > 0 else np.random.uniform(0, 15)
        humidity = np.random.uniform(30, 60)
        weather = np.random.choice(["Snowy", "Overcast", "Sunny"])
    elif month in [3, 4, 5]:  # Spring
        temp = np.random.uniform(10, 20)
        humidity = np.random.uniform(40, 70)
        weather = np.random.choice(["Sunny", "Windy", "Rainy"])
    elif month in [6, 7, 8]:  # Summer
        temp = np.random.uniform(20, 35)
        humidity = np.random.uniform(50, 80)
        weather = np.random.choice(["Sunny", "Hot", "Rainy"])
    else:  # Fall
        temp = np.random.uniform(10, 20)
        humidity = np.random.uniform(40, 70)
        weather = np.random.choice(["Windy", "Overcast", "Rainy"])

    return round(temp, 1), round(humidity, 1), weather

# Function to determine injury probability
def calculate_injury_risk(
    athlete_id,
    training_load,
    chronic_load,
    acute_load,
    sleep_quality,
    hrv,
    base_hrv,
    stress,
    recovery_capacity,
    age,
    previous_injury_days,
    injury_history
):
    """
    Calculate injury risk based on multiple factors including training load ratios,
    recovery metrics, and athlete characteristics.
    """
    # Base risk - age-related
    if age < 30:
        base_risk = 0.02
    elif age < 40:
        base_risk = 0.03
    else:
        base_risk = 0.04 + (age - 40) * 0.002
    
    # Acute:Chronic Workload Ratio (ACWR) risk
    if chronic_load > 0:
        acwr = acute_load / chronic_load
    else:
        acwr = 1.0
        
    if acwr > 1.5:
        # Exponential risk increase for high ACWR
        acwr_risk = 0.08 * (acwr - 1.5) ** 2
    elif acwr > 1.3:
        acwr_risk = 0.03
    elif acwr < 0.8:
        # Detraining also increases injury risk slightly
        acwr_risk = 0.01
    else:
        acwr_risk = 0
    
    # HRV-based risk (deviation from baseline)
    hrv_deviation = (base_hrv - hrv) / base_hrv
    if hrv_deviation > 0.15:
        hrv_risk = 0.05
    elif hrv_deviation > 0.08:
        hrv_risk = 0.02
    else:
        hrv_risk = 0
    
    # Sleep quality impact
    if sleep_quality < 50:
        sleep_risk = 0.04
    elif sleep_quality < 70:
        sleep_risk = 0.02
    else:
        sleep_risk = 0
    
    # Stress impact
    if stress > 10000:
        stress_risk = 0.05
    elif stress > 7000:
        stress_risk = 0.02
    else:
        stress_risk = 0
    
    # Previous/recent injury impact
    recent_injury_risk = 0
    if previous_injury_days > 0:
        recent_injury_risk = 0.1  # Currently injured/recovering
    elif injury_history > 0:
        # Risk decreases over time but remains elevated for ~30 days after full recovery
        recent_injury_risk = 0.08 * max(0, (30 - injury_history) / 30)
    
    # Recovery capacity (protective factor)
    recovery_factor = max(0.5, recovery_capacity / 7)  # Normalize to ~1
    
    # Calculate total risk
    total_risk = (base_risk + acwr_risk + hrv_risk + sleep_risk + 
                 stress_risk + recent_injury_risk) / recovery_factor
    
    # Add small random component for realistic variation
    total_risk += np.random.uniform(-0.01, 0.01)
    
    return max(0.01, total_risk)  # Ensure minimum risk

def check_injury(injury_risk):
    """Determine if injury occurs based on calculated risk probability"""
    return np.random.rand() < injury_risk

def calculate_stress_score(training_load, sleep_quality, low_stress, medium_stress, high_stress):
    # Convert stress durations from seconds to minutes
    low_stress_minutes = low_stress / 60
    medium_stress_minutes = medium_stress / 60
    high_stress_minutes = high_stress / 60

    # Sleep penalty: Poor sleep increases stress
    sleep_penalty = (100 - sleep_quality) * 0.2  

    # Normalize stress durations (weighting more intense stress more heavily)
    stress_component = (low_stress_minutes * 0.1) + (medium_stress_minutes * 0.3) + (high_stress_minutes * 0.6)

    # Training load impact, scaled properly
    training_impact = training_load * 30  

    # Composite stress score, capped at 100
    stress_score = min(100, sleep_penalty + stress_component + training_impact)
    
    return round(stress_score, 1)

# Function to generate daily activities
def generate_daily_activities(athlete_id, training_load, is_race_day=False, is_rest_day=False):
    if is_rest_day:
        return "[]"
    
    if is_race_day:
        return generate_race_activity(athlete_id)
    
    activities = []
    sports = ["Running", "Cycling", "Swimming"]

    # Assign athlete's weekly training volume
    athlete_training_hours = athlete_profiles[athlete_id]["Weekly_Training_Hours"]
    # Scale daily hours by training load
    daily_hours = (athlete_training_hours / 6) * training_load
    daily_target_seconds = daily_hours * 3600  # Convert to seconds

    # For very low training loads (recovery days), reduce activity count
    if training_load < 0.3:
        num_activities_probs = [0.8, 0.2, 0]
    elif training_load < 0.6:
        num_activities_probs = [0.6, 0.4, 0]
    else:
        num_activities_probs = [0.5, 0.3, 0.2]
        
    num_activities = np.random.choice([1, 2, 3], p=num_activities_probs)
    if num_activities == 0:
        return "[]"  # No activities
        
    total_duration = np.random.uniform(daily_target_seconds * 0.8, daily_target_seconds * 1.2)

    for _ in range(num_activities):
        sport = random.choice(sports)
        activity_duration = total_duration / num_activities

        if sport == "Running":
            pace = round(np.random.uniform(3.5, 6), 2)  # min/km
            distance = round(activity_duration / 60 / pace, 1)  # km
            avg_hr = round(athlete_profiles[athlete_id]["Resting_HR"] + (pace - 3.5) * 30, 1)
            cadence = np.random.randint(160, 190)
            stride_length = round(distance / (cadence * (activity_duration / 60)), 2)

            activity = {
                "Type": sport,
                "Duration_s": int(activity_duration),
                "Distance_km": distance,
                "Avg_Pace_min_per_km": pace,
                "Cadence_spm": cadence,
                "Stride_Length_m": stride_length,
                "Avg_HR": avg_hr,
                "Max_HR": avg_hr + np.random.randint(10, 25),
            }

        elif sport == "Cycling":
            avg_speed = round(np.random.uniform(25, 40), 1)  # km/h
            distance = round(activity_duration / 3600 * avg_speed, 1)
            ftp = athlete_profiles[athlete_id]["FTP"]
            avg_power = round(ftp * np.random.uniform(0.65, 0.9))
            cadence = np.random.randint(70, 110)
            elevation_gain = np.random.randint(0, 2000)

            activity = {
                "Type": sport,
                "Duration_s": int(activity_duration),
                "Distance_km": distance,
                "Avg_Power_W": avg_power,
                "Cadence_rpm": cadence,
                "Elevation_Gain_m": elevation_gain,
                "Avg_Speed_kmh": avg_speed,
                "Max_Speed_kmh": avg_speed + np.random.uniform(5, 20),
                "Avg_HR": round(athlete_profiles[athlete_id]["Resting_HR"] + avg_power / ftp * 80, 1),
                "Max_HR": round(athlete_profiles[athlete_id]["Max_HR"] * np.random.uniform(0.8, 0.95), 1),
            }

        elif sport == "Swimming":
            distance = np.random.randint(200, 4000)  # meters
            avg_pace = round(np.random.uniform(1.1, 2.0), 2)  # min/100m
            strokes_per_min = np.random.randint(30, 50)
            swolf = np.random.randint(30, 50)

            activity = {
                "Type": sport,
                "Duration_s": int(activity_duration),
                "Distance_m": distance,
                "Avg_Pace_min_per_100m": avg_pace,
                "Strokes_per_Min": strokes_per_min,
                "SWOLF": swolf,
                "Avg_HR": round(athlete_profiles[athlete_id]["Resting_HR"] + np.random.randint(20, 40), 1),
                "Max_HR": round(athlete_profiles[athlete_id]["Max_HR"] * np.random.uniform(0.75, 0.9), 1),
            }

        activities.append(activity)

    return json.dumps(activities)

import numpy as np

def generate_race_activity(athlete_id):
    """Generate a race activity (triathlon or single-sport race)"""
    # 70% chance of single sport race, 30% chance of triathlon
    race_type = np.random.choice(["Triathlon", "Single"], p=[0.3, 0.7])
    
    if race_type == "Triathlon":
        # Choose race distance
        distance_type = np.random.choice(["Sprint", "Olympic", "70.3", "140.6"], p=[0.4, 0.3, 0.2, 0.1])
        
        if distance_type == "Sprint":
            swim_dist, bike_dist, run_dist = 0.75, 20, 5 # km
            total_duration = np.random.uniform(3600*1, 3600*1.5)  # 1-1.5 hours
        elif distance_type == "Olympic":
            swim_dist, bike_dist, run_dist = 1.5, 40, 10 # km
            total_duration = np.random.uniform(3600*2, 3600*3)  # 2-3 hours
        elif distance_type == "70.3":
            swim_dist, bike_dist, run_dist = 1.9, 90, 21.1 # km
            total_duration = np.random.uniform(3600*4, 3600*7)  # 4-7 hours
        else:  # 140.6
            swim_dist, bike_dist, run_dist = 3.8, 180, 42.2 # km
            total_duration = np.random.uniform(3600*8, 3600*16)  # 8-16 hours
        
        # Distribute time across segments
        swim_time, bike_time, run_time = total_duration * 0.2, total_duration * 0.5, total_duration * 0.3
        
        max_hr = athlete_profiles[athlete_id]["Max_HR"]
        ftp = athlete_profiles[athlete_id]["FTP"]
        
        activities = [
            {
                "Type": "Swimming",
                "Race": True,
                "Race_Type": f"{distance_type} Triathlon",
                "Duration_s": int(swim_time),
                "Distance_m": int(swim_dist * 1000),
                "Avg_Pace_min_per_100m": round((swim_time / 60) / (swim_dist * 10), 2),
                "Strokes_per_Min": np.random.randint(35, 45),
                "SWOLF": np.random.randint(35, 45),
                "Avg_HR": round(max_hr * np.random.uniform(0.8, 0.9), 1),
                "Max_HR": round(max_hr * np.random.uniform(0.9, 0.98), 1),
            },
            {
                "Type": "Cycling",
                "Race": True,
                "Race_Type": f"{distance_type} Triathlon",
                "Duration_s": int(bike_time),
                "Distance_km": bike_dist,
                "Avg_Power_W": round(ftp * np.random.uniform(0.8, 0.9)),
                "Normalized_Power_W": round(ftp * np.random.uniform(0.85, 0.95)),
                "Cadence_rpm": np.random.randint(85, 95),
                "Elevation_Gain_m": round(bike_dist * np.random.uniform(5, 15)),
                "Avg_Speed_kmh": round(bike_dist / (bike_time/3600), 1),
                "Max_Speed_kmh": round(bike_dist / (bike_time/3600) * np.random.uniform(1.3, 1.5), 1),
                "Avg_HR": round(max_hr * np.random.uniform(0.8, 0.9), 1),
                "Max_HR": round(max_hr * np.random.uniform(0.9, 0.98), 1),
            },
            {
                "Type": "Running",
                "Race": True,
                "Race_Type": f"{distance_type} Triathlon",
                "Duration_s": int(run_time),
                "Distance_km": run_dist,
                "Avg_Pace_min_per_km": round((run_time / 60) / run_dist, 2),
                "Cadence_spm": np.random.randint(170, 190),
                "Stride_Length_m": round(np.random.uniform(1.0, 1.3), 2),
                "Avg_HR": round(max_hr * np.random.uniform(0.85, 0.95), 1),
                "Max_HR": round(max_hr * np.random.uniform(0.95, 1.0), 1),
            }
        ]
        
    else:  # Single sport race limited to Running or Cycling
        sport = np.random.choice(["Running", "Cycling"])
        
        if sport == "Running":
            # Running races: 5K, 10K, Half Marathon, Marathon
            race_distance = np.random.choice([5, 10, 21.1, 42.2])
            race_name = {5: "5K", 10: "10K", 21.1: "Half Marathon", 42.2: "Marathon"}[race_distance]

            # Estimate duration based on ability and distance
            vo2max = athlete_profiles[athlete_id]["VO2max"]
            base_pace = np.interp(vo2max, [40, 75], [6, 3.5])  # min/km
            estimated_duration = race_distance * base_pace * 60  
            # Add race day variation
            race_duration = estimated_duration * np.random.uniform(0.95, 1.10)
            max_hr = athlete_profiles[athlete_id]["Max_HR"]
            
            activities = [{
                "Type": "Running",
                "Race": True,
                "Race_Type": race_name,
                "Duration_s": int(race_duration),
                "Distance_km": race_distance,
                "Avg_Pace_min_per_km": round(race_duration/60/race_distance, 2),
                "Cadence_spm": np.random.randint(175, 195),
                "Stride_Length_m": round(np.random.uniform(1.1, 1.4), 2),
                "Avg_HR": round(max_hr * np.random.uniform(0.85, 0.95), 1),
                "Max_HR": round(max_hr * np.random.uniform(0.95, 1.0), 1),
            }]
            
        elif sport == "Cycling":
             # Cycling races/events: Criterium, Road Race, Time Trial, Gran Fondo
            race_type = np.random.choice(["Criterium", "Road Race", "Time Trial", "Gran Fondo"])
            distance, duration = {
                "Criterium": (np.random.uniform(30, 60), np.random.uniform(3600, 5400)),
                "Road Race": (np.random.uniform(60, 120), np.random.uniform(5400, 14400)),
                "Time Trial": (np.random.uniform(20, 40), np.random.uniform(1800, 3600)),
                "Gran Fondo": (np.random.uniform(80, 160), np.random.uniform(8000, 24000))
            }[race_type]
            
            ftp = athlete_profiles[athlete_id]["FTP"]
            max_hr = athlete_profiles[athlete_id]["Max_HR"]
            
            activities = [{
                "Type": "Cycling",
                "Race": True,
                "Race_Type": race_type,
                "Duration_s": int(duration),
                "Distance_km": round(distance, 1),
                "Avg_Power_W": round(ftp * np.random.uniform(0.8, 0.95)),
                "Normalized_Power_W": round(ftp * np.random.uniform(0.85, 1.0)),
                "Cadence_rpm": np.random.randint(85, 100),
                "Elevation_Gain_m": round(distance * np.random.uniform(5, 15)),
                "Avg_Speed_kmh": round(distance / (duration / 3600), 1),
                "Max_Speed_kmh": round(distance / (duration / 3600) * np.random.uniform(1.2, 1.4), 1),
                "Avg_HR": round(max_hr * np.random.uniform(0.85, 0.95), 1),
                "Max_HR": round(max_hr * np.random.uniform(0.95, 1.0), 1),
            }]
        
    return activities


# Generate dataset
data = []
injury_history = {athlete_id: 0 for athlete_id in range(1, N_ATHLETES + 1)}
current_injuries = {athlete_id: 0 for athlete_id in range(1, N_ATHLETES + 1)}

# Keep track of chronic (28-day) and acute (7-day) loads
chronic_loads = {athlete_id: np.zeros(N_DAYS) for athlete_id in range(1, N_ATHLETES + 1)}
acute_loads = {athlete_id: np.zeros(N_DAYS) for athlete_id in range(1, N_ATHLETES + 1)}

# First pass - calculate loads for ACWR
for athlete_id in range(1, N_ATHLETES + 1):
    athlete_loads = athlete_training_plans[athlete_id]
    
    # Calculate acute load (7-day rolling average)
    for day in range(N_DAYS):
        if day < 7:
            acute_loads[athlete_id][day] = np.mean(athlete_loads[:day+1])
        else:
            acute_loads[athlete_id][day] = np.mean(athlete_loads[day-7:day+1])
    
    # Calculate chronic load (28-day rolling average)
    for day in range(N_DAYS):
        if day < 28:
            chronic_loads[athlete_id][day] = np.mean(athlete_loads[:day+1])
        else:
            chronic_loads[athlete_id][day] = np.mean(athlete_loads[day-28:day+1])

# Second pass - actually generate the data
for athlete_id in range(1, N_ATHLETES + 1):
    athlete_race_days = [day for day, _ in athlete_races.get(athlete_id, [])]
    
    for day_idx, date in enumerate(dates):
        # Get target training load from periodized plan
        training_load = athlete_training_plans[athlete_id][day_idx]
        is_race_day = day_idx in athlete_race_days
        
        # If injured, reduce training load significantly
        if current_injuries[athlete_id] > 0:
            training_load *= 0.2  # 80% reduction if injured
            
        base_altitude = athlete_profiles[athlete_id]["Base_Altitude"]
        temp, humidity, weather = get_environmental_factors(date, base_altitude)

        # Randomly assign rest days (if not already dictated by training plan)
        is_rest_day = training_load < 0.2 or np.random.rand() < 0.05
        
        # Sleep stages - influenced by training load
        base_sleep_hrs = 7 + training_load  # More training = more sleep need
        sleep_efficiency = np.random.uniform(0.8, 0.95)
        
        total_sleep_min = int(base_sleep_hrs * 60 * sleep_efficiency)
        rem_sleep = int(total_sleep_min * np.random.uniform(0.2, 0.25))
        deep_sleep = int(total_sleep_min * np.random.uniform(0.15, 0.3))
        awake_time = int(total_sleep_min * np.random.uniform(0.05, 0.15))
        light_sleep = total_sleep_min - rem_sleep - deep_sleep - awake_time
        
        sleep_quality = calculate_sleep_quality(light_sleep, deep_sleep, rem_sleep, awake_time)

        # Training stress
        low_stress = np.random.randint(600, 3600)
        medium_stress = np.random.randint(600, 5400)
        high_stress = np.random.randint(0, 2700)

        # Calculate overall stress score
        stress = calculate_stress_score(training_load, sleep_quality, low_stress, medium_stress, high_stress)

        # Adjust resting HR
        resting_hr = adjust_resting_hr(athlete_profiles[athlete_id]["Resting_HR"], 
                                      sleep_quality, high_stress, training_load)

        # Calculate HRV based on multiple factors
        base_hrv = athlete_profiles[athlete_id]["Base_HRV"]
        chronic_load = chronic_loads[athlete_id][day_idx]
        acute_load = acute_loads[athlete_id][day_idx]
        recovery_capacity = athlete_profiles[athlete_id]["Recovery_Capacity"]
        
        hrv = calculate_hrv(base_hrv, sleep_quality, chronic_load, 
                           acute_load, stress, recovery_capacity)

        # Calculate injury risk (improved model)
        injury_risk = calculate_injury_risk(
            athlete_id,
            training_load,
            chronic_load,
            acute_load,
            sleep_quality,
            hrv,
            base_hrv,
            stress,
            recovery_capacity,
            athlete_profiles[athlete_id]["Age"],
            current_injuries[athlete_id],
            injury_history[athlete_id]
        )
        
        # Check if injury occurs
        new_injury = check_injury(injury_risk)
        if new_injury and current_injuries[athlete_id] == 0:
            # New injury - severity determines recovery time
            severity = np.random.choice(["Minor", "Moderate", "Major"], p=[0.6, 0.3, 0.1])
            if severity == "Minor":
                current_injuries[athlete_id] = np.random.randint(3, 8)
            elif severity == "Moderate":
                current_injuries[athlete_id] = np.random.randint(10, 21)
            else:  # Major
                current_injuries[athlete_id] = np.random.randint(28, 90)
        
        # Update injury status
        injured_today = current_injuries[athlete_id] > 0
        if injured_today:
            current_injuries[athlete_id] -= 1
            if current_injuries[athlete_id] == 0:
                injury_history[athlete_id] = 1  # Start counting days since recovery
        elif injury_history[athlete_id] > 0:
            injury_history[athlete_id] += 1

        # Generate activities (empty list if rest day)
        activities = generate_daily_activities(athlete_id, training_load, is_race_day, is_rest_day)

        # Append to dataset
        data.append([
            athlete_id, date, is_rest_day, is_race_day, 
            total_sleep_min, sleep_quality, resting_hr, hrv,
            light_sleep, deep_sleep, rem_sleep, awake_time,
            low_stress, medium_stress, high_stress, stress,
            temp, humidity, weather, 
            training_load, acute_load, chronic_load,
            injured_today, injury_risk, 
            activities
        ])

# Convert to DataFrame & Save
df = pd.DataFrame(data, columns=[
    "Athlete_ID", "Date", "Rest_Day", "Race_Day",
    "Total_Sleep_Min", "Sleep_Quality", "Resting_HR", "HRV", 
    "Light_Sleep_Min", "Deep_Sleep_Min", "REM_Sleep_Min", "Awake_Min",
    "Low_Stress", "Medium_Stress", "High_Stress", "Stress_Score",
    "Temperature_C", "Humidity_%", "Weather", 
    "Training_Load", "Acute_Load_7d", "Chronic_Load_28d",
    "Injured", "Injury_Risk", "Activities"
])

df.to_csv("synthetic_triathlete_data.csv", index=False)

print(df.head())