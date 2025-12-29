//! Athlete profile generation logic.

use rand::prelude::*;
use rand_chacha::ChaCha8Rng;
use rand_distr::{Distribution, Normal, Uniform};
use statrs::distribution::Beta;
use uuid::Uuid;

use crate::config::AthleteConfig;
use super::lifestyle::generate_lifestyle_factors;
use super::zones::{calculate_hr_zones, calculate_power_zones};
use super::types::*;

/// Generate a complete athlete profile with deterministic seed (uses default config).
pub fn generate_athlete_profile(seed: u64) -> Athlete {
    generate_athlete_profile_with_config(seed, &AthleteConfig::default())
}

/// Generate a complete athlete profile with deterministic seed and configuration.
pub fn generate_athlete_profile_with_config(seed: u64, config: &AthleteConfig) -> Athlete {
    let mut rng = ChaCha8Rng::seed_from_u64(seed);

    // Gender based on configured probability
    let gender = if rng.gen::<f64>() < (1.0 - config.female_probability) {
        Gender::Male
    } else {
        Gender::Female
    };

    // Age: Mean 33, std 6, range from config
    let age_dist = Normal::new(33.0, 6.0).unwrap();
    let age: f64 = age_dist.sample(&mut rng);
    let age = age.clamp(config.min_age as f64, config.max_age as f64) as u8;

    // Height with gender-based differences
    let (height_mean, height_std) = match gender {
        Gender::Male => (178.0, 7.0),
        Gender::Female => (165.0, 6.0),
    };
    let height_dist = Normal::new(height_mean, height_std).unwrap();
    let height_cm = height_dist.sample(&mut rng);

    // Weight calculation
    let (base_weight, weight_std, height_ref) = match gender {
        Gender::Male => (72.0, 6.0, 165.0),
        Gender::Female => (58.0, 5.0, 165.0),
    };
    let weight_factor = match gender {
        Gender::Male => 0.4,
        Gender::Female => 0.3,
    };
    let weight_dist = Normal::new(
        base_weight + (height_cm - height_ref) * weight_factor,
        weight_std,
    ).unwrap();
    let mut weight_kg = weight_dist.sample(&mut rng);

    // Genetic factor: truncated normal with mean 1.0, range 0.8-1.2
    let genetic_factor = sample_truncated_normal(&mut rng, 1.0, 0.1, 0.8, 1.2);

    // Generate lifestyle factors
    let lifestyle = generate_lifestyle_factors(&mut rng);

    // Adjust weight based on lifestyle
    weight_kg += lifestyle.nutrition * (-2.0)
        + lifestyle.drinking * 1.5
        - lifestyle.exercise * 1.5;

    // Specialization assignment (25% each)
    let specialization = match rng.gen_range(0..4) {
        0 => Specialization::SwimStrong,
        1 => Specialization::BikeStrong,
        2 => Specialization::RunStrong,
        _ => Specialization::Balanced,
    };

    // Training experience
    let training_experience = generate_training_experience(&mut rng, age);

    // VO2max calculation
    let vo2max = generate_vo2max(
        &mut rng,
        age,
        training_experience,
        gender,
        &lifestyle,
        specialization,
        genetic_factor,
    );

    // Weekly training hours from config
    let weekly_training_hours = calculate_training_volume(
        &mut rng,
        lifestyle.drinking,
        training_experience,
        lifestyle.exercise,
        config.min_weekly_hours,
        config.max_weekly_hours,
    );

    // FTP calculation
    let ftp = calculate_ftp(
        &mut rng,
        gender,
        weight_kg,
        training_experience,
        genetic_factor,
        specialization,
        lifestyle.smoking,
        lifestyle.drinking,
    );
    let power_zones = calculate_power_zones(ftp);

    // CSS (Critical Swim Speed) in s/100m
    let css = calculate_css(vo2max, weekly_training_hours, training_experience, specialization);

    // Resting HR
    let resting_hr = estimate_resting_hr(&mut rng, vo2max, &lifestyle);

    // Max HR (Tanaka method: 208 - 0.7 * age)
    let max_hr_dist = Normal::new(0.0, 5.0).unwrap();
    let mut max_hr = 208.0 - 0.7 * (age as f64) + max_hr_dist.sample(&mut rng);
    if gender == Gender::Female {
        max_hr *= 1.03;
    }

    // Running specificity for threshold pace
    let running_specificity = if specialization == Specialization::RunStrong {
        1.2
    } else {
        1.0
    };

    // Lactate threshold HR
    let lthr = estimate_lactate_threshold_hr(
        &mut rng,
        age,
        gender,
        max_hr,
        resting_hr,
        training_experience,
        vo2max,
    );

    // Threshold pace
    let run_threshold_pace = estimate_threshold_pace(
        &mut rng,
        gender,
        age,
        weight_kg,
        vo2max,
        training_experience,
        weekly_training_hours,
        &lifestyle,
        genetic_factor,
        lthr,
        max_hr,
        running_specificity,
    );

    // HR zones
    let hr_zones = calculate_hr_zones(lthr, resting_hr, max_hr);

    // Recovery rate
    let recovery_rate = calculate_recovery_rate(
        genetic_factor,
        vo2max,
        &lifestyle,
        age,
    );

    // HRV estimation
    let (hrv_baseline, hrv_range) = estimate_hrv(
        &mut rng,
        age,
        vo2max,
        resting_hr,
        &lifestyle,
        training_experience,
    );

    // Recovery characteristics
    let (recovery_profile, recovery_signature) = add_recovery_characteristics(&mut rng);

    // Sensor profile (70% Garmin, 30% optical)
    let sensor_profile = if rng.gen::<f64>() < 0.7 {
        SensorProfile::Garmin
    } else {
        SensorProfile::Optical
    };

    // Chronotype (20% lark, 20% owl, 60% intermediate)
    let chronotype_roll: f64 = rng.gen();
    let chronotype = if chronotype_roll < 0.2 {
        Chronotype::Lark
    } else if chronotype_roll < 0.4 {
        Chronotype::Owl
    } else {
        Chronotype::Intermediate
    };

    // Menstrual cycle config for female athletes
    let menstrual_cycle_config = if gender == Gender::Female {
        let cycle_dist = Normal::new(28.0, 2.0).unwrap();
        let cycle_length: f64 = cycle_dist.sample(&mut rng);
        let cycle_length = cycle_length.clamp(21.0, 35.0) as u8;

        let beta = Beta::new(5.0, 1.0).unwrap();
        let regularity = beta.sample(&mut rng);

        let luteal_dist = Normal::new(14.0, 1.0).unwrap();
        let luteal_phase_length: f64 = luteal_dist.sample(&mut rng);
        let luteal_phase_length = luteal_phase_length.clamp(10.0, 16.0) as u8;

        Some(MenstrualCycleConfig {
            cycle_length,
            regularity,
            luteal_phase_length,
        })
    } else {
        None
    };

    Athlete {
        id: Uuid::new_v4().to_string(),
        gender,
        age,
        height_cm: (height_cm * 10.0).round() / 10.0,
        weight_kg: (weight_kg * 10.0).round() / 10.0,
        genetic_factor: (genetic_factor * 100.0).round() / 100.0,
        hrv_baseline,
        hrv_range,
        max_hr: (max_hr * 10.0).round() / 10.0,
        resting_hr: (resting_hr * 10.0).round() / 10.0,
        lthr: (lthr * 10.0).round() / 10.0,
        hr_zones,
        vo2max: (vo2max * 10.0).round() / 10.0,
        ftp: (ftp * 10.0).round() / 10.0,
        power_zones,
        css,
        run_threshold_pace: (run_threshold_pace * 100.0).round() / 100.0,
        training_experience,
        weekly_training_hours: (weekly_training_hours * 10.0).round() / 10.0,
        recovery_rate: (recovery_rate * 100.0).round() / 100.0,
        specialization,
        lifestyle,
        recovery_profile,
        recovery_signature,
        sensor_profile,
        chronotype,
        menstrual_cycle_config,
    }
}

/// Sample from truncated normal distribution.
fn sample_truncated_normal<R: Rng>(rng: &mut R, mean: f64, std: f64, min: f64, max: f64) -> f64 {
    let normal = Normal::new(mean, std).unwrap();
    loop {
        let sample = normal.sample(rng);
        if sample >= min && sample <= max {
            return sample;
        }
    }
}

/// Generate training experience based on age.
fn generate_training_experience<R: Rng>(rng: &mut R, age: u8) -> u8 {
    let experience_distribution = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20];
    let experience_weights = [0.10, 0.10, 0.10, 0.10, 0.10, 0.08, 0.08, 0.06, 0.06, 0.04, 0.04, 0.03, 0.03, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01];

    let dist = Uniform::new(0.0, 1.0);
    let roll: f64 = dist.sample(rng);
    let mut cumulative = 0.0;
    let mut training_experience = 2u8;

    for (i, &weight) in experience_weights.iter().enumerate() {
        cumulative += weight;
        if roll < cumulative {
            training_experience = experience_distribution[i];
            break;
        }
    }

    // Adjust based on age (max experience = age - 15)
    let max_experience = ((age as i32 - 15).max(2)) as u8;
    training_experience.min(max_experience).max(2)
}

/// Calculate weekly training volume.
fn calculate_training_volume<R: Rng>(
    rng: &mut R,
    drinking: f64,
    training_experience: u8,
    exercise: f64,
    min_hours: f64,
    max_hours: f64,
) -> f64 {
    let mean_hours = (min_hours + max_hours) / 2.0;
    let std_hours = (max_hours - min_hours) / 4.0;
    let dist = Normal::new(mean_hours, std_hours).unwrap();
    let mut hours = dist.sample(rng);

    // Lifestyle adjustments
    hours *= (2.0 - 0.3 * drinking).min(1.0);
    hours *= 1.0 + (training_experience as f64) * 0.03;
    hours *= exercise;

    hours.clamp(min_hours, max_hours)
}

/// Calculate FTP (Functional Threshold Power).
fn calculate_ftp<R: Rng>(
    rng: &mut R,
    gender: Gender,
    weight: f64,
    training_experience: u8,
    genetic_factor: f64,
    specialization: Specialization,
    smoking: f64,
    drinking: f64,
) -> f64 {
    let (mean, std) = match gender {
        Gender::Male => (3.8, 0.7),
        Gender::Female => (3.4, 0.7),
    };
    let dist = Normal::new(mean, std).unwrap();
    let mut power_to_weight = dist.sample(rng);

    power_to_weight *= 1.0 + (training_experience as f64) * 0.01;
    power_to_weight *= genetic_factor;

    if specialization == Specialization::BikeStrong {
        power_to_weight *= 1.1;
    }

    if smoking > 0.2 || drinking > 0.2 {
        power_to_weight *= 0.95;
    }

    power_to_weight = power_to_weight.clamp(2.5, 5.5);
    power_to_weight * weight
}

/// Calculate CSS (Critical Swim Speed) in s/100m.
fn calculate_css(
    vo2max: f64,
    weekly_training_hours: f64,
    training_experience: u8,
    specialization: Specialization,
) -> f64 {
    let mut base_css = 0.80; // m/s

    // VO2max contribution
    let vo2_factor = (vo2max - 50.0) * 0.008;

    // Swim training factor
    let swim_hours = weekly_training_hours * 0.25;
    let training_factor = swim_hours.min(15.0) * 0.015;

    // Experience factor
    let experience_factor = (training_experience as f64).min(10.0) * 0.015;

    // Specialization bonus
    if specialization == Specialization::SwimStrong {
        base_css *= 1.08;
    }

    let estimated_css = (base_css + vo2_factor + training_factor + experience_factor).clamp(0.80, 1.55);

    // Convert to s/100m
    (100.0 / estimated_css * 10.0).round() / 10.0
}

/// Generate VO2max based on various factors.
fn generate_vo2max<R: Rng>(
    rng: &mut R,
    age: u8,
    training_experience: u8,
    gender: Gender,
    lifestyle: &LifestyleProfile,
    specialization: Specialization,
    genetic_factor: f64,
) -> f64 {
    let (mean, std) = match gender {
        Gender::Female => (45.0, 4.0),
        Gender::Male => (49.0, 4.0),
    };
    let base_dist = Normal::new(mean, std).unwrap();
    let base_vo2max = base_dist.sample(rng);

    // Genetic boost
    let genetic_boost = if genetic_factor < 1.0 {
        Uniform::new(-2.0, 0.0).sample(rng)
    } else {
        Uniform::new(0.0, 5.0).sample(rng)
    };

    // Training boost (capped at 30)
    let training_boost = ((training_experience as f64 + 3.0) * Uniform::new(1.5, 2.0).sample(rng)).min(30.0);

    // Age decline after 30
    let age_decline = ((age as f64 - 30.0).max(0.0)) * 0.5;

    // Lifestyle effects
    let sleep_effect = lifestyle.sleep_hours * Uniform::new(0.5, 1.5).sample(rng);
    let nutrition_effect = lifestyle.nutrition * Uniform::new(1.0, 2.0).sample(rng);
    let exercise_effect = lifestyle.exercise * Uniform::new(1.5, 3.0).sample(rng);
    let stress_effect = -lifestyle.stress * Uniform::new(2.0, 5.0).sample(rng);
    let smoking_effect = -lifestyle.smoking * Uniform::new(5.0, 15.0).sample(rng);
    let drinking_effect = -lifestyle.drinking * Uniform::new(2.0, 7.0).sample(rng);

    let lifestyle_effect = (sleep_effect + nutrition_effect + exercise_effect + stress_effect + smoking_effect + drinking_effect).clamp(-20.0, 15.0);

    let mut vo2max = base_vo2max + training_boost - age_decline + lifestyle_effect + genetic_boost;

    if specialization == Specialization::RunStrong {
        vo2max *= 1.05;
    }

    // Clip to competitive ranges
    let (min_vo2, max_vo2) = match gender {
        Gender::Male => (50.0, 75.0),
        Gender::Female => (50.0, 70.0),
    };
    vo2max = vo2max.clamp(min_vo2, max_vo2);

    if lifestyle.smoking > 0.7 {
        vo2max *= 0.85;
    }

    vo2max
}

/// Estimate resting heart rate.
fn estimate_resting_hr<R: Rng>(rng: &mut R, vo2max: f64, lifestyle: &LifestyleProfile) -> f64 {
    let dist = Normal::new(53.0, 5.0).unwrap();
    let mut resting_hr = dist.sample(rng) - vo2max * 0.05;

    if lifestyle.sleep_hours > 6.0 {
        resting_hr += lifestyle.stress * 2.0
            + lifestyle.smoking * 3.0
            - lifestyle.sleep_hours * 0.2
            - lifestyle.exercise * 2.0;
    } else {
        resting_hr += lifestyle.stress * 2.0
            + lifestyle.smoking * 3.0
            + lifestyle.sleep_hours * 0.5
            - lifestyle.exercise * 2.0;
    }

    resting_hr.clamp(38.0, 60.0)
}

/// Estimate lactate threshold heart rate.
fn estimate_lactate_threshold_hr<R: Rng>(
    rng: &mut R,
    age: u8,
    gender: Gender,
    max_hr: f64,
    resting_hr: f64,
    training_experience: u8,
    vo2max: f64,
) -> f64 {
    let base_lthr_percentage = 0.87;

    // Age modifier
    let age_modifier = if age < 25 {
        1.03
    } else if age <= 35 {
        1.02
    } else if age <= 45 {
        1.0
    } else {
        0.98
    };

    // Training years modifier
    let years_modifier = (1.0 + (training_experience as f64) * 0.015).min(1.15);

    // VO2max modifier
    let vo2_modifier = if vo2max > 65.0 {
        1.0 + ((vo2max - 65.0) / 100.0) * 0.15
    } else if vo2max < 55.0 {
        1.0 - ((55.0 - vo2max) / 100.0) * 0.1
    } else {
        1.0
    };

    // Heart rate reserve modifier
    let hrr = max_hr - resting_hr;
    let hrr_modifier = if hrr > 130.0 {
        1.02
    } else if hrr < 120.0 {
        0.98
    } else {
        1.0
    };

    // Gender modifier
    let gender_modifier = if gender == Gender::Female { 1.03 } else { 1.0 };

    let final_modifier = age_modifier * years_modifier * vo2_modifier * hrr_modifier * gender_modifier;

    // Random variation
    let variation = Uniform::new(-0.015, 0.015).sample(rng);

    let lthr = max_hr * base_lthr_percentage * final_modifier * (1.0 + variation);
    lthr.clamp(160.0, 190.0)
}

/// Estimate running threshold pace.
fn estimate_threshold_pace<R: Rng>(
    rng: &mut R,
    gender: Gender,
    age: u8,
    weight_kg: f64,
    vo2max: f64,
    training_experience: u8,
    weekly_training_hours: f64,
    lifestyle: &LifestyleProfile,
    genetic_factor: f64,
    lthr: f64,
    max_hr: f64,
    running_specificity: f64,
) -> f64 {
    let variation = Uniform::new(-0.025, 0.025).sample(rng);
    let base_pace = match gender {
        Gender::Male => 16.2 - 0.16 * vo2max * (1.0 + variation),
        Gender::Female => 16.7 - 0.16 * vo2max * (1.0 + variation),
    };

    // Weight adjustment
    let weight_reference = if gender == Gender::Male { 70.0 } else { 55.0 };
    let weight_sensitivity = if gender == Gender::Male { 0.0025 } else { 0.0035 };

    let weight_factor = if weight_kg < weight_reference {
        1.0 + weight_sensitivity * (weight_kg - weight_reference) / 150.0
    } else {
        1.0 + weight_sensitivity * (weight_kg - weight_reference) * (weight_kg - weight_reference).abs() / 100.0
    };

    // Age factor with bell curve
    let optimal_age = 28.0;
    let age_performance_curve = (-((age as f64 - optimal_age).powi(2)) / (2.0 * 11.0_f64.powi(2))).exp();
    let age_factor = 1.0 + (1.0 - age_performance_curve) * 0.12;

    // HR performance modifier
    let lt_percentage = lthr / max_hr;
    let optimal_lt_range = 0.86;
    let hr_performance_modifier = 1.0 - (lt_percentage - optimal_lt_range).abs().powf(1.7) * 0.45;

    // Experience and volume modifiers
    let experience_modifier = (0.08 * (training_experience as f64 + 1.0).ln() * running_specificity).min(0.85);
    let volume_modifier = (0.065 * (weekly_training_hours + 1.0).ln() * running_specificity).min(0.8);

    // Lifestyle factor
    let lifestyle_factor = calculate_lifestyle_factor(lifestyle);

    // Comprehensive calculation
    let adjusted_pace = base_pace
        * weight_factor
        * age_factor
        * hr_performance_modifier
        * (1.0 - experience_modifier)
        * (1.0 - volume_modifier);

    let final_pace = adjusted_pace * (1.0 + (1.0 - lifestyle_factor) * 0.2) / (genetic_factor * 0.8 + 0.2);

    // Add variation
    let noise = Normal::new(0.0, 0.1).unwrap().sample(rng);
    (final_pace + noise).clamp(3.0, 5.5)
}

/// Calculate combined lifestyle factor.
fn calculate_lifestyle_factor(lifestyle: &LifestyleProfile) -> f64 {
    let weights = [
        ("sleep", 0.20),
        ("sleep_quality", 0.15),
        ("nutrition", 0.20),
        ("drinking", 0.10),
        ("smoking", 0.15),
        ("stress", 0.10),
        ("exercise", 0.10),
    ];

    let sleep_normalized = (lifestyle.sleep_hours / 9.0).clamp(0.0, 1.0);
    let drinking_inverted = 1.0 - (lifestyle.drinking / 6.0).min(1.0);
    let smoking_inverted = 1.0 - lifestyle.smoking;
    let stress_inverted = 1.0 - lifestyle.stress;

    let mut factor = weights[0].1 * sleep_normalized
        + weights[1].1 * lifestyle.sleep_quality
        + weights[2].1 * lifestyle.nutrition
        + weights[3].1 * drinking_inverted
        + weights[4].1 * smoking_inverted
        + weights[5].1 * stress_inverted
        + weights[6].1 * lifestyle.exercise;

    if smoking_inverted < 0.2 {
        factor *= 0.5;
    }

    factor
}

/// Calculate recovery rate.
fn calculate_recovery_rate(
    genetic_factor: f64,
    vo2max: f64,
    lifestyle: &LifestyleProfile,
    age: u8,
) -> f64 {
    let mut rate = 0.8 * genetic_factor + (vo2max - 40.0) / 150.0;

    if lifestyle.sleep_hours > 6.0 {
        rate += (lifestyle.sleep_hours - 6.0).max(0.0) * lifestyle.sleep_quality * 0.12;
    } else {
        rate += (lifestyle.sleep_hours - 6.0) * 0.1;
    }

    rate += lifestyle.nutrition * 0.08;
    rate -= (age as f64) * 0.002;
    rate -= lifestyle.drinking * 0.15;
    rate -= lifestyle.smoking * 0.15;
    rate -= lifestyle.stress * 0.12;

    rate.clamp(0.5, 1.3)
}

/// Estimate HRV baseline and range.
fn estimate_hrv<R: Rng>(
    rng: &mut R,
    age: u8,
    vo2max: f64,
    resting_hr: f64,
    lifestyle: &LifestyleProfile,
    training_experience: u8,
) -> (f64, (f64, f64)) {
    let mut hrv = 110.0 + vo2max * 1.2 - resting_hr * 0.5
        + lifestyle.sleep_hours * 2.0
        - lifestyle.stress * 5.0
        - lifestyle.smoking * 10.0
        - lifestyle.drinking * 7.0
        + (training_experience as f64) * 0.8;

    // Age-based decline
    let age_factor = (100.0 - (age as f64) * 0.8) / 100.0;
    hrv *= age_factor;

    // Clip to realistic range
    let hrv_min = (110.0 - (age as f64) * 1.2).max(40.0);
    let hrv_max = (150.0 - (age as f64) * 1.5).max(50.0);
    hrv = hrv.clamp(hrv_min, hrv_max);

    let hrv_baseline = (hrv * 10.0).round() / 10.0;
    let hrv_range = (
        (hrv * 0.85 * 10.0).round() / 10.0,
        (hrv * 1.15 * 10.0).round() / 10.0,
    );

    (hrv_baseline, hrv_range)
}

/// Add recovery characteristics.
fn add_recovery_characteristics<R: Rng>(rng: &mut R) -> (RecoveryProfile, RecoverySignature) {
    let profiles = [
        RecoveryProfile::HrvDominant,
        RecoveryProfile::SleepDominant,
        RecoveryProfile::RhrDominant,
        RecoveryProfile::StressDominant,
        RecoveryProfile::Balanced,
    ];
    let profile = profiles[rng.gen_range(0..5)];

    let base_range = Uniform::new(0.8, 1.2);
    let mut signature = RecoverySignature {
        hrv_sensitivity: base_range.sample(rng),
        sleep_sensitivity: base_range.sample(rng),
        rhr_sensitivity: base_range.sample(rng),
        stress_sensitivity: base_range.sample(rng),
    };

    match profile {
        RecoveryProfile::HrvDominant => {
            signature.hrv_sensitivity *= 1.6;
            signature.sleep_sensitivity *= 0.8;
        }
        RecoveryProfile::SleepDominant => {
            signature.sleep_sensitivity *= 1.6;
            signature.hrv_sensitivity *= 0.9;
        }
        RecoveryProfile::RhrDominant => {
            signature.rhr_sensitivity *= 1.6;
            signature.hrv_sensitivity *= 0.9;
        }
        RecoveryProfile::StressDominant => {
            signature.stress_sensitivity *= 1.6;
            signature.sleep_sensitivity *= 0.8;
        }
        RecoveryProfile::Balanced => {}
    }

    (profile, signature)
}
