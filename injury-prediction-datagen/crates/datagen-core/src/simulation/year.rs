//! Year-long simulation orchestration.

use chrono::{NaiveDate, Datelike};
use rand::prelude::*;
use rand_chacha::ChaCha8Rng;
use rand_distr::{Distribution, Normal};

use crate::athlete::Athlete;
use crate::config::SimulationParams;
use crate::training::{generate_annual_plan, TrainingState, initialize_tss_history, initialize_hrv_history};
use crate::activity::{generate_activities, Activity};
use super::daily::simulate_daily_metrics_with_config;
use super::types::{AthleteSimulationResult, DailyMetrics};

/// Simulate a full year for an athlete (uses default config).
pub fn simulate_full_year(athlete: &Athlete, year: i32, base_seed: u64) -> AthleteSimulationResult {
    simulate_full_year_with_config(athlete, year, base_seed, &SimulationParams::default())
}

/// Simulate a full year for an athlete with configuration.
pub fn simulate_full_year_with_config(
    athlete: &Athlete,
    year: i32,
    base_seed: u64,
    params: &SimulationParams,
) -> AthleteSimulationResult {
    // Create deterministic RNG from base seed + athlete ID
    let athlete_seed = base_seed.wrapping_add(
        athlete.id.as_bytes().iter().map(|&b| b as u64).sum::<u64>()
    );
    let mut rng = ChaCha8Rng::seed_from_u64(athlete_seed);

    // Generate annual training plan
    let plan = generate_annual_plan(athlete, year, athlete_seed);

    // Initialize training state with config
    let tss_history = initialize_tss_history(
        athlete.weekly_training_hours,
        athlete.recovery_rate,
        &params.training,
    );
    let hrv_history = initialize_hrv_history(
        athlete.hrv_baseline,
        athlete.hrv_range,
        &params.training,
    );

    let initial_ctl = tss_history.iter().sum::<f64>() / params.training.acwr_chronic_window as f64;
    let mut training_state = TrainingState::new_with_config(
        initial_ctl,
        athlete.hrv_baseline,
        params.training.clone(),
    );
    training_state.tss_history = tss_history;
    training_state.hrv_history = hrv_history;

    let mut daily_metrics = Vec::with_capacity(366);
    let mut all_activities = Vec::with_capacity(1000);

    // Simulate each day
    for training_day in &plan.days {
        // Determine workout completion (may skip due to fatigue, life, etc.)
        let completion_rate = calculate_completion_rate(&mut rng, athlete, &training_state, training_day);

        // Generate activities for the day
        let (activities, actual_tss) = generate_activities(
            &mut rng,
            athlete,
            training_day,
            completion_rate,
        );

        // Simulate daily metrics with config
        let metrics = simulate_daily_metrics_with_config(
            &mut rng,
            athlete,
            training_day.date,
            training_day,
            &training_state,
            actual_tss,
            &params.injury,
        );

        // Update training state
        training_state.update(actual_tss, metrics.hrv);

        daily_metrics.push(metrics);
        all_activities.extend(activities);
    }

    AthleteSimulationResult {
        athlete: athlete.clone(),
        daily_metrics,
        activities: all_activities,
    }
}

/// Calculate workout completion rate based on various factors.
fn calculate_completion_rate<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    training_state: &TrainingState,
    training_day: &crate::training::TrainingDay,
) -> f64 {
    if training_day.is_rest_day {
        return 0.0;
    }

    let mut base_rate = 0.95; // 95% base completion rate

    // Fatigue reduces completion
    if training_state.atl > 100.0 {
        base_rate -= (training_state.atl - 100.0) / 500.0;
    }

    // Poor form reduces completion
    if training_state.tsb < -30.0 {
        base_rate -= (-training_state.tsb - 30.0) / 200.0;
    }

    // Lifestyle factors
    base_rate *= athlete.lifestyle.exercise;

    // Random variation
    let noise = Normal::new(0.0, 0.05).unwrap();
    base_rate += noise.sample(rng);

    // Race day always completed
    if training_day.is_race_day {
        return 1.0;
    }

    base_rate.clamp(0.0, 1.0)
}
