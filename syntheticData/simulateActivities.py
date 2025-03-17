import random, math, numpy as np

def simulate_workout_execution(athlete, day_plan, daily_data, fatigue):
    """
    Simulates whether an athlete follows the planned training session, adjusts it, or skips it based on HRV, fatigue, and sleep.
    
    :param athlete: Dictionary containing athlete parameters.
    :param day_plan: Dictionary containing the planned workout for the day.
    :param daily_data: Dictionary with the athlete's physiological data for the day.
    :param fatigue: Current fatigue level.
    
    :return: Dictionary with actual workouts performed.
    """

    hrv_baseline = athlete['hrv_baseline']
    is_hrv_very_low = daily_data['hrv'] < hrv_baseline * 0.75
    is_hrv_slightly_low = hrv_baseline - 20 <= daily_data['hrv'] < hrv_baseline * 0.85
    is_hrv_high = daily_data['hrv'] > hrv_baseline * 1.15
    planned_activities = {}

    # Extract planned workouts
    for sport in ['bike', 'run', 'swim', 'strength']:
        if day_plan[f"{sport}_workout"] is not None:
            planned_activities[sport] = {
                "workout": day_plan[f"{sport}_workout"],
                "duration": day_plan[f"{sport}_duration"],
                "tss": day_plan[f"{sport}_tss"]
            }

    actual_activities = {}
    # Workout completion probability based on fatigue & sleep
    base_completion_prob = 1 / (1 + math.exp((fatigue - 75) / 10))  # Logistic function
    base_completion_prob += (daily_data['sleep_quality'] * 100 - 50) / 200  # Adjust for sleep quality

    for sport, details in planned_activities.items():
        # Calculate probability of completing this specific workout
        completion_prob = base_completion_prob

        # Modify probability based on HRV deviation
        if is_hrv_very_low:
            completion_prob *= 0.5  # Strong suppression
        elif is_hrv_slightly_low:
            completion_prob *= 0.8
        elif is_hrv_high and fatigue < 40:
            completion_prob *= 1.2  # Athlete may overperform

        # Introduce a hard threshold where workouts are almost certainly skipped
        if fatigue > 90 or (daily_data['sleep_quality'] < 25 and is_hrv_very_low):
            completion_prob = 0.05  # Only 5% chance of completing

        # Determine if workout happens
        if random.random() < completion_prob:
            # Adjust workout duration and intensity
            duration_factor = 1.0
            intensity_factor = 1.0

            if fatigue > 80:
                duration_factor *= random.uniform(0.7, 0.9)  # Reduce duration significantly
                intensity_factor *= random.uniform(0.8, 0.95)  # Reduce intensity

            elif fatigue < 40 and is_hrv_high:
                duration_factor *= random.uniform(1.1, 1.2)  # Athlete may extend session
                intensity_factor *= random.uniform(1.05, 1.15)  # Push harder

            # Workout Type Adjustments
            planned_intensity = math.sqrt(details["tss"] / 100 * 60 / details["duration"])
            actual_duration = details["duration"] * duration_factor
            actual_intensity = planned_intensity * intensity_factor

            # Calculate TSS more dynamically
            actual_tss = 100 * (actual_intensity ** 2) * (actual_duration / 60)
            if "interval" in details["workout"].lower():  
                actual_tss *= 1.1  # Slight boost for interval-based sessions

            actual_activities[sport] = {
                "date": daily_data['date'],
                "workout": details["workout"],
                "actual_duration": round(actual_duration, 1),
                "actual_tss": round(actual_tss, 1),
                "intensity_factor": round(actual_intensity, 2),
                "planned_duration": details["duration"],
                "planned_tss": details["tss"]
            }
        else:
            actual_activities[sport] = {
                "date": daily_data['date'],
                "workout": "Skipped",
                "actual_duration": 0,
                "actual_tss": 0,
                "intensity_factor": 0,
                "planned_duration": details["duration"],
                "planned_tss": details["tss"]
            }

    # **Unplanned Extra Workouts** (some athletes tend to overtrain)
    extra_prob = 0.1 if fatigue > 70 else 0.3  # 30% chance if feeling fresh

    if len(actual_activities) < 2 and random.random() < extra_prob:
        extra_sport = random.choice(['bike', 'run', 'swim'])  # Strength less likely as extra
        extra_duration = random.randint(30, 60)
        extra_intensity = random.uniform(0.7, 1.0)

        extra_tss = 100 * (extra_intensity ** 2) * (extra_duration / 60)

        actual_activities[extra_sport] = {
            "date": daily_data['date'],
            "workout": "Unplanned extra session",
            "actual_duration": extra_duration,
            "actual_tss": round(extra_tss, 1),
            "intensity_factor": round(extra_intensity, 2),
            "planned_duration": 0,
            "planned_tss": 0
        }

    # Update daily data with total TSS
    daily_data['planned_tss'] = day_plan['total_tss']
    daily_data['actual_tss'] = sum(activity['actual_tss'] for activity in actual_activities.values())

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
    
    # Sport-specific parameters
    sport_params = {
        'bike': {
            'speed_range': (20, 35),  # km/h
            'cadence_range': (80, 95),  # rpm
            'power_ftp': athlete.get('bike_ftp', 250),  # watts
            'hr_drift_factor': 0.1,  # HR drift per hour
            'power_variability': 0.2,  # NP vs AP ratio
            'speed_variability': 0.15
        },
        'run': {
            'speed_range': (8, 15),  # km/h
            'cadence_range': (160, 180),  # spm
            'pace_threshold': athlete.get('run_threshold_pace', 4.5),  # min/km
            'vertical_oscillation_range': (7, 12),  # cm
            'ground_contact_range': (200, 250),  # ms
            'speed_variability': 0.2
        },
        'swim': {
            'speed_range': (2, 4),  # km/h
            'stroke_rate_range': (25, 35),  # strokes/min
            'swolf_range': (50, 80),  # efficiency score
            'stroke_length_range': (1.5, 2.2),  # meters
            'speed_variability': 0.1
        },
        'strength': {
            'rep_range': (8, 15),
            'set_range': (3, 5),
            'rest_period_range': (45, 120),  # seconds
            'muscle_oxygen_range': (60, 85)  # percentage
        }
    }
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
        
        # Find workout type in libraries
        workout_type = None
        if sport in workout_libraries and workout_name in workout_libraries[sport]:
            workout_type = workout_libraries[sport][workout_name]
        
        # Initialize activity data
        activity_data = {
            'athlete_id': athlete['id'],
            'date': activity['date'],
            'sport': sport,
            'workout_type': workout_name,
            'workout_description': workout_type['description'] if workout_type else "Custom workout",
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
        activity_data['hr_zones'] = calculate_time_in_zones(hr_series, athlete['hr_zones'])
        
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
            speed_variability = sport_params['bike']['speed_variability']
            if "hills" in workout_name.lower():
                speed_variability *= 1.5  # More variable speed on hills
                
            base_speed = random.uniform(*sport_params['bike']['speed_range'])
            speed_profile = generate_speed_profile(
                time_points, 
                base_speed * intensity_factor**0.8, 
                workout_name, 
                speed_variability
            )
            avg_speed = round(sum(speed_profile) / len(speed_profile), 1)
            
            # Distance
            distance = round(avg_speed * (duration_minutes / 60), 2)
            
            # Cadence based on workout type
            cadence_base = sport_params['bike']['cadence_range']
            if "recovery" in workout_name.lower():
                cadence_adj = (cadence_base[0] + 5, cadence_base[1] - 5)  # Higher cadence, lower power
            elif "hill" in workout_name.lower():
                cadence_adj = (cadence_base[0] - 10, cadence_base[1] - 15)  # Lower cadence on hills
            else:
                cadence_adj = cadence_base
                
            avg_cadence = round(random.uniform(cadence_adj[0], cadence_adj[1]))
            
            # Additional cycling metrics
            activity_data.update({
                'distance_km': distance,
                'avg_speed_kph': avg_speed,
                'avg_power': avg_power,
                'normalized_power': norm_power,
                'avg_cadence': avg_cadence,
                'power_zones': calculate_power_zones(power_series, athlete['power_zones'], ftp),
                'intensity_variability': round(norm_power / avg_power, 2),
                'work_kilojoules': round(avg_power * duration_minutes / 60 * 3.6),
                'elevation_gain': round(distance * (5 + (15 if "hill" in workout_name.lower() else 0)))
            })
            
        elif sport == 'run':
            # Running metrics
            pace_threshold = athlete.get('run_threshold_pace', 4.5)
            target_pace = pace_threshold / intensity_factor
            
            # Generate pace variations based on workout type
            pace_variability = sport_params['run']['speed_variability']
            if "interval" in workout_name.lower() or "speed" in workout_name.lower():
                pace_variability = 0.3
            elif "hill" in workout_name.lower():
                pace_variability = 0.25
            elif "threshold" in workout_name.lower():
                pace_variability = 0.1  # More consistent pace
                
            # Generate pace profile
            pace_profile = generate_pace_profile(
                time_points, 
                target_pace, 
                workout_name, 
                pace_variability
            )
            
            avg_pace = sum(pace_profile) / len(time_points)

            print(f"Workout: {workout_name}, Avg. Pace: {avg_pace}")
            
            # Speed in km/h
            avg_speed = round(60 / avg_pace, 2)
            
            # Distance
            distance = round(avg_speed * (duration_minutes / 60), 2)
            
            # Running form metrics adjusted for workout type
            cadence_range = sport_params['run']['cadence_range']
            if "recovery" in workout_name.lower():
                cadence_adj = (cadence_range[0] - 5, cadence_range[1] - 10)  # Lower cadence on recovery
            elif "speed" in workout_name.lower() or "interval" in workout_name.lower():
                cadence_adj = (cadence_range[0] + 5, cadence_range[1] + 5)  # Higher cadence on speed work
            else:
                cadence_adj = cadence_range
                
            avg_cadence = round(random.uniform(cadence_adj[0], cadence_adj[1]))
            
            # Vertical oscillation varies by pace
            vo_base = sport_params['run']['vertical_oscillation_range']
            if "recovery" in workout_name.lower():
                vo_adj = (vo_base[0] - 1, vo_base[1] - 1)  # Lower oscillation on recovery
            elif "speed" in workout_name.lower():
                vo_adj = (vo_base[0] + 1, vo_base[1] + 2)  # Higher on speed work
            else:
                vo_adj = vo_base
                
            vertical_oscillation = round(random.uniform(*vo_adj), 1)
            
            # Ground contact time varies inversely with pace
            gc_base = sport_params['run']['ground_contact_range']
            if "recovery" in workout_name.lower():
                gc_adj = (gc_base[0] + 10, gc_base[1] + 20)  # Longer contact on recovery
            elif "speed" in workout_name.lower():
                gc_adj = (gc_base[0] - 20, gc_base[1] - 30)  # Shorter on speed work
            else:
                gc_adj = gc_base
                
            ground_contact = round(random.uniform(*gc_adj))
            
            # Additional running metrics
            activity_data.update({
                'distance_km': distance,
                'avg_pace_min_km': round(avg_pace, 2),
                'avg_speed_kph': avg_speed,
                'avg_cadence_spm': avg_cadence,
                'vertical_oscillation_cm': vertical_oscillation,
                'ground_contact_ms': ground_contact,
                'stride_length_m': round(avg_speed * 1000 / 60 / avg_cadence * 2, 2),
                'elevation_gain': round(distance * (10 + (40 if "hill" in workout_name.lower() else 0))),
                'training_effect_aerobic': round(min(5.0, intensity_factor * duration_minutes / 40), 1),
                'training_effect_anaerobic': round(min(5.0, (intensity_factor - 0.7) * 2 * duration_minutes / 60), 1) if intensity_factor > 0.8 else 1.0
            })
            
        elif sport == 'swim':
            # Swimming metrics
            base_speed = random.uniform(*sport_params['swim']['speed_range'])
            speed_factor = intensity_factor**0.7  # Different relationship for swimming
            
            # Speed varies by workout type
            if "threshold" in workout_name.lower() or "speed" in workout_name.lower():
                speed_variability = sport_params['swim']['speed_variability'] * 1.5
            else:
                speed_variability = sport_params['swim']['speed_variability']
                
            # Generate speed profile
            speed_profile = generate_speed_profile(
                time_points, 
                base_speed * speed_factor, 
                workout_name, 
                speed_variability
            )
            avg_speed = round(sum(speed_profile) / len(speed_profile), 2)
            
            # Distance
            distance = round(avg_speed * (duration_minutes / 60), 2)
            
            # Swimming metrics vary by workout type
            stroke_rate_base = sport_params['swim']['stroke_rate_range']
            if "endurance" in workout_name.lower() or "recovery" in workout_name.lower():
                # Lower stroke rate for endurance/recovery
                stroke_rate_adj = (stroke_rate_base[0] - 3, stroke_rate_base[1] - 5)
                stroke_length_adj = (sport_params['swim']['stroke_length_range'][0] + 0.1, 
                                 sport_params['swim']['stroke_length_range'][1] + 0.2)
            elif "speed" in workout_name.lower() or "threshold" in workout_name.lower():
                # Higher stroke rate for speed work
                stroke_rate_adj = (stroke_rate_base[0] + 3, stroke_rate_base[1] + 5)
                stroke_length_adj = (sport_params['swim']['stroke_length_range'][0] - 0.1, 
                                 sport_params['swim']['stroke_length_range'][1])
            else:
                stroke_rate_adj = stroke_rate_base
                stroke_length_adj = sport_params['swim']['stroke_length_range']
                
            stroke_rate = round(random.uniform(*stroke_rate_adj))
            stroke_length = round(random.uniform(*stroke_length_adj), 2)
            
            # SWOLF score (efficiency) - lower is better
            # Affected by workout type and fatigue
            swolf_base = sport_params['swim']['swolf_range']
            swolf_adj = swolf_base[0] + (swolf_base[1] - swolf_base[0]) * (
                0.3 + 0.4 * fatigue/100 + 
                (0.3 if "threshold" in workout_name.lower() or "speed" in workout_name.lower() else 0.0)
            )
            swolf = round(swolf_adj)
            
            # Additional swimming metrics
            activity_data.update({
                'distance_km': distance,
                'distance_m': distance * 1000,
                'avg_pace_min_100m': round(100 / avg_speed * 60 / 1000, 2),
                'avg_speed_kph': avg_speed,
                'stroke_rate': stroke_rate,
                'stroke_length_m': stroke_length,
                'swolf_score': swolf,
                'strokes_per_length': round(25 / stroke_length),
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
                rep_range = sport_params['strength']['rep_range']
                set_range = sport_params['strength']['set_range']
                rest_range = sport_params['strength']['rest_period_range']
            
            reps = round(random.uniform(*rep_range))
            sets = round(random.uniform(*set_range))
            rest_period = round(random.uniform(*rest_range))
            
            # Muscle oxygen varies by workout intensity
            muscle_oxygen_base = sport_params['strength']['muscle_oxygen_range']
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
    
def generate_speed_profile(time_points, base_speed, workout_name, variability):
    """
    Generate a speed profile for cycling or swimming workouts.
    
    Parameters:
    - time_points: Array of time points for the workout
    - base_speed: Base speed in km/h
    - workout_name: Name of the workout to determine pattern
    - variability: Base variability factor for the speed
    
    Returns:
    - Array of speed values for each time point
    """
    speed_series = []
    
    # Determine pattern based on workout type
    if "interval" in workout_name.lower() or "vo2max" in workout_name.lower():
        # Interval pattern for speed
        interval_length = 3 if "vo2max" in workout_name.lower() else 5  # minutes
        recovery_length = 2 if "vo2max" in workout_name.lower() else 3  # minutes
        high_speed = base_speed * 1.15  # Less variation in speed than in power
        low_speed = base_speed * 0.85
        
        # Warm-up period (first 15% of workout)
        warmup_end = int(len(time_points) * 0.15)
        # Cool-down period (last 10% of workout)
        cooldown_start = int(len(time_points) * 0.9)
        
        # Convert minutes to time points
        interval_points = int(interval_length * 4)  # Assuming 15-second intervals
        recovery_points = int(recovery_length * 4)
        
        for i, t in enumerate(time_points):
            if i < warmup_end:
                # Warm-up progression
                progress = i / warmup_end
                speed = base_speed * 0.7 * progress + base_speed * 0.3
                # Add more variability during warmup
                speed_var = variability * 1.2
            elif i >= cooldown_start:
                # Cool-down
                progress = (i - cooldown_start) / (len(time_points) - cooldown_start)
                speed = base_speed - progress * (base_speed * 0.3)
                speed_var = variability * 1.2
            else:
                # Intervals section
                cycle_length = interval_points + recovery_points
                position_in_cycle = (i - warmup_end) % cycle_length
                
                if position_in_cycle < interval_points:
                    # In high-intensity interval
                    speed = high_speed
                    speed_var = variability * 0.8  # More consistent speed in intervals
                else:
                    # In recovery
                    speed = low_speed
                    speed_var = variability
            
            # Add random variations (smaller than power variations)
            speed *= random.uniform(1 - speed_var, 1 + speed_var)
            speed_series.append(max(0, speed))
    
    elif "threshold" in workout_name.lower() or "sweetspot" in workout_name.lower():
        # Threshold/sweetspot pattern - more steady speed
        
        # Warm-up period (first 15% of workout)
        warmup_end = int(len(time_points) * 0.15)
        # Build period (next 10% of workout)
        build_end = warmup_end + int(len(time_points) * 0.1)
        # Main set (next 60% of workout)
        main_end = build_end + int(len(time_points) * 0.6)
        
        threshold_speed = base_speed * 1.03  # Smaller delta than power
        
        for i, t in enumerate(time_points):
            if i < warmup_end:
                # Warm-up progression
                progress = i / warmup_end
                speed = base_speed * 0.7 + progress * (base_speed * 0.9 - base_speed * 0.7)
                speed_var = variability * 1.2
            elif i < build_end:
                # Build to threshold
                progress = (i - warmup_end) / (build_end - warmup_end)
                speed = base_speed * 0.9 + progress * (threshold_speed - base_speed * 0.9)
                speed_var = variability
            elif i < main_end:
                # Main threshold block with consistent speed
                speed = threshold_speed
                speed_var = variability * 0.6  # Less variation during threshold
            else:
                # Cool down
                progress = (i - main_end) / (len(time_points) - main_end)
                speed = threshold_speed - progress * (threshold_speed - base_speed * 0.7)
                speed_var = variability * 1.2
            
            # Add random variations
            speed *= random.uniform(1 - speed_var, 1 + speed_var)
            speed_series.append(max(0, speed))
    
    elif "hill" in workout_name.lower():
        # Hill pattern - more variable speed
        
        # Generate more variable speed with clear drops for hills
        interval_length = 4  # minutes for hill climbing
        recovery_length = 3  # minutes for descent/recovery
        low_speed = base_speed * 0.7  # Slower uphill
        high_speed = base_speed * 1.1  # Faster downhill
        
        # Warm-up period (first 15% of workout)
        warmup_end = int(len(time_points) * 0.15)
        # Cool-down period (last 10% of workout)
        cooldown_start = int(len(time_points) * 0.9)
        
        # Convert minutes to time points
        interval_points = int(interval_length * 4)
        recovery_points = int(recovery_length * 4)
        
        for i, t in enumerate(time_points):
            if i < warmup_end:
                progress = i / warmup_end
                speed = base_speed * 0.7 * progress + base_speed * 0.3
                speed_var = variability
            elif i >= cooldown_start:
                progress = (i - cooldown_start) / (len(time_points) - cooldown_start)
                speed = base_speed - progress * (base_speed * 0.3)
                speed_var = variability
            else:
                cycle_length = interval_points + recovery_points
                position_in_cycle = (i - warmup_end) % cycle_length
                
                if position_in_cycle < interval_points:
                    # Slower uphill
                    speed = low_speed
                    speed_var = variability * 1.2
                else:
                    # Faster downhill
                    speed = high_speed
                    speed_var = variability * 1.5  # More variable on descents
            
            # Add random variations
            speed *= random.uniform(1 - speed_var, 1 + speed_var)
            speed_series.append(max(0, speed))
    
    elif "recovery" in workout_name.lower():
        # Recovery ride - very steady, low-intensity speed
        
        recovery_speed = base_speed * 0.8  # 80% of base speed
        
        # Warm-up period (just first 10% of workout)
        warmup_end = int(len(time_points) * 0.1)
        
        for i, t in enumerate(time_points):
            if i < warmup_end:
                # Very gentle warm-up
                progress = i / warmup_end
                speed = base_speed * 0.6 + progress * (recovery_speed - base_speed * 0.6)
                speed_var = variability
            else:
                # Main portion - gentle undulations
                speed = recovery_speed
                
                # Add occasional very small variations
                cycle_position = i % 100
                speed *= (1 + 0.05 * math.sin(2 * math.pi * cycle_position / 100))
                speed_var = variability * 0.7  # Less variability for recovery
            
            # Add minimal random variations
            speed *= random.uniform(1 - speed_var/2, 1 + speed_var/2)
            speed_series.append(max(0, speed))
    
    elif "endurance" in workout_name.lower():
        # Endurance ride - steady speed with natural variations
        
        # Warm-up period (first 15% of workout)
        warmup_end = int(len(time_points) * 0.15)
        # Build to endurance (next 10%)
        build_end = warmup_end + int(len(time_points) * 0.1)
        # Main endurance period (next 65%)
        main_end = build_end + int(len(time_points) * 0.65)
        
        endurance_speed = base_speed * 0.95  # 95% of base speed
        
        for i, t in enumerate(time_points):
            if i < warmup_end:
                # Gradual warm-up
                progress = i / warmup_end
                speed = base_speed * 0.7 + progress * (base_speed * 0.9 - base_speed * 0.7)
                speed_var = variability * 1.2
            elif i < build_end:
                # Build to endurance speed
                progress = (i - warmup_end) / (build_end - warmup_end)
                speed = base_speed * 0.9 + progress * (endurance_speed - base_speed * 0.9)
                speed_var = variability
            elif i < main_end:
                # Main endurance block
                speed = endurance_speed
                
                # Add some rolling variations
                cycle_length = 80  # 20-minute undulating cycles
                position_in_cycle = i % cycle_length
                cycle_factor = math.sin(2 * math.pi * position_in_cycle / cycle_length)
                speed *= (1 + 0.05 * cycle_factor)  # ±5% undulations
                
                speed_var = variability * 0.9  # Slightly reduced variability
            else:
                # Cool down
                progress = (i - main_end) / (len(time_points) - main_end)
                speed = endurance_speed * (1 - progress * 0.3)  # Gradual reduction
                speed_var = variability * 1.1
            
            # Add random variations
            speed *= random.uniform(1 - speed_var, 1 + speed_var)
            speed_series.append(max(0, speed))
    
    elif "tempo" in workout_name.lower():
        # Tempo ride - moderately hard sustained effort
        
        # Warm-up period (first 15% of workout)
        warmup_end = int(len(time_points) * 0.15)
        # Build to tempo (next 10%)
        build_end = warmup_end + int(len(time_points) * 0.1)
        # First tempo block (next 25%)
        first_tempo_end = build_end + int(len(time_points) * 0.25)
        # Recovery period (next 5%)
        recovery_end = first_tempo_end + int(len(time_points) * 0.05)
        # Second tempo block (next 30%)
        second_tempo_end = recovery_end + int(len(time_points) * 0.3)
        
        tempo_speed = base_speed * 1.02  # 102% of base
        recovery_speed = base_speed * 0.85  # 85% recovery
        
        for i, t in enumerate(time_points):
            if i < warmup_end:
                # Progressive warm-up
                progress = i / warmup_end
                speed = base_speed * 0.7 + progress * (base_speed * 0.9 - base_speed * 0.7)
                speed_var = variability * 1.1
            elif i < build_end:
                # Build to tempo
                progress = (i - warmup_end) / (build_end - warmup_end)
                speed = base_speed * 0.9 + progress * (tempo_speed - base_speed * 0.9)
                speed_var = variability
            elif i < first_tempo_end:
                # First tempo block
                speed = tempo_speed
                
                # Add mild surges
                if (i - build_end) % 20 < 4:  # 1-minute surge every 5 minutes
                    speed *= 1.03  # 3% increase for surges
                    
                speed_var = variability * 0.8  # More controlled during tempo
            elif i < recovery_end:
                # Short recovery between tempo blocks
                speed = recovery_speed
                speed_var = variability * 1.1
            elif i < second_tempo_end:
                # Second tempo block
                speed = tempo_speed
                
                # Add mild surges
                if (i - recovery_end) % 16 < 4:  # 1-minute surge every 4 minutes
                    speed *= 1.05  # 5% increase for surges (slightly harder in second block)
                    
                speed_var = variability * 0.8
            else:
                # Cool down
                progress = (i - second_tempo_end) / (len(time_points) - second_tempo_end)
                speed = tempo_speed - progress * (tempo_speed - base_speed * 0.7)
                speed_var = variability * 1.1
            
            # Add random variations
            speed *= random.uniform(1 - speed_var, 1 + speed_var)
            speed_series.append(max(0, speed))
    
    # Added support for specific workout types from the templates
    elif "speed" in workout_name.lower():
        # Speed work - high intensity, short bursts
        
        interval_length = 1  # 1 minute fast
        recovery_length = 3  # 3 minutes recovery
        high_speed = base_speed * 1.2  # 20% faster during speed bursts
        low_speed = base_speed * 0.75  # Recovery pace
        
        # Warm-up period (first 20% of workout)
        warmup_end = int(len(time_points) * 0.2)
        # Cool-down period (last 15% of workout)
        cooldown_start = int(len(time_points) * 0.85)
        
        # Convert minutes to time points
        interval_points = int(interval_length * 4)
        recovery_points = int(recovery_length * 4)
        
        for i, t in enumerate(time_points):
            if i < warmup_end:
                # Longer warm-up for speed work
                progress = i / warmup_end
                speed = base_speed * 0.7 + progress * (base_speed * 0.9 - base_speed * 0.7)
                speed_var = variability * 1.2
            elif i >= cooldown_start:
                # Cool-down
                progress = (i - cooldown_start) / (len(time_points) - cooldown_start)
                speed = base_speed - progress * (base_speed * 0.3)
                speed_var = variability * 1.2
            else:
                # Speed intervals
                cycle_length = interval_points + recovery_points
                position_in_cycle = (i - warmup_end) % cycle_length
                
                if position_in_cycle < interval_points:
                    # Very fast burst
                    speed = high_speed
                    speed_var = variability * 0.6  # More consistent during speed bursts
                else:
                    # Full recovery
                    speed = low_speed
                    speed_var = variability * 1.1
            
            # Add random variations
            speed *= random.uniform(1 - speed_var, 1 + speed_var)
            speed_series.append(max(0, speed))
    
    elif "long" in workout_name.lower():
        # Long workout - steady with occasional harder efforts
        
        endurance_speed = base_speed * 0.9  # 90% of base speed
        
        # Warm-up period (first 10% of workout for long sessions)
        warmup_end = int(len(time_points) * 0.1)
        # Main portion
        main_end = int(len(time_points) * 0.9)
        
        for i, t in enumerate(time_points):
            if i < warmup_end:
                # Gradual warm-up
                progress = i / warmup_end
                speed = base_speed * 0.7 + progress * (endurance_speed - base_speed * 0.7)
                speed_var = variability * 1.2
            elif i >= main_end:
                # Cool down
                progress = (i - main_end) / (len(time_points) - main_end)
                speed = endurance_speed - progress * (endurance_speed - base_speed * 0.7)
                speed_var = variability * 1.1
            else:
                # Main portion - endurance with occasional efforts
                speed = endurance_speed
                
                # Every 30 minutes, add a 5-minute moderate effort
                if (i - warmup_end) % 120 >= 0 and (i - warmup_end) % 120 < 20:
                    effort_progress = ((i - warmup_end) % 120) / 20
                    # Bell curve for effort
                    if effort_progress < 0.5:
                        effort_factor = effort_progress * 2
                    else:
                        effort_factor = (1 - effort_progress) * 2
                    
                    speed *= (1 + 0.05 * effort_factor)  # Up to 5% higher
                
                # Add some rolling variations
                cycle_length = 100  # 25-minute undulating cycles
                position_in_cycle = i % cycle_length
                cycle_factor = math.sin(2 * math.pi * position_in_cycle / cycle_length)
                speed *= (1 + 0.03 * cycle_factor)  # ±3% undulations
                
                speed_var = variability * 0.9
            
            # Add random variations
            speed *= random.uniform(1 - speed_var, 1 + speed_var)
            speed_series.append(max(0, speed))
            
    else:
        # Default pattern
        
        warmup_end = int(len(time_points) * 0.15)
        cooldown_start = int(len(time_points) * 0.85)
        
        for i, t in enumerate(time_points):
            if i < warmup_end:
                # Warm-up progression
                progress = i / warmup_end
                speed = base_speed * 0.7 + progress * (base_speed * 0.9 - base_speed * 0.7)
                speed_var = variability * 1.1
            elif i >= cooldown_start:
                # Cool-down
                progress = (i - cooldown_start) / (len(time_points) - cooldown_start)
                speed = base_speed - progress * (base_speed * 0.3)
                speed_var = variability * 1.1
            else:
                # Main set with some natural variations
                speed = base_speed
                
                # Add some rolling variations
                cycle_position = i % 60
                speed *= (1 + 0.03 * math.sin(2 * math.pi * cycle_position / 60))
                
                speed_var = variability
            
            # Add random variations
            speed *= random.uniform(1 - speed_var, 1 + speed_var)
            speed_series.append(max(0, speed))
    
    return speed_series

def generate_pace_profile(time_points, target_pace, workout_name, variability):
    """
    Generate a pace profile for running workouts.
    Pace is in minutes/km (lower is faster).
    
    Parameters:
    - time_points: Array of time points for the workout
    - target_pace: Target pace in minutes/km
    - workout_name: Name of the workout to determine pattern
    - variability: Base variability factor for the pace
    
    Returns:
    - Array of pace values for each time point (minutes/km)
    """
    pace_series = []
    
    # Note: For pace, lower values mean faster running
    # So the logic is inverted compared to speed profiles
    
    if "interval" in workout_name.lower():
        # Interval pattern for pace
        interval_length = 3  # minutes
        recovery_length = 3  # minutes
        
        # Fast pace is lower number
        is_vo2max = "vo2max" in workout_name.lower()
        fast_pace = target_pace * 0.85 if is_vo2max else target_pace * 0.9
        recovery_pace = target_pace * 1.4  # Much slower recovery
        
        # Warm-up period (first 15% of workout)
        warmup_end = int(len(time_points) * 0.15)
        # Cool-down period (last 10% of workout)
        cooldown_start = int(len(time_points) * 0.9)
        
        # Convert minutes to time points
        interval_points = int(interval_length * 4)  # Assuming 15-second intervals
        recovery_points = int(recovery_length * 4)
        
        for i, t in enumerate(time_points):
            if i < warmup_end:
                # Warm-up progression (start slow, get faster)
                progress = i / warmup_end
                pace = target_pace * 1.5 - progress * (target_pace * 1.5 - target_pace * 1.1)
                pace_var = variability * 1.2
            elif i >= cooldown_start:
                # Cool-down (gradually slow down)
                progress = (i - cooldown_start) / (len(time_points) - cooldown_start)
                pace = target_pace * 1.1 + progress * (target_pace * 0.4)
                pace_var = variability * 1.2
            else:
                # Intervals section
                cycle_length = interval_points + recovery_points
                position_in_cycle = (i - warmup_end) % cycle_length
                
                if position_in_cycle < interval_points:
                    # In high-intensity interval - consistent fast pace
                    pace = fast_pace
                    pace_var = variability * 0.6  # More consistent during intervals
                else:
                    # In recovery - slower, more variable
                    pace = recovery_pace
                    pace_var = variability * 1.3
            
            # Add random variations (avoid negative pace)
            pace *= random.uniform(1 - pace_var, 1 + pace_var)
            pace_series.append(max(2.0, pace))  # Minimum realistic pace
    
    elif "threshold" in workout_name.lower() or "tempo" in workout_name.lower():
        # Threshold/tempo pattern - consistent pace

        interval_length = 6  # Default for threshold
        recovery_length = 2  # Default recovery duration
        
        # Warm-up period (first 15% of workout)
        warmup_end = int(len(time_points) * 0.15)
        # Build period (next 10% of workout)
        build_end = warmup_end + int(len(time_points) * 0.1)
        # Main set (next 60% of workout)
        main_end = build_end + int(len(time_points) * 0.6)
        
        # Slightly faster for threshold than tempo
        if "threshold" in workout_name.lower():
            main_pace = target_pace * 0.93  # Faster pace for threshold
            use_intervals = True
        else:  # tempo
            main_pace = target_pace * 0.98  # Slightly faster than target
            use_intervals = False
        
        # For interval-based threshold
        interval_points = int(interval_length * 4)
        recovery_points = int(recovery_length * 4)
        recovery_pace = target_pace * 1.2  # Recovery between threshold intervals
        
        for i, t in enumerate(time_points):
            if i < warmup_end:
                # Warm-up progression (start slow, get faster)
                progress = i / warmup_end
                pace = target_pace * 1.4 - progress * (target_pace * 1.4 - target_pace * 1.1)
                pace_var = variability * 1.2
            elif i < build_end:
                # Build to threshold/tempo (gradually get faster)
                progress = (i - warmup_end) / (build_end - warmup_end)
                pace = target_pace * 1.1 - progress * (target_pace * 1.1 - main_pace)
                pace_var = variability
            elif i < main_end:
                # Main threshold/tempo block
                if use_intervals:
                    cycle_length = interval_points + recovery_points
                    position_in_cycle = (i - build_end) % cycle_length
                    
                    if position_in_cycle < interval_points:
                        # In threshold interval
                        pace = main_pace
                        pace_var = variability * 0.5  # Very consistent
                    else:
                        # Recovery between intervals
                        pace = recovery_pace
                        pace_var = variability
                else:
                    # Continuous tempo
                    pace = main_pace
                    pace_var = variability * 0.6  # Consistent during tempo
            else:
                # Cool down (gradually slow down)
                progress = (i - main_end) / (len(time_points) - main_end)
                pace = main_pace + progress * (target_pace * 1.3 - main_pace)
                pace_var = variability * 1.2
            
            # Add random variations
            pace *= random.uniform(1 - pace_var, 1 + pace_var)
            pace_series.append(max(2.0, pace))
    
    elif "hill" in workout_name.lower():
        # Hill repeats pattern
        
        # Hill pace is much slower (higher number), downhill is faster (lower number)
        uphill_pace = target_pace * 1.4  # Much slower uphill
        downhill_pace = target_pace * 0.9  # Faster downhill
        
        # Warm-up period (first 15% of workout)
        warmup_end = int(len(time_points) * 0.15)
        # Cool-down period (last 10% of workout)
        cooldown_start = int(len(time_points) * 0.9)
        
        # Hill and recovery durations
        hill_length = 4  # minutes
        recovery_length = 3  # minutes
        
        # Convert minutes to time points
        hill_points = int(hill_length * 4)
        recovery_points = int(recovery_length * 4)
        
        for i, t in enumerate(time_points):
            if i < warmup_end:
                # Warm-up progression
                progress = i / warmup_end
                pace = target_pace * 1.4 - progress * (target_pace * 1.4 - target_pace * 1.1)
                pace_var = variability
            elif i >= cooldown_start:
                # Cool-down
                progress = (i - cooldown_start) / (len(time_points) - cooldown_start)
                pace = target_pace * 1.1 + progress * (target_pace * 0.3)
                pace_var = variability
            else:
                cycle_length = hill_points + recovery_points
                position_in_cycle = (i - warmup_end) % cycle_length
                
                if position_in_cycle < hill_points:
                    # Slower uphill
                    progress = position_in_cycle / hill_points
                    # Pace gets slower throughout the hill
                    pace = uphill_pace * (1 + progress * 0.2)
                    pace_var = variability * 1.3  # More variable on hills
                else:
                    # Faster downhill/recovery
                    recovery_progress = (position_in_cycle - hill_points) / recovery_points
                    # Start fast downhill, then level off
                    if recovery_progress < 0.3:
                        pace = downhill_pace
                    else:
                        pace = downhill_pace + (recovery_progress - 0.3) * (target_pace - downhill_pace) / 0.7
                    pace_var = variability * 1.2
            
            # Add random variations
            pace *= random.uniform(1 - pace_var, 1 + pace_var)
            pace_series.append(max(2.0, pace))
    
    elif "recovery" in workout_name.lower():
        # Recovery run - slow, consistent pace
        
        recovery_pace = target_pace * 1.3  # 30% slower than target
        
        for i, t in enumerate(time_points):
            if i < len(time_points) * 0.1:  # Short warm-up
                # Start even slower, gradually reach recovery pace
                progress = i / (len(time_points) * 0.1)
                pace = target_pace * 1.5 - progress * (target_pace * 1.5 - recovery_pace)
                pace_var = variability * 0.8
            elif i > len(time_points) * 0.9:  # Short cool-down
                # Gradually slow down more
                progress = (i - len(time_points) * 0.9) / (len(time_points) * 0.1)
                pace = recovery_pace + progress * (target_pace * 1.5 - recovery_pace)
                pace_var = variability * 0.8
            else:
                # Main recovery portion - consistent slow pace
                pace = recovery_pace
                
                # Add very mild undulations
                cycle_position = i % 80
                pace *= (1 + 0.02 * math.sin(2 * math.pi * cycle_position / 80))
                
                pace_var = variability * 0.7  # More consistent for recovery
            
            # Add smaller random variations
            pace *= random.uniform(1 - pace_var/2, 1 + pace_var/2)
            pace_series.append(max(2.0, pace))
    
    elif "endurance" in workout_name.lower() or "easy" in workout_name.lower():
        # Endurance run - steady, moderate pace
        
        endurance_pace = target_pace * 1.15  # 15% slower than target
        
        # Warm-up period (first 15% of workout)
        warmup_end = int(len(time_points) * 0.15)
        # Main portion (next 75%)
        main_end = int(len(time_points) * 0.9)
        
        for i, t in enumerate(time_points):
            if i < warmup_end:
                # Warm-up progression
                progress = i / warmup_end
                pace = target_pace * 1.4 - progress * (target_pace * 1.4 - endurance_pace)
                pace_var = variability
            elif i < main_end:
                # Main endurance portion
                pace = endurance_pace
                
                # Add gentle rolling terrain simulation
                cycle_position = i % 120
                pace *= (1 + 0.04 * math.sin(2 * math.pi * cycle_position / 120))
                
                pace_var = variability * 0.9
            else:
                # Cool-down
                progress = (i - main_end) / (len(time_points) - main_end)
                pace = endurance_pace + progress * (target_pace * 1.3 - endurance_pace)
                pace_var = variability
            
            # Add random variations
            pace *= random.uniform(1 - pace_var, 1 + pace_var)
            pace_series.append(max(2.0, pace))
    
    elif "long" in workout_name.lower():
        # Long run - steady pace with gradual fatigue
        
        long_pace = target_pace * 1.2  # 20% slower than target
        
        # Warm-up period (first 10% of workout)
        warmup_end = int(len(time_points) * 0.1)
        # Main portion (next 80%)
        main_end = int(len(time_points) * 0.9)
        
        for i, t in enumerate(time_points):
            if i < warmup_end:
                # Warm-up progression
                progress = i / warmup_end
                pace = target_pace * 1.4 - progress * (target_pace * 1.4 - long_pace)
                pace_var = variability
            elif i < main_end:
                # Main long run portion with gradual fatigue
                progress = (i - warmup_end) / (main_end - warmup_end)
                
                # Pace gradually slows as fatigue sets in
                fatigue_factor = 1 + 0.1 * (progress ** 2)
                pace = long_pace * fatigue_factor
                
                # Add gentle rolling terrain simulation
                cycle_position = i % 180
                pace *= (1 + 0.05 * math.sin(2 * math.pi * cycle_position / 180))
                
                pace_var = variability * (1 + 0.2 * progress)  # More variable with fatigue
            else:
                # Cool-down
                progress = (i - main_end) / (len(time_points) - main_end)
                current_pace = long_pace * 1.1  # Slightly slower at end of main set
                pace = current_pace + progress * (target_pace * 1.3 - current_pace)
                pace_var = variability
            
            # Add random variations
            pace *= random.uniform(1 - pace_var, 1 + pace_var)
            pace_series.append(max(2.0, pace))
    
    else:
        # Default pattern - steady pace with slight variations
        # This handles any workout types not explicitly covered
        
        default_pace = target_pace * 1.1  # 10% slower than target by default
        
        for i, t in enumerate(time_points):
            if i < len(time_points) * 0.15:  # Warm-up
                progress = i / (len(time_points) * 0.15)
                pace = target_pace * 1.4 - progress * (target_pace * 1.4 - default_pace)
                pace_var = variability
            elif i > len(time_points) * 0.85:  # Cool-down
                progress = (i - len(time_points) * 0.85) / (len(time_points) * 0.15)
                pace = default_pace + progress * (target_pace * 1.3 - default_pace)
                pace_var = variability
            else:
                # Main workout portion
                pace = default_pace
                
                # Add gentle undulations
                cycle_position = i % 100
                pace *= (1 + 0.03 * math.sin(2 * math.pi * cycle_position / 100))
                
                pace_var = variability * 0.8
            
            # Add random variations
            pace *= random.uniform(1 - pace_var, 1 + pace_var)
            pace_series.append(max(2.0, pace))
    
    return pace_series

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
                'tss_per_hour': 40
            },
            'endurance': {
                'name': 'Endurance Swim',
                'description': 'Steady-paced endurance swim with some drill sets',
                'tss_per_hour': 60
            },
            'intervals': {
                'name': 'Swim Intervals',
                'description': 'Mixed intervals focusing on speed and technique',
                'tss_per_hour': 80
            },
            'threshold': {
                'name': 'Threshold Swim',
                'description': 'Sustained effort at or near threshold pace',
                'tss_per_hour': 90
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
                'tss_per_hour': 60
            },
            'tempo': {
                'name': 'Tempo Ride',
                'description': 'Sustained moderate effort with some harder efforts',
                'tss_per_hour': 75
            },
            'sweetspot': {
                'name': 'Sweet Spot Intervals',
                'description': 'Intervals at 88-93% of FTP',
                'tss_per_hour': 85
            },
            'threshold': {
                'name': 'Threshold Intervals',
                'description': 'Intervals at or just below FTP',
                'tss_per_hour': 95
            },
            'vo2max': {
                'name': 'VO2max Intervals',
                'description': 'Short, high-intensity intervals',
                'tss_per_hour': 110
            },
            'hills': {
                'name': 'Hill Repeats',
                'description': 'Uphill intervals to build strength',
                'tss_per_hour': 100
            }
        },

        'run': {
            'recovery': {
                'name': 'Recovery Run',
                'description': 'Very easy pace to promote recovery',
                'tss_per_hour': 40
            },
            'endurance': {
                'name': 'Endurance Run',
                'description': 'Steady effort to build aerobic endurance',
                'tss_per_hour': 70
            },
            'long': {
                'name': 'Long Run',
                'description': 'Extended duration at easy to moderate pace',
                'tss_per_hour': 80
            },
            'tempo': {
                'name': 'Tempo Run',
                'description': 'Sustained effort at moderate intensity',
                'tss_per_hour': 85
            },
            'threshold': {
                'name': 'Threshold Intervals',
                'description': 'Intervals at or near threshold pace',
                'tss_per_hour': 95
            },
            'intervals': {
                'name': 'Speed Intervals',
                'description': 'Short, high-intensity repeats with recovery',
                'tss_per_hour': 110
            },
            'hills': {
                'name': 'Hill Repeats',
                'description': 'Uphill intervals to build strength and form',
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