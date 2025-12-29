//! Daily metrics simulation.

use chrono::NaiveDate;
use rand::prelude::*;
use rand_distr::{Distribution, Normal};

use crate::athlete::Athlete;
use crate::config::InjuryModelConfig;
use crate::injury::calculate_injury_probability;
use crate::training::{TrainingDay, TrainingState};
use super::types::{DailyMetrics, InjuryType};

/// Simulate daily metrics for an athlete on a given day (uses default config).
pub fn simulate_daily_metrics<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    date: NaiveDate,
    training_day: &TrainingDay,
    training_state: &TrainingState,
    actual_tss: f64,
) -> DailyMetrics {
    simulate_daily_metrics_with_config(
        rng,
        athlete,
        date,
        training_day,
        training_state,
        actual_tss,
        &InjuryModelConfig::default(),
    )
}

/// Simulate daily metrics for an athlete on a given day with configuration.
pub fn simulate_daily_metrics_with_config<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    date: NaiveDate,
    training_day: &TrainingDay,
    training_state: &TrainingState,
    actual_tss: f64,
    injury_config: &InjuryModelConfig,
) -> DailyMetrics {
    // Morning metrics
    let (resting_hr, hrv) = simulate_morning_hr(rng, athlete, training_state);
    let (sleep_hours, deep_sleep, light_sleep, rem_sleep, sleep_quality) =
        simulate_sleep(rng, athlete, training_state);
    let body_battery_morning = simulate_body_battery_morning(rng, athlete, sleep_quality, training_state);

    // Evening metrics
    let stress = simulate_stress(rng, athlete, actual_tss, training_state);
    let body_battery_evening = simulate_body_battery_evening(body_battery_morning, actual_tss, athlete);

    // Injury calculation with config
    let (injury, injury_type, injury_probability) = calculate_injury_with_config(
        rng,
        athlete,
        training_state,
        actual_tss,
        injury_config,
    );

    DailyMetrics {
        athlete_id: athlete.id.clone(),
        date,
        resting_hr,
        hrv,
        sleep_hours,
        deep_sleep,
        light_sleep,
        rem_sleep,
        sleep_quality,
        body_battery_morning,
        stress,
        body_battery_evening,
        planned_tss: training_day.total_tss,
        actual_tss,
        ctl: training_state.ctl,
        atl: training_state.atl,
        tsb: training_state.tsb,
        acwr: training_state.acwr,
        injury,
        injury_type,
        injury_probability,
    }
}

/// Simulate morning heart rate and HRV.
fn simulate_morning_hr<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    training_state: &TrainingState,
) -> (f64, f64) {
    // Base resting HR with fatigue effect
    let fatigue_effect = (training_state.atl / 100.0).min(0.1); // Up to 10% increase
    let base_rhr = athlete.resting_hr * (1.0 + fatigue_effect);

    let rhr_noise = Normal::new(0.0, 2.0).unwrap().sample(rng);
    let resting_hr = (base_rhr + rhr_noise).clamp(athlete.resting_hr * 0.9, athlete.resting_hr * 1.2);

    // HRV (inversely correlated with fatigue)
    let hrv_suppression = (training_state.atl / 200.0).min(0.2); // Up to 20% suppression
    let base_hrv = athlete.hrv_baseline * (1.0 - hrv_suppression);

    let hrv_noise = Normal::new(0.0, 5.0).unwrap().sample(rng);
    let hrv = (base_hrv + hrv_noise).clamp(athlete.hrv_range.0, athlete.hrv_range.1);

    (resting_hr, hrv)
}

/// Simulate sleep metrics.
fn simulate_sleep<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    training_state: &TrainingState,
) -> (f64, f64, f64, f64, f64) {
    // Base sleep hours from lifestyle
    let base_sleep = athlete.lifestyle.sleep_hours;

    // Fatigue can disrupt sleep
    let fatigue_disruption = if training_state.atl > 80.0 {
        (training_state.atl - 80.0) / 200.0 // Up to 0.3 hours disruption
    } else {
        0.0
    };

    let sleep_noise = Normal::new(0.0, 0.5).unwrap().sample(rng);
    let sleep_hours = (base_sleep - fatigue_disruption + sleep_noise).clamp(4.0, 10.0);

    // Sleep stage distribution
    let deep_pct = 0.15 + rng.gen_range(-0.05..0.05);
    let rem_pct = 0.20 + rng.gen_range(-0.05..0.05);
    let light_pct = 1.0 - deep_pct - rem_pct;

    let deep_sleep = sleep_hours * deep_pct;
    let rem_sleep = sleep_hours * rem_pct;
    let light_sleep = sleep_hours * light_pct;

    // Sleep quality
    let base_quality = athlete.lifestyle.sleep_quality;
    let quality_noise = Normal::new(0.0, 0.1).unwrap().sample(rng);
    let sleep_quality = (base_quality + quality_noise - fatigue_disruption * 0.5).clamp(0.0, 1.0);

    (sleep_hours, deep_sleep, light_sleep, rem_sleep, sleep_quality)
}

/// Simulate morning body battery.
fn simulate_body_battery_morning<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    sleep_quality: f64,
    training_state: &TrainingState,
) -> f64 {
    // Base: 50-100 based on recovery
    let base_battery = 50.0 + 50.0 * athlete.recovery_rate * sleep_quality;

    // Fatigue reduces battery
    let fatigue_drain = (training_state.atl / 100.0) * 20.0;

    let noise = Normal::new(0.0, 5.0).unwrap().sample(rng);
    (base_battery - fatigue_drain + noise).clamp(20.0, 100.0)
}

/// Simulate stress level.
fn simulate_stress<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    actual_tss: f64,
    training_state: &TrainingState,
) -> f64 {
    // Base stress from lifestyle
    let base_stress = athlete.lifestyle.stress * 50.0; // 0-50

    // Training adds stress
    let training_stress = (actual_tss / 100.0) * 20.0;

    // Fatigue accumulation adds stress
    let fatigue_stress = (training_state.atl / 100.0) * 10.0;

    let noise = Normal::new(0.0, 5.0).unwrap().sample(rng);
    (base_stress + training_stress + fatigue_stress + noise).clamp(0.0, 100.0)
}

/// Simulate evening body battery.
fn simulate_body_battery_evening(
    morning_battery: f64,
    actual_tss: f64,
    athlete: &Athlete,
) -> f64 {
    // Drain based on activity
    let activity_drain = (actual_tss / 100.0) * 40.0;

    // Recovery rate helps maintain battery
    let drain_modifier = 1.0 - (athlete.recovery_rate - 0.5) * 0.2;

    (morning_battery - activity_drain * drain_modifier).clamp(5.0, 100.0)
}

/// Calculate injury probability and determine if injury occurs (with config).
fn calculate_injury_with_config<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    training_state: &TrainingState,
    actual_tss: f64,
    config: &InjuryModelConfig,
) -> (bool, Option<InjuryType>, f64) {
    // Use the configurable injury probability calculation
    let injury_prob = calculate_injury_probability(athlete, training_state, actual_tss, config);

    // Determine if injury occurs
    let roll: f64 = rng.gen();
    let injury = roll < injury_prob;

    let injury_type = if injury {
        // Determine injury type based on ACWR vs fatigue
        if training_state.acwr > config.acwr_danger_threshold {
            Some(InjuryType::Exposure)
        } else if training_state.atl > config.fatigue_high_threshold {
            Some(InjuryType::Physiological)
        } else {
            Some(InjuryType::Baseline)
        }
    } else {
        None
    };

    (injury, injury_type, injury_prob)
}
