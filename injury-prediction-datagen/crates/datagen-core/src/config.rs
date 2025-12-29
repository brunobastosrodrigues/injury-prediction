//! Configuration for data generation models.
//!
//! This module provides runtime configuration for injury models, training parameters,
//! and other simulation settings, allowing experimentation without recompilation.

use serde::{Deserialize, Serialize};

/// Complete configuration for the simulation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimulationParams {
    /// Injury model configuration
    #[serde(default)]
    pub injury: InjuryModelConfig,

    /// Training/fitness-fatigue model configuration
    #[serde(default)]
    pub training: TrainingModelConfig,

    /// Athlete generation configuration
    #[serde(default)]
    pub athlete: AthleteConfig,
}

impl Default for SimulationParams {
    fn default() -> Self {
        Self {
            injury: InjuryModelConfig::default(),
            training: TrainingModelConfig::default(),
            athlete: AthleteConfig::default(),
        }
    }
}

/// Configuration for the injury probability model.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct InjuryModelConfig {
    // === ACWR Thresholds ===
    /// ACWR threshold for danger zone (default: 1.5)
    pub acwr_danger_threshold: f64,
    /// ACWR threshold for caution zone (default: 1.3)
    pub acwr_caution_threshold: f64,
    /// ACWR threshold for undertrained zone (default: 0.8)
    pub acwr_undertrained_threshold: f64,

    // === Base Probabilities ===
    /// Base injury probability per day (default: 0.005 = 0.5%)
    pub base_injury_probability: f64,
    /// Maximum injury probability cap (default: 0.30 = 30%)
    pub max_injury_probability: f64,

    // === Risk Multipliers ===
    /// Multiplier for ACWR danger zone risk (default: 0.15)
    pub acwr_danger_multiplier: f64,
    /// Multiplier for ACWR caution zone risk (default: 0.05)
    pub acwr_caution_multiplier: f64,
    /// Multiplier for undertrained risk (default: 0.03)
    pub acwr_undertrained_multiplier: f64,

    // === Fatigue Thresholds ===
    /// ATL threshold for high fatigue risk (default: 120.0)
    pub fatigue_high_threshold: f64,
    /// ATL threshold for moderate fatigue risk (default: 100.0)
    pub fatigue_moderate_threshold: f64,

    // === Form (TSB) Thresholds ===
    /// TSB threshold for high form risk (default: -30.0)
    pub form_high_risk_threshold: f64,
    /// TSB threshold for moderate form risk (default: -20.0)
    pub form_moderate_risk_threshold: f64,

    // === Load Spike Thresholds ===
    /// Ratio threshold for high spike risk (default: 2.0)
    pub spike_high_threshold: f64,
    /// Ratio threshold for moderate spike risk (default: 1.5)
    pub spike_moderate_threshold: f64,
}

impl Default for InjuryModelConfig {
    fn default() -> Self {
        Self {
            // ACWR thresholds (based on Gabbett 2016)
            acwr_danger_threshold: 1.5,
            acwr_caution_threshold: 1.3,
            acwr_undertrained_threshold: 0.8,

            // Base probabilities
            base_injury_probability: 0.005,
            max_injury_probability: 0.30,

            // Risk multipliers
            acwr_danger_multiplier: 0.15,
            acwr_caution_multiplier: 0.05,
            acwr_undertrained_multiplier: 0.03,

            // Fatigue thresholds
            fatigue_high_threshold: 120.0,
            fatigue_moderate_threshold: 100.0,

            // Form thresholds
            form_high_risk_threshold: -30.0,
            form_moderate_risk_threshold: -20.0,

            // Spike thresholds
            spike_high_threshold: 2.0,
            spike_moderate_threshold: 1.5,
        }
    }
}

/// Configuration for the fitness-fatigue (training load) model.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct TrainingModelConfig {
    /// Time constant for Chronic Training Load (CTL) in days (default: 42)
    pub ctl_time_constant: f64,
    /// Time constant for Acute Training Load (ATL) in days (default: 7)
    pub atl_time_constant: f64,

    /// Window size for acute load calculation in ACWR (default: 7)
    pub acwr_acute_window: usize,
    /// Window size for chronic load calculation in ACWR (default: 28)
    pub acwr_chronic_window: usize,

    /// Average TSS per hour of training (default: 60.0)
    pub tss_per_hour: f64,
}

impl Default for TrainingModelConfig {
    fn default() -> Self {
        Self {
            ctl_time_constant: 42.0,
            atl_time_constant: 7.0,
            acwr_acute_window: 7,
            acwr_chronic_window: 28,
            tss_per_hour: 60.0,
        }
    }
}

/// Configuration for athlete generation.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct AthleteConfig {
    /// Minimum age for generated athletes (default: 18)
    pub min_age: u32,
    /// Maximum age for generated athletes (default: 55)
    pub max_age: u32,

    /// Minimum weekly training hours (default: 5.0)
    pub min_weekly_hours: f64,
    /// Maximum weekly training hours (default: 25.0)
    pub max_weekly_hours: f64,

    /// Probability of female athlete (default: 0.35)
    pub female_probability: f64,
}

impl Default for AthleteConfig {
    fn default() -> Self {
        Self {
            min_age: 18,
            max_age: 55,
            min_weekly_hours: 5.0,
            max_weekly_hours: 25.0,
            female_probability: 0.35,
        }
    }
}

impl SimulationParams {
    /// Create from JSON string.
    pub fn from_json(json: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(json)
    }

    /// Serialize to JSON string.
    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(self)
    }

    /// Create from a JSON file.
    pub fn from_file(path: &std::path::Path) -> anyhow::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        Ok(Self::from_json(&content)?)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = SimulationParams::default();
        assert_eq!(config.injury.acwr_danger_threshold, 1.5);
        assert_eq!(config.training.ctl_time_constant, 42.0);
    }

    #[test]
    fn test_json_roundtrip() {
        let config = SimulationParams::default();
        let json = config.to_json().unwrap();
        let parsed = SimulationParams::from_json(&json).unwrap();
        assert_eq!(parsed.injury.acwr_danger_threshold, config.injury.acwr_danger_threshold);
    }
}
