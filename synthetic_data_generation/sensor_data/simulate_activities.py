import random, math, numpy as np
from scipy.optimize import fsolve

# Random seed for reproducibility
np.random.seed(42)
random.seed(42)

def simulate_workout_execution(athlete, day_plan, daily_data, fatigue):
    """
    Simulates whether an athlete follows the planned training session, adjusts it, or skips it.
    
    Args:
        athlete: Dictionary containing athlete parameters.
        day_plan: Dictionary containing the planned workout for the day.
        daily_data: Dictionary with the athlete's physiological data for the day.
        fatigue: Current fatigue level.
    
    Returns:
        Dictionary with actual workouts performed.
    """
    # Calculate HRV status
    hrv_status = _calculate_hrv_status(athlete['hrv_baseline'], daily_data['hrv'])
    
    # Extract planned workouts
    planned_activities = _extract_planned_activities(day_plan)
    
    # Calculate base completion probability
    base_completion_prob = _calculate_base_completion_probability(fatigue, daily_data['sleep_quality'])
    
    # Chronotype impact
    chronotype = athlete.get('chronotype', 'intermediate')
    
    # Process each planned activity
    actual_activities = {}
    circadian_injury_modifier = 1.0

    for sport, details in planned_activities.items():
        # Assign a random training hour (simulating life schedule)
        # Larks more likely early, Owls more likely late
        if chronotype == 'lark':
            training_hour = random.choices(range(5, 22), weights=[10, 15, 20, 15, 10, 5, 4, 3, 3, 3, 2, 2, 2, 2, 2, 1, 1], k=1)[0]
        elif chronotype == 'owl':
            training_hour = random.choices(range(5, 22), weights=[1, 1, 2, 2, 3, 3, 4, 5, 8, 10, 15, 20, 15, 10, 5, 2, 1], k=1)[0]
        else:
            training_hour = random.randint(6, 20)

        # Performance penalty for misalignment
        performance_penalty = 1.0
        if chronotype == 'lark' and training_hour >= 19:
            performance_penalty = 0.92 # 8% drop in late evening
            circadian_injury_modifier *= 1.15
        elif chronotype == 'owl' and training_hour <= 8:
            performance_penalty = 0.88 # 12% drop in early morning
            circadian_injury_modifier *= 1.25

        activity = _process_planned_activity(
            sport, details, daily_data['date'], hrv_status, 
            fatigue, base_completion_prob, daily_data['sleep_quality'],
            performance_penalty
        )
        activity['training_hour'] = training_hour
        actual_activities[sport] = activity
    
    # Add unplanned workouts
    actual_activities = _add_unplanned_workouts(actual_activities, daily_data['date'], fatigue)
    
    # Update daily data with total TSS
    daily_data['planned_tss'] = day_plan['total_tss']
    daily_data['actual_tss'] = sum(activity['actual_tss'] for activity in actual_activities.values())
    daily_data['circadian_injury_modifier'] = circadian_injury_modifier
    
    return actual_activities

def _calculate_hrv_status(hrv_baseline, current_hrv):
    """Calculate HRV status based on baseline and current values."""
    return {
        'very_low': current_hrv < hrv_baseline * 0.75,
        'slightly_low': hrv_baseline * 0.75 <= current_hrv < hrv_baseline * 0.85,
        'normal': hrv_baseline * 0.85 <= current_hrv <= hrv_baseline * 1.15,
        'high': current_hrv > hrv_baseline * 1.15
    }

def _extract_planned_activities(day_plan):
    """Extract planned activities from day plan."""
    planned_activities = {}
    for sport in ['bike', 'run', 'swim', 'strength']:
        if day_plan[f"{sport}_workout"] is not None:
            planned_activities[sport] = {
                "workout": day_plan[f"{sport}_workout"],
                "duration": day_plan[f"{sport}_duration"],
                "tss": day_plan[f"{sport}_tss"]
            }
    return planned_activities

def _calculate_base_completion_probability(fatigue, sleep_quality):
    """Calculate base probability of completing workouts."""
    # Logistic function for fatigue impact
    base_prob = 1 / (1 + math.exp((fatigue - 75) / 10))
    # Adjust for sleep quality
    base_prob += (sleep_quality * 100 - 50) / 200
    return base_prob

def _process_planned_activity(sport, details, date, hrv_status, fatigue, base_completion_prob, sleep_quality, performance_penalty=1.0):
    """Process a planned activity to determine if and how it's completed."""
    # Calculate completion probability
    completion_prob = _adjust_completion_probability(
        base_completion_prob, hrv_status, fatigue, sleep_quality
    )
    
    # Create default activity structure
    activity = {
        "date": date,
        "workout": details["workout"],
        "planned_duration": details["duration"],
        "planned_tss": details["tss"]
    }
    
    # Determine if workout happens
    if random.random() < completion_prob:
        # Calculate adjustment factors
        duration_factor, intensity_factor = _calculate_adjustment_factors(
            fatigue, hrv_status
        )
        
        # Apply performance penalty (misalignment with chronotype)
        intensity_factor *= performance_penalty
        
        # Calculate actual workout values
        planned_intensity = math.sqrt(details["tss"] / 100 * 60 / details["duration"])
        actual_duration = details["duration"] * duration_factor
        actual_intensity = planned_intensity * intensity_factor
        
        # Calculate actual TSS
        actual_tss = _calculate_actual_tss(
            actual_intensity, actual_duration, details["workout"]
        )
        
        # Complete activity data
        activity.update({
            "actual_duration": round(actual_duration, 1),
            "actual_tss": round(actual_tss, 1),
            "intensity_factor": round(actual_intensity, 2)
        })
    else:
        # Workout skipped
        activity.update({
            "workout": "Skipped",
            "actual_duration": 0,
            "actual_tss": 0,
            "intensity_factor": 0
        })
    
    return activity

def _adjust_completion_probability(base_prob, hrv_status, fatigue, sleep_quality):
    """Adjust completion probability based on HRV, fatigue and sleep."""
    completion_prob = base_prob
    
    # Modify based on HRV status
    if hrv_status['very_low']:
        completion_prob *= 0.5  # Strong suppression
    elif hrv_status['slightly_low']:
        completion_prob *= 0.8
    elif hrv_status['high'] and fatigue < 40:
        completion_prob *= 1.2  # Athlete may overperform
    
    # Introduce hard thresholds for extreme cases
    if fatigue > 90 or (sleep_quality < 0.25 and hrv_status['very_low']):
        completion_prob = 0.05
    
    return completion_prob

def _calculate_adjustment_factors(fatigue, hrv_status):
    """Calculate duration and intensity adjustment factors."""
    duration_factor = 1.0
    intensity_factor = 1.0
    
    if fatigue > 80:
        duration_factor *= random.uniform(0.7, 0.9)
        intensity_factor *= random.uniform(0.8, 0.95)
    elif fatigue < 40 and hrv_status['high']:
        duration_factor *= random.uniform(1.1, 1.2)
        intensity_factor *= random.uniform(1.05, 1.15)
    
    return duration_factor, intensity_factor

def _calculate_actual_tss(intensity, duration, workout_type):
    """Calculate actual TSS based on intensity, duration and workout type."""
    tss = 100 * (intensity ** 2) * (duration / 60)
    
    if "interval" in workout_type.lower():
        tss *= 1.1  # Slight boost for interval-based sessions
    
    return tss

def _add_unplanned_workouts(actual_activities, date, fatigue):
    """Add unplanned workouts based on fatigue level."""
    # Determine probability of extra workout
    extra_prob = 0.1 if fatigue > 70 else 0.3
    
    # Add extra workout if conditions are met
    if len(actual_activities) < 2 and random.random() < extra_prob:
        extra_sport = random.choice(['bike', 'run', 'swim'])
        extra_duration = random.randint(30, 60)
        extra_intensity = random.uniform(0.7, 1.0)
        
        extra_tss = 100 * (extra_intensity ** 2) * (extra_duration / 60)
        
        actual_activities[extra_sport] = {
            "date": date,
            "workout": "Unplanned extra session",
            "actual_duration": extra_duration,
            "actual_tss": round(extra_tss, 1),
            "intensity_factor": round(extra_intensity, 2),
            "planned_duration": 0,
            "planned_tss": 0
        }
    
    return actual_activities



def simulate_wearable_activity_data(athlete, actual_activities, fatigue, workout_libraries):
    """
    Simulate wearable sensor data for completed workouts based on specific workout types.
    
    Parameters:
    - athlete: Dict containing athlete profile (thresholds, zones, etc.)
    - actual_activities: Dict of completed activities from simulate_workout_execution
    - daily_data: Dict containing daily metrics (HRV, sleep, etc.)
    - fatigue: Current fatigue level (0-100)
    - workout_libraries: Dict containing workout definitions for each sport
    
    Returns:
    - Dict of activities with detailed wearable metrics
    """
    wearable_data = {}
    
    # Athlete baseline parameters
    max_hr = athlete.get('max_hr', 190)
    rest_hr = athlete.get('rest_hr', 60)

    for sport, activity in actual_activities.items():
        if activity['workout'] == "Skipped" or activity['actual_duration'] == 0:
            continue

        if activity['workout'] == "Unplanned extra session":
            duration_hours = activity['actual_duration'] / 60
            extra_tss_per_hour = activity['actual_tss'] / duration_hours
            sport_workouts = workout_libraries[sport]
            closest_match = min(sport_workouts.items(), 
                            key=lambda item: abs(item[1]['tss_per_hour'] - extra_tss_per_hour))
            workout_type = closest_match[0]  # Get workout category key
            workout_name = closest_match[1]['name']  # Get workout name
            activity['workout'] = f"Unplanned Extra Workout ({workout_type.capitalize()})"

            
        # Basic activity metrics
        duration_minutes = activity['actual_duration']
        intensity_factor = activity['intensity_factor']
        workout_name = activity['workout']
        
        # Initialize activity data
        activity_data = {
            'athlete_id': athlete['id'],
            'date': activity['date'],
            'sport': sport,
            'workout_type': workout_name,
            'duration_minutes': duration_minutes,
            'tss': activity['actual_tss'],
            'intensity_factor': intensity_factor
        }
        
        # Generate time series data based on workout type
        time_points = np.linspace(0, duration_minutes, int(duration_minutes * 4))  # 15-second intervals
        
        # Heart rate simulation based on workout type
        hr_series = generate_hr_series(
            time_points, 
            athlete['hr_zones'],
            workout_name,
            sport,
            activity['planned_duration'],
            activity['actual_duration'],
            activity['planned_tss'],
            activity['actual_tss'],
            rest_hr,
            max_hr, 
            fatigue
        ) 
        
        avg_hr = round(sum(hr_series) / len(hr_series))
        max_hr_activity = round(max(hr_series))
        
        activity_data['avg_hr'] = avg_hr
        activity_data['max_hr'] = max_hr_activity
        activity_data['hr_zones'] = calculate_time_in_zones(hr_series, athlete['hr_zones']) # percentage
        
        # Sport-specific metrics
        if sport == 'bike':
            # Cycling metrics
            ftp = athlete.get('ftp', 250)
            
            # Generate power series based on workout type
            power_series = generate_power_series(
                time_points,
                athlete['power_zones'],
                workout_name,
                activity['planned_duration'],
                activity['actual_duration'],
                activity['planned_tss'],
                activity['actual_tss'], 
                ftp,
                fatigue
            )
            
            avg_power = round(sum(power_series) / len(power_series))
            norm_power = round(calculate_normalized_power(power_series))
            
            # Speed calculation based on power and conditions
            speed_profile = cycling_speed_profile(power_series, athlete["weight"])
            avg_speed = round(sum(speed_profile) / len(speed_profile), 1)
            
            # Distance
            distance = round(avg_speed * (duration_minutes / 60), 2)
            
            # Additional cycling metrics
            activity_data.update({
                'distance_km': distance,
                'avg_speed_kph': avg_speed,
                'avg_power': avg_power,
                'normalized_power': norm_power,
                'power_zones': calculate_power_zones(power_series, athlete['power_zones'], ftp),
                'intensity_variability': round(norm_power / avg_power, 2),
                'work_kilojoules': round(avg_power * duration_minutes / 60 * 3.6),
                'elevation_gain': round(distance * 5)
            })
            
        elif sport == 'run':
            # Generate pace profile
            pace_profile = running_pace(hr_series, athlete["hr_zones"], athlete["run_threshold_pace"], fatigue)
            
            avg_pace = sum(pace_profile) / len(time_points)
            
            # Speed in km/h
            avg_speed = round(60 / avg_pace, 2)
            
            # Distance
            distance = round(avg_speed * (duration_minutes / 60), 2)
            
            # Additional running metrics
            activity_data.update({
                'distance_km': distance,
                'avg_pace_min_km': round(avg_pace, 2),
                'avg_speed_kph': avg_speed,
                'elevation_gain': round(distance * (10 + (40 if "hill" in workout_name.lower() else 0))),
                'training_effect_aerobic': round(min(5.0, intensity_factor * duration_minutes / 40), 1),
                'training_effect_anaerobic': round(min(5.0, (intensity_factor - 0.7) * 2 * duration_minutes / 60), 1) if intensity_factor > 0.8 else 1.0
            })
            
        elif sport == 'swim':
            # Swimming metrics
            css = athlete.get('css', 100)  # Critical Swim Speed (s/100m)
                
            # Generate speed profile
            speed_profile = generate_swim_speed_profile(
                time_points, 
                css, 
                workout_name
            )
            avg_speed = round(sum(speed_profile) / len(speed_profile), 2) #s/100m
            
            # Distance
            distance = (duration_minutes * 60) / avg_speed * 100
            
            # Additional swimming metrics
            activity_data.update({
                'distance_km': distance/1000,
                'distance_m': distance,
                'avg_pace_min_100m': avg_speed/60,
                'avg_speed_kph': 360/avg_speed,
                'training_effect_aerobic': round(min(5.0, intensity_factor * duration_minutes / 45), 1)
            })
            
        elif sport == 'strength':
            # Strength training metrics
            # Vary based on workout type
            if "core" in workout_name.lower():
                rep_range = (12, 20)
                set_range = (2, 4)
                rest_range = (30, 60)
            elif "plyometric" in workout_name.lower():
                rep_range = (6, 12)
                set_range = (3, 5)
                rest_range = (60, 90)
            else:
                rep_range = (8, 15)
                set_range = (3, 5)
                rest_range = (45, 120)
            
            reps = round(random.uniform(*rep_range))
            sets = round(random.uniform(*set_range))
            rest_period = round(random.uniform(*rest_range))
            
            # Muscle oxygen varies by workout intensity
            muscle_oxygen_base = (60, 85)
            if "plyometric" in workout_name.lower():
                oxygen_adj = (muscle_oxygen_base[0] - 5, muscle_oxygen_base[1] - 10)
            else:
                oxygen_adj = muscle_oxygen_base
                
            muscle_oxygen = round(random.uniform(*oxygen_adj))
            
            # Additional strength metrics
            activity_data.update({
                'avg_reps': reps,
                'avg_sets': sets,
                'rest_period_sec': rest_period,
                'muscle_oxygen_percent': muscle_oxygen,
                'total_reps': reps * sets,
                'estimated_1rm_change': round(random.uniform(-2, 5), 1),
                'avg_heart_rate_percentage': round((avg_hr / max_hr) * 100, 1)
            })
        
        wearable_data[sport] = activity_data
    
    return wearable_data

def determine_target_zones(workout_name, sport):
    """Determine target HR zones based on workout name and sport with percentage distributions"""
    workout_name = workout_name.lower()

    if sport == "strength":
        # Default pattern for strength workouts
        zone_pattern = {
            "main": {
                "Z1": 30,  # 30% in Zone 1
                "Z2": 70   # 70% in Zone 2
            }
        }
        return zone_pattern
    
    # Default pattern for endurance workouts with percentages
    zone_pattern = {
        "warmup": {"Z1": 70, "Z2": 30},
        "main": {"Z2": 100},
        "cooldown": {"Z1": 100}
    }
    
    # Adjust based on workout type - much more conservative distributions
    if "recovery" in workout_name:
        zone_pattern["main"] = {"Z1": 95, "Z2": 5}
    elif "endurance" in workout_name or "long" in workout_name:
        # Much more conservative for long runs - primarily Z1/Z2
        zone_pattern["main"] = {"Z1": 40, "Z2": 55, "Z3": 5}
    elif "tempo" in workout_name:
        zone_pattern["main"] = {"Z2": 40, "Z3": 55, "Z4": 5}
    elif "sweetspot" in workout_name:
        zone_pattern["main"] = {"Z3": 70, "Z4": 30}
    elif "threshold" in workout_name or "ftp" in workout_name:
        zone_pattern["main"] = {"Z3": 30, "Z4": 65, "Z5": 5}
    elif "vo2max" in workout_name or "speed" in workout_name:
        zone_pattern["main"] = {"Z3": 10, "Z4": 35, "Z5": 55}
    elif "anaerobic" in workout_name:
        zone_pattern["main"] = {"Z4": 20, "Z5": 55, "Z6": 25}
    elif "sprint" in workout_name:
        zone_pattern["main"] = {"Z4": 15, "Z5": 40, "Z6": 45}
    elif "interval" in workout_name:
        if "high" in workout_name:
            zone_pattern["main"] = {"Z2": 50, "Z4": 20, "Z5": 30}  # High-intensity intervals
        else:
            zone_pattern["main"] = {"Z2": 60, "Z3": 20, "Z4": 20}  # Default intervals
    elif "hill" in workout_name:
        zone_pattern["main"] = {"Z2": 60, "Z3": 25, "Z4": 15}  # Hill repeats
    
    # Sport-specific adjustments
    if sport == "swim":
        # Swimming HR is typically lower than running/cycling
        adjusted_pattern = {}
        for segment, zones in zone_pattern.items():
            adjusted_pattern[segment] = {}
            for zone, percentage in zones.items():
                new_zone = adjust_zone_down(zone)
                adjusted_pattern[segment][new_zone] = percentage
        zone_pattern = adjusted_pattern
    
    return zone_pattern

def adjust_zones_for_tss(target_zones, tss_ratio, duration_ratio):
    """Adjust target zones based on TSS ratio and duration ratio using percentage redistribution"""
    adjusted_zones = {}
    
    # Calculate intensity factor
    intensity_factor = tss_ratio / duration_ratio if duration_ratio > 0 else 1.0
    
    # Process each segment (warmup, main, cooldown)
    for segment, zones in target_zones.items():
        adjusted_zones[segment] = {}
        
        # If not the main segment, keep the same
        if segment != "main":
            adjusted_zones[segment] = zones.copy()
            continue
            
        # For main segment, adjust based on intensity
        if abs(intensity_factor - 1.0) < 0.1:
            # Within 10% of planned intensity, keep the same
            adjusted_zones[segment] = zones.copy()
        else:
            # Cap the adjustment factor to prevent extreme shifts
            # This ensures even if TSS is much higher, we don't create unrealistic zone distributions
            capped_intensity_factor = min(1.5, max(0.75, intensity_factor))
            
            # Adjust shift percentage based on capped intensity
            shift_percentage = min(20, abs(capped_intensity_factor - 1.0) * 100)  # Maximum 20% shift (reduced from 30%)
            
            if intensity_factor > 1.0:
                # Workout was harder than planned - shift percentages up
                adjusted_zones[segment] = shift_percentages_up(zones, shift_percentage)
            else:
                # Workout was easier than planned - shift percentages down
                adjusted_zones[segment] = shift_percentages_down(zones, shift_percentage)
    
    # Validate the zone distribution - make sure no unrealistic distributions occur
    for segment, zones in adjusted_zones.items():
        if segment == "main":
            adjusted_zones[segment] = validate_zone_distribution(zones, target_zones[segment])
    
    return adjusted_zones

def validate_zone_distribution(adjusted_zones, original_zones):
    """Validate and correct unrealistic zone distributions"""
    # Check if distribution shifted too much to high zones
    total_high_intensity = sum(adjusted_zones.get(f"Z{i}", 0) for i in range(4, 7))
    original_high_intensity = sum(original_zones.get(f"Z{i}", 0) for i in range(4, 7))
    
    # If high intensity zones increased by more than 50% over original, cap them
    if total_high_intensity > original_high_intensity * 1.5:
        # Scale back high intensity zones
        scale_factor = (original_high_intensity * 1.5) / total_high_intensity if total_high_intensity > 0 else 1
        
        for zone in [f"Z{i}" for i in range(4, 7)]:
            if zone in adjusted_zones:
                adjusted_zones[zone] = adjusted_zones[zone] * scale_factor
        
        # Redistribute to lower zones
        deficit = 100 - sum(adjusted_zones.values())
        if deficit > 0:
            # Find lowest available zone
            lowest_zones = [f"Z{i}" for i in range(1, 4) if f"Z{i}" in adjusted_zones]
            if lowest_zones:
                lowest_zone = min(lowest_zones, key=lambda z: int(z[1]))
                adjusted_zones[lowest_zone] = adjusted_zones.get(lowest_zone, 0) + deficit
            else:
                # If no lower zones exist, add Z1
                adjusted_zones["Z1"] = deficit
    
    # For endurance/long runs, make sure Z5/Z6 never exceed a small percentage
    workout_type = detect_workout_type(original_zones)
    if workout_type == "endurance":
        # Cap Z5 and Z6 for endurance workouts
        for zone in ["Z5", "Z6"]:
            if zone in adjusted_zones and adjusted_zones[zone] > 5:  # Cap at 5%
                excess = adjusted_zones[zone] - 5
                adjusted_zones[zone] = 5
                
                # Redistribute excess to Z1/Z2
                for redistribution_zone in ["Z2", "Z1"]:
                    if redistribution_zone in adjusted_zones:
                        adjusted_zones[redistribution_zone] += excess
                        break
                else:
                    # If neither Z1 nor Z2 exist, add Z1
                    adjusted_zones["Z1"] = excess
    
    # Normalize to ensure percentages sum to 100
    total = sum(adjusted_zones.values())
    if total != 100:
        adjusted_zones = {zone: pct / total * 100 for zone, pct in adjusted_zones.items()}
    
    return adjusted_zones

def detect_workout_type(zone_distribution):
    """Detect workout type based on zone distribution pattern"""
    # Endurance workouts have most time in Z1/Z2
    z1_z2_percentage = zone_distribution.get("Z1", 0) + zone_distribution.get("Z2", 0)
    
    if z1_z2_percentage > 70:
        return "endurance"
    elif "Z5" in zone_distribution and zone_distribution["Z5"] > 40:
        return "high_intensity"
    else:
        return "mixed"

def shift_percentages_up(zones, shift_amount):
    """Shift zone percentages up in intensity with protection against extreme shifts"""
    sorted_zones = sorted([(zone, pct) for zone, pct in zones.items()], 
                         key=lambda x: int(x[0][1]))
    new_zones = {}
    
    # Initialize with zeros
    for zone, _ in sorted_zones:
        zone_num = int(zone[1])
        if zone_num < 6:  # Up to Z6
            new_zones[zone] = 0
            new_zones[f"Z{zone_num + 1}"] = 0
        else:
            new_zones[zone] = 0
    
    # Redistribute percentages with protection for higher zones
    for zone, percentage in sorted_zones:
        zone_num = int(zone[1])
        if zone_num < 6:  # Don't exceed Z6
            # Calculate how much to shift to next zone
            # Apply a damping factor to higher zones to prevent excessive shifting
            damping_factor = max(0.5, 1.0 - (zone_num / 10))
            amount_to_shift = min(percentage * 0.5, (percentage * shift_amount * damping_factor) / 100)
            
            # Update zones
            new_zones[zone] += percentage - amount_to_shift
            new_zones[f"Z{zone_num + 1}"] += amount_to_shift
        else:
            new_zones[zone] += percentage
    
    # Remove zones with 0%
    return {k: v for k, v in new_zones.items() if v > 0}

def shift_percentages_down(zones, shift_amount):
    """Shift zone percentages down in intensity"""
    sorted_zones = sorted([(zone, pct) for zone, pct in zones.items()], 
                         key=lambda x: int(x[0][1]), reverse=True)
    new_zones = {}
    
    # Initialize with zeros
    for zone, _ in sorted_zones:
        zone_num = int(zone[1])
        if zone_num > 1:  # Down to Z1
            new_zones[zone] = 0
            new_zones[f"Z{zone_num - 1}"] = 0
        else:
            new_zones[zone] = 0
    
    # Redistribute percentages
    for zone, percentage in sorted_zones:
        zone_num = int(zone[1])
        if zone_num > 1:  # Don't go below Z1
            # Calculate how much to shift to previous zone
            amount_to_shift = min(percentage * 0.7, (percentage * shift_amount) / 100)
            
            # Update zones
            new_zones[zone] += percentage - amount_to_shift
            new_zones[f"Z{zone_num - 1}"] += amount_to_shift
        else:
            new_zones[zone] += percentage
    
    # Remove zones with 0%
    return {k: v for k, v in new_zones.items() if v > 0}

def generate_hr_series(time_points, athlete_zones, workout_name, sport, 
                       planned_duration, actual_duration, planned_tss, actual_tss, 
                       rest_hr, max_hr, fatigue_level=0):
    """Generate heart rate time series based on workout type"""

    # Calculate TSS ratio to determine intensity adjustment
    tss_ratio = actual_tss / planned_tss if planned_tss > 0 else 1.0
    duration_ratio = actual_duration / planned_duration if planned_duration > 0 else 1.0
    
    # Determine target zones based on workout name and sport
    target_zones = determine_target_zones(workout_name, sport)
    
    # Adjust zones based on TSS ratio
    adjusted_zones = adjust_zones_for_tss(target_zones, tss_ratio, duration_ratio)
    
    # Generate time series based on workout type
    if "interval" in workout_name.lower() or "vo2max" in workout_name.lower() or "hill" in workout_name.lower():
        hr_series = generate_interval_hr(time_points, athlete_zones, adjusted_zones, 
                                        rest_hr, max_hr, workout_name, fatigue_level)
    elif sport == 'strength':
        hr_series = generate_strength_hr_series(time_points, athlete_zones, rest_hr, max_hr, fatigue_level)
    else:
        hr_series = generate_steady_pattern(time_points, athlete_zones, adjusted_zones, 
                                       rest_hr, max_hr, workout_name, fatigue_level)
    
    return hr_series

def generate_steady_pattern(time_points, athlete_zones, target_zones, rest_hr, max_hr, workout_name, fatigue_level):
    """Generate a steady heart rate pattern with drift using zone percentages"""
    hr_series = []
    
    # Warm-up period (first 10% of workout)
    warmup_end = int(len(time_points) * 0.1)
    cooldown_start = int(len(time_points) * 0.85)
    main_duration = cooldown_start - warmup_end
    
    # Apply fatigue effect
    fatigue_effect = 1 + (fatigue_level / 400)
    
    # Cardiac drift parameters
    drift_factor = 0.04 if "endurance" in workout_name.lower() else 0.06
    
    for i, t in enumerate(time_points):
        if i < warmup_end:
            # Warm-up progression using zone percentages
            progress = i / warmup_end
            warmup_zones = target_zones["warmup"]
            warmup_hr = calculate_target_hr(warmup_zones, athlete_zones, progress)
            hr = rest_hr + progress * (warmup_hr - rest_hr)
            
        elif i >= cooldown_start:
            # Cool-down progression
            progress = (i - cooldown_start) / (len(time_points) - cooldown_start)
            cooldown_zones = target_zones["cooldown"]
            cooldown_hr = calculate_target_hr(cooldown_zones, athlete_zones, 0)
            
            # Calculate main target HR for transition
            main_zones = target_zones["main"]
            main_hr = calculate_target_hr(main_zones, athlete_zones, 1)
            
            hr = cooldown_hr + (1 - progress) * (main_hr - cooldown_hr)
            
        else:
            # Main set with drift and zone distribution
            main_progress = (i - warmup_end) / main_duration
            main_zones = target_zones["main"]
            
            # Use zone percentages to determine target HR
            base_hr = calculate_target_hr(main_zones, athlete_zones, main_progress)
            
            # Apply cardiac drift
            time_hours = t / 60
            drift = 1 + (drift_factor * time_hours)
            hr = base_hr * drift
        
        # Apply fatigue effect
        hr = hr * fatigue_effect
        
        # Add natural variability
        hr += random.normalvariate(0, 1.5)
        
        # Ensure HR stays within bounds
        hr = min(max_hr, max(rest_hr, hr))
        hr_series.append(hr)
    
    return hr_series

def calculate_target_hr(zone_percentages, athlete_zones, progress):
    """Calculate target HR based on zone percentages and progression through workout segment"""
    target_hr = 0
    total_percentage = sum(zone_percentages.values())
    
    # Normalize percentages if they don't sum to 100
    if total_percentage != 100:
        normalized_percentages = {zone: (pct / total_percentage * 100) for zone, pct in zone_percentages.items()}
    else:
        normalized_percentages = zone_percentages
    
    # Sort zones by intensity
    sorted_zones = sorted(normalized_percentages.items(), key=lambda x: int(x[0][1]))
    
    # Progressively weight higher zones more as workout progresses (if progress > 0)
    if progress > 0:
        # Adjust zone percentages based on progress
        adjusted_percentages = {}
        for i, (zone, pct) in enumerate(sorted_zones):
            # Higher zones get progressively more weight as workout progresses
            weight = 1 + (i / (len(sorted_zones) - 1 if len(sorted_zones) > 1 else 1)) * progress * 0.2
            adjusted_percentages[zone] = pct * weight
        
        # Re-normalize to 100%
        total = sum(adjusted_percentages.values())
        normalized_percentages = {zone: (pct / total * 100) for zone, pct in adjusted_percentages.items()}
    
    # Calculate weighted average HR based on zone percentages
    for zone, percentage in normalized_percentages.items():
        zone_mid_hr = np.mean([athlete_zones[zone][0], athlete_zones[zone][1]])
        target_hr += zone_mid_hr * (percentage / 100)
    
    return target_hr

def generate_interval_hr(time_points, athlete_zones, target_zones, 
                         rest_hr, max_hr, workout_name, fatigue_level):
    """Generate heart rate series for interval workouts using zone percentages"""
    hr_series = []
    total_points = len(time_points)
    
    # Define segment durations
    warmup_end = int(total_points * 0.15)
    cooldown_start = int(total_points * 0.85)
    
    # Interval parameters based on workout type
    if "vo2max" in workout_name.lower():
        interval_duration = 3  # minutes
        recovery_duration = 2  # minutes
    elif "sprint" in workout_name.lower():
        interval_duration = 1  # minutes
        recovery_duration = 3  # minutes
    else:
        interval_duration = 4  # minutes
        recovery_duration = 2  # minutes
    
    # Convert to time points (assuming 15-second intervals)
    interval_points = int(interval_duration * 4)
    recovery_points = int(recovery_duration * 4)
    
    # Apply fatigue effect
    fatigue_effect = 1 + (fatigue_level / 400)
    
    # Calculate target HRs for each segment using zone percentages
    warmup_hr = calculate_target_hr(target_zones["warmup"], athlete_zones, 0.5)
    
    # For intervals, find the highest and lowest zone
    main_zones = target_zones["main"]
    sorted_zones = sorted(main_zones.items(), key=lambda x: int(x[0][1]))
    
    # Lowest zone used for recovery
    low_zone = sorted_zones[0][0]
    low_hr = np.mean([athlete_zones[low_zone][0], athlete_zones[low_zone][1]])
    
    # Highest zone used for intervals
    high_zone = sorted_zones[-1][0]
    high_hr = np.mean([athlete_zones[high_zone][0], athlete_zones[high_zone][1]])
    
    # Cooldown HR
    cooldown_hr = calculate_target_hr(target_zones["cooldown"], athlete_zones, 0.5)
    
    for i, t in enumerate(time_points):
        if i < warmup_end:
            # Warm-up progression
            progress = i / warmup_end
            hr = rest_hr + progress * (warmup_hr - rest_hr)
            
        elif i >= cooldown_start:
            # Cool-down progression
            progress = (i - cooldown_start) / (total_points - cooldown_start)
            hr = cooldown_hr + (1 - progress) * (low_hr - cooldown_hr)
            
        else:
            # Intervals
            cycle_length = interval_points + recovery_points
            position_in_cycle = (i - warmup_end) % cycle_length
            
            if position_in_cycle < interval_points:
                # In high-intensity interval
                interval_progress = position_in_cycle / interval_points
                
                # Heart rate response during interval
                if interval_progress < 0.2:
                    # Quick rise at start of interval
                    hr_progress = interval_progress * 3
                    hr = low_hr + hr_progress * (high_hr - low_hr)
                else:
                    # Steady or slight rise during interval
                    hr = high_hr * (1 + 0.02 * interval_progress)
            else:
                # In recovery
                recovery_progress = (position_in_cycle - interval_points) / recovery_points
                
                # Heart rate response during recovery
                if recovery_progress < 0.3:
                    # Quick initial drop
                    hr_drop = recovery_progress * 2.5
                    hr = high_hr - hr_drop * (high_hr - low_hr)
                else:
                    # Slower drop toward end of recovery
                    hr = low_hr
        
        # Apply fatigue effect
        hr = hr * fatigue_effect
        
        # Add natural variability (higher during intervals, lower during steady-state)
        variability = 3 if warmup_end <= i < cooldown_start else 1.5
        hr += random.normalvariate(0, variability)
        
        # Ensure HR stays within bounds
        hr = min(max_hr, max(rest_hr, hr))
        hr_series.append(hr)
    
    return hr_series

def generate_strength_hr_series(time_points, athlete_zones, rest_hr, max_hr, fatigue_level, num_sets=4, reps_per_set=10, rest_period=60):
    """Generate heart rate series for strength training"""
    hr_series = []
    set_duration = (reps_per_set * 3)  # Approximate duration of each set in seconds (3 seconds per rep)

    # Warm-up phase (10% of total time)
    warmup_end = int(len(time_points) * 0.1)
    # Cool-down phase (last 10% of total time)
    cooldown_start = int(len(time_points) * 0.9)

    # Fatigue effect
    fatigue_effect = 1 + (fatigue_level / 400)

    for i, t in enumerate(time_points):
        if i < warmup_end:
            # Warm-up progression
            progress = i / warmup_end
            hr = rest_hr + progress * (athlete_zones["Z1"][0] - rest_hr)
        elif i >= cooldown_start:
            # Cool-down progression
            progress = (i - cooldown_start) / (len(time_points) - cooldown_start)
            hr = athlete_zones["Z1"][0] - progress * (athlete_zones["Z1"][0] - rest_hr)
        else:
            # Main workout phase
            time_in_workout = (i - warmup_end) * 15  # Convert to seconds
            cycle_time = set_duration + rest_period
            position_in_cycle = time_in_workout % cycle_time

            if position_in_cycle < set_duration:
                # During a set
                progress = position_in_cycle / set_duration
                hr = athlete_zones["Z2"][0] + progress * (athlete_zones["Z3"][0] - athlete_zones["Z2"][0])
            else:
                # During rest
                rest_progress = (position_in_cycle - set_duration) / rest_period
                hr = athlete_zones["Z3"][0] - rest_progress * (athlete_zones["Z3"][0] - athlete_zones["Z1"][0])

        # Apply fatigue effect
        hr *= fatigue_effect

        # Add natural variability
        hr += random.normalvariate(0, 2)

        # Ensure HR stays within bounds
        hr = min(max_hr, max(rest_hr, hr))
        hr_series.append(hr)

    return hr_series

def adjust_zone_down(zone):
    """Move zone down one level if possible"""
    zone_num = int(zone[1])
    if zone_num > 1:
        return f"Z{zone_num - 1}"
    return zone

def generate_power_series(time_points, athlete_zones, workout_name, planned_duration, actual_duration, 
                          planned_tss, actual_tss, ftp, fatigue_level=0):
    """Generate power time series based on cycling workout type"""

    # Calculate TSS ratio for intensity adjustment
    tss_ratio = actual_tss / planned_tss if planned_tss > 0 else 1.0
    duration_ratio = actual_duration / planned_duration if planned_duration > 0 else 1.0
    
    # Determine target power zones
    target_zones = determine_power_target_zones(workout_name)
    
    # Adjust zones for TSS variations
    adjusted_zones = adjust_power_zones_for_tss(target_zones, tss_ratio, duration_ratio)

    # Generate power series based on workout type
    if "interval" in workout_name.lower() or "vo2max" in workout_name.lower() or "sprint" in workout_name.lower():
        power_series = generate_interval_power(time_points, athlete_zones, adjusted_zones, ftp, fatigue_level)
    else:
        power_series = generate_steady_power(time_points, athlete_zones, adjusted_zones, ftp, fatigue_level)
    
    return power_series

def determine_power_target_zones(workout_name):
    """Determine power target zones based on workout type"""
    workout_name = workout_name.lower()

    # Default zone structure
    zone_pattern = {
        "warmup": ["Z1", "Z2"],
        "main": ["Z2"],
        "cooldown": ["Z1"]
    }
    
    if "recovery" in workout_name:
        zone_pattern["main"] = ["Z1"]
    elif "endurance" in workout_name or "long" in workout_name:
        zone_pattern["main"] = ["Z2"]
    elif "tempo" in workout_name:
        zone_pattern["main"] = ["Z3"]
    elif "sweetspot" in workout_name:
        zone_pattern["main"] = ["Z3", "Z4"]
    elif "threshold" in workout_name or "ftp" in workout_name:
        zone_pattern["main"] = ["Z4"]
    elif "vo2max" in workout_name or "speed" in workout_name:
        zone_pattern["main"] = ["Z5"]
    elif "anaerobic" in workout_name:
        zone_pattern["main"] = ["Z6"]
    elif "sprint" in workout_name:
        zone_pattern["main"] = ["Z7"]
    elif "interval" in workout_name:
        if "high" in workout_name:
            zone_pattern["main"] = ["Z2", "Z6"]  # High-intensity intervals
        else:
            zone_pattern["main"] = ["Z2", "Z4"]  # Default intervals
    elif "hill" in workout_name:
        zone_pattern["main"] = ["Z3", "Z5"]  # Sustained hill climbing

    return zone_pattern

def adjust_power_zones_for_tss(target_zones, tss_ratio, duration_ratio):
    """Adjust power zones based on TSS ratio"""
    adjusted_zones = target_zones.copy()
    intensity_factor = tss_ratio / duration_ratio if duration_ratio > 0 else 1.0

    if intensity_factor > 1.1:
        new_main_zones = []
        for zone in target_zones["main"]:
            zone_num = int(zone[1])
            if zone_num < 6:
                new_main_zones.append(f"Z{zone_num + 1}")
            else:
                new_main_zones.append(zone)
        adjusted_zones["main"] = new_main_zones
    elif intensity_factor < 0.9:
        new_main_zones = []
        for zone in target_zones["main"]:
            zone_num = int(zone[1])
            if zone_num > 1:
                new_main_zones.append(f"Z{zone_num - 1}")
            else:
                new_main_zones.append(zone)
        adjusted_zones["main"] = new_main_zones

    return adjusted_zones

def generate_steady_power(time_points, athlete_zones, target_zones, ftp, fatigue_level):
    """Generate a steady power pattern with fatigue and drift"""
    power_series = []
    warmup_end = int(len(time_points) * 0.1)
    cooldown_start = int(len(time_points) * 0.85)

    main_zone = target_zones["main"][0]
    warmup_zone = target_zones["warmup"][0]
    cooldown_zone = target_zones["cooldown"][0]

    target_warmup_power = np.mean(athlete_zones[warmup_zone]) 
    target_main_power = np.mean(athlete_zones[main_zone]) 
    target_cooldown_power = np.mean(athlete_zones[cooldown_zone]) 

    drift_factor = 0.02 if "endurance" in main_zone else 0.04
    fatigue_effect = 1 - (fatigue_level / 500)

    for i, t in enumerate(time_points):
        if i < warmup_end:
            progress = i / warmup_end
            power = target_warmup_power + progress * (target_main_power - target_warmup_power)
        elif i >= cooldown_start:
            progress = (i - cooldown_start) / (len(time_points) - cooldown_start)
            power = target_cooldown_power + (1 - progress) * (target_main_power - target_cooldown_power)
        else:
            drift = 1 + (drift_factor * (t / 3600))
            power = target_main_power * drift

        power *= fatigue_effect
        power += random.normalvariate(0, 5)
        power = max(ftp * 0.5, min(power, ftp * 1.5))
        power_series.append(power)

    return power_series

def generate_interval_power(time_points, athlete_zones, target_zones, ftp, fatigue_level):
    """Generate power series for interval workouts"""
    power_series = []
    warmup_end = int(len(time_points) * 0.15)
    cooldown_start = int(len(time_points) * 0.85)

    warmup_zone = target_zones["warmup"][0]
    high_zone = target_zones["main"][-1]
    low_zone = target_zones["main"][0]
    cooldown_zone = target_zones["cooldown"][0]

    warmup_power = np.mean(athlete_zones[warmup_zone]) 
    high_power = np.mean(athlete_zones[high_zone]) 
    low_power = np.mean(athlete_zones[low_zone]) 
    cooldown_power = np.mean(athlete_zones[cooldown_zone]) 

    interval_points = 60  # 4 minutes on
    recovery_points = 30  # 2 minutes off
    cycle_length = interval_points + recovery_points

    fatigue_effect = 1 - (fatigue_level / 500)

    for i, t in enumerate(time_points):
        if i < warmup_end:
            progress = i / warmup_end
            power = warmup_power + progress * (low_power - warmup_power)
        elif i >= cooldown_start:
            progress = (i - cooldown_start) / (len(time_points) - cooldown_start)
            power = cooldown_power + (1 - progress) * (low_power - cooldown_power)
        else:
            position = (i - warmup_end) % cycle_length
            if position < interval_points:
                power = high_power * (1 + 0.02 * (position / interval_points))
            else:
                power = low_power

        power *= fatigue_effect
        power += random.normalvariate(0, 10)
        power = max(ftp * 0.5, min(power, ftp * 1.75))
        power_series.append(power)

    return power_series
    
def generate_swim_speed_profile(time_points, css, workout_name):
    """
    Generate a swim speed profile based on CSS (Critical Swim Speed) in seconds per 100m.
    
    Parameters:
    - time_points: Array of time points for the workout
    - css: Critical Swim Speed (s/100m)
    - workout_name: Name of the workout to determine pattern
    - variability: Base variability factor for the speed
    
    Returns:
    - Array of speed values (s/100m) for each time point
    """
    speed_series = []
    
    # Convert CSS to base pace
    base_pace = css  # Reference pace in s/100m
    
    if "interval" in workout_name.lower():
        interval_length = 5  # minutes
        recovery_length = 3  # minutes
        fast_pace = base_pace * 0.85  # 15% faster
        slow_pace = base_pace * 1.15  # 15% slower
        
        warmup_end = int(len(time_points) * 0.15)
        cooldown_start = int(len(time_points) * 0.9)
        
        interval_points = int(interval_length * 4)
        recovery_points = int(recovery_length * 4)
        cycle_length = interval_points + recovery_points
        
        for i in range(len(time_points)):
            if i < warmup_end:
                progress = i / warmup_end
                pace = base_pace * (1.1 - 0.2 * progress)
            elif i >= cooldown_start:
                progress = (i - cooldown_start) / (len(time_points) - cooldown_start)
                pace = base_pace * (1 - 0.2 * progress)
            else:
                position_in_cycle = (i - warmup_end) % cycle_length
                if position_in_cycle < interval_points:
                    pace = fast_pace
                else:
                    pace = slow_pace
            speed_series.append(max(0, pace))
    
    elif "threshold" in workout_name.lower():
        warmup_end = int(len(time_points) * 0.15)
        build_end = warmup_end + int(len(time_points) * 0.1)
        main_end = build_end + int(len(time_points) * 0.6)
        
        threshold_pace = base_pace * 0.97  # Slightly faster pace
        
        for i in range(len(time_points)):
            if i < warmup_end:
                progress = i / warmup_end
                pace = base_pace * (1.1 - 0.2 * progress)
            elif i < build_end:
                progress = (i - warmup_end) / (build_end - warmup_end)
                pace = base_pace * (1.0 - 0.03 * progress)
            elif i < main_end:
                pace = threshold_pace
            else:
                progress = (i - main_end) / (len(time_points) - main_end)
                pace = threshold_pace * (1 + 0.1 * progress)

            speed_series.append(max(0, pace))
    
    elif "recovery" in workout_name.lower():
        recovery_pace = base_pace * 1.1
        warmup_end = int(len(time_points) * 0.1)
        
        for i in range(len(time_points)):
            if i < warmup_end:
                progress = i / warmup_end
                pace = base_pace * (1.2 - 0.1 * progress)
            else:
                cycle_position = i % 100
                pace = recovery_pace * (1 + 0.03 * math.sin(2 * math.pi * cycle_position / 100))
            
            speed_series.append(max(0, pace))
    
    elif "endurance" in workout_name.lower():
        warmup_end = int(len(time_points) * 0.15)
        build_end = warmup_end + int(len(time_points) * 0.1)
        main_end = build_end + int(len(time_points) * 0.65)
        
        endurance_pace = base_pace * 1.05
        
        for i in range(len(time_points)):
            if i < warmup_end:
                progress = i / warmup_end
                pace = base_pace * (1.1 - 0.1 * progress)
            elif i < build_end:
                progress = (i - warmup_end) / (build_end - warmup_end)
                pace = base_pace * (1 - 0.05 * progress)
            elif i < main_end:
                cycle_position = i % 80
                pace = endurance_pace * (1 + 0.03 * math.sin(2 * math.pi * cycle_position / 80))
            else:
                progress = (i - main_end) / (len(time_points) - main_end)
                pace = endurance_pace * (1 + 0.1 * progress)
            
            speed_series.append(max(0, pace))
    
    else:
        warmup_end = int(len(time_points) * 0.15)
        cooldown_start = int(len(time_points) * 0.85)
        
        for i in range(len(time_points)):
            if i < warmup_end:
                progress = i / warmup_end
                pace = base_pace * (1.1 - 0.1 * progress)
            elif i >= cooldown_start:
                progress = (i - cooldown_start) / (len(time_points) - cooldown_start)
                pace = base_pace * (1 + 0.1 * progress)
            else:
                cycle_position = i % 60
                pace = base_pace * (1 + 0.02 * math.sin(2 * math.pi * cycle_position / 60))
            
            speed_series.append(max(0, pace))
    
    return speed_series

def cycling_speed_profile(power_series, weight, cda=0.3, crr=0.004, air_density=1.225, g=9.81, slope=0):
    """Generate synthetic cycling speed (km/h) based on power, weight, and fatigue effects."""
    speed_series = []
    mass = weight + 8  # Rider + bike mass in kg

    for power in power_series:

        def speed_equation(V):
            """Equation to solve for speed (V in m/s)."""
            aero = 0.5 * air_density * cda * V**3
            rolling = mass * g * crr * V
            gravity = mass * g * np.sin(np.arctan(slope / 100)) * V  # Convert slope % to radians
            return power - (aero + rolling + gravity)

        # Solve for speed using initial guess (10 m/s ~ 36 km/h)
        V_solution = fsolve(speed_equation, 10)[0]  
        V_kmh = max(5, min(V_solution * 3.6, 70))  # Convert to km/h and limit range
        
        speed_series.append(V_kmh)

    return np.array(speed_series)

def running_pace(hr_series, hr_zones, ftp, fatigue_level=0):
    """Estimate running pace (min/km) based on HR zones and FTPace"""
    
    pace_series = []
    fatigue_factor = 1 + (fatigue_level / 400)  # Fatigue makes paces slower
    
    for hr in hr_series:
        if hr < hr_zones["Z2"][1]:  # Low-intensity run
            pace_factor = 1.25  # Run ~25% slower than FTPace
        elif hr < hr_zones["Z3"][1]:  # Aerobic endurance
            pace_factor = 1.15  # Run ~15% slower
        elif hr < hr_zones["Z4"][1]:  # Tempo/threshold
            pace_factor = 1.00  # At threshold pace
        elif hr < hr_zones["Z5"][1]:  # VO2 max effort
            pace_factor = 0.85  # Faster than threshold pace
        else:  # Sprint efforts
            pace_factor = 0.70  # Much faster
        
        # Adjust pace for fatigue & endurance drift
        pace_seconds = ftp * pace_factor * fatigue_factor 
        pace_series.append(pace_seconds)
    
    return np.array(pace_series)

def calculate_normalized_power(power_series):
    """Calculate normalized power from a power series"""
    # 30-second rolling average
    rolling_avg = []
    window_size = 8  # Assuming 15-second intervals, 8 samples = 2 minutes
    
    for i in range(len(power_series) - window_size + 1):
        window = power_series[i:i+window_size]
        rolling_avg.append(sum(window) / window_size)
    
    # Fourth power average
    fourth_power_avg = sum(p**4 for p in rolling_avg) / len(rolling_avg)
    
    # Fourth root
    return fourth_power_avg**(1/4)

def calculate_time_in_zones(hr_series, athlete_zones):
    """Calculate time spent in each heart rate zone"""
    # Initialize counters for each zone
    zone_counts = {zone: 0 for zone in athlete_zones}
    
    # Count data points in each zone
    for hr in hr_series:
        for zone, (min_hr, max_hr) in athlete_zones.items():
            if min_hr <= hr < max_hr:
                zone_counts[zone] += 1
                break
    
    # Calculate percentages
    total_points = len(hr_series)
    zone_percentages = {zone: (count / total_points) * 100 for zone, count in zone_counts.items()}
    
    # Calculate time in seconds (assuming 15-second intervals between data points)
    seconds_per_point = 15  # Adjust this if your data has different time intervals
    zone_seconds = {zone: count * seconds_per_point for zone, count in zone_counts.items()}
    
    # Convert seconds to HH:MM:SS format
    zone_time_formatted = {}
    for zone, seconds in zone_seconds.items():
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        zone_time_formatted[zone] = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    return zone_percentages

def calculate_power_zones(power_series, power_zones, ftp):
    """Calculate time spent in each power zone"""

    # Define power zones as percentages of FTP
    power_zones = {
        "Z1": (0, 0.55),          # Active recovery: < 55% of FTP
        "Z2": (0.55, 0.75),       # Endurance: 55-75% of FTP
        "Z3": (0.75, 0.9),        # Tempo: 75-90% of FTP
        "Z4": (0.9, 1.05),        # Threshold: 90-105% of FTP
        "Z5": (1.05, 1.2),        # VO2Max: 105-120% of FTP
        "Z6": (1.2, 1.5),         # Anaerobic: 120-150% of FTP
        "Z7": (1.5, float('inf')) # Neuromuscular: > 150% of FTP
    }
    
    # Count data points in each zone
    zone_counts = {zone: 0 for zone in power_zones}
    total_points = len(power_series)
    
    for power in power_series:
        # Convert power to percentage of FTP
        power_percent = power / ftp
        
        # Check which zone this power value falls into
        for zone, (lower, upper) in power_zones.items():
            if lower <= power_percent < upper:
                zone_counts[zone] += 1
                break
    
    # Calculate percentages
    zone_percentages = {zone: (count / total_points) * 100 for zone, count in zone_counts.items()}
    
    return zone_percentages

def simulate_training_day_with_wearables(athlete, day_plan, daily_data, fatigue):
    """
    Complete simulation of a training day including wearable data
    
    Parameters:
    - athlete: Dict with athlete profile
    - day_plan: Training plan for the day
    - performance: Performance history
    - daily_data: Current day's data (HRV, sleep, etc.)
    - fatigue: Current fatigue level
    
    Returns:
    - Dict containing actual activities and wearable data
    """
    
    # Run the original workout execution simulation
    actual_activities = simulate_workout_execution(athlete, day_plan, daily_data, fatigue)

    # Define workout libraries for different sports
    workout_libraries = {
        'swim': {
            'recovery': {
                'name': 'Easy Swim',
                'description': 'Easy technique-focused swim with drills',
                'tss_per_hour': 25
            },
            'endurance': {
                'name': 'Endurance Swim',
                'description': 'Steady-paced endurance swim with some drill sets',
                'tss_per_hour': 50
            },
            'intervals': {
                'name': 'Swim Intervals',
                'description': 'Mixed intervals focusing on speed and technique',
                'tss_per_hour': 90
            },
            'threshold': {
                'name': 'Threshold Swim',
                'description': 'Sustained effort at or near threshold pace',
                'tss_per_hour': 80
            },
            'speed': {
                'name': 'Speed Work',
                'description': 'Short, high-intensity repeats with full recovery',
                'tss_per_hour': 100
            }
        },
        
        'bike': {
            'recovery': {
                'name': 'Recovery Ride',
                'description': 'Very easy spinning to promote recovery',
                'tss_per_hour': 30
            },
            'endurance': {
                'name': 'Endurance Ride',
                'description': 'Steady effort to build aerobic endurance',
                'tss_per_hour': 40
            },
            'tempo': {
                'name': 'Tempo Ride',
                'description': 'Sustained moderate effort with some harder efforts',
                'tss_per_hour': 60
            },
            'sweetspot': {
                'name': 'Sweet Spot Intervals',
                'description': 'Intervals at 88-93% of FTP',
                'tss_per_hour': 70
            },
            'threshold': {
                'name': 'Threshold Intervals',
                'description': 'Intervals at or just below FTP',
                'tss_per_hour': 80
            },
            'vo2max': {
                'name': 'VO2max Intervals',
                'description': 'Short, high-intensity intervals',
                'tss_per_hour': 100
            }
        },

        'run': {
            'recovery': {
                'name': 'Recovery Run',
                'description': 'Very easy pace to promote recovery',
                'tss_per_hour': 30
            },
            'endurance': {
                'name': 'Endurance Run',
                'description': 'Steady effort to build aerobic endurance',
                'tss_per_hour': 50
            },
            'long': {
                'name': 'Long Run',
                'description': 'Extended duration at easy to moderate pace',
                'tss_per_hour': 50
            },
            'tempo': {
                'name': 'Tempo Run',
                'description': 'Sustained effort at moderate intensity',
                'tss_per_hour': 70
            },
            'threshold': {
                'name': 'Threshold Intervals',
                'description': 'Intervals at or near threshold pace',
                'tss_per_hour': 95
            },
            'intervals': {
                'name': 'Speed Intervals',
                'description': 'Short, high-intensity repeats with recovery',
                'tss_per_hour': 100
            }
        },

        'strength': {
            'core': {
                'name': 'Core Strength',
                'description': 'Core-focused exercises to improve stability',
                'tss_per_hour': 40
            },
            'general': {
                'name': 'General Strength',
                'description': 'Full-body strength routine',
                'tss_per_hour': 50
            },
            'sport_specific': {
                'name': 'Sport-Specific Strength',
                'description': 'Strength exercises targeting swim/bike/run muscles',
                'tss_per_hour': 60
            },
            'plyometric': {
                'name': 'Plyometric Training',
                'description': 'Explosive exercises to build power',
                'tss_per_hour': 70
            }
        }
    }

    
    # Generate detailed wearable data for completed activities
    wearable_data = simulate_wearable_activity_data(athlete, actual_activities, fatigue, workout_libraries)
    
    return wearable_data