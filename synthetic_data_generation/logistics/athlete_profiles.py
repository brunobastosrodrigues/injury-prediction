import random
import numpy as np
import uuid
from scipy.stats import truncnorm

# Random seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_athlete_profile(athlete_id = None):
    """Generate a single athlete's physiological and performance profile."""

    # Generate unique ID if not provided
    if athlete_id is None:
        athlete_id = str(uuid.uuid4())
    
    gender = random.choices(["male", "female"], weights=[0.6, 0.4], k=1)[0] # USA Triathlon reported a 60/40 split in 2020 
    age = max(18, min(50, int(np.random.normal(33, 6))))  # Endurance athletes tend to be ~30-40 -> Mean 33, std 6, realistic range ~18-50

    # Height and weight with gender-based differences
    height = int(np.random.normal(178, 7) if gender == "male" else np.random.normal(165, 6))

    base_weight = 72 if gender == "male" else 58
    weight = np.random.normal(base_weight + (height - 165) * 0.4, 6) if gender == "male" else np.random.normal(base_weight + (height - 165) * 0.3, 5)

    genetic_factor = truncnorm.rvs((0.8 - 1) / 0.1, (1.2 - 1) / 0.1, loc=1, scale=0.1)  # Genetic predisposition for fitness (0.8-1.2)

    # Generate lifestyle factors
    lifestyle_factors = generate_lifestyle_factors()

    # adjust weight based on lifestyle 
    weight += lifestyle_factors['nutrition'] * (-2) + lifestyle_factors["drinking"] * 1.5 - lifestyle_factors['exercise'] * 1.5

    athlete_type = assign_specialization()

    training_experience = get_training_experience(age)

    vo2max = generate_vo2max(age, training_experience, gender, lifestyle_factors, athlete_type, genetic_factor)
    # Force VO2max into 50-75 range for this population
    vo2max = np.clip(vo2max, 50, 75)

    # Training volume for competitive age-groupers (8-16 h/week)
    weekly_training_hours = calculate_training_volume(lifestyle_factors['drinking'], training_experience, lifestyle_factors['exercise'])

    ftp = calculate_FTP(gender, weight, training_experience, genetic_factor, athlete_type, lifestyle_factors['smoking'], lifestyle_factors['drinking'])
    power_zones = calculate_power_zones(ftp)

    css_s_per_100m = calculate_CSS(vo2max, weekly_training_hours, training_experience, athlete_type)

    resting_hr = estimate_resting_hr(vo2max, lifestyle_factors)

    # Maximum heart rate (208 - 0.7 * age) + random individual variation (Tanaka Method)
    max_hr = 208 - (0.7 * age) + np.random.normal(0, 5)
    if gender == 'female':
        max_hr *= 1.03

    if athlete_type == "run_strong":
        running_specificity = 1.2
    else:
        running_specificity = 1.0

    lactate_threshold_hr = estimate_lactate_threshold_hr(age, gender, max_hr, resting_hr, training_experience, vo2max)
    threshold_pace = estimate_threshold_pace(gender, age, weight, vo2max, training_experience, weekly_training_hours, lifestyle_factors, genetic_factor, lactate_threshold_hr, max_hr, running_specificity) 
    heart_rate_zones = calculate_hr_zones_lthr(lactate_threshold_hr, resting_hr, max_hr)

    # Adjust recovery rate, and resting HR based on lifestyle factors
    recovery_rate = np.clip(
        0.8 * genetic_factor +
        ((vo2max-40) / 150) +
        max(0, (lifestyle_factors['sleep']-6)) * lifestyle_factors['sleep_quality'] * 0.12 +
        min(0, lifestyle_factors['sleep']-6) * 0.1 +
        lifestyle_factors['nutrition'] * 0.08 -
        (age * 0.002) -
        lifestyle_factors['drinking'] * 0.15 -
        lifestyle_factors['smoking'] * 0.15 -
        lifestyle_factors['stress'] * 0.12,
        0.5, 1.3
    )

    hrv = estimate_hrv(age, vo2max, resting_hr, lifestyle_factors['sleep'], lifestyle_factors['stress'], lifestyle_factors['smoking'], lifestyle_factors['drinking'], training_experience)

    recovery_profile, recovery_signature = add_recovery_characteristics()

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
        'lthr': round(lactate_threshold_hr, 1),
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
        'drinking_factor': lifestyle_factors['drinking'],
        'specialization': athlete_type,
        'recovery_profile': recovery_profile,
        'recovery_signature': recovery_signature
    }

def get_training_experience(age):
    """Generates training experience based on age."""
    # Training experience (2-20 years) - adjusted weights for competitive athletes
    # More experienced athletes are more common in this population
    experience_distribution = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    experience_weights = [0.1, 0.1, 0.1, 0.1, 0.1, 0.08, 0.08, 0.06, 0.06, 0.04, 0.04, 0.03, 0.03, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01]
    training_experience = random.choices(experience_distribution, weights=experience_weights, k=1)[0]

    # Adjust experience based on age (older athletes are more likely to have more experience)
    max_experience = min(age - 15, 20)  # Assuming athletes start training around age 15
    training_experience = min(training_experience, max_experience)
    training_experience = max(training_experience, 2)  # Ensure at least 2 years of experience

    return training_experience

def calculate_training_volume(drinking, training_experience, exercise):
    """calculates the weekly training hours based on training expereience and lifestyle."""
    # Training volume for competitive age-groupers (8-16 h/week)
    weekly_training_hours = np.random.normal(12, 2)  # Mean ~12h, std deviation 2h
    
    # Adjust for lifestyle impact (less drastic than before, but still relevant)
    weekly_training_hours *= (min(2.0 - 0.3 * drinking, 1))  # Drinking affects consistency slightly
    weekly_training_hours *= (1 + training_experience * 0.03)  # Experience boosts training slightly
    weekly_training_hours *= exercise  # Higher adherence = more training
    
    # Keep within specified range (8-16 hours)
    weekly_training_hours = np.clip(weekly_training_hours, 8, 16)

    return weekly_training_hours

def calculate_FTP(gender, weight, training_experience, genetic_factor, athlete_type, smoking, drinking):
    """Generates Functional Threshold Power."""
    power_to_weight = np.random.normal(3.8, 0.7) if gender == "male" else np.random.normal(3.4, 0.7)
    power_to_weight *= (1 + (training_experience * 0.01))  # Experience increases power
    power_to_weight *= genetic_factor  
    if athlete_type == "bike_strong":
        power_to_weight *= 1.1
    if smoking > 0.2 or drinking > 0.2:
        power_to_weight *= 0.95
    power_to_weight = np.clip(power_to_weight, 2.5, 5.5)  # Reasonable range for power-to-weight ratio
    ftp = power_to_weight * weight
    return ftp

def calculate_CSS(vo2max, weekly_training_hours, training_experience, athlete_type):
    """Calculates CSS (Critical Swim Speed) based on fitness and training habits."""
    
    # Adjusted base CSS
    base_css = 0.80  # More reasonable starting point  

    # VO2max contribution (less aggressive)
    vo2_factor = (vo2max - 50) * 0.008  # Each +10 VO2max now adds ~0.08 m/s instead of 0.1

    # Swim training factor (stronger emphasis on actual swim volume)
    swim_hours = weekly_training_hours * 0.25  # Assuming ~25% of total training is swimming
    training_factor = min(swim_hours, 15) * 0.015  # Each extra hour adds ~0.015 m/s, capped at 15 hours

    # Training experience effect (capped at 10 years, reduced impact)
    experience_factor = min(training_experience, 10) * 0.015  # Each year adds ~0.015 m/s instead of 0.02

    # Specialization bonus for strong swimmers
    if athlete_type == "swim_strong":
        base_css *= 1.08  # Less boost than before (1.08x instead of 1.1x)

    # Final calculation
    estimated_css = base_css + vo2_factor + training_factor + experience_factor
    estimated_css = max(0.80, min(estimated_css, 1.55))  # Stricter upper/lower limits  

    # Convert to seconds per 100m
    css_s_per_100m = round(100 / estimated_css, 1)

    return css_s_per_100m

def generate_vo2max(age, training_experience, gender, lifestyle, athlete_type, genetic_factor):
    """Generates VO2max based on age, training experience, genetic factors, gender, and lifestyle factors."""
    # Baseline VO2max for competitive athletes (higher than general population)
    base_vo2max = np.random.normal(45, 4) if gender == "female" else np.random.normal(49, 4)

    # Genetic predisposition (±5 ml/kg/min variation)
    if genetic_factor < 1:
        genetic_boost = np.random.uniform(-2, 0)
    elif genetic_factor > 1:
        genetic_boost = np.random.uniform(0, 5)

    # Training experience effect (2-20 years → +5 to +30 ml/kg/min)
    training_boost = (training_experience + 3) * np.random.uniform(1.5, 2.0)
    training_boost = min(training_boost, 30)  # Cap the training boost at 30 ml/kg/min 

    # Age decline (Starting ~30, ~0.5 per year)
    age_decline = max(0, (age - 30) * 0.5)  

    # Lifestyle factor adjustments
    sleep_effect = lifestyle["sleep"] * np.random.uniform(0.5, 1.5)
    nutrition_effect = lifestyle["nutrition"] * np.random.uniform(1, 2)
    exercise_effect = lifestyle["exercise"] * np.random.uniform(1.5, 3)
    stress_effect = -lifestyle["stress"] * np.random.uniform(2, 5)
    smoking_effect = -lifestyle["smoking"] * np.random.uniform(5, 15)
    drinking_effect = -lifestyle["drinking"] * np.random.uniform(2, 7)

    lifestyle_effect = sleep_effect + nutrition_effect + exercise_effect + stress_effect + smoking_effect + drinking_effect
    lifestyle_effect = np.clip(lifestyle_effect, -20, 15)  # Cap the lifestyle effect at ±20 ml/kg/min

    # Final VO2max calculation
    vo2max = (base_vo2max + training_boost - age_decline + lifestyle_effect + genetic_boost)
    
    if athlete_type == "swim_strong":
        vo2max *= 1
    elif athlete_type == "bike_strong":
        vo2max *= 1
    elif athlete_type == "run_strong":
        vo2max *= 1.05

    # Clip to competitive athlete ranges (50-75 ml/kg/min)
    if gender == "male":
        vo2max = np.clip(vo2max, 50, 75)
    else:
        vo2max = np.clip(vo2max, 50, 70)
        
    if lifestyle["smoking"] > 0.7:
        vo2max *= 0.85
        
    return round(vo2max, 1)

def estimate_resting_hr(vo2max, lifestyle_factors):
    # Resting HR for competitive athletes (38-60 range)
    resting_hr = int(np.random.normal(53, 5) - (vo2max * 0.05))
    if lifestyle_factors['sleep'] > 6:
        resting_hr += lifestyle_factors['stress'] * 2 + lifestyle_factors['smoking'] * 3 - lifestyle_factors['sleep'] * 0.2 - lifestyle_factors['exercise'] * 2
    else:
        resting_hr += lifestyle_factors['stress'] * 2 + lifestyle_factors['smoking'] * 3 + lifestyle_factors['sleep'] * 0.5 - lifestyle_factors['exercise'] * 2
    
    # Force resting HR into competitive athlete range (38-60 bpm)
    resting_hr = np.clip(resting_hr, 38, 60)

    return resting_hr

def estimate_lactate_threshold_hr(age, gender, max_hr, resting_hr, training_experience, vo2max):
     # Base LTHR percentage - increase for competitive triathletes
    # Competitive triathletes often have LTHR at 85-90% of max HR
    base_lthr_percentage = 0.87  # Increased from 0.82 to better match competitive athletes
    
    # Modifiers based on various factors
    modifiers = []
    
    # Age modifier - adjusted for triathlon performance curve
    age_modifier = 1.0
    if age < 25:
        age_modifier = 1.03  # Slightly higher for younger athletes
    elif 25 <= age <= 35:
        age_modifier = 1.02  # Prime age for endurance performance
    elif 35 < age <= 45:
        age_modifier = 1.0   # Still strong but starting to decline
    else:
        age_modifier = 0.98  # Modest reduction for older athletes
    modifiers.append(age_modifier)
    
    # Training years impact - more significant for experienced athletes
    years_modifier = min(1.15, 1.0 + (training_experience * 0.015))
    modifiers.append(years_modifier)
    
    # VO2max impact - stronger correlation with LTHR
    # Using a more pronounced curve for triathletes
    vo2_modifier = 1.0
    if vo2max > 65:  # High VO2max indicates better lactate clearance
        vo2_modifier = 1.0 + ((vo2max - 65) / 100) * 0.15
    elif vo2max < 55:  # Lower VO2max may indicate earlier lactate accumulation
        vo2_modifier = 1.0 - ((55 - vo2max) / 100) * 0.1
    modifiers.append(vo2_modifier)
    
    # Heart Rate Reserve (HRR) consideration - better indicator than just resting HR
    hrr = max_hr - resting_hr
    hrr_modifier = 1.0
    if hrr > 130:  # Large heart rate reserve often indicates better conditioning
        hrr_modifier = 1.02
    elif hrr < 120:
        hrr_modifier = 0.98
    modifiers.append(hrr_modifier)
    
    # Gender-specific adjustment - refined based on physiological differences
    gender_modifier = 1.03 if gender == 'female' else 1.0
    modifiers.append(gender_modifier)
    
    # Calculate final modifier
    final_modifier = np.prod(modifiers)
    
    # Add small random variation for synthetic data
    variation = random.uniform(-0.015, 0.015)
    
    # Calculate estimated LTHR
    estimated_lthr = (
        max_hr *
        base_lthr_percentage *
        final_modifier *
        (1 + variation)
    )
    
    # Adjusted range for competitive triathletes (160-190 bpm)
    estimated_lthr = max(160, min(estimated_lthr, 190))
    
    return round(estimated_lthr)

def estimate_threshold_pace(gender, age, weight_kg, VO2max, training_experience, weekly_training_hours, lifestyle_factors, genetic_factor,lactate_threshold_hr,max_heart_rate,running_specificity=1.0):
    
    # Base calculation
    if gender == "male":
        base_pace = 16.2 - 0.16 * VO2max * (1 + random.uniform(-0.025, 0.025))
    else:
        base_pace = 16.7 - 0.16 * VO2max * (1 + random.uniform(-0.025, 0.025))

    # Advanced weight adjustment with quadratic scaling
    weight_reference = 70 if gender == "male" else 55
    weight_sensitivity = 0.0025 if gender == "male" else 0.0035 
    
    if weight_kg < weight_reference:
        weight_factor = 1.0 + weight_sensitivity * (weight_kg - weight_reference) / 150  # Less penalty for light runners
    else:
        weight_factor = 1.0 + weight_sensitivity * (weight_kg - weight_reference) * abs(weight_kg - weight_reference) / 100

    
    # Sophisticated age factor with bell curve performance peak
    optimal_age = 28
    age_performance_curve = np.exp(-((age - optimal_age) ** 2) / (2 * 11 ** 2))
    age_factor = 1.0 + (1 - age_performance_curve) * 0.12
    
    # Normalized lactate threshold percentage
    lt_percentage = lactate_threshold_hr / max_heart_rate
        
    # Performance modifier based on lactate threshold
    # Peak performance around 85-87% of max heart rate
    optimal_lt_range = 0.86
    hr_performance_modifier = 1.0 - (abs(lt_percentage - optimal_lt_range) ** 1.7) * 0.45
    
    
    # Training experience & volume effects
    experience_modifier = min(0.85, 0.08 * np.log1p(training_experience) * running_specificity)
    volume_modifier = min(0.8, 0.065 * np.log1p(weekly_training_hours) * running_specificity)
    
    
    # Lifestyle and genetic factors
    lifestyle_factor = calculate_lifestyle_factor(lifestyle_factors)
    
    # Comprehensive pace calculation
    adjusted_pace = base_pace * (
        weight_factor * 
        age_factor * 
        hr_performance_modifier * 
        (1 - experience_modifier) * 
        (1 - volume_modifier)
    )
    
    # Final adjustments
    final_pace = adjusted_pace * (1 + (1 - lifestyle_factor) * 0.2) / (genetic_factor * 0.8 + 0.2)
    
    # Add controlled variation
    variation = np.random.normal(0, 0.1)
    final_pace += variation
   
    # Strict output range (3:00-5:30 min/km)
    final_pace = max(3.0, min(5.5, final_pace))
    
    return round(final_pace, 2)

def estimate_hrv(age, vo2max, resting_hr, sleep, stress, smoking, drinking, training_experience):
    """Estimate an athlete's HRV baseline (RMSSD in ms) with a realistic age-adjusted range."""
    # Base HRV calculation considering fitness, lifestyle, and experience - adjusted for competitive athletes
    hrv = (110 + (vo2max * 1.2) - (resting_hr * 0.5) +
           (sleep * 2) - (stress * 5) - (smoking * 10) -
           (drinking * 7) + (training_experience * 0.8))
    
    # Apply age-based decline (approx. -0.8 ms per year after 20)
    age_factor = 100 - (age * 0.8)
    hrv *= (age_factor / 100)  # Scaling HRV down with age
    
    # Clip to realistic age-based range for competitive athletes
    hrv_min = max(40, 110 - (age * 1.2))  # Adjusted minimums for competitive athletes
    hrv_max = max(50, 150 - (age * 1.5))
    hrv = np.clip(hrv, hrv_min, hrv_max)
    
    # Calculate HRV range (±15%)
    hrv_low = round(hrv * 0.85, 1)
    hrv_high = round(hrv * 1.15, 1)
    
    return {
        "HRV_baseline": round(hrv, 1),
        "HRV_range": (hrv_low, hrv_high)
    }

def generate_lifestyle_factors():
    """Generate lifestyle factors for competitive age-group triathletes."""
    
    lifestyle_profiles = [
        {
            'name': 'Highly Disciplined Athlete',
            'sleep': np.random.uniform(7.5, 9),
            'sleep_quality': np.random.uniform(0.9, 1.0),
            'nutrition': np.random.uniform(0.9, 1.0),
            'drinking': np.random.uniform(0, 0.1),
            'smoking': 0,
            'stress': np.random.uniform(0, 0.2),
            'exercise': np.random.uniform(0.9, 1.0)
        },
        {
            'name': 'Balanced Competitor',
            'sleep': np.random.uniform(6.5, 8),
            'sleep_quality': np.random.uniform(0.7, 0.9),
            'nutrition': np.random.uniform(0.7, 0.9),
            'drinking': np.random.uniform(0.1, 0.2),
            'smoking': 0,
            'stress': np.random.uniform(0.2, 0.4),
            'exercise': np.random.uniform(0.7, 0.9)
        },
        {
            'name': 'Weekend Socializer',
            'sleep': np.random.uniform(6, 7.5),
            'sleep_quality': np.random.uniform(0.6, 0.8),
            'nutrition': np.random.uniform(0.6, 0.8),
            'drinking': np.random.uniform(0.3, 0.6),
            'smoking': np.random.uniform(0, 0.1),  # Occasional social smoking
            'stress': np.random.uniform(0.3, 0.6),
            'exercise': np.random.uniform(0.6, 0.8)
        },
        {
            'name': 'Sleep-Deprived Workaholic',
            'sleep': np.random.uniform(4.5, 6.5),
            'sleep_quality': np.random.uniform(0.4, 0.7),
            'nutrition': np.random.uniform(0.5, 0.8),
            'drinking': np.random.uniform(0.2, 0.4),
            'smoking': 0,
            'stress': np.random.uniform(0.6, 0.9),
            'exercise': np.random.uniform(0.6, 0.8)
        },
        {
            'name': 'Under-Recovered Athlete',
            'sleep': np.random.uniform(5, 7),
            'sleep_quality': np.random.uniform(0.3, 0.6),
            'nutrition': np.random.uniform(0.4, 0.7),
            'drinking': np.random.uniform(0.2, 0.4),
            'smoking': 0,
            'stress': np.random.uniform(0.4, 0.8),
            'exercise': np.random.uniform(0.7, 0.9)
        },
        {
            'name': 'Health-Conscious Athlete',
            'sleep': np.random.uniform(7, 8.5),
            'sleep_quality': np.random.uniform(0.8, 1.0),
            'nutrition': np.random.uniform(0.8, 1.0),
            'drinking': np.random.uniform(0, 0.2),
            'smoking': 0,
            'stress': np.random.uniform(0.1, 0.3),
            'exercise': np.random.uniform(0.8, 1.0)
        }
    ]
    
    # probability weights based on likely distribution in competitive triathletes
    lifestyle_weights = [0.30, 0.25, 0.12, 0.12, 0.11, 0.10]
    
    lifestyle = random.choices(lifestyle_profiles, weights=lifestyle_weights, k=1)[0]

    # Ensure sleep falls within 5-9 hour range
    lifestyle['sleep'] = max(5, min(9, lifestyle['sleep']))

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
    drinking_inverted = 1 - min(1, lifestyle_dict.get('drinking', 0.3) / 6)  # Rescale to 0-1
    smoking_inverted = 1 - lifestyle_dict.get('smoking', 0)
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
    
    if smoking_inverted < 0.2:
        lifestyle_factor *= 0.5
    
    return lifestyle_factor

def assign_specialization():
    """Assigns a specialization to an athlete (swim, bike, run, or balanced)."""
    
    athlete_type = random.choices(
        ["swim_strong", "bike_strong", "run_strong", "balanced"],
        weights=[0.25, 0.25, 0.25, 0.25]
    )[0]

    return athlete_type

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

def add_recovery_characteristics():
    # Add recovery profile characteristics
    recovery_profile = random.choice([
        "hrv_dominant",      # Shows strong HRV changes with fatigue
        "sleep_dominant",    # Shows strong sleep disruption with fatigue
        "rhr_dominant",      # Shows strong RHR changes with fatigue
        "stress_dominant",   # Shows strong stress response with fatigue
        "balanced"           # Shows balanced changes across metrics
    ])

    recovery_signature = {
        "hrv_sensitivity": random.uniform(0.8, 1.2),
        "sleep_sensitivity": random.uniform(0.8, 1.2),
        "rhr_sensitivity": random.uniform(0.8, 1.2),
        "stress_sensitivity": random.uniform(0.8, 1.2)
    }

    # Adjust sensitivities based on recovery profile
    if recovery_profile == "hrv_dominant":
        recovery_signature["hrv_sensitivity"] *= 1.6
        recovery_signature["sleep_sensitivity"] *= 0.8
    elif recovery_profile == "sleep_dominant":
        recovery_signature["sleep_sensitivity"] *= 1.6
        recovery_signature["hrv_sensitivity"] *= 0.9
    elif recovery_profile == "rhr_dominant":
        recovery_signature["rhr_sensitivity"] *= 1.6
        recovery_signature["hrv_sensitivity"] *= 0.9
    elif recovery_profile == "stress_dominant":
        recovery_signature["stress_sensitivity"] *= 1.6
        recovery_signature["sleep_sensitivity"] *= 0.8

    return recovery_profile, recovery_signature

def generate_athlete_cohort(n):
    """Generate a cohort of athletes with specializations."""
    cohort = [generate_athlete_profile() for _ in range(n)]
     # Validate cohort against specified constraints
    for athlete in cohort:
        # Ensure age is between 18-50
        athlete['age'] = max(18, min(50, athlete['age']))
        
        # Ensure VO2max is between 50-75
        athlete['vo2max'] = max(50, min(75, athlete['vo2max']))
        
        # Ensure training hours is between 8-16
        athlete['weekly_training_hours'] = max(8, min(16, athlete['weekly_training_hours']))
        
        # Ensure resting HR is between 38-60
        athlete['resting_hr'] = max(38, min(60, athlete['resting_hr']))
        
        # Ensure training experience is at least 2 years
        athlete['training_experience'] = max(2, athlete['training_experience'])
        
        # Ensure sleep is between 5-9 hours
        athlete['sleep_time_norm'] = max(5, min(9, athlete['sleep_time_norm']))
    return cohort