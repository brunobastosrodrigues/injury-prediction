//! Activity data types.

use chrono::NaiveDate;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use crate::training::Sport;

/// Completed activity record.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Activity {
    pub athlete_id: String,
    pub date: NaiveDate,
    pub sport: Sport,
    pub workout_type: String,
    pub duration_minutes: f64,
    pub tss: f64,
    pub intensity_factor: f64,

    // Heart rate metrics
    pub avg_hr: Option<f64>,
    pub max_hr: Option<f64>,
    pub hr_zones: Option<HashMap<String, f64>>,

    // Distance/speed
    pub distance_km: Option<f64>,
    pub avg_speed_kph: Option<f64>,

    // Cycling specific
    pub avg_power: Option<f64>,
    pub normalized_power: Option<f64>,
    pub power_zones: Option<HashMap<String, f64>>,
    pub intensity_variability: Option<f64>,
    pub work_kilojoules: Option<f64>,
    pub elevation_gain: Option<f64>,

    // Running specific
    pub avg_pace_min_km: Option<f64>,
    pub training_effect_aerobic: Option<f64>,
    pub training_effect_anaerobic: Option<f64>,

    // Swimming specific
    pub distance_m: Option<f64>,
    pub avg_pace_min_100m: Option<f64>,
}

impl Activity {
    /// Create a new activity with required fields.
    pub fn new(
        athlete_id: String,
        date: NaiveDate,
        sport: Sport,
        workout_type: String,
        duration_minutes: f64,
        tss: f64,
        intensity_factor: f64,
    ) -> Self {
        Self {
            athlete_id,
            date,
            sport,
            workout_type,
            duration_minutes,
            tss,
            intensity_factor,
            avg_hr: None,
            max_hr: None,
            hr_zones: None,
            distance_km: None,
            avg_speed_kph: None,
            avg_power: None,
            normalized_power: None,
            power_zones: None,
            intensity_variability: None,
            work_kilojoules: None,
            elevation_gain: None,
            avg_pace_min_km: None,
            training_effect_aerobic: None,
            training_effect_anaerobic: None,
            distance_m: None,
            avg_pace_min_100m: None,
        }
    }
}
