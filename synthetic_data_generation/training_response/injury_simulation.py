import random
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SimConfig as cfg

# set seed for reproducibility
random.seed(42)

def calculate_decline_curve(t, alpha, beta):
    """
    Calculate the decay multiplier based on time t.
    
    Implements the formula: M(t) = 1 - alpha * t^beta
    
    Where:
    - t: normalized time/progression (0 to 1)
    - alpha: maximum decline magnitude (e.g., 0.2 for 20% drop)
    - beta: shape parameter (e.g., >1 for convex, <1 for concave)
    
    Returns:
    - Multiplier M(t) to be applied to a baseline value.
    """
    return 1 - alpha * (t ** beta)

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
    
    # Load pre-injury pattern configuration
    pattern_cfg = cfg.get('preinjury_patterns', {})
    strength_cfg = pattern_cfg.get('pattern_strength', {})
    visibility_cfg = pattern_cfg.get('visibility', {})
    acute_cfg = pattern_cfg.get('acute_injury', {})

    # Add some athlete-specific variability to pattern strength (some athletes show stronger patterns)
    modifier_range = strength_cfg.get('modifier_range', [0.7, 1.3])
    pattern_strength_modifier = random.uniform(modifier_range[0], modifier_range[1])

    # Add some randomness to the pattern onset (not all patterns start at the same time)
    start_fraction = strength_cfg.get('start_point_fraction', 0.33)
    pattern_start_point = random.randint(1, min(5, int(period_length * start_fraction)))
    effective_days = period_length - pattern_start_point

    # Decide which patterns this athlete will exhibit (not all athletes show all patterns)
    show_hrv_pattern = random.random() < visibility_cfg.get('hrv', 0.85)
    show_rhr_pattern = random.random() < visibility_cfg.get('rhr', 0.80)
    show_sleep_pattern = random.random() < visibility_cfg.get('sleep', 0.70)
    show_bb_pattern = random.random() < visibility_cfg.get('body_battery', 0.75)

    hrv_sensitivity = athlete['recovery_signature']['hrv_sensitivity']
    rhr_sensitivity = athlete['recovery_signature']['rhr_sensitivity'] 
    sleep_sensitivity = athlete['recovery_signature']['sleep_sensitivity']
    stress_sensitivity = athlete['recovery_signature']['stress_sensitivity']
    
    # Sometimes injuries happen with minimal warning (acute injuries)
    acute_prob = acute_cfg.get('probability', 0.15)
    is_acute_injury = random.random() < acute_prob
    if is_acute_injury:
        # For acute injuries, only modify minimal days before injury
        warning_range = acute_cfg.get('warning_window_days', [1, 3])
        pattern_start_point = period_length - random.randint(warning_range[0], warning_range[1])
    
    # Create a recent history of the athlete's data
    if len(daily_data_list) > 3:
        # Get recent history for temporal effects
        recent_history = daily_data_list[max(0, injury_day_index-3):injury_day_index]
    else:
        recent_history = None

    # Load metric-specific configuration
    hrv_cfg = pattern_cfg.get('hrv', {})
    rhr_cfg = pattern_cfg.get('rhr', {})
    sleep_cfg = pattern_cfg.get('sleep', {})
    bb_cfg = pattern_cfg.get('body_battery', {})
    stress_cfg = pattern_cfg.get('stress', {})

    # Create pattern alterations with realistic noise
    for i, day_data in enumerate(pre_injury_period):
        # Skip early days before pattern starts
        if i < pattern_start_point:
            continue

        # Calculate progression factor (0 to 1) - how close to injury day
        progression = (i - pattern_start_point) / (period_length - pattern_start_point) if (period_length - pattern_start_point) > 0 else 0

        # Add day-to-day variability (good days even during overall decline)
        noise_range = hrv_cfg.get('noise_range', [0.0, 0.2])
        daily_variability = random.normalvariate(0, noise_range[1])

        # Calculate cross-stress multipliers
        cross_stress_mults = calculate_cross_stress_effects(day_data, recent_history)

        # 1. Modify HRV if this athlete shows HRV pattern
        if show_hrv_pattern:
            # Alpha: Maximum decline magnitude (from config)
            hrv_max_decline = hrv_cfg.get('max_decline', 0.25)
            hrv_base_decline = hrv_cfg.get('base_decline', 0.05)
            hrv_progression_factor = hrv_cfg.get('progression_factor', 0.20)
            alpha = min(hrv_max_decline, hrv_base_decline + progression * hrv_progression_factor) * pattern_strength_modifier * hrv_sensitivity * cross_stress_mults['hrv']
            # Beta: Curve shape (from config)
            beta = hrv_cfg.get('curve_shape', 1.2)

            # Calculate multiplier using the formal mathematical curve
            hrv_multiplier = calculate_decline_curve(progression, alpha, beta)

            # Add daily variability - some days HRV might improve slightly despite overall decline
            daily_hrv_adjustment = daily_variability * baseline_hrv * 0.15

            # Calculate new HRV
            new_hrv = baseline_hrv * hrv_multiplier + daily_hrv_adjustment

            # Ensure within physiological limits (from config)
            hrv_bounds = hrv_cfg.get('bounds', [0.65, 1.10])
            day_data['hrv'] = max(baseline_hrv * hrv_bounds[0], min(baseline_hrv * hrv_bounds[1], new_hrv))
        
        if show_hrv_pattern and random.random() < 0.3:  # 30% chance of non-linear pattern
            # Sometimes HRV improves briefly before crashing (false recovery)
            if 0.5 < progression < 0.8 and random.random() < 0.4:
                # Temporary improvement in HRV (false recovery)
                # Since alpha is defined locally above, we can't easily modify it for the helper without recalculating.
                # However, the original code modified 'hrv_decline_factor' (which is alpha).
                # To maintain logic:
                # alpha = alpha * 0.3
                # Recalculate curve? Or just adjust the logic. 
                # The original logic modified hrv_decline_factor BEFORE usage. 
                # But here we used it already.
                # Let's adjust day_data['hrv'] directly to simulate this anomaly or move the logic up.
                pass # Simplified: The helper function formalizes the main trend. Anomalies are noise.
        
        # 2. Modify resting heart rate if this athlete shows RHR pattern
        if show_rhr_pattern:
            # Base increase factor (from config)
            rhr_max_increase = rhr_cfg.get('max_increase', 0.12)
            rhr_base_increase = rhr_cfg.get('base_increase', 0.02)
            rhr_progression_factor = rhr_cfg.get('progression_factor', 0.10)
            rhr_increase_factor = min(rhr_max_increase, rhr_base_increase + progression * rhr_progression_factor) * pattern_strength_modifier * rhr_sensitivity * cross_stress_mults['rhr']

            # Add daily variability
            daily_rhr_adjustment = -daily_variability * baseline_rhr * 0.08  # Negative because lower is better for RHR

            # Calculate new RHR with realistic noise
            new_rhr = baseline_rhr * (1 + rhr_increase_factor * (progression ** 1.1)) + daily_rhr_adjustment

            # Ensure within physiological limits (from config)
            rhr_bounds = rhr_cfg.get('bounds', [0.92, 1.15])
            day_data['resting_hr'] = max(baseline_rhr * rhr_bounds[0], min(baseline_rhr * rhr_bounds[1], new_rhr))
        
        # 3. Modify sleep quality if this athlete shows sleep pattern
        sleep_offset = sleep_cfg.get('pattern_offset', 0.3)
        if show_sleep_pattern and progression > sleep_offset:
            # Alpha for sleep (from config)
            sleep_max_decline = sleep_cfg.get('max_decline', 0.20)
            sleep_progression_factor = sleep_cfg.get('progression_factor', 0.30)
            sleep_alpha = min(sleep_max_decline, (progression - sleep_offset) * sleep_progression_factor) * pattern_strength_modifier * sleep_sensitivity * cross_stress_mults['sleep']

            # Add daily variability - some nights are better than others
            daily_sleep_adjustment = daily_variability * 0.15

            # Apply changes with noise
            new_sleep_quality = day_data['sleep_quality'] * (1 - sleep_alpha) + daily_sleep_adjustment

            # Ensure within limits (from config)
            sleep_quality_bounds = sleep_cfg.get('quality_bounds', [0.4, 0.95])
            day_data['sleep_quality'] = max(sleep_quality_bounds[0], min(sleep_quality_bounds[1], new_sleep_quality))

            # Also adjust sleep stages (from config)
            stage_var = sleep_cfg.get('stage_variation', [-0.3, 0.3])
            deep_sleep_reduction = sleep_alpha * (1.0 + random.uniform(stage_var[0], stage_var[1]))
            rem_sleep_reduction = sleep_alpha * (0.8 + random.uniform(stage_var[0], stage_var[1]))

            # Cap reduction to prevent negative sleep values (max 95% reduction)
            deep_sleep_reduction = min(deep_sleep_reduction, 0.95)
            rem_sleep_reduction = min(rem_sleep_reduction, 0.95)

            day_data['deep_sleep'] = max(0, day_data['deep_sleep'] * (1 - deep_sleep_reduction))
            day_data['rem_sleep'] = max(0, day_data['rem_sleep'] * (1 - rem_sleep_reduction))
            # Ensure light_sleep doesn't go negative (sleep stages must sum to total)
            day_data['light_sleep'] = max(0, day_data['sleep_hours'] - day_data['deep_sleep'] - day_data['rem_sleep'])
        
        # 4. Modify body battery metrics if this athlete shows that pattern
        if show_bb_pattern and 'body_battery_morning' in day_data:
            # Alpha for body battery (from config)
            bb_max_decline = bb_cfg.get('max_decline', 0.25)
            bb_base_decline = bb_cfg.get('base_decline', 0.05)
            bb_progression_factor = bb_cfg.get('progression_factor', 0.10)
            bb_alpha = min(bb_max_decline, bb_base_decline + progression * bb_progression_factor) * pattern_strength_modifier * cross_stress_mults['body_battery']

            # Add daily variability
            daily_bb_adjustment = daily_variability * 8  # Some days feel better than others

            # Apply to morning body battery using decline curve (beta=1.0)
            bb_multiplier = calculate_decline_curve(progression, bb_alpha, 1.0)
            new_bb_morning = day_data['body_battery_morning'] * bb_multiplier + daily_bb_adjustment
            bb_morning_bounds = bb_cfg.get('morning_bounds', [40, 100])
            day_data['body_battery_morning'] = max(bb_morning_bounds[0], min(bb_morning_bounds[1], new_bb_morning))

            # Apply to evening body battery (beta=1.1)
            if 'body_battery_evening' in day_data:
                bb_evening_multiplier = calculate_decline_curve(progression, bb_alpha, 1.1)
                new_bb_evening = day_data['body_battery_evening'] * bb_evening_multiplier + daily_bb_adjustment * 0.5
                bb_evening_bounds = bb_cfg.get('evening_bounds', [15, 60])
                day_data['body_battery_evening'] = max(bb_evening_bounds[0], min(bb_evening_bounds[1], new_bb_evening))
        
        # 5. Increase stress levels as injury approaches - most athletes show this (from config)
        stress_max_increase = stress_cfg.get('max_increase', 30)
        stress_progression_cap = stress_cfg.get('progression_cap', 20)
        stress_increase = min(stress_progression_cap, progression * stress_max_increase * pattern_strength_modifier) * stress_sensitivity * cross_stress_mults['stress']
        stress_daily_variability = random.normalvariate(0, 8)  # High daily stress variability

        new_stress = day_data['stress'] + stress_increase + stress_daily_variability
        stress_bounds = stress_cfg.get('bounds', [20, 95])
        day_data['stress'] = min(stress_bounds[1], max(stress_bounds[0], new_stress))

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

    # Load false alarm configuration
    false_alarm_cfg = cfg.get('false_alarms', {})
    strong_prob = false_alarm_cfg.get('strong_probability', 0.3)
    strong_range = false_alarm_cfg.get('strong_strength_range', [0.8, 1.1])
    weak_range = false_alarm_cfg.get('weak_strength_range', [0.4, 0.8])

    if random.random() < strong_prob:
        pattern_strength = random.uniform(strong_range[0], strong_range[1])
    else:
        pattern_strength = random.uniform(weak_range[0], weak_range[1])

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

    Configuration loaded from: config/simulation_config.yaml (metric_interactions section)

    Args:
        metrics: Dictionary of current day's metrics
        history: Optional list of previous days' metrics

    Returns:
        Dictionary of interaction multipliers for various metrics
    """
    # Load interaction configuration
    interaction_cfg = cfg.get('metric_interactions', {})
    sleep_stress_cfg = interaction_cfg.get('sleep_stress', {})
    fatigue_sleep_cfg = interaction_cfg.get('fatigue_sleep', {})
    chronic_cfg = interaction_cfg.get('chronic_stress_training', {})

    multipliers = {
        'hrv': 1.0,
        'rhr': 1.0,
        'sleep': 1.0,
        'stress': 1.0,
        'body_battery': 1.0
    }

    # Sleep and stress interaction (poor sleep + high stress = worse effect)
    sleep_thresh = sleep_stress_cfg.get('sleep_threshold', 0.6)
    stress_thresh = sleep_stress_cfg.get('stress_threshold', 70)
    if metrics['sleep_quality'] < sleep_thresh and metrics['stress'] > stress_thresh:
        multipliers['hrv'] *= sleep_stress_cfg.get('hrv_multiplier', 1.4)
        multipliers['rhr'] *= sleep_stress_cfg.get('rhr_multiplier', 1.3)

    # High fatigue and poor sleep interaction
    fatigue_thresh = fatigue_sleep_cfg.get('fatigue_threshold', 75)
    fatigue_sleep_thresh = fatigue_sleep_cfg.get('sleep_threshold', 0.7)
    if 'fatigue' in metrics and metrics['fatigue'] > fatigue_thresh and metrics['sleep_quality'] < fatigue_sleep_thresh:
        multipliers['hrv'] *= fatigue_sleep_cfg.get('hrv_multiplier', 1.5)
        multipliers['body_battery'] *= fatigue_sleep_cfg.get('battery_multiplier', 1.4)

    # Temporal sequence effects (if we have history)
    consecutive_days = chronic_cfg.get('stress_consecutive_days', 3)
    if history and len(history) >= consecutive_days:
        # High stress followed by high training load
        if (history[-3]['stress'] > stress_thresh and
            history[-2]['stress'] > stress_thresh and
            history[-1]['actual_tss'] > history[-1]['planned_tss'] * 1.1):
            multipliers['hrv'] *= chronic_cfg.get('hrv_multiplier', 1.6)
            multipliers['sleep'] *= chronic_cfg.get('sleep_multiplier', 1.3)

    return multipliers