import numpy as np
import pandas as pd
import random
from datetime import timedelta

def calculate_training_metrics(tss_history, hrv_history, baseline_hrv):
    """
    Calculates fitness, fatigue, form, and ACWR using an HRV-adjusted TSS model.
    
    Parameters:
    - tss_history (list): Last 28 days of TSS values (list of 28 elements).
    - hrv_history (list): Last 28 days of HRV values (list of 28 elements).
    - baseline_hrv (float): Baseline HRV value for scaling.
    
    Returns:
    - fitness (float): Chronic training load (28-day EWMA).
    - fatigue (float): Acute training load (7-day EWMA).
    - form (float): Readiness indicator (fitness - fatigue).
    - acwr (float): Acute:Chronic Workload Ratio.
    """
    
    if len(tss_history) < 28 or len(hrv_history) < 28:
        raise ValueError("TSS and HRV history must be at least 28 days long.")

    # Calculate HRV scaling factor for each day
    hrv_scaling = np.array(hrv_history) / baseline_hrv
    adjusted_tss = np.array(tss_history) * hrv_scaling  # Adjust TSS by HRV

    # Exponentially Weighted Moving Averages (EWMA)
    lambda_chronic = 2 / (28 + 1)  # 28-day decay rate
    lambda_acute = 2 / (7 + 1)  # 7-day decay rate
    
    fitness = pd.Series(adjusted_tss).ewm(alpha=lambda_chronic, adjust=False).mean().iloc[-1]
    fatigue = pd.Series(adjusted_tss[-7:]).ewm(alpha=lambda_acute, adjust=False).mean().iloc[-1]

    # Training Form = Fitness - Fatigue
    form = fitness - fatigue

    # ACWR (Acute:Chronic Workload Ratio)
    acwr = fatigue / fitness if fitness > 0 else 0

    return round(fitness, 2), round(fatigue, 2), round(form, 2), round(acwr, 2)

def initialize_tss_history(athlete, end_date, days_of_history=28):
    """
    Initialize a realistic TSS history for an athlete based on their profile.
    
    Parameters:
    -----------
    athlete_data : dict
        Dictionary containing athlete metrics and characteristics
    days_of_history : int, optional
        Number of days of historical data to generate (default 42, 6 weeks)
    
    Returns:
    --------
    list
        List of daily Training Stress Scores (TSS) over the past `days_of_history` days.
    
    """
    # Extract relevant athlete data
    weekly_training_hours = athlete.get('weekly_training_hours', 10)
    training_experience_years = athlete.get('training_experience', 3)
    recovery_rate = athlete.get('recovery_rate', 1.0)
    vo2max = athlete.get('vo2max', 45)
    ftp = athlete.get('ftp', 250)
    lifestyle_factors = {
        'sleep_time_norm': athlete.get('sleep_time_norm', 7),
        'sleep_quality': athlete.get('sleep_quality', 0.8),
        'nutrition_factor': athlete.get('nutrition_factor', 0.8),
        'stress_factor': athlete.get('stress_factor', 0.8),
        'smoking_factor': athlete.get('smoking_factor', 1.0),
        'drinking_factor': athlete.get('drinking_factor', 0.9)
    }
    
    # Convert years of experience to training parameters
    # Athletes with more experience typically handle higher TSS and show less variability
    if training_experience_years < 1:
        base_tss = 40
        variability = 0.35
    elif training_experience_years < 3:
        base_tss = 60
        variability = 0.30
    elif training_experience_years < 5:
        base_tss = 70
        variability = 0.25
    elif training_experience_years < 8:
        base_tss = 85
        variability = 0.20
    elif training_experience_years < 12:
        base_tss = 95
        variability = 0.15
    else:
        base_tss = 100
        variability = 0.12
    
    # Adjust base TSS based on fitness metrics
    fitness_factor = 1.0
    if 'vo2max' in athlete and 'ftp' in athlete:
        # Higher VO2max and FTP generally correlate with higher training loads
        fitness_factor = 1.0 + np.log1p(vo2max / 60) + np.log1p(ftp / 350)
    
    # Calculate baseline daily TSS based on weekly training hours and fitness
    daily_base_tss = base_tss * (weekly_training_hours / 10) * fitness_factor
    
    # Apply lifestyle factors to adjust recovery potential and consistency
    lifestyle_score = (
        lifestyle_factors['sleep_time_norm'] / 8 * 
        lifestyle_factors['sleep_quality'] * 
        lifestyle_factors['nutrition_factor'] * 
        lifestyle_factors['stress_factor'] * 
        lifestyle_factors['smoking_factor'] * 
        lifestyle_factors['drinking_factor']
    )
    
    # Adjust variability based on lifestyle factors
    # Poor lifestyle leads to more erratic training patterns
    adjusted_variability = variability * (1 + (1 - lifestyle_score))
    
    start_date = end_date - timedelta(days=days_of_history-1)
    
    # Initialize TSS values
    tss_values = []
    
    # Create weekly pattern - typically 2 harder days, 1-2 rest days, 3-4 moderate days
    for i in range(days_of_history):
        day_of_week = (start_date + timedelta(days=i)).weekday()
        
        # Create weekly pattern
        if day_of_week == 0:  # Monday - moderate
            day_factor = 1.0
        elif day_of_week == 1:  # Tuesday - harder
            day_factor = 1.5
        elif day_of_week == 2:  # Wednesday - moderate
            day_factor = 0.9
        elif day_of_week == 3:  # Thursday - harder
            day_factor = 1.4
        elif day_of_week == 4:  # Friday - easy
            day_factor = 0.6
        elif day_of_week == 5:  # Saturday - long/hard
            day_factor = 1.7
        else:  # Sunday - rest/very easy
            day_factor = 0.3
        
        # Add randomness to simulate real-world variations
        random_factor = np.random.normal(1.0, adjusted_variability)
        
        # Calculate daily TSS
        daily_tss = max(0, round(daily_base_tss * day_factor * random_factor))
        tss_values.append(daily_tss)
    
    # Create "build" and "recovery" weeks pattern (3:1 ratio typically used in training)
    for week in range(days_of_history // 7):
        week_start = week * 7
        week_end = min((week + 1) * 7, days_of_history)
        
        # Every 4th week is a recovery week
        if week % 4 == 3:
            recovery_factor = 0.7
            for i in range(week_start, week_end):
                tss_values[i] = round(tss_values[i] * recovery_factor)
    
    # Advanced athletes may exhibit more structured periodization
    if training_experience_years >= 5:
        # Simulate slight upward trend to indicate current training block
        trend_factor = np.linspace(0.9, 1.1, days_of_history)
        for i in range(days_of_history):
            tss_values[i] = round(tss_values[i] * trend_factor[i])
    
    # Return TSS history as a list (oldest to newest)
    return tss_values

def initialize_hrv_history(athlete, tss_history, end_date, days_of_history=28):
    """
    Initialize a realistic HRV history for an athlete based on training load and lifestyle.

    Parameters:
    -----------
    athlete : dict
        Dictionary containing athlete characteristics (age, VO2max, sleep, etc.)
    tss_history : list
        List of daily Training Stress Scores (TSS) over the past `days_of_history` days.
    end_date : datetime
        The last date in the HRV history.
    days_of_history : int, optional
        Number of historical days to generate (default 28 days).

    Returns:
    --------
    list
        List of daily HRV values over the past `days_of_history` days.
    """
    base_hrv = athlete.get('hrv_baseline', 60)  
    print(base_hrv)
    sleep_quality = athlete.get('sleep_quality', 0.8)

    # HRV fluctuations based on TSS history
    hrv_values = []
    start_date = end_date - timedelta(days=days_of_history - 1)

    for i in range(days_of_history):
        # Get today's TSS and previous day's HRV
        daily_tss = tss_history[i]
        prev_hrv = hrv_values[-1] if i > 0 else base_hrv

        # Training impact: High TSS → Lower HRV (fatigue effect)
        tss_impact = -0.03 * daily_tss  # Adjusted to make it more gradual

        # Recovery day (low TSS) boosts HRV slightly
        if daily_tss < 30:
            tss_impact += 2

        # Sleep effect: Poor sleep lowers HRV recovery
        sleep_effect = np.random.normal(sleep_quality * 2, 1)  # Better sleep = More HRV gain

        # Random physiological variation (limit to smaller range)
        random_variation = np.random.normal(0, 1)  # Reduced the randomness

        # Compute today's HRV with a cap to prevent values going too low
        daily_hrv = max(40, prev_hrv + tss_impact + sleep_effect + random_variation)  # HRV lower bound is 40

        hrv_values.append(round(daily_hrv))

    return hrv_values


def update_history(tss_history, hrv_history, new_tss_value, new_hrv_value, max_history_length=28):
    # Append new values to both TSS and HRV histories
    tss_history.append(new_tss_value)
    hrv_history.append(new_hrv_value)
    
    # Ensure the history length does not exceed the maximum size
    if len(tss_history) > max_history_length:
        tss_history.pop(0)  # Remove the oldest value
    if len(hrv_history) > max_history_length:
        hrv_history.pop(0)  # Remove the oldest value

    return tss_history, hrv_history

def calculate_max_daily_tss(weekly_hours, experience_years):
    """
    Calculate max daily TSS based on weekly training hours and experience in years.

    Parameters:
    - weekly_hours (float): Number of weekly training hours.
    - experience_years (int): Number of years of training experience.

    Returns:
    - max_daily_tss (float): Maximum TSS allowed for a single day.
    """
    
    # Determine base weekly TSS based on experience (scaling smoothly)
    if experience_years <= 1:  # Beginner
        base_weekly_tss = weekly_hours * random.uniform(40, 50)
        daily_tss_factor = 0.3
    elif experience_years <= 4:  # Intermediate
        base_weekly_tss = weekly_hours * random.uniform(50, 65)
        daily_tss_factor = 0.35
    elif experience_years <= 7:  # Advanced
        base_weekly_tss = weekly_hours * random.uniform(65, 80)
        daily_tss_factor = 0.4
    else:  # Elite (8+ years)
        base_weekly_tss = weekly_hours * random.uniform(80, 90)
        daily_tss_factor = 0.45

    # Calculate maximum daily TSS
    max_daily_tss = base_weekly_tss * daily_tss_factor
    return max_daily_tss