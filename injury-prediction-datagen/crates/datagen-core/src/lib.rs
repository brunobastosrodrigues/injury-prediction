//! Core library for synthetic triathlete data generation.
//!
//! This crate provides high-performance data generation for injury prediction
//! research, producing synthetic athlete profiles, training plans, daily metrics,
//! and activity data.

pub mod athlete;
pub mod config;
pub mod training;
pub mod simulation;
pub mod activity;
pub mod injury;
pub mod physiology;
pub mod output;

use anyhow::Result;
use rayon::prelude::*;
use std::path::Path;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;

pub use athlete::Athlete;
pub use config::{SimulationParams, InjuryModelConfig, TrainingModelConfig, AthleteConfig};
pub use training::{AnnualPlan, TrainingDay};
pub use simulation::{DailyMetrics, SimulationResult, AthleteSimulationResult};
pub use activity::Activity;

/// Configuration for the data generation process.
#[derive(Debug, Clone)]
pub struct SimulationConfig {
    /// Number of athletes to generate
    pub n_athletes: usize,
    /// Simulation year (e.g., 2024)
    pub year: i32,
    /// Random seed for reproducibility
    pub seed: u64,
    /// Number of threads (0 = auto-detect)
    pub threads: usize,
    /// Model parameters (injury thresholds, training constants, etc.)
    pub params: SimulationParams,
}

impl Default for SimulationConfig {
    fn default() -> Self {
        Self {
            n_athletes: 100,
            year: 2024,
            seed: 42,
            threads: 0,
            params: SimulationParams::default(),
        }
    }
}

/// Generate a complete dataset with parallel processing.
///
/// # Arguments
/// * `config` - Simulation configuration
/// * `progress_callback` - Optional callback for progress updates (completed, total)
///
/// # Returns
/// Complete simulation results for all athletes
pub fn generate_dataset_parallel<F>(
    config: &SimulationConfig,
    progress_callback: Option<F>,
) -> Result<SimulationResult>
where
    F: Fn(usize, usize) + Sync,
{
    // Configure thread pool if specified
    if config.threads > 0 {
        rayon::ThreadPoolBuilder::new()
            .num_threads(config.threads)
            .build_global()
            .ok(); // Ignore if already initialized
    }

    let completed = Arc::new(AtomicUsize::new(0));
    let params = Arc::new(config.params.clone());

    // Generate athletes in parallel
    let athletes: Vec<Athlete> = (0..config.n_athletes)
        .into_par_iter()
        .map(|i| {
            let athlete_seed = config.seed.wrapping_add(i as u64);
            athlete::generate_athlete_profile_with_config(athlete_seed, &params.athlete)
        })
        .collect();

    // Simulate each athlete's year in parallel
    let params_clone = params.clone();
    let results: Vec<AthleteSimulationResult> = athletes
        .into_par_iter()
        .map(|athlete| {
            let result = simulation::simulate_full_year_with_config(
                &athlete,
                config.year,
                config.seed,
                &params_clone,
            );

            // Progress tracking
            let prev = completed.fetch_add(1, Ordering::SeqCst);
            if let Some(ref callback) = progress_callback {
                callback(prev + 1, config.n_athletes);
            }

            result
        })
        .collect();

    Ok(SimulationResult { results })
}

/// Write simulation results to Parquet files.
pub fn write_to_parquet(result: &SimulationResult, output_dir: &Path) -> Result<()> {
    output::write_all(result, output_dir)
}
