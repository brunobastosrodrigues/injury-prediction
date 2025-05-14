import random

# set seed for reproducibility
random.seed(42)

def inject_realistic_injury_patterns(athlete, daily_data_list, injury_day_index, lookback_days=14):
    """
    Inject realistic physiological patterns before injuries with appropriate noise and variability.
    
    Parameters:
    -----------
    athlete : dict
        Athlete profile with baseline metrics
    daily_data_list : list
        List of daily data dictionaries
    injury_day_index : int
        Index of the day when injury occurs
    lookback_days : int
        Number of days before injury to modify data
    """
    # Ensure we don't go beyond the beginning of the data
    start_idx = max(0, injury_day_index - lookback_days)
    
    # Get the relevant data slice leading to injury
    pre_injury_period = daily_data_list[start_idx:injury_day_index+1]
    period_length = len(pre_injury_period)
    
    # Calculate baseline values from athlete profile
    baseline_hrv = athlete['hrv_baseline']
    baseline_rhr = athlete['resting_hr']
    
    # Add some athlete-specific variability to pattern strength (some athletes show stronger patterns)
    pattern_strength_modifier = random.uniform(0.7, 1.3)
    
    # Add some randomness to the pattern onset (not all patterns start at the same time)
    pattern_start_point = random.randint(1, min(5, period_length//3))
    effective_days = period_length - pattern_start_point
    
    # Decide which patterns this athlete will exhibit (not all athletes show all patterns)
    show_hrv_pattern = random.random() < 0.85  # 85% show HRV decline
    show_rhr_pattern = random.random() < 0.80  # 80% show RHR increase
    show_sleep_pattern = random.random() < 0.70  # 70% show sleep quality decline
    show_bb_pattern = random.random() < 0.75  # 75% show body battery decline

    hrv_sensitivity = athlete['recovery_signature']['hrv_sensitivity']
    rhr_sensitivity = athlete['recovery_signature']['rhr_sensitivity'] 
    sleep_sensitivity = athlete['recovery_signature']['sleep_sensitivity']
    stress_sensitivity = athlete['recovery_signature']['stress_sensitivity']
    
    # Sometimes injuries happen with minimal warning (acute injuries)
    is_acute_injury = random.random() < 0.15  # 15% of injuries are acute with minimal warning
    if is_acute_injury:
        # For acute injuries, only modify 1-3 days before injury
        pattern_start_point = period_length - random.randint(1, 3)
    
    # Create a recent history of the athlete's data
    if len(daily_data_list) > 3:
        # Get recent history for temporal effects
        recent_history = daily_data_list[max(0, injury_day_index-3):injury_day_index]
    else:
        recent_history = None

    # Create pattern alterations with realistic noise
    for i, day_data in enumerate(pre_injury_period):
        # Skip early days before pattern starts
        if i < pattern_start_point:
            continue
            
        # Calculate progression factor (0 to 1) - how close to injury day
        progression = (i - pattern_start_point) / (period_length - pattern_start_point) if (period_length - pattern_start_point) > 0 else 0
        
        # Add day-to-day variability (good days even during overall decline)
        daily_variability = random.normalvariate(0, 0.2)  # Higher variability

        # Calculate cross-stress multipliers
        cross_stress_mults = calculate_cross_stress_effects(day_data, recent_history)
        
        # 1. Modify HRV if this athlete shows HRV pattern
        if show_hrv_pattern:
            # Base decline factor - more subtle max decline (25%)
            hrv_decline_factor = min(0.25, 0.05 + progression * 0.20) * pattern_strength_modifier * hrv_sensitivity * cross_stress_mults['hrv']
            
            # Add daily variability - some days HRV might improve slightly despite overall decline
            daily_hrv_adjustment = daily_variability * baseline_hrv * 0.15
            
            # Calculate new HRV with realistic noise
            new_hrv = baseline_hrv * (1 - hrv_decline_factor * (progression ** 1.2)) + daily_hrv_adjustment
            
            # Ensure within physiological limits (don't let it drop too low)
            day_data['hrv'] = max(baseline_hrv * 0.65, min(baseline_hrv * 1.1, new_hrv))
        
        if show_hrv_pattern and random.random() < 0.3:  # 30% chance of non-linear pattern
            # Sometimes HRV improves briefly before crashing (false recovery)
            if 0.5 < progression < 0.8 and random.random() < 0.4:
                # Temporary improvement in HRV (false recovery)
                hrv_decline_factor = hrv_decline_factor * 0.3
        
        # 2. Modify resting heart rate if this athlete shows RHR pattern
        if show_rhr_pattern:
            # Base increase factor - more subtle (12% max)
            rhr_increase_factor = min(0.12, 0.02 + progression * 0.10) * pattern_strength_modifier * rhr_sensitivity * cross_stress_mults['rhr']
            
            # Add daily variability
            daily_rhr_adjustment = -daily_variability * baseline_rhr * 0.08  # Negative because lower is better for RHR
            
            # Calculate new RHR with realistic noise
            new_rhr = baseline_rhr * (1 + rhr_increase_factor * (progression ** 1.1)) + daily_rhr_adjustment
            
            # Ensure within physiological limits
            day_data['resting_hr'] = max(baseline_rhr * 0.92, min(baseline_rhr * 1.15, new_rhr))
        
        # 3. Modify sleep quality if this athlete shows sleep pattern
        if show_sleep_pattern and progression > 0.3:  # Sleep issues often start later
            # More subtle sleep reduction
            sleep_reduction = min(0.2, (progression - 0.3) * 0.3) * pattern_strength_modifier * sleep_sensitivity * cross_stress_mults['sleep']
            
            # Add daily variability - some nights are better than others
            daily_sleep_adjustment = daily_variability * 0.15  # Some nights are better/worse
            
            # Apply changes with noise
            new_sleep_quality = day_data['sleep_quality'] * (1 - sleep_reduction) + daily_sleep_adjustment
            
            # Ensure within limits
            day_data['sleep_quality'] = max(0.4, min(0.95, new_sleep_quality))
            
            # Also adjust sleep stages
            deep_sleep_reduction = sleep_reduction * (1.0 + random.uniform(-0.3, 0.3))
            rem_sleep_reduction = sleep_reduction * (0.8 + random.uniform(-0.3, 0.3))
            
            day_data['deep_sleep'] = day_data['deep_sleep'] * (1 - deep_sleep_reduction)
            day_data['rem_sleep'] = day_data['rem_sleep'] * (1 - rem_sleep_reduction)
            day_data['light_sleep'] = day_data['sleep_hours'] - day_data['deep_sleep'] - day_data['rem_sleep']
        
        # 4. Modify body battery metrics if this athlete shows that pattern
        if show_bb_pattern and 'body_battery_morning' in day_data:
            # More subtle battery reduction
            bb_reduction = min(0.25, 0.05 + progression * 0.10) * pattern_strength_modifier * cross_stress_mults['body_battery']
            
            # Add daily variability
            daily_bb_adjustment = daily_variability * 8  # Some days feel better than others
            
            # Apply to morning body battery
            new_bb_morning = day_data['body_battery_morning'] * (1 - bb_reduction * (progression ** 1.0)) + daily_bb_adjustment
            day_data['body_battery_morning'] = max(40, min(100, new_bb_morning))
            
            # Apply to evening body battery
            if 'body_battery_evening' in day_data:
                new_bb_evening = day_data['body_battery_evening'] * (1 - bb_reduction * (progression ** 1.1)) + daily_bb_adjustment * 0.5
                day_data['body_battery_evening'] = max(15, min(60, new_bb_evening))
        
        # 5. Increase stress levels as injury approaches - most athletes show this
        stress_increase = min(20, progression * 30 * pattern_strength_modifier) * stress_sensitivity * cross_stress_mults['stress']
        stress_daily_variability = random.normalvariate(0, 8)  # High daily stress variability
        
        new_stress = day_data['stress'] + stress_increase + stress_daily_variability
        day_data['stress'] = min(95, max(20, new_stress))  # Keep within range

    return daily_data_list


def create_false_alarm_patterns(athlete, daily_data_list, start_index, pattern_days=10):
    """
    Create false alarm patterns that look like injury warnings but don't result in injury.
    This makes the data more realistic by including "close calls" that the model needs to distinguish.
    
    Parameters:
    -----------
    athlete : dict
        Athlete profile with baseline metrics
    daily_data_list : list
        List of daily data dictionaries
    start_index : int
        Index to start inserting false alarm patterns
    pattern_days : int
        Duration of the false alarm pattern
    """
    # Ensure we have enough days to work with
    if start_index + pattern_days >= len(daily_data_list):
        return daily_data_list
    
    if random.random() < 0.3:  # 30% of false alarms are "strong" 
        pattern_strength = random.uniform(0.8, 1.1)
    else:
        pattern_strength = random.uniform(0.4, 0.8)
    
    # Baseline values
    baseline_hrv = athlete['hrv_baseline']
    baseline_rhr = athlete['resting_hr']
    hrv_sensitivity = athlete['recovery_signature']['hrv_sensitivity']
    rhr_sensitivity = athlete['recovery_signature']['rhr_sensitivity'] 
    sleep_sensitivity = athlete['recovery_signature']['sleep_sensitivity']
    stress_sensitivity = athlete['recovery_signature']['stress_sensitivity']
    
    # Decide which patterns to show (usually fewer than real injury patterns)
    show_hrv_pattern = random.random() < 0.7
    show_rhr_pattern = random.random() < 0.6
    show_sleep_pattern = random.random() < 0.5

    # Create a recent history of the athlete's data
    # Create a recent history of the athlete's data
    if len(daily_data_list) > 3:
        # Get recent history for temporal effects
        recent_history = daily_data_list[max(0, start_index-3):start_index]
    else:
        recent_history = None
    
    # Create mild warning patterns that resolve without injury
    for i in range(pattern_days):
        day_index = start_index + i
        day_data = daily_data_list[day_index]
        
        # Calculate progression factor: rises then falls (peak in the middle)
        if i < pattern_days // 2:
            # First half - metrics worsen
            progression = i / (pattern_days // 2)
        else:
            # Second half - metrics improve (pattern resolves)
            progression = 1.0 - ((i - pattern_days // 2) / (pattern_days - pattern_days // 2))
        
        # Add daily variability
        daily_variability = random.normalvariate(0, 0.25)

        # Calculate cross-stress multipliers
        cross_stress_mults = calculate_cross_stress_effects(day_data, recent_history)
        
        # 1. HRV modification
        if show_hrv_pattern:
            hrv_change_factor = 0.15 * progression * pattern_strength * hrv_sensitivity * cross_stress_mults['hrv']
            daily_hrv_adjustment = daily_variability * baseline_hrv * 0.1
            
            new_hrv = baseline_hrv * (1 - hrv_change_factor) + daily_hrv_adjustment
            day_data['hrv'] = max(baseline_hrv * 0.75, min(baseline_hrv * 1.1, new_hrv))
        
        # 2. RHR modification
        if show_rhr_pattern:
            rhr_change_factor = 0.08 * progression * pattern_strength * rhr_sensitivity * cross_stress_mults['rhr']
            daily_rhr_adjustment = -daily_variability * baseline_rhr * 0.05
            
            new_rhr = baseline_rhr * (1 + rhr_change_factor) + daily_rhr_adjustment
            day_data['resting_hr'] = max(baseline_rhr * 0.95, min(baseline_rhr * 1.1, new_rhr))
        
        # 3. Sleep quality modification
        if show_sleep_pattern and i > pattern_days // 3:  # Start sleep issues later
            sleep_reduction = 0.1 * progression * pattern_strength * sleep_sensitivity * cross_stress_mults['sleep']
            daily_sleep_adjustment = daily_variability * 0.12
            
            new_sleep_quality = day_data['sleep_quality'] * (1 - sleep_reduction) + daily_sleep_adjustment
            day_data['sleep_quality'] = max(0.6, min(0.95, new_sleep_quality))
            
            # Mild sleep stage adjustments
            deep_sleep_reduction = sleep_reduction * (1.0 + random.uniform(-0.2, 0.2))
            day_data['deep_sleep'] = day_data['deep_sleep'] * (1 - deep_sleep_reduction)
            day_data['light_sleep'] = day_data['sleep_hours'] - day_data['deep_sleep'] - day_data['rem_sleep']
        
        # 4. Mild stress increase
        stress_increase = min(20, progression * 25 * pattern_strength) * stress_sensitivity * cross_stress_mults['stress']
        stress_daily_variability = random.normalvariate(0, 6)
        
        new_stress = day_data['stress'] + stress_increase + stress_daily_variability
        day_data['stress'] = min(85, max(20, new_stress))
    
    return daily_data_list

def calculate_cross_stress_effects(metrics, history=None):
    """
    Calculate multiplicative effects between different stressors.
    
    Args:
        metrics: Dictionary of current day's metrics
        history: Optional list of previous days' metrics
    
    Returns:
        Dictionary of interaction multipliers for various metrics
    """
    multipliers = {
        'hrv': 1.0,
        'rhr': 1.0,
        'sleep': 1.0,
        'stress': 1.0,
        'body_battery': 1.0
    }
    
    # Sleep and stress interaction (poor sleep + high stress = worse effect)
    if metrics['sleep_quality'] < 0.6 and metrics['stress'] > 70:
        multipliers['hrv'] *= 1.4  # 40% stronger HRV impact
        multipliers['rhr'] *= 1.3  # 30% stronger RHR impact
    
    # High fatigue and poor sleep interaction
    if 'fatigue' in metrics and metrics['fatigue'] > 75 and metrics['sleep_quality'] < 0.7:
        multipliers['hrv'] *= 1.5
        multipliers['body_battery'] *= 1.4
    
    # Temporal sequence effects (if we have history)
    if history and len(history) >= 3:
        # High stress followed by high training load
        if (history[-3]['stress'] > 70 and 
            history[-2]['stress'] > 70 and 
            history[-1]['actual_tss'] > history[-1]['planned_tss'] * 1.1):
            multipliers['hrv'] *= 1.6
            multipliers['sleep'] *= 1.3
    
    return multipliers