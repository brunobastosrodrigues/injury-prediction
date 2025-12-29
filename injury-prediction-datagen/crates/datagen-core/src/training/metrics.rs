//! Fitness-fatigue model calculations (CTL, ATL, TSB, ACWR).

use crate::config::TrainingModelConfig;

/// Training state tracking fitness and fatigue.
#[derive(Debug, Clone)]
pub struct TrainingState {
    /// TSS history (last 28 days)
    pub tss_history: Vec<f64>,
    /// HRV history (last 28 days)
    pub hrv_history: Vec<f64>,
    /// Chronic Training Load (fitness)
    pub ctl: f64,
    /// Acute Training Load (fatigue)
    pub atl: f64,
    /// Training Stress Balance (form)
    pub tsb: f64,
    /// Acute:Chronic Workload Ratio
    pub acwr: f64,
    /// Configuration for time constants
    config: TrainingModelConfig,
}

impl Default for TrainingState {
    fn default() -> Self {
        Self::with_config(TrainingModelConfig::default())
    }
}

impl TrainingState {
    /// Create new training state with configuration.
    pub fn with_config(config: TrainingModelConfig) -> Self {
        Self {
            tss_history: vec![0.0; config.acwr_chronic_window],
            hrv_history: vec![60.0; config.acwr_chronic_window],
            ctl: 0.0,
            atl: 0.0,
            tsb: 0.0,
            acwr: 1.0,
            config,
        }
    }

    /// Create new training state with initial baseline.
    pub fn new(initial_ctl: f64, initial_hrv: f64) -> Self {
        Self::new_with_config(initial_ctl, initial_hrv, TrainingModelConfig::default())
    }

    /// Create new training state with initial baseline and configuration.
    pub fn new_with_config(initial_ctl: f64, initial_hrv: f64, config: TrainingModelConfig) -> Self {
        let chronic_window = config.acwr_chronic_window;
        Self {
            tss_history: vec![initial_ctl * 0.8; chronic_window],
            hrv_history: vec![initial_hrv; chronic_window],
            ctl: initial_ctl,
            atl: initial_ctl * 0.9,
            tsb: initial_ctl * 0.1,
            acwr: 1.0,
            config,
        }
    }

    /// Update state with new daily TSS.
    pub fn update(&mut self, daily_tss: f64, daily_hrv: f64) {
        // Update histories (sliding window)
        self.tss_history.remove(0);
        self.tss_history.push(daily_tss);

        self.hrv_history.remove(0);
        self.hrv_history.push(daily_hrv);

        // Calculate CTL using configurable time constant
        // CTL = CTL_yesterday + (TSS_today - CTL_yesterday) / time_constant
        self.ctl = self.ctl + (daily_tss - self.ctl) / self.config.ctl_time_constant;

        // Calculate ATL using configurable time constant
        self.atl = self.atl + (daily_tss - self.atl) / self.config.atl_time_constant;

        // Calculate TSB (Form)
        self.tsb = self.ctl - self.atl;

        // Calculate ACWR using configurable windows
        let acute_window = self.config.acwr_acute_window;
        let chronic_window = self.config.acwr_chronic_window;

        let acute_load: f64 = self.tss_history.iter().rev().take(acute_window).sum::<f64>()
            / acute_window as f64;
        let chronic_load: f64 = self.tss_history.iter().sum::<f64>()
            / chronic_window as f64;

        self.acwr = if chronic_load > 0.0 {
            acute_load / chronic_load
        } else {
            1.0
        };
    }

    /// Get 7-day rolling average TSS.
    pub fn rolling_tss_7day(&self) -> f64 {
        let window = self.config.acwr_acute_window.min(self.tss_history.len());
        self.tss_history.iter().rev().take(window).sum::<f64>() / window as f64
    }

    /// Get chronic window rolling average TSS.
    pub fn rolling_tss_chronic(&self) -> f64 {
        self.tss_history.iter().sum::<f64>() / self.tss_history.len() as f64
    }

    /// Get 7-day rolling average HRV.
    pub fn rolling_hrv_7day(&self) -> f64 {
        let window = self.config.acwr_acute_window.min(self.hrv_history.len());
        self.hrv_history.iter().rev().take(window).sum::<f64>() / window as f64
    }

    /// Check if ACWR is in "danger zone" (>1.5 or sudden spike).
    pub fn is_acwr_risky(&self) -> bool {
        self.acwr > 1.5 || self.acwr < 0.8
    }

    /// Get ACWR risk category.
    pub fn acwr_risk_category(&self) -> &'static str {
        if self.acwr < 0.8 {
            "undertrained"
        } else if self.acwr <= 1.0 {
            "optimal_low"
        } else if self.acwr <= 1.3 {
            "optimal_high"
        } else if self.acwr <= 1.5 {
            "caution"
        } else {
            "danger"
        }
    }

    /// Get the configuration.
    pub fn config(&self) -> &TrainingModelConfig {
        &self.config
    }
}

/// Initialize TSS history for a new athlete based on their training level.
pub fn initialize_tss_history(weekly_training_hours: f64, recovery_rate: f64, config: &TrainingModelConfig) -> Vec<f64> {
    let avg_daily_tss = weekly_training_hours * config.tss_per_hour / 7.0 * recovery_rate;
    let chronic_window = config.acwr_chronic_window;

    (0..chronic_window)
        .map(|i| {
            // Add some variation to historical data
            let day_of_week = i % 7;
            let day_mult = match day_of_week {
                0 => 0.3,  // Rest day
                1 => 1.0,
                2 => 1.1,
                3 => 0.9,
                4 => 0.8,
                5 => 1.3,  // Long day
                6 => 1.0,
                _ => 1.0,
            };
            avg_daily_tss * day_mult
        })
        .collect()
}

/// Initialize TSS history with default config.
pub fn initialize_tss_history_default(weekly_training_hours: f64, recovery_rate: f64) -> Vec<f64> {
    initialize_tss_history(weekly_training_hours, recovery_rate, &TrainingModelConfig::default())
}

/// Initialize HRV history for a new athlete.
pub fn initialize_hrv_history(hrv_baseline: f64, hrv_range: (f64, f64), config: &TrainingModelConfig) -> Vec<f64> {
    let chronic_window = config.acwr_chronic_window;

    (0..chronic_window)
        .map(|i| {
            // Slight variation day to day
            let variation = ((i as f64 * 0.3).sin() * 0.05 + 1.0);
            (hrv_baseline * variation).clamp(hrv_range.0, hrv_range.1)
        })
        .collect()
}

/// Initialize HRV history with default config.
pub fn initialize_hrv_history_default(hrv_baseline: f64, hrv_range: (f64, f64)) -> Vec<f64> {
    initialize_hrv_history(hrv_baseline, hrv_range, &TrainingModelConfig::default())
}
