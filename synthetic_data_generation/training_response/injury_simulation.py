import random
import numpy as np
import pandas as pd

def calculate_baseline_injury_risk(athlete):
    # ----- Baseline risk factors -----
    
    # Age-related risk (increases exponentially after 30)
    age = athlete['age']
    age_risk = max(0, ((age - 30) / 50) ** 1.5) if age > 30 else 0
    
    # Training experience reduces risk
    experience_risk_reduction = min(0.5, athlete['training_experience'] / 20)
    
    # Genetic factors - some people are naturally more injury-prone
    genetic_risk = (1.2 - athlete['genetic_factor']) * 0.5  # Invert genetic_factor (higher is better)
    
    # BMI as risk factor (both very low and very high increase risk)
    height_m = athlete['height'] / 100  # convert cm to m
    bmi = athlete['weight'] / (height_m * height_m)
    bmi_risk = 0.1 * abs(bmi - 22) / 10  # Optimal BMI around 22
    
    # Baseline risk composite
    baseline_risk = (
        0.05 +  # Everyone has some minimum risk
        age_risk * 0.2 +
        genetic_risk * 0.15 +
        bmi_risk * 0.05 
    ) * (1 - experience_risk_reduction)  # Experience reduces all baseline risks

    return baseline_risk

def check_injury_occurrence(athlete, baseline_risk, performance, fatigue, acwr_timeline, tss_history, hrv_history, sleep_hours, sleep_quality, resting_hr):
    """
    Calculate injury probability based on various athlete metrics and training load trends.

    Returns:
    --------
    bool
        True if an injury occurs, False otherwise
    """

    # --- Establish baseline injury risk ---
    base_daily_risk = baseline_risk * 0.002

    # --- Extract ACWR features ---
    acwr_series = pd.Series(acwr_timeline)
    acwr_last = acwr_series.iloc[-1]  # Most recent ACWR
    acwr_ma7 = acwr_series.rolling(7).mean().iloc[-1]  # 7-day moving average
    acwr_volatility = acwr_series.rolling(7).std().iloc[-1]  # ACWR variability

    # --- Extract TSS features ---
    tss_series = pd.Series(tss_history)
    acute_load = tss_series.rolling(7).sum().iloc[-1]  # Last 7 days sum
    chronic_load = tss_series.rolling(28).sum().iloc[-1]  # Last 28 days sum
    tss_ratio = acute_load / (chronic_load + 1e-6)  # Acute:Chronic ratio

    # --- Extract HRV features ---
    hrv_series = pd.Series(hrv_history)
    hrv_ma7 = hrv_series.rolling(7).mean().iloc[-1]  # 7-day HRV average
    hrv_trend = hrv_series.iloc[-1] - hrv_series.iloc[0]  # Change in HRV over 28 days
    hrv_volatility = hrv_series.rolling(7).std().iloc[-1]  # HRV variability

    # --- Acute risk factors ---

    # Fatigue-to-Performance ratio
    fatigue_performance_ratio = fatigue / max(performance, 1)
    fatigue_risk = max(0, (fatigue_performance_ratio - 1.3) * 0.1)

    # HRV risk - Only significant when HRV is substantially depressed
    hrv_baseline = athlete['hrv_baseline']
    hrv_ratio = hrv_ma7 / max(hrv_baseline, 1)
    hrv_risk = max(0, (0.7 - hrv_ratio) * 0.2) if hrv_ratio < 0.7 else 0

    # Resting HR risk
    rhr_baseline = athlete['resting_hr']
    rhr_ratio = resting_hr / max(rhr_baseline, 40)
    rhr_risk = max(0, (rhr_ratio - 1.2) * 0.15) if rhr_ratio > 1.2 else 0

    # Sleep debt risk
    sleep_norm = athlete['sleep_time_norm']
    sleep_debt = max(0, sleep_norm - sleep_hours)
    sleep_hours_risk = max(0, (sleep_debt - 2) * 0.02) if sleep_debt > 2 else 0

    # Sleep quality risk
    sleep_quality_risk = max(0, (0.5 - sleep_quality) * 0.08) if sleep_quality < 0.5 else 0

    # Nutrition risk
    nutrition_risk = max(0, (0.4 - athlete['nutrition_factor']) * 0.05) if athlete['nutrition_factor'] < 0.4 else 0

    # Stress risk
    stress_risk = max(0, (athlete['stress_factor'] - 0.7) * 0.05) if athlete['stress_factor'] > 0.7 else 0

    # Lifestyle risk
    lifestyle_risk = (
        athlete['smoking_factor'] * 0.1 + 
        athlete['drinking_factor'] * 0.05
    )

    # --- Training load risks ---

    # TSS risk (high workload)
    tss_threshold = 200 + (athlete['training_experience'] * 15)
    tss_risk = max(0, (tss_ratio - 1.5) * 0.2) if tss_ratio > 1.5 else 0

    # ACWR risk - considers trends and volatility
    if acwr_last < 0.6:
        acwr_risk = (0.6 - acwr_last) * 0.05
    elif acwr_last > 1.8:
        acwr_risk = (acwr_last - 1.8) * 0.1
    else:
        acwr_risk = 0

    acwr_volatility_risk = min(0.1, acwr_volatility * 0.2)  # More variability increases risk

    # HRV volatility risk (unstable HRV patterns suggest poor recovery)
    hrv_volatility_risk = min(0.1, hrv_volatility * 0.15)

    # --- Risk modifiers ---

    # Recovery rate modifier
    recovery_modifier = 1.0 - (athlete['recovery_rate'] * 0.3)

    # Experience modifier
    experience_modifier = 1.0 - (min(athlete['training_experience'], 10) * 0.03)

    # Combined modifier (caps risk reduction at 50%)
    risk_modifier = max(0.5, recovery_modifier * experience_modifier)

    # --- Combine all risk factors ---

    # Training load composite risk
    training_load_risk = (
        tss_risk * 0.1 +
        acwr_risk * 0.15 +
        acwr_volatility_risk * 0.05 +
        hrv_volatility_risk * 0.05
    )

    # Acute risks composite
    acute_risk_composite = (
        fatigue_risk * 0.15 +
        hrv_risk * 0.1 +
        rhr_risk * 0.05 +
        sleep_hours_risk * 0.05 +
        sleep_quality_risk * 0.05 +
        nutrition_risk * 0.03 +
        stress_risk * 0.03 +
        lifestyle_risk * 0.04 +
        training_load_risk * 0.2
    )

    # High risk multiplier (non-linearity when many factors align)
    high_risk_threshold = 0.3
    high_risk_multiplier = 1.0 + max(0, (acute_risk_composite - high_risk_threshold) * 2.0)

    # Final probability calculation
    raw_injury_probability = (base_daily_risk + (acute_risk_composite * 0.01)) * high_risk_multiplier * risk_modifier
    noise_factor = np.random.normal(1.0, 0.1)  # Small noise factor

    # Cap injury probability at 5%
    injury_probability = min(0.05, raw_injury_probability * noise_factor)

    # Determine if injury occurs
    injury_occurs = random.random() < injury_probability

    return injury_occurs

def check_injury_patterns(athlete_data, recent_days=7):
    """
    Calculate the probability of injury based on patterns in recent data.
    This provides a more deterministic approach to injury prediction.
    
    Parameters:
    -----------
    athlete_data : dict
        Dictionary containing athlete information and daily data
    recent_days : int
        Number of recent days to analyze for patterns
    
    Returns:
    --------
    float
        Probability of injury (0-1)
    """
    athlete = athlete_data['athlete']
    daily_data = athlete_data['daily_data']
    
    # If we don't have enough data yet, return low probability
    if len(daily_data) < recent_days:
        return 0.01
    
    # Get the most recent days' data
    recent_data = daily_data[-recent_days:]
    
    # Initialize risk factors
    risk_factors = {
        'hrv_decline': 0,
        'rhr_increase': 0,
        'sleep_quality_decline': 0,
        'body_battery_decline': 0,
        'high_acwr': 0,
        'consecutive_high_load': 0,
        'stress_increase': 0
    }
    
    # 1. Check for HRV decline trend
    hrv_values = [day['hrv'] for day in recent_data]
    hrv_baseline = athlete['hrv_baseline']
    hrv_trend = np.polyfit(range(len(hrv_values)), hrv_values, 1)[0]  # Slope of linear fit
    hrv_latest_ratio = hrv_values[-1] / hrv_baseline
    
    if hrv_trend < -0.5:  # Significant negative trend
        risk_factors['hrv_decline'] = min(1.0, abs(hrv_trend) * 0.3)
    if hrv_latest_ratio < 0.8:  # Latest HRV below 80% of baseline
        risk_factors['hrv_decline'] += min(1.0, (1 - hrv_latest_ratio) * 2)
    
    # 2. Check for RHR increase trend
    rhr_values = [day['resting_hr'] for day in recent_data]
    rhr_baseline = athlete['resting_hr']
    rhr_trend = np.polyfit(range(len(rhr_values)), rhr_values, 1)[0]
    rhr_latest_ratio = rhr_values[-1] / rhr_baseline
    
    if rhr_trend > 0.3:  # Significant positive trend
        risk_factors['rhr_increase'] = min(1.0, rhr_trend * 0.5)
    if rhr_latest_ratio > 1.08:  # Latest RHR more than 8% above baseline
        risk_factors['rhr_increase'] += min(1.0, (rhr_latest_ratio - 1) * 5)
    
    # 3. Check for sleep quality decline
    sleep_quality_values = [day['sleep_quality'] for day in recent_data]
    sleep_quality_trend = np.polyfit(range(len(sleep_quality_values)), sleep_quality_values, 1)[0]
    
    if sleep_quality_trend < -0.03:  # Negative trend in sleep quality
        risk_factors['sleep_quality_decline'] = min(1.0, abs(sleep_quality_trend) * 10)
    
    # 4. Check body battery trend (morning)
    if 'body_battery_morning' in recent_data[0]:
        bb_values = [day.get('body_battery_morning', 50) for day in recent_data]
        bb_trend = np.polyfit(range(len(bb_values)), bb_values, 1)[0]
        
        if bb_trend < -1.5:  # Significant negative trend
            risk_factors['body_battery_decline'] = min(1.0, abs(bb_trend) * 0.2)
    
    # 5. Check ACWR (if available)
    if len(daily_data) > 28:
        # Calculate ACWR
        recent_tss = sum([day.get('actual_tss', 0) for day in daily_data[-7:]])
        chronic_tss = sum([day.get('actual_tss', 0) for day in daily_data[-28:]]) / 4
        acwr = recent_tss / chronic_tss if chronic_tss > 0 else 1.0
        
        if acwr > 1.3:
            risk_factors['high_acwr'] = min(1.0, (acwr - 1.3) * 2)
    
    # 6. Check for consecutive high load days
    max_daily_tss = calculate_max_daily_tss(athlete['weekly_training_hours'], athlete['training_experience'])
    high_load_count = sum(1 for day in recent_data if day.get('actual_tss', 0) > max_daily_tss * 0.9)
    
    if high_load_count >= 3:
        risk_factors['consecutive_high_load'] = min(1.0, high_load_count * 0.2)
    
    # 7. Check stress increase
    stress_values = [day.get('stress', 50) for day in recent_data]
    stress_trend = np.polyfit(range(len(stress_values)), stress_values, 1)[0]
    
    if stress_trend > 2:  # Positive trend in stress
        risk_factors['stress_increase'] = min(1.0, stress_trend * 0.1)
    
    # Calculate overall risk score (weighted sum of risk factors)
    weights = {
        'hrv_decline': 0.25,
        'rhr_increase': 0.20,
        'sleep_quality_decline': 0.15,
        'body_battery_decline': 0.10,
        'high_acwr': 0.15,
        'consecutive_high_load': 0.10,
        'stress_increase': 0.05
    }
    
    risk_score = sum(risk_factors[k] * weights[k] for k in risk_factors)
    
    # Apply non-linear transformation to make injury more likely when multiple factors align
    if risk_score > 0.4:
        risk_score = min(0.95, risk_score * 1.5)
    
    # Add some randomness for variable onset
    risk_score = min(0.99, risk_score * (0.9 + np.random.random() * 0.2))
    
    return risk_score

def calculate_max_daily_tss(weekly_hours, training_experience):
    """Calculate maximum sustainable daily TSS based on athlete factors."""
    # Base value scaled by training hours and experience
    base_tss = 75 + (weekly_hours * 4)
    experience_factor = 1 + (min(training_experience, 15) / 30)
    
    return base_tss * experience_factor