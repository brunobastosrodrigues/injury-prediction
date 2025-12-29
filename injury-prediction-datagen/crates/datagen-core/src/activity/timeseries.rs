//! Time-series data generation for activities.

use rand::prelude::*;
use rand_distr::{Distribution, Normal};

use crate::athlete::Athlete;

/// Generate heart rate time series for an activity.
pub fn generate_hr_series<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    duration_minutes: f64,
    intensity_factor: f64,
) -> Vec<f64> {
    let n_points = (duration_minutes * 4.0) as usize; // 15-second intervals
    let mut hr_series = Vec::with_capacity(n_points);

    // Target HR based on intensity
    let target_hr = athlete.resting_hr +
        (athlete.max_hr - athlete.resting_hr) * intensity_factor;

    let noise_dist = Normal::new(0.0, 2.0).unwrap();

    for i in 0..n_points {
        let progress = i as f64 / n_points as f64;

        // Warm-up effect (first 10 minutes)
        let warmup_factor = if progress < 0.1 {
            0.7 + progress * 3.0
        } else {
            1.0
        };

        // Fatigue effect (last 20%)
        let fatigue_factor = if progress > 0.8 {
            1.0 + (progress - 0.8) * 0.1
        } else {
            1.0
        };

        let hr = target_hr * warmup_factor * fatigue_factor + noise_dist.sample(rng);
        hr_series.push(hr.clamp(athlete.resting_hr, athlete.max_hr));
    }

    hr_series
}

/// Generate power time series for cycling.
pub fn generate_power_series<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    duration_minutes: f64,
    intensity_factor: f64,
) -> Vec<f64> {
    let n_points = (duration_minutes * 4.0) as usize;
    let mut power_series = Vec::with_capacity(n_points);

    let target_power = athlete.ftp * intensity_factor;
    let noise_dist = Normal::new(0.0, target_power * 0.1).unwrap();

    for i in 0..n_points {
        let progress = i as f64 / n_points as f64;

        // Power variation throughout ride
        let variation = ((progress * 10.0).sin() * 0.05 + 1.0);

        let power = target_power * variation + noise_dist.sample(rng);
        power_series.push(power.max(0.0));
    }

    power_series
}

/// Calculate statistics from a time series.
pub fn series_stats(series: &[f64]) -> (f64, f64) {
    if series.is_empty() {
        return (0.0, 0.0);
    }

    let sum: f64 = series.iter().sum();
    let avg = sum / series.len() as f64;
    let max = series.iter().cloned().fold(f64::MIN, f64::max);

    (avg, max)
}

/// Calculate zone distribution from HR series.
pub fn calculate_hr_zone_distribution(series: &[f64], athlete: &Athlete) -> std::collections::HashMap<String, f64> {
    use std::collections::HashMap;

    let mut zone_counts = HashMap::new();
    for zone in 1..=6 {
        zone_counts.insert(format!("Z{}", zone), 0.0);
    }

    if series.is_empty() {
        return zone_counts;
    }

    for &hr in series {
        let zone = athlete.hr_zones.zone_for_hr(hr);
        let key = format!("Z{}", zone);
        *zone_counts.get_mut(&key).unwrap() += 1.0;
    }

    // Convert to percentages
    let total = series.len() as f64;
    for (_, count) in zone_counts.iter_mut() {
        *count = (*count / total) * 100.0;
    }

    zone_counts
}

/// Calculate normalized power from power series.
pub fn calculate_normalized_power(series: &[f64]) -> f64 {
    if series.len() < 30 {
        return series_stats(series).0;
    }

    // 30-second rolling average
    let window_size = 30 * 4; // 30 seconds at 4 samples/second
    let mut rolling_avg = Vec::new();

    for i in 0..series.len() {
        let start = if i >= window_size { i - window_size } else { 0 };
        let window: Vec<_> = series[start..=i].to_vec();
        let avg = window.iter().sum::<f64>() / window.len() as f64;
        rolling_avg.push(avg);
    }

    // Fourth power average, then fourth root
    let fourth_power_avg = rolling_avg.iter()
        .map(|&p| p.powi(4))
        .sum::<f64>() / rolling_avg.len() as f64;

    fourth_power_avg.powf(0.25)
}
