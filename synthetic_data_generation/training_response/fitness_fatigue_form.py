import numpy as np
import pandas as pd
import random
import sys
import os
from datetime import timedelta

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SimConfig as cfg

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

    # Load EWMA constants from config
    ewma_cfg = cfg.get('training_model.ewma', {})
    chronic_days = ewma_cfg.get('chronic_days', 28)
    acute_days = ewma_cfg.get('acute_days', 7)

    # Exponentially Weighted Moving Averages (EWMA)
    lambda_chronic = 2 / (chronic_days + 1)
    lambda_acute = 2 / (acute_days + 1)

    fitness = pd.Series(adjusted_tss).ewm(alpha=lambda_chronic, adjust=False).mean().iloc[-1]
    fatigue = pd.Series(adjusted_tss[-acute_days:]).ewm(alpha=lambda_acute, adjust=False).mean().iloc[-1]
    
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
    athlete : dict
        Dictionary containing athlete metrics and characteristics
    end_date : datetime
        The last date in the history
    days_of_history : int, optional
        Number of days of historical data to generate (default 28)
        
    Returns:
    --------
    list
        List of daily Training Stress Scores (TSS) over the past `days_of_history` days.
    """
    # Extract athlete data with defaults
    weekly_training_hours = athlete.get('weekly_training_hours', 10)
    training_experience_years = athlete.get('training_experience', 3)
    vo2max = athlete.get('vo2max', 45)
    ftp = athlete.get('ftp', 250)
    
    # Get lifestyle factors
    lifestyle_factors = _get_lifestyle_factors(athlete)
    
    # Calculate base TSS and variability based on experience
    base_tss, variability = _calculate_base_tss_and_variability(training_experience_years)
    
    # Calculate fitness factor
    fitness_factor = _calculate_fitness_factor(vo2max, ftp)
    
    # Calculate baseline daily TSS
    daily_base_tss = base_tss * (weekly_training_hours / 10) * fitness_factor
    
    # Calculate lifestyle score and adjust variability
    lifestyle_score = _calculate_lifestyle_score(lifestyle_factors)
    adjusted_variability = variability * (1 + (1 - lifestyle_score))
    
    # Generate TSS values
    tss_values = _generate_tss_values(daily_base_tss, adjusted_variability, end_date, days_of_history)
    
    # Apply training periodization
    tss_values = _apply_periodization(tss_values, training_experience_years, days_of_history)
    
    return tss_values


def _get_lifestyle_factors(athlete):
    """Extract lifestyle factors from athlete data with defaults."""
    return {
        'sleep_time_norm': athlete.get('sleep_time_norm', 7),
        'sleep_quality': athlete.get('sleep_quality', 0.8),
        'nutrition_factor': athlete.get('nutrition_factor', 0.8),
        'stress_factor': athlete.get('stress_factor', 0.8),
        'smoking_factor': athlete.get('smoking_factor', 1.0),
        'drinking_factor': athlete.get('drinking_factor', 0.9)
    }


def _calculate_base_tss_and_variability(experience_years):
    """Calculate base TSS and variability based on training experience."""
    if experience_years < 1:
        return 40, 0.35
    elif experience_years < 3:
        return 60, 0.30
    elif experience_years < 5:
        return 70, 0.25
    elif experience_years < 8:
        return 85, 0.20
    elif experience_years < 12:
        return 95, 0.15
    else:
        return 100, 0.12


def _calculate_fitness_factor(vo2max, ftp):
    """Calculate fitness factor based on VO2max and FTP."""
    return 1.0 + np.log1p(vo2max / 60) + np.log1p(ftp / 350)


def _calculate_lifestyle_score(lifestyle_factors):
    """Calculate overall lifestyle score."""
    return (
        lifestyle_factors['sleep_time_norm'] / 8 *
        lifestyle_factors['sleep_quality'] *
        lifestyle_factors['nutrition_factor'] *
        lifestyle_factors['stress_factor'] *
        lifestyle_factors['smoking_factor'] *
        lifestyle_factors['drinking_factor']
    )


def _generate_tss_values(daily_base_tss, variability, end_date, days_of_history):
    """Generate daily TSS values based on weekly patterns."""
    tss_values = []
    start_date = end_date - timedelta(days=days_of_history-1)
    
    # Day of week factors
    day_factors = {
        0: 1.0,  # Monday - moderate
        1: 1.5,  # Tuesday - harder
        2: 0.9,  # Wednesday - moderate
        3: 1.4,  # Thursday - harder
        4: 0.6,  # Friday - easy
        5: 1.7,  # Saturday - long/hard
        6: 0.3   # Sunday - rest/very easy
    }
    
    for i in range(days_of_history):
        current_date = start_date + timedelta(days=i)
        day_of_week = current_date.weekday()
        day_factor = day_factors[day_of_week]
        
        # Add randomness to simulate real-world variations
        random_factor = np.random.normal(1.0, variability)
        
        # Calculate daily TSS
        daily_tss = max(0, round(daily_base_tss * day_factor * random_factor))
        tss_values.append(daily_tss)
    
    return tss_values


def _apply_periodization(tss_values, experience_years, days_of_history):
    """Apply training periodization to TSS values."""
    # Create "build" and "recovery" weeks pattern (3:1 ratio)
    for week in range(days_of_history // 7):
        week_start = week * 7
        week_end = min((week + 1) * 7, days_of_history)
        
        # Every 4th week is a recovery week
        if week % 4 == 3:
            recovery_factor = 0.7
            for i in range(week_start, week_end):
                tss_values[i] = round(tss_values[i] * recovery_factor)
    
    # Advanced athletes may exhibit more structured periodization
    if experience_years >= 5:
        # Simulate slight upward trend to indicate current training block
        trend_factor = np.linspace(0.9, 1.1, days_of_history)
        for i in range(days_of_history):
            tss_values[i] = round(tss_values[i] * trend_factor[i])
    
    return tss_values


def initialize_hrv_history(athlete, tss_history, days_of_history=28):
    """
    Initialize a realistic HRV history for an athlete based on training load and lifestyle.
    
    Parameters:
    -----------
    athlete : dict
        Dictionary containing athlete characteristics (age, VO2max, sleep, etc.)
    tss_history : list
        List of daily Training Stress Scores (TSS) over the past `days_of_history` days.
    days_of_history : int, optional
        Number of historical days to generate (default 28 days).
        
    Returns:
    --------
    list
        List of daily HRV values over the past `days_of_history` days.
    """
    base_hrv = athlete.get('hrv_baseline', 60)
    sleep_quality = athlete.get('sleep_quality', 0.8)
    
    # HRV fluctuations based on TSS history
    hrv_values = []
    
    for i in range(days_of_history):
        # Get today's TSS and previous day's HRV
        daily_tss = tss_history[i]
        prev_hrv = hrv_values[-1] if i > 0 else base_hrv
        
        # Calculate daily HRV value
        daily_hrv = _calculate_daily_hrv(daily_tss, prev_hrv, sleep_quality)
        hrv_values.append(round(daily_hrv))
    
    return hrv_values


def _calculate_daily_hrv(daily_tss, prev_hrv, sleep_quality):
    """Calculate a single day's HRV based on TSS, previous HRV, and sleep quality."""
    # Training impact: High TSS → Lower HRV (fatigue effect)
    tss_impact = -0.03 * daily_tss
    
    # Recovery day (low TSS) boosts HRV slightly
    if daily_tss < 30:
        tss_impact += 2
    
    # Sleep effect: Poor sleep lowers HRV recovery
    sleep_effect = np.random.normal(sleep_quality * 2, 1)
    
    # Random physiological variation (limit to smaller range)
    random_variation = np.random.normal(0, 1)
    
    # Compute today's HRV with a cap to prevent values going too low
    return max(40, prev_hrv + tss_impact + sleep_effect + random_variation)


def update_history(tss_history, hrv_history, new_tss_value, new_hrv_value, max_history_length=28):
    """
    Update TSS and HRV histories with new values.
    
    Parameters:
    -----------
    tss_history : list
        Current TSS history
    hrv_history : list
        Current HRV history
    new_tss_value : float
        New TSS value to add
    new_hrv_value : float
        New HRV value to add
    max_history_length : int, optional
        Maximum length of history to maintain (default 28)
        
    Returns:
    --------
    tuple
        Updated (tss_history, hrv_history)
    """
    # Create new lists to avoid modifying the originals
    updated_tss = tss_history.copy()
    updated_hrv = hrv_history.copy()
    
    # Append new values
    updated_tss.append(new_tss_value)
    updated_hrv.append(new_hrv_value)
    
    # Maintain maximum history length
    if len(updated_tss) > max_history_length:
        updated_tss = updated_tss[-max_history_length:]
    if len(updated_hrv) > max_history_length:
        updated_hrv = updated_hrv[-max_history_length:]
    
    return updated_tss, updated_hrv


def calculate_max_daily_tss(weekly_hours, experience_years):
    """
    Calculate max daily TSS based on weekly training hours and experience in years.
    
    Parameters:
    - weekly_hours (float): Number of weekly training hours.
    - experience_years (int): Number of years of training experience.
    
    Returns:
    - max_daily_tss (float): Maximum TSS allowed for a single day.
    """
    # Determine base weekly TSS and daily TSS factor based on experience
    base_weekly_tss, daily_tss_factor = _get_tss_parameters(experience_years, weekly_hours)
    
    # Calculate maximum daily TSS
    max_daily_tss = base_weekly_tss * daily_tss_factor
    
    return max_daily_tss


def _get_tss_parameters(experience_years, weekly_hours):
    """Get TSS parameters based on experience level."""
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
    
    return base_weekly_tss, daily_tss_factor