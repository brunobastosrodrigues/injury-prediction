import numpy as np

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

def check_injury_occurence(athlete, baseline_risk, performance, fatigue, acwr, tss, hrv, sleep_hours, sleep_quality, resting_hr):
    """
    Calculate injury probability based on various athlete metrics and training load.
    
    Returns:
    --------
    bool
        True if an injury occurs, False otherwise
    """
    import random
    
    # Establish realistic injury rates
    # Elite triathletes might experience 1-3 significant injuries per year
    # This means a daily injury probability of approximately 0.005-0.008 (0.5-0.8%)
    # We'll use baseline_risk to establish the athlete's intrinsic injury risk
    
    # Normalize baseline_risk to a very low probability (max 0.2% daily injury chance)
    base_daily_risk = baseline_risk * 0.002
    
    # ----- Acute risk factors -----
    # Much more conservative risk factors
    
    # Fatigue-to-Performance ratio
    # Only significant when fatigue is much higher than performance
    fatigue_performance_ratio = fatigue / max(performance, 1)
    fatigue_risk = max(0, (fatigue_performance_ratio - 1.3) * 0.1)
    
    # HRV risk - only significant when HRV is substantially depressed
    hrv_baseline = athlete['hrv_baseline']
    hrv_ratio = hrv / max(hrv_baseline, 1)
    hrv_risk = max(0, (0.7 - hrv_ratio) * 0.2) if hrv_ratio < 0.7 else 0
    
    # Resting HR risk - only significant when RHR is substantially elevated
    rhr_baseline = athlete['resting_hr']
    rhr_ratio = resting_hr / max(rhr_baseline, 40)
    rhr_risk = max(0, (rhr_ratio - 1.2) * 0.15) if rhr_ratio > 1.2 else 0
    
    # Sleep debt risk - only significant with substantial sleep debt
    sleep_norm = athlete['sleep_time_norm']
    sleep_debt = max(0, sleep_norm - sleep_hours)
    sleep_hours_risk = max(0, (sleep_debt - 2) * 0.02) if sleep_debt > 2 else 0
    
    # Sleep quality risk - only significant with very poor sleep quality
    sleep_quality_risk = max(0, (0.5 - sleep_quality) * 0.08) if sleep_quality < 0.5 else 0
    
    # Nutrition risk - only significant with very poor nutrition
    nutrition_risk = max(0, (0.4 - athlete['nutrition_factor']) * 0.05) if athlete['nutrition_factor'] < 0.4 else 0
    
    # Stress risk - only significant with high stress
    stress_risk = max(0, (athlete['stress_factor'] - 0.7) * 0.05) if athlete['stress_factor'] > 0.7 else 0
    
    # Alcohol/smoking risk - still significant but reduced
    lifestyle_risk = (
        athlete['smoking_factor'] * 0.1 + 
        athlete['drinking_factor'] * 0.05
    )
    
    # ----- Training load risks -----
    
    # Acute high TSS risk - much more tolerant based on experience
    tss_threshold = 200 + (athlete['training_experience'] * 15)  # Experience increases threshold
    tss_risk = max(0, (tss - tss_threshold) / 400) * 0.2  # Dramatically reduced impact
    
    # ACWR risk - much wider optimal range (0.6-1.8)
    if acwr < 0.6:
        # Detraining risk
        acwr_risk = (0.6 - acwr) * 0.05
    elif acwr > 1.8:  # Much more tolerant upper bound
        # Overload risk (linear growth)
        acwr_risk = (acwr - 1.8) * 0.1
    else:
        acwr_risk = 0
    
    # ----- Risk modifiers -----
    
    # Recovery rate modifier (athletes with better recovery have lower risk)
    recovery_modifier = 1.0 - (athlete['recovery_rate'] * 0.3)
    
    # Experience modifier (more experienced athletes have lower risk)
    experience_modifier = 1.0 - (min(athlete['training_experience'], 10) * 0.03)
    
    # Combined modifier (can reduce risk by up to 50%)
    risk_modifier = max(0.5, recovery_modifier * experience_modifier)
    
    # ----- Combine all risk factors -----
    
    # Training load composite risk
    training_load_risk = (
        tss_risk * 0.1 +
        acwr_risk * 0.2 
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
        training_load_risk * 0.15
    )
    
    # High risk situations multiplier
    # This adds non-linearity - when multiple risk factors align, risk increases more than linearly
    high_risk_threshold = 0.3
    high_risk_multiplier = 1.0
    if acute_risk_composite > high_risk_threshold:
        high_risk_multiplier = 1.0 + ((acute_risk_composite - high_risk_threshold) * 2.0)
    
    # Final probability calculation
    raw_injury_probability = (base_daily_risk + (acute_risk_composite * 0.01)) * high_risk_multiplier * risk_modifier
    
    # Cap the probability at a reasonable level (max 5% chance per day even in worst conditions)
    injury_probability = min(0.05, raw_injury_probability)
    
    # With this model, even a high-risk day should have <5% chance of injury
    # This will yield approximately 1-3 injuries per year for most athletes
    
    # Determine if injury occurs
    injury_occurs = random.random() < injury_probability
    
    return injury_occurs