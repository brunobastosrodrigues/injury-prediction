//! Sensor noise models.

use rand::prelude::*;
use rand_distr::{Distribution, Normal};

use crate::athlete::SensorProfile;

/// Apply sensor-specific noise to heart rate reading.
pub fn apply_hr_noise<R: Rng>(rng: &mut R, hr: f64, profile: SensorProfile) -> f64 {
    let noise = match profile {
        SensorProfile::Garmin => Normal::new(0.0, 1.0).unwrap().sample(rng),
        SensorProfile::Optical => Normal::new(0.0, 3.0).unwrap().sample(rng), // More noise
    };

    (hr + noise).max(30.0)
}

/// Apply sensor-specific noise to HRV reading.
pub fn apply_hrv_noise<R: Rng>(rng: &mut R, hrv: f64, profile: SensorProfile) -> f64 {
    let noise = match profile {
        SensorProfile::Garmin => Normal::new(0.0, 2.0).unwrap().sample(rng),
        SensorProfile::Optical => Normal::new(0.0, 5.0).unwrap().sample(rng),
    };

    (hrv + noise).max(10.0)
}

/// Apply noise to power meter reading.
pub fn apply_power_noise<R: Rng>(rng: &mut R, power: f64) -> f64 {
    // Power meters are typically ±2% accurate
    let noise = Normal::new(0.0, power * 0.02).unwrap().sample(rng);
    (power + noise).max(0.0)
}
