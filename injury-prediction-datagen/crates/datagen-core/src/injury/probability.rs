//! Injury probability calculations.

use crate::config::InjuryModelConfig;
use crate::training::TrainingState;
use crate::athlete::Athlete;

/// Calculate injury probability based on ACWR and other factors.
pub fn calculate_injury_probability(
    athlete: &Athlete,
    training_state: &TrainingState,
    actual_tss: f64,
    config: &InjuryModelConfig,
) -> f64 {
    // ZERO-LOAD GUARD: No training = No injury
    // Critical fix: Athletes cannot get injured while resting.
    // This prevents the "Couch Injury" artifact that causes
    // Sim2Real AUC < 0.50 (anti-predictive models).
    if actual_tss <= 0.0 {
        return 0.0;
    }

    // Base injury probability
    let mut injury_prob = config.base_injury_probability;

    // ACWR risk factor (asymmetric model)
    let acwr_risk = calculate_acwr_risk(training_state.acwr, config);

    // Fatigue risk factor
    let fatigue_risk = calculate_fatigue_risk(training_state.atl, config);

    // Form (TSB) risk factor
    let form_risk = calculate_form_risk(training_state.tsb, config);

    // Load spike risk
    let spike_risk = calculate_spike_risk(actual_tss, training_state, config);

    // Recovery rate modifier
    let recovery_modifier = 1.5 - athlete.recovery_rate;

    // Combine risks
    injury_prob += (acwr_risk + fatigue_risk + form_risk + spike_risk) * recovery_modifier;

    // Cap at configured maximum
    injury_prob.clamp(0.0, config.max_injury_probability)
}

/// Calculate injury probability with default config (for backwards compatibility).
pub fn calculate_injury_probability_default(
    athlete: &Athlete,
    training_state: &TrainingState,
    actual_tss: f64,
) -> f64 {
    calculate_injury_probability(athlete, training_state, actual_tss, &InjuryModelConfig::default())
}

/// Calculate risk contribution from ACWR (asymmetric model).
fn calculate_acwr_risk(acwr: f64, config: &InjuryModelConfig) -> f64 {
    if acwr > config.acwr_danger_threshold {
        // High risk zone
        (acwr - config.acwr_danger_threshold) * config.acwr_danger_multiplier
    } else if acwr > config.acwr_caution_threshold {
        // Caution zone
        (acwr - config.acwr_caution_threshold) * config.acwr_caution_multiplier
    } else if acwr < config.acwr_undertrained_threshold {
        // Under-training can also increase risk
        (config.acwr_undertrained_threshold - acwr) * config.acwr_undertrained_multiplier
    } else {
        // Sweet spot
        0.0
    }
}

/// Calculate risk from acute fatigue.
fn calculate_fatigue_risk(atl: f64, config: &InjuryModelConfig) -> f64 {
    if atl > config.fatigue_high_threshold {
        (atl - config.fatigue_high_threshold) / 300.0
    } else if atl > config.fatigue_moderate_threshold {
        (atl - config.fatigue_moderate_threshold) / 500.0
    } else {
        0.0
    }
}

/// Calculate risk from negative form (TSB).
fn calculate_form_risk(tsb: f64, config: &InjuryModelConfig) -> f64 {
    if tsb < config.form_high_risk_threshold {
        (-tsb - (-config.form_high_risk_threshold)) / 150.0
    } else if tsb < config.form_moderate_risk_threshold {
        (-tsb - (-config.form_moderate_risk_threshold)) / 300.0
    } else {
        0.0
    }
}

/// Calculate risk from load spikes (sudden increases).
fn calculate_spike_risk(daily_tss: f64, training_state: &TrainingState, config: &InjuryModelConfig) -> f64 {
    let recent_avg = training_state.rolling_tss_7day();

    if recent_avg > 0.0 {
        let spike_ratio = daily_tss / recent_avg;
        if spike_ratio > config.spike_high_threshold {
            (spike_ratio - config.spike_high_threshold) * 0.05
        } else if spike_ratio > config.spike_moderate_threshold {
            (spike_ratio - config.spike_moderate_threshold) * 0.02
        } else {
            0.0
        }
    } else {
        0.0
    }
}

/// Determine injury type based on contributing factors.
pub fn determine_injury_type(
    acwr_contribution: f64,
    fatigue_contribution: f64,
    form_contribution: f64,
) -> &'static str {
    if acwr_contribution > fatigue_contribution && acwr_contribution > form_contribution {
        "exposure"
    } else if fatigue_contribution > form_contribution {
        "physiological"
    } else {
        "baseline"
    }
}
