//! Simulation data types.

use chrono::NaiveDate;
use serde::{Deserialize, Serialize};

use crate::athlete::Athlete;
use crate::activity::Activity;

/// Injury type classification.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum InjuryType {
    Physiological,
    Exposure,
    Baseline,
}

impl InjuryType {
    pub fn as_str(&self) -> &'static str {
        match self {
            InjuryType::Physiological => "physiological",
            InjuryType::Exposure => "exposure",
            InjuryType::Baseline => "baseline",
        }
    }
}

/// Daily metrics for an athlete.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DailyMetrics {
    pub athlete_id: String,
    pub date: NaiveDate,

    // Morning metrics
    pub resting_hr: f64,
    pub hrv: f64,
    pub sleep_hours: f64,
    pub deep_sleep: f64,
    pub light_sleep: f64,
    pub rem_sleep: f64,
    pub sleep_quality: f64,
    pub body_battery_morning: f64,

    // Evening metrics
    pub stress: f64,
    pub body_battery_evening: f64,

    // Training metrics
    pub planned_tss: f64,
    pub actual_tss: f64,

    // Fitness-fatigue
    pub ctl: f64,
    pub atl: f64,
    pub tsb: f64,
    pub acwr: f64,

    // Injury tracking
    pub injury: bool,
    pub injury_type: Option<InjuryType>,
    pub injury_probability: f64,
}

/// Complete simulation result for one athlete.
#[derive(Debug, Clone)]
pub struct AthleteSimulationResult {
    pub athlete: Athlete,
    pub daily_metrics: Vec<DailyMetrics>,
    pub activities: Vec<Activity>,
}

impl AthleteSimulationResult {
    /// Get total number of injuries.
    pub fn injury_count(&self) -> usize {
        self.daily_metrics.iter().filter(|d| d.injury).count()
    }

    /// Get injury rate (injuries per 100 days).
    pub fn injury_rate(&self) -> f64 {
        let n_days = self.daily_metrics.len() as f64;
        if n_days > 0.0 {
            (self.injury_count() as f64 / n_days) * 100.0
        } else {
            0.0
        }
    }
}

/// Complete simulation results for all athletes.
#[derive(Debug)]
pub struct SimulationResult {
    pub results: Vec<AthleteSimulationResult>,
}

impl SimulationResult {
    /// Get total number of daily records.
    pub fn total_daily_records(&self) -> usize {
        self.results.iter().map(|r| r.daily_metrics.len()).sum()
    }

    /// Get total number of activities.
    pub fn total_activities(&self) -> usize {
        self.results.iter().map(|r| r.activities.len()).sum()
    }

    /// Get overall injury rate.
    pub fn injury_rate(&self) -> f64 {
        let total_injuries: usize = self.results.iter().map(|r| r.injury_count()).sum();
        let total_days: usize = self.results.iter().map(|r| r.daily_metrics.len()).sum();

        if total_days > 0 {
            (total_injuries as f64 / total_days as f64) * 100.0
        } else {
            0.0
        }
    }

    /// Get all athletes.
    pub fn athletes(&self) -> Vec<&Athlete> {
        self.results.iter().map(|r| &r.athlete).collect()
    }

    /// Get all daily metrics.
    pub fn all_daily_metrics(&self) -> Vec<&DailyMetrics> {
        self.results.iter().flat_map(|r| &r.daily_metrics).collect()
    }

    /// Get all activities.
    pub fn all_activities(&self) -> Vec<&Activity> {
        self.results.iter().flat_map(|r| &r.activities).collect()
    }
}
