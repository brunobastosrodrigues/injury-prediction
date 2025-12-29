//! Athlete data types and structures.

use serde::{Deserialize, Serialize};

/// Gender of the athlete.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Gender {
    Male,
    Female,
}

impl Gender {
    pub fn as_str(&self) -> &'static str {
        match self {
            Gender::Male => "male",
            Gender::Female => "female",
        }
    }
}

/// Athletic specialization in triathlon.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Specialization {
    SwimStrong,
    BikeStrong,
    RunStrong,
    Balanced,
}

impl Specialization {
    pub fn as_str(&self) -> &'static str {
        match self {
            Specialization::SwimStrong => "swim_strong",
            Specialization::BikeStrong => "bike_strong",
            Specialization::RunStrong => "run_strong",
            Specialization::Balanced => "balanced",
        }
    }
}

/// Chronotype (sleep preference).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Chronotype {
    Lark,        // Early bird
    Owl,         // Night owl
    Intermediate,
}

impl Chronotype {
    pub fn as_str(&self) -> &'static str {
        match self {
            Chronotype::Lark => "lark",
            Chronotype::Owl => "owl",
            Chronotype::Intermediate => "intermediate",
        }
    }
}

/// Sensor device profile.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum SensorProfile {
    Garmin,
    Optical,
}

impl SensorProfile {
    pub fn as_str(&self) -> &'static str {
        match self {
            SensorProfile::Garmin => "garmin",
            SensorProfile::Optical => "optical",
        }
    }
}

/// Recovery profile type.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RecoveryProfile {
    HrvDominant,
    SleepDominant,
    RhrDominant,
    StressDominant,
    Balanced,
}

impl RecoveryProfile {
    pub fn as_str(&self) -> &'static str {
        match self {
            RecoveryProfile::HrvDominant => "hrv_dominant",
            RecoveryProfile::SleepDominant => "sleep_dominant",
            RecoveryProfile::RhrDominant => "rhr_dominant",
            RecoveryProfile::StressDominant => "stress_dominant",
            RecoveryProfile::Balanced => "balanced",
        }
    }
}

/// Heart rate zone boundaries (lower, upper) in BPM.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HeartRateZones {
    pub z1: (f64, f64),  // Recovery
    pub z2: (f64, f64),  // Endurance
    pub z3: (f64, f64),  // Tempo
    pub z4: (f64, f64),  // Threshold
    pub z5: (f64, f64),  // VO2 Max
    pub z6: (f64, f64),  // Anaerobic
}

impl HeartRateZones {
    /// Get zone by number (1-6).
    pub fn get_zone(&self, zone: u8) -> Option<(f64, f64)> {
        match zone {
            1 => Some(self.z1),
            2 => Some(self.z2),
            3 => Some(self.z3),
            4 => Some(self.z4),
            5 => Some(self.z5),
            6 => Some(self.z6),
            _ => None,
        }
    }

    /// Determine which zone a heart rate falls into.
    pub fn zone_for_hr(&self, hr: f64) -> u8 {
        if hr <= self.z1.1 { 1 }
        else if hr <= self.z2.1 { 2 }
        else if hr <= self.z3.1 { 3 }
        else if hr <= self.z4.1 { 4 }
        else if hr <= self.z5.1 { 5 }
        else { 6 }
    }
}

/// Power zone boundaries (lower, upper) in watts.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PowerZones {
    pub z1: (f64, f64),  // Active Recovery
    pub z2: (f64, f64),  // Endurance
    pub z3: (f64, f64),  // Tempo
    pub z4: (f64, f64),  // Threshold
    pub z5: (f64, f64),  // VO2 Max
    pub z6: (f64, f64),  // Anaerobic Capacity
}

impl PowerZones {
    /// Get zone by number (1-6).
    pub fn get_zone(&self, zone: u8) -> Option<(f64, f64)> {
        match zone {
            1 => Some(self.z1),
            2 => Some(self.z2),
            3 => Some(self.z3),
            4 => Some(self.z4),
            5 => Some(self.z5),
            6 => Some(self.z6),
            _ => None,
        }
    }

    /// Determine which zone a power value falls into.
    pub fn zone_for_power(&self, power: f64) -> u8 {
        if power <= self.z1.1 { 1 }
        else if power <= self.z2.1 { 2 }
        else if power <= self.z3.1 { 3 }
        else if power <= self.z4.1 { 4 }
        else if power <= self.z5.1 { 5 }
        else { 6 }
    }
}

/// Lifestyle profile name.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LifestyleProfile {
    pub name: String,
    pub sleep_hours: f64,
    pub sleep_quality: f64,
    pub nutrition: f64,
    pub stress: f64,
    pub smoking: f64,
    pub drinking: f64,
    pub exercise: f64,
}

/// Recovery sensitivity signature.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecoverySignature {
    pub hrv_sensitivity: f64,
    pub sleep_sensitivity: f64,
    pub rhr_sensitivity: f64,
    pub stress_sensitivity: f64,
}

/// Menstrual cycle configuration (for female athletes).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MenstrualCycleConfig {
    pub cycle_length: u8,
    pub regularity: f64,
    pub luteal_phase_length: u8,
}

/// Complete athlete profile.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Athlete {
    // Identity
    pub id: String,
    pub gender: Gender,
    pub age: u8,

    // Physical attributes
    pub height_cm: f64,
    pub weight_kg: f64,
    pub genetic_factor: f64,

    // Heart rate metrics
    pub hrv_baseline: f64,
    pub hrv_range: (f64, f64),
    pub max_hr: f64,
    pub resting_hr: f64,
    pub lthr: f64,  // Lactate threshold HR
    pub hr_zones: HeartRateZones,

    // Performance metrics
    pub vo2max: f64,
    pub ftp: f64,  // Functional threshold power
    pub power_zones: PowerZones,
    pub css: f64,  // Critical swim speed (s/100m)
    pub run_threshold_pace: f64,  // min/km

    // Training profile
    pub training_experience: u8,  // years
    pub weekly_training_hours: f64,
    pub recovery_rate: f64,
    pub specialization: Specialization,

    // Lifestyle factors
    pub lifestyle: LifestyleProfile,
    pub recovery_profile: RecoveryProfile,
    pub recovery_signature: RecoverySignature,

    // Device/sensor profile
    pub sensor_profile: SensorProfile,
    pub chronotype: Chronotype,

    // Female-specific
    pub menstrual_cycle_config: Option<MenstrualCycleConfig>,
}

impl Athlete {
    /// Check if athlete is female.
    pub fn is_female(&self) -> bool {
        self.gender == Gender::Female
    }

    /// Get heart rate reserve (HRR).
    pub fn heart_rate_reserve(&self) -> f64 {
        self.max_hr - self.resting_hr
    }

    /// Calculate target HR at given percentage of max.
    pub fn target_hr_percent(&self, percent: f64) -> f64 {
        self.resting_hr + (self.max_hr - self.resting_hr) * percent
    }

    /// Get power-to-weight ratio (W/kg).
    pub fn power_to_weight(&self) -> f64 {
        self.ftp / self.weight_kg
    }
}
