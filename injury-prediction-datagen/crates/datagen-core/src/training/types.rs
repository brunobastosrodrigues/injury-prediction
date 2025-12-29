//! Training plan data types.

use chrono::NaiveDate;
use serde::{Deserialize, Serialize};

/// Training phase in periodization.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TrainingPhase {
    Base,
    Build,
    Peak,
    RacePrep,
    Race,
    Taper,
    Recovery,
    OffSeason,
    Transition,
}

impl TrainingPhase {
    pub fn as_str(&self) -> &'static str {
        match self {
            TrainingPhase::Base => "base",
            TrainingPhase::Build => "build",
            TrainingPhase::Peak => "peak",
            TrainingPhase::RacePrep => "race_prep",
            TrainingPhase::Race => "race",
            TrainingPhase::Taper => "taper",
            TrainingPhase::Recovery => "recovery",
            TrainingPhase::OffSeason => "off_season",
            TrainingPhase::Transition => "transition",
        }
    }
}

/// Sport type.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Sport {
    Swim,
    Bike,
    Run,
    Strength,
}

impl Sport {
    pub fn as_str(&self) -> &'static str {
        match self {
            Sport::Swim => "swim",
            Sport::Bike => "bike",
            Sport::Run => "run",
            Sport::Strength => "strength",
        }
    }
}

/// Workout specification.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkoutSpec {
    pub name: String,
    pub sport: Sport,
    pub duration_minutes: f64,
    pub tss_per_hour: f64,
    pub intensity_factor: f64,
}

/// Daily training plan.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingDay {
    pub date: NaiveDate,
    pub day_of_week: u8,
    pub week_number: u8,
    pub phase: TrainingPhase,

    // TSS targets
    pub total_tss: f64,
    pub swim_tss: f64,
    pub bike_tss: f64,
    pub run_tss: f64,
    pub strength_tss: f64,

    // Workout specifications
    pub swim_workout: Option<WorkoutSpec>,
    pub bike_workout: Option<WorkoutSpec>,
    pub run_workout: Option<WorkoutSpec>,
    pub strength_workout: Option<WorkoutSpec>,

    pub is_rest_day: bool,
    pub is_race_day: bool,
}

/// Annual training plan.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnnualPlan {
    pub days: Vec<TrainingDay>,
    pub race_dates: Vec<NaiveDate>,
}

impl AnnualPlan {
    /// Get training day for a specific date.
    pub fn get_day(&self, date: NaiveDate) -> Option<&TrainingDay> {
        self.days.iter().find(|d| d.date == date)
    }
}
