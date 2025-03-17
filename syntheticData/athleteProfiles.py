import random
import numpy as np
import pandas as pd
import uuid

# Random seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_athlete_profile(athlete_id = None):
    """Generate a single athlete's physiological and performance profile."""

    # Generate unique ID if not provided
    if athlete_id is None:
        athlete_id = str(uuid.uuid4())
    
    gender = random.choice(["male", "female"])
    age = int(np.random.normal(35, 7))  # Endurance athletes tend to be ~30-40 -> Mean 35, std 7, realistic range ~20-50

    # Height and weight with gender-based differences
    height = int(np.random.normal(178, 7) if gender == "male" else np.random.normal(165, 6))

    genetic_factor = np.clip(np.random.normal(1, 0.1))  # Genetic predisposition for fitness (0.8-1.2)

    # Generate lifestyle factors
    lifestyle_factors = generate_lifestyle_factors(age)

    athlete_type = assign_specialization()
    
    # Weight correlated with height
    base_weight = 72 if gender == "male" else 58
    weight = np.random.normal(base_weight + (height - 165) * 0.4, 6) if gender == "male" else np.random.normal(base_weight + (height - 165) * 0.3, 5)

    # Training experience (1-20 years), with more experienced athletes being rarer
    experience_distribution = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    experience_weights = [0.2, 0.18, 0.16, 0.14, 0.12, 0.1, 0.08, 0.06, 0.04, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01]
    training_experience = random.choices(experience_distribution, weights=experience_weights, k=1)[0]

    # Adjust experience based on age (older athletes are more likely to have more experience)
    max_experience = min(age - 15, 20)  # Assuming athletes start training around age 15
    training_experience = min(training_experience, max_experience)

    vo2max = generate_vo2max(age, training_experience, gender, lifestyle_factors, athlete_type, genetic_factor)

    # Weekly training volume (hours)
    weekly_training_hours = np.random.normal(10, 3) * (1 + training_experience * 0.03) * lifestyle_factors['exercise']
    weekly_training_hours = np.clip(weekly_training_hours, 5, 25)  
    

    # FTP scales with training experience & weight
    power_to_weight = np.random.normal(3.8, 0.8) if gender == "male" else np.random.normal(3.4, 0.8)
    power_to_weight *= (1 + (training_experience * 0.01))  # Experience increases power
    power_to_weight *= genetic_factor  
    if athlete_type == "bike_strong":
        power_to_weight *= 1.1
    
    if lifestyle_factors['smoking'] > 0.2 or lifestyle_factors['drinking'] > 0.2:
        power_to_weight *= 0.9
    power_to_weight = np.clip(power_to_weight, 2.5, 5.5)  # Reasonable range for power-to-weight ratio
    ftp = power_to_weight * weight
    power_zones = calculate_power_zones(ftp)
    # critical swim speed (CSS) scales with VO2max and experience
    # Base CSS for an untrained swimmer (~1.0 m/s)
    base_css = 1.0  
    # Adjust CSS based on VO2max and swim training volume
    vo2_factor = (vo2max - 50) * 0.01  # Each +10 in VO2max adds ~0.1 m/s
    training_factor = weekly_training_hours * 0.2 * 0.02  # 20% of the total volume done swimming, each extra swimming hour adds ~0.02 m/s
    experience_factor = min(training_experience, 15) * 0.02  # Each year adds ~0.02 m/s (capped at 15 years)

    estimated_css = base_css + vo2_factor + training_factor + experience_factor
    estimated_css = max(0.9, min(estimated_css, 1.7))  # Keep within a reasonable range
    css_s_per_100m = 60 * 100 / estimated_css  # Convert to seconds per 100m
    css_s_per_100m = round(css_s_per_100m, 1)

    # Resting HR decreases with VO2max (more fit → lower HR)
    resting_hr = int(np.random.normal(60, 7) - (vo2max * 0.15))

    # Maximum heart rate (208 - 0.7 * age) + random individual variation
    max_hr = 208 - (0.7 * age) + np.random.normal(0, 5)

    # lactate threshold as % of max HR (typically 85-90%)
    lactate_threshold_hr = max_hr * np.random.uniform(0.82, 0.92)
    threshold_pace = estimate_threshold_pace(training_experience, vo2max, lifestyle_factors, genetic_factor, weekly_training_hours)
    heart_rate_zones = calculate_hr_zones_lthr(lactate_threshold_hr, resting_hr, max_hr)

    # Adjust weight, recovery rate, and resting HR based on lifestyle factors
    weight += lifestyle_factors['nutrition'] * (-2) + lifestyle_factors["drinking"] * 1.5 - lifestyle_factors['exercise'] * 1.5
    recovery_rate = np.clip(np.random.normal(1.0, 0.2) + (vo2max / 100) + lifestyle_factors['sleep'] * 0.1 + lifestyle_factors['nutrition'] * 0.1 - (age * 0.001) - lifestyle_factors['drinking'] * 0.1 - lifestyle_factors['smoking'] * 0.1 - lifestyle_factors['stress'], 0.6, 1.4)
    if lifestyle_factors['sleep'] > 6:
        resting_hr += lifestyle_factors['stress'] * 2 + lifestyle_factors['smoking'] * 3 - lifestyle_factors['sleep'] * 0.2 - lifestyle_factors['exercise'] * 2 
    else:
        resting_hr += lifestyle_factors['stress'] * 2 + lifestyle_factors['smoking'] * 3 + lifestyle_factors['sleep'] * 0.5 - lifestyle_factors['exercise'] * 2
    resting_hr = np.clip(resting_hr, 35, 90)

    hrv = estimate_hrv(age, vo2max, resting_hr, lifestyle_factors['sleep'], lifestyle_factors['stress'], lifestyle_factors['smoking'], lifestyle_factors['drinking'], training_experience)

    return {
        'id': athlete_id,
        'gender': gender,
        'age': age,
        'height': height,
        'weight': round(weight, 1),
        'genetic_factor': round(genetic_factor, 2),
        'hrv_baseline': hrv['HRV_baseline'],
        'hrv_range': hrv['HRV_range'],
        'max_hr': round(max_hr, 1),
        'resting_hr': round(resting_hr, 1),
        'hr_zones': heart_rate_zones,
        'run_threshold_pace': threshold_pace,
        'vo2max': round(vo2max, 1),
        'ftp': round(ftp, 1),
        'power_zones': power_zones,
        'css': css_s_per_100m,
        'training_experience': training_experience,
        'weekly_training_hours': round(weekly_training_hours, 1),
        'recovery_rate': round(recovery_rate, 2),
        'lifestyle': lifestyle_factors['name'],
        'sleep_time_norm': lifestyle_factors['sleep'],
        'sleep_quality': lifestyle_factors['sleep_quality'],
        'nutrition_factor': lifestyle_factors['nutrition'],
        'stress_factor': lifestyle_factors['stress'],
        'smoking_factor': lifestyle_factors['smoking'],
        'drinking_factor': lifestyle_factors['drinking']
    }

def generate_vo2max(age, training_experience, gender, lifestyle, athlete_type, genetic_factor):
    """Generates VO2max based on age, training experience, genetic factors, gender, and lifestyle factors."""
    
    # Baseline VO2max (Untrained individuals)
    base_vo2max = np.random.normal(38, 4) if gender == "female" else np.random.normal(42, 4)
    if lifestyle['smoking'] == 0 and random.random() < 0.02:  # 2% chance of an elite genetic outlier
        base_vo2max = random.uniform(85, 95)
    elif lifestyle['smoking'] == 0 and random.random() < 0.1:  # 10% chance of high-end athlete
        base_vo2max = random.uniform(70, 85)

    # Genetic predisposition (±5 ml/kg/min variation)
    if genetic_factor < 1:
        genetic_boost = np.random.uniform(-2, 0)
    elif genetic_factor > 1:
        genetic_boost = np.random.uniform(0, 5)

    # Training experience effect (1-20 years → +1.5 to +40 ml/kg/min)
    training_boost = training_experience * np.random.uniform(1.5, 2.0)  

    # Age decline (Starting ~30, ~0.5 per year)
    age_decline = max(0, (age - 30) * 0.5)  

    # Lifestyle factor adjustments
    sleep_effect = lifestyle["sleep"] * np.random.uniform(0.5, 2)
    nutrition_effect = lifestyle["nutrition"] * np.random.uniform(1, 3)
    exercise_effect = lifestyle["exercise"] * np.random.uniform(2, 5)
    stress_effect = -lifestyle["stress"] * np.random.uniform(2, 5)
    smoking_effect = -lifestyle["smoking"] * np.random.uniform(5, 15)
    drinking_effect = -lifestyle["drinking"] * np.random.uniform(2, 7)

    # Final VO2max calculation
    vo2max = (base_vo2max + training_boost - age_decline + genetic_boost +
              sleep_effect + nutrition_effect + exercise_effect +
              stress_effect + smoking_effect + drinking_effect)
    
    if athlete_type == "swim_strong":
        vo2max *= 1.05
    elif athlete_type == "bike_strong":
        vo2max *= 1.05
    elif athlete_type == "run_strong":
        vo2max *= 1.1

    # Clip to realistic athlete ranges (35-85 ml/kg/min)
    vo2max = np.clip(vo2max, 35, 95)

    return round(vo2max, 1)

def estimate_threshold_pace(training_experience, VO2max, lifestyle_factors, genetic_factor, weekly_training_hours):
    # Base calculation from VO2max (higher VO2max = faster pace)
    # Using a simplified variation of Daniels' formula
    base_pace = 29.0 - 0.25 * VO2max
    
    # Training experience modifier (diminishing returns after ~10 years)
    experience_modifier = min(0.9, 0.05 * training_experience)
    
    # Training volume modifier (diminishing returns after ~10 hours)
    volume_modifier = min(0.85, 0.05 * weekly_training_hours)
    
    # Apply modifiers
    adjusted_pace = base_pace * (1 - experience_modifier) * (1 - volume_modifier)

    lifestyle_factor = calculate_lifestyle_factor(lifestyle_factors)
    
    # Apply lifestyle and genetic factors
    final_pace = adjusted_pace * (2 - lifestyle_factor) / genetic_factor
    
    # Ensure reasonable output range (2:30-6:00 min/km)
    final_pace = max(2.5, min(6.0, final_pace))
    
    return round(final_pace, 2)

def estimate_hrv(age, vo2max, resting_hr, sleep, stress, smoking, drinking, training_experience):
    """Estimate an athlete's HRV baseline (RMSSD in ms) with a realistic age-adjusted range."""
    
    # Base HRV calculation considering fitness, lifestyle, and experience
    hrv = (100 + (vo2max * 1.2) - (resting_hr * 0.5) + 
           (sleep * 2) - (stress * 5) - (smoking * 10) - 
           (drinking * 7) + (training_experience * 0.8))
    
    # Apply age-based decline (approx. -0.8 ms per year after 20)
    age_factor = 100 - (age * 0.8)
    hrv *= (age_factor / 100)  # Scaling HRV down with age
    
    # Clip to realistic age-based range (from observed HRV chart)
    hrv_min = max(30, 110 - (age * 1.2))  # Upper limit declines with age
    hrv_max = max(40, 150 - (age * 1.5))  # Lower limit declines faster
    hrv = np.clip(hrv, hrv_min, hrv_max)
    
    # Calculate HRV range (±15%)
    hrv_low = round(hrv * 0.85, 1)
    hrv_high = round(hrv * 1.15, 1)
    
    return {
        "HRV_baseline": round(hrv, 1),
        "HRV_range": (hrv_low, hrv_high)
    }

def generate_lifestyle_factors(age):
    """Generate lifestyle factors that affect performance, weight, recovery, and heart rate."""
    
    lifestyle_profiles = [
        {
            'name': 'Perfect',
            'sleep': 8,
            'sleep_quality': 1,
            'nutrition': 1,
            'drinking': 0,
            'smoking': 0,
            'stress': 0,
            'exercise': 1
        },
        {
            'name': 'Weekend Drinker',
            'sleep': np.random.uniform(5, 7),
            'sleep_quality': np.random.uniform(0.5, 0.8),
            'nutrition': np.random.uniform(0.5, 0.8),
            'drinking': 0.8,
            'smoking': 0,
            'stress': np.random.uniform(0.3, 0.6),
            'exercise': np.random.uniform(0.5, 0.7)
        },
        {
            'name': 'Irregular Sleeper',
            'sleep': np.random.uniform(4, 6),
            'sleep_quality': np.random.uniform(0.3, 0.6),
            'nutrition': np.random.uniform(0.3, 0.6),
            'drinking': 0.5,
            'smoking': 0,
            'stress': np.random.uniform(0.5, 0.8),
            'exercise': np.random.uniform(0.3, 0.5)
        },
        {
            'name': 'Moderate Drinker',
            'sleep': np.random.uniform(6, 8),
            'sleep_quality': np.random.uniform(0.6, 0.9),
            'nutrition': np.random.uniform(0.6, 0.9),
            'drinking': 0.3,
            'smoking': 0,
            'stress': np.random.uniform(0.2, 0.5),
            'exercise': np.random.uniform(0.6, 0.8)
        },
        {
            'name': 'Balanced',
            'sleep': 7,
            'sleep_quality': 0.9,
            'nutrition': 0.8,
            'drinking': 0.1,
            'smoking': 0,
            'stress': 0.2,
            'exercise': 0.9
        },
        {
            'name': 'Heavy Smoker',
            'sleep': np.random.uniform(4, 6),
            'sleep_quality': np.random.uniform(0.3, 0.6),
            'nutrition': np.random.uniform(0.4, 0.7),
            'drinking': np.random.uniform(0.3, 0.6),
            'smoking': 1,  # Heavy smoker
            'stress': np.random.uniform(0.5, 0.8),
            'exercise': np.random.uniform(0.2, 0.5)
        },
        {
            'name': 'Casual Smoker',
            'sleep': np.random.uniform(5, 7),
            'sleep_quality': np.random.uniform(0.6, 0.9),
            'nutrition': np.random.uniform(0.5, 0.8),
            'drinking': np.random.uniform(0.3, 0.6),
            'smoking': 0.5,  # Occasional smoking
            'stress': np.random.uniform(0.3, 0.6),
            'exercise': np.random.uniform(0.5, 0.7)
        },
        {
            'name': 'Workaholic',
            'sleep': np.random.uniform(4, 6),
            'sleep_quality': np.random.uniform(0.3, 0.6),
            'nutrition': np.random.uniform(0.5, 0.9),
            'drinking': np.random.uniform(0.2, 0.4),
            'smoking': np.random.uniform(0, 0.3),
            'stress': np.random.uniform(0.6, 0.9),  # Very high stress
            'exercise': np.random.uniform(0.5, 0.7)
        },
        {
            'name': 'Party Enthusiast',
            'sleep': np.random.uniform(3, 6),
            'sleep_quality': np.random.uniform(0.2, 0.5),
            'nutrition': np.random.uniform(0.3, 0.7),
            'drinking': 1,  # Heavy drinker
            'smoking': np.random.uniform(0.5, 1),  # Likely a heavy smoker
            'stress': np.random.uniform(0.3, 0.7),
            'exercise': np.random.uniform(0.2, 0.5)
        },
        {
            'name': 'Health-Conscious Athlete',
            'sleep': np.random.uniform(7, 8),
            'sleep_quality': np.random.uniform(0.8, 1),
            'nutrition': np.random.uniform(0.8, 1),
            'drinking': 0.1,
            'smoking': 0,
            'stress': np.random.uniform(0.1, 0.3),
            'exercise': np.random.uniform(0.8, 1)
        }
    ]

    # More realistic probability weights based on age groups
    if age < 16:
        lifestyle_weights = [0.3, 0, 0, 0, 0.4, 0, 0, 0, 0, 0.3]  # Mostly Perfect, Balanced, and Health-Conscious
    elif 16 <= age < 20:
        lifestyle_weights = [0.2, 0.05, 0.1, 0.05, 0.3, 0, 0, 0.05, 0.1, 0.15]  # Few drinkers, still mostly healthy
    elif 20 <= age < 35:
        lifestyle_weights = [0.15, 0.2, 0.1, 0.1, 0.2, 0.05, 0.05, 0.1, 0.05, 0.1]  # More weekend drinkers, some irregular sleepers
    elif 35 <= age < 50:
        lifestyle_weights = [0.15, 0.1, 0.1, 0.15, 0.2, 0.05, 0.05, 0.15, 0.05, 0.1]  # More workaholics & moderate drinkers
    elif 50 <= age < 65:
        lifestyle_weights = [0.2, 0.05, 0.1, 0.15, 0.2, 0.1, 0.05, 0.1, 0.05, 0.1]  # Some smokers, still many balanced
    else:
        lifestyle_weights = [0.25, 0.05, 0.1, 0.15, 0.2, 0.1, 0.05, 0.05, 0, 0.05]  # Very few smokers & partygoers
    
    lifestyle = random.choices(lifestyle_profiles, weights=lifestyle_weights, k=1)[0]

    # Ensure no smoking or drinking if age < 16
    if age < 16:
        lifestyle["smoking"] = 0
        lifestyle["drinking"] = 0
    return lifestyle

def calculate_lifestyle_factor(lifestyle_dict):
    """
    Calculate an overall lifestyle factor from detailed lifestyle components.
    
    Parameters:
    - lifestyle_dict (dict): Dictionary containing lifestyle components with following keys:
        - sleep: Hours of sleep per night (typically 5-9)
        - sleep_quality: Quality of sleep (0-1)
        - nutrition: Quality of nutrition (0-1)
        - drinking: Alcohol consumption (0-1, where 0 = no drinking, 1 = heavy drinking)
        - smoking: Tobacco use (0-1, where 0 = no smoking, 1 = heavy smoking)
        - stress: Stress levels (0-1, where 0 = low stress, 1 = high stress)
        - exercise: Quality of exercise routine (0-1)
    
    Returns:
    - lifestyle_factor (float): Combined lifestyle factor (0-1)
    """
    # Define weights for each component based on their impact on performance
    weights = {
        'sleep': 0.20,
        'sleep_quality': 0.15,
        'nutrition': 0.20,
        'drinking': 0.10,
        'smoking': 0.15,
        'stress': 0.10,
        'exercise': 0.10
    }
    
    # Normalize sleep hours to 0-1 scale (considering 8-9 hours as optimal)
    sleep_normalized = min(1.0, max(0.0, lifestyle_dict.get('sleep', 7) / 9))
    
    # For negative factors (drinking, smoking, stress), we invert the scale (1 - value)
    # so that 0 = bad effect and 1 = good effect for consistent calculation
    drinking_inverted = 1 - lifestyle_dict.get('drinking', 0.3)
    smoking_inverted = 1 - lifestyle_dict.get('smoking', 0.3)
    stress_inverted = 1 - lifestyle_dict.get('stress', 0.3)
    
    # Combine all factors with their weights
    lifestyle_factor = (
        weights['sleep'] * sleep_normalized +
        weights['sleep_quality'] * lifestyle_dict.get('sleep_quality', 0.7) +
        weights['nutrition'] * lifestyle_dict.get('nutrition', 0.7) +
        weights['drinking'] * drinking_inverted +
        weights['smoking'] * smoking_inverted +
        weights['stress'] * stress_inverted +
        weights['exercise'] * lifestyle_dict.get('exercise', 0.7)
    )
    
    return lifestyle_factor

def assign_specialization():
    """Assigns a specialization to an athlete (swim, bike, run, or balanced)."""
    
    athlete_type = random.choices(
        ["swim_strong", "bike_strong", "run_strong", "balanced"],
        weights=[0.25, 0.25, 0.25, 0.25]
    )[0]

    return athlete_type

def generate_athlete_cohort(n):
    """Generate a cohort of athletes with specializations."""
    cohort = [generate_athlete_profile() for _ in range(n)]
    return cohort

def calculate_hr_zones_lthr(lthr, rest_hr, max_hr):
    """Calculate HR zones based on lactate threshold heart rate"""
    return {
        "Z1": (rest_hr * 1.5, 0.80 * lthr),            # Recovery
        "Z2": (0.80 * lthr, 0.9 * lthr),         # Endurance
        "Z3": (0.9 * lthr, 0.95 * lthr),         # Tempo
        "Z4": (0.95 * lthr, 1.02 * lthr),        # Threshold
        "Z5": (1.02 * lthr, 1.06 * lthr),        # VO2 Max
        "Z6": (1.06 * lthr, max_hr)              # Anaerobic
    }

def calculate_power_zones(ftp):
    """Calculate power zones based on functional threshold power (FTP)"""
    return {
        "Z1": (0, 0.55 * ftp),                  # Active Recovery
        "Z2": (0.56 * ftp, 0.75 * ftp),         # Endurance
        "Z3": (0.76 * ftp, 0.90 * ftp),         # Tempo
        "Z4": (0.91 * ftp, 1.05 * ftp),         # Threshold
        "Z5": (1.06 * ftp, 1.20 * ftp),         # VO2 Max
        "Z6": (1.21 * ftp, float("inf"))        # Aneaerobic Capacity
    }