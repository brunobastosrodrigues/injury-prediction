//! Activity generation from training plans.

use rand::prelude::*;
use rand_distr::{Distribution, Normal};
use std::collections::HashMap;

use crate::athlete::Athlete;
use crate::training::{TrainingDay, Sport};
use super::types::Activity;
use super::timeseries::{generate_hr_series, generate_power_series, series_stats, calculate_hr_zone_distribution, calculate_normalized_power};
use super::physics::{solve_cycling_speed, default_cda, default_crr};

/// Generate activities for a training day.
///
/// Returns the activities and total actual TSS.
pub fn generate_activities<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    training_day: &TrainingDay,
    completion_rate: f64,
) -> (Vec<Activity>, f64) {
    let mut activities = Vec::new();
    let mut total_tss = 0.0;

    if training_day.is_rest_day || completion_rate < 0.1 {
        return (activities, 0.0);
    }

    // Generate swim workout
    if let Some(ref spec) = training_day.swim_workout {
        if rng.gen::<f64>() < completion_rate {
            let activity = generate_swim_activity(rng, athlete, training_day.date, spec);
            total_tss += activity.tss;
            activities.push(activity);
        }
    }

    // Generate bike workout
    if let Some(ref spec) = training_day.bike_workout {
        if rng.gen::<f64>() < completion_rate {
            let activity = generate_bike_activity(rng, athlete, training_day.date, spec);
            total_tss += activity.tss;
            activities.push(activity);
        }
    }

    // Generate run workout
    if let Some(ref spec) = training_day.run_workout {
        if rng.gen::<f64>() < completion_rate {
            let activity = generate_run_activity(rng, athlete, training_day.date, spec);
            total_tss += activity.tss;
            activities.push(activity);
        }
    }

    // Generate strength workout
    if let Some(ref spec) = training_day.strength_workout {
        if rng.gen::<f64>() < completion_rate {
            let activity = generate_strength_activity(rng, athlete, training_day.date, spec);
            total_tss += activity.tss;
            activities.push(activity);
        }
    }

    (activities, total_tss)
}

/// Generate a swim activity.
fn generate_swim_activity<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    date: chrono::NaiveDate,
    spec: &crate::training::WorkoutSpec,
) -> Activity {
    let duration = spec.duration_minutes;
    let intensity = spec.intensity_factor;

    // Calculate TSS
    let tss = intensity.powi(2) * (duration / 60.0) * 100.0;

    // Generate HR series
    let hr_series = generate_hr_series(rng, athlete, duration, intensity);
    let (avg_hr, max_hr) = series_stats(&hr_series);
    let hr_zones = calculate_hr_zone_distribution(&hr_series, athlete);

    // Calculate distance (CSS is in s/100m)
    let avg_pace = athlete.css / intensity; // Faster at higher intensity
    let distance_m = (duration * 60.0) / avg_pace * 100.0;

    let mut activity = Activity::new(
        athlete.id.clone(),
        date,
        Sport::Swim,
        spec.name.clone(),
        duration,
        tss,
        intensity,
    );

    activity.avg_hr = Some(avg_hr);
    activity.max_hr = Some(max_hr);
    activity.hr_zones = Some(hr_zones);
    activity.distance_m = Some(distance_m);
    activity.avg_pace_min_100m = Some(avg_pace / 60.0); // Convert to min/100m

    activity
}

/// Generate a bike activity.
fn generate_bike_activity<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    date: chrono::NaiveDate,
    spec: &crate::training::WorkoutSpec,
) -> Activity {
    let duration = spec.duration_minutes;
    let intensity = spec.intensity_factor;

    // Calculate TSS
    let tss = intensity.powi(2) * (duration / 60.0) * 100.0;

    // Generate power series
    let power_series = generate_power_series(rng, athlete, duration, intensity);
    let (avg_power, _max_power) = series_stats(&power_series);
    let normalized_power = calculate_normalized_power(&power_series);

    // Generate HR series
    let hr_series = generate_hr_series(rng, athlete, duration, intensity);
    let (avg_hr, max_hr) = series_stats(&hr_series);
    let hr_zones = calculate_hr_zone_distribution(&hr_series, athlete);

    // Calculate speed using physics solver
    let total_mass = athlete.weight_kg + 8.0; // Bike weight
    let cda = default_cda("hoods");
    let crr = default_crr("road");
    let avg_slope = Normal::new(0.0, 2.0).unwrap().sample(rng); // Random terrain

    let avg_speed = solve_cycling_speed(avg_power, total_mass, cda, crr, avg_slope, None);
    let distance_km = avg_speed * (duration / 60.0);

    // Calculate work
    let work_kj = avg_power * duration * 60.0 / 1000.0;

    // Elevation gain (rough estimate based on power and distance)
    let elevation_gain = (avg_slope.abs() / 100.0) * distance_km * 1000.0;

    // Intensity variability (VI = NP / AP)
    let variability = if avg_power > 0.0 { normalized_power / avg_power } else { 1.0 };

    let mut activity = Activity::new(
        athlete.id.clone(),
        date,
        Sport::Bike,
        spec.name.clone(),
        duration,
        tss,
        intensity,
    );

    activity.avg_hr = Some(avg_hr);
    activity.max_hr = Some(max_hr);
    activity.hr_zones = Some(hr_zones);
    activity.avg_power = Some(avg_power);
    activity.normalized_power = Some(normalized_power);
    activity.distance_km = Some(distance_km);
    activity.avg_speed_kph = Some(avg_speed);
    activity.work_kilojoules = Some(work_kj);
    activity.elevation_gain = Some(elevation_gain.max(0.0));
    activity.intensity_variability = Some(variability);

    activity
}

/// Generate a run activity.
fn generate_run_activity<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    date: chrono::NaiveDate,
    spec: &crate::training::WorkoutSpec,
) -> Activity {
    let duration = spec.duration_minutes;
    let intensity = spec.intensity_factor;

    // Calculate TSS
    let tss = intensity.powi(2) * (duration / 60.0) * 100.0;

    // Generate HR series
    let hr_series = generate_hr_series(rng, athlete, duration, intensity);
    let (avg_hr, max_hr) = series_stats(&hr_series);
    let hr_zones = calculate_hr_zone_distribution(&hr_series, athlete);

    // Calculate pace (threshold pace adjusted by intensity)
    let avg_pace = athlete.run_threshold_pace / intensity.max(0.5);
    let distance_km = duration / avg_pace;
    let avg_speed = distance_km / (duration / 60.0);

    // Training effects
    let training_effect_aerobic = (intensity * 3.0 + rng.gen_range(-0.5..0.5)).clamp(1.0, 5.0);
    let training_effect_anaerobic = if intensity > 0.85 {
        (intensity * 2.5 + rng.gen_range(-0.3..0.3)).clamp(0.0, 5.0)
    } else {
        rng.gen_range(0.0..1.0)
    };

    let mut activity = Activity::new(
        athlete.id.clone(),
        date,
        Sport::Run,
        spec.name.clone(),
        duration,
        tss,
        intensity,
    );

    activity.avg_hr = Some(avg_hr);
    activity.max_hr = Some(max_hr);
    activity.hr_zones = Some(hr_zones);
    activity.distance_km = Some(distance_km);
    activity.avg_speed_kph = Some(avg_speed);
    activity.avg_pace_min_km = Some(avg_pace);
    activity.training_effect_aerobic = Some(training_effect_aerobic);
    activity.training_effect_anaerobic = Some(training_effect_anaerobic);

    activity
}

/// Generate a strength activity.
fn generate_strength_activity<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    date: chrono::NaiveDate,
    spec: &crate::training::WorkoutSpec,
) -> Activity {
    let duration = spec.duration_minutes;
    let intensity = spec.intensity_factor;

    // Strength TSS is typically lower
    let tss = intensity.powi(2) * (duration / 60.0) * 50.0;

    // Generate HR series (lower and more variable for strength)
    let mut hr_series = generate_hr_series(rng, athlete, duration, intensity * 0.7);
    // Add rest periods (drops in HR)
    for (i, hr) in hr_series.iter_mut().enumerate() {
        if i % 8 < 3 { // Rest between sets
            *hr *= 0.8;
        }
    }
    let (avg_hr, max_hr) = series_stats(&hr_series);

    let mut activity = Activity::new(
        athlete.id.clone(),
        date,
        Sport::Strength,
        spec.name.clone(),
        duration,
        tss,
        intensity,
    );

    activity.avg_hr = Some(avg_hr);
    activity.max_hr = Some(max_hr);

    activity
}
