//! CLI for synthetic triathlete data generation.

use anyhow::Result;
use clap::Parser;
use datagen_core::{generate_dataset_parallel, write_to_parquet, SimulationConfig, SimulationParams};
use indicatif::{ProgressBar, ProgressStyle};
use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use tracing_subscriber::EnvFilter;

/// Generate synthetic triathlete training data for injury prediction.
#[derive(Parser, Debug)]
#[command(name = "datagen")]
#[command(version = "0.1.0")]
#[command(about = "Generate synthetic triathlete training data")]
struct Args {
    /// Number of athletes to generate
    #[arg(short, long, default_value_t = 100)]
    n_athletes: usize,

    /// Simulation year
    #[arg(short = 'y', long, default_value_t = 2024)]
    year: i32,

    /// Random seed for reproducibility
    #[arg(short, long, default_value_t = 42)]
    seed: u64,

    /// Output directory for Parquet files
    #[arg(short, long, default_value = "./output")]
    output_dir: PathBuf,

    /// Number of threads (0 = auto-detect)
    #[arg(short, long, default_value_t = 0)]
    threads: usize,

    /// Enable JSON progress reporting to stderr
    #[arg(long)]
    json_progress: bool,

    /// Disable progress bar (useful for non-interactive mode)
    #[arg(long)]
    no_progress: bool,

    /// Verbosity level
    #[arg(short, long, action = clap::ArgAction::Count)]
    verbose: u8,

    // === Injury Model Parameters ===
    /// ACWR danger threshold (default: 1.5)
    #[arg(long, default_value_t = 1.5)]
    acwr_danger: f64,

    /// ACWR caution threshold (default: 1.3)
    #[arg(long, default_value_t = 1.3)]
    acwr_caution: f64,

    /// ACWR undertrained threshold (default: 0.8)
    #[arg(long, default_value_t = 0.8)]
    acwr_undertrained: f64,

    /// Base injury probability per day (default: 0.005)
    #[arg(long, default_value_t = 0.005)]
    base_injury_prob: f64,

    /// Maximum injury probability (default: 0.30)
    #[arg(long, default_value_t = 0.30)]
    max_injury_prob: f64,

    // === Training Model Parameters ===
    /// CTL time constant in days (default: 42)
    #[arg(long, default_value_t = 42.0)]
    ctl_days: f64,

    /// ATL time constant in days (default: 7)
    #[arg(long, default_value_t = 7.0)]
    atl_days: f64,

    /// ACWR acute window in days (default: 7)
    #[arg(long, default_value_t = 7)]
    acwr_acute_window: usize,

    /// ACWR chronic window in days (default: 28)
    #[arg(long, default_value_t = 28)]
    acwr_chronic_window: usize,

    // === Athlete Parameters ===
    /// Minimum athlete age (default: 18)
    #[arg(long, default_value_t = 18)]
    min_age: u32,

    /// Maximum athlete age (default: 55)
    #[arg(long, default_value_t = 55)]
    max_age: u32,

    /// Minimum weekly training hours (default: 5.0)
    #[arg(long, default_value_t = 5.0)]
    min_hours: f64,

    /// Maximum weekly training hours (default: 25.0)
    #[arg(long, default_value_t = 25.0)]
    max_hours: f64,

    /// Probability of female athlete (default: 0.35)
    #[arg(long, default_value_t = 0.35)]
    female_prob: f64,

    /// Load configuration from JSON file (overrides individual params)
    #[arg(long)]
    config_file: Option<PathBuf>,
}

fn main() -> Result<()> {
    let args = Args::parse();

    // Setup logging
    let filter = match args.verbose {
        0 => "warn",
        1 => "info",
        2 => "debug",
        _ => "trace",
    };
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new(filter)))
        .init();

    tracing::info!("Starting data generation");
    tracing::info!("  Athletes: {}", args.n_athletes);
    tracing::info!("  Year: {}", args.year);
    tracing::info!("  Seed: {}", args.seed);
    tracing::info!("  Output: {}", args.output_dir.display());

    // Build configuration
    let params = if let Some(config_path) = &args.config_file {
        tracing::info!("  Loading config from: {}", config_path.display());
        SimulationParams::from_file(config_path)?
    } else {
        build_params_from_args(&args)
    };

    // Log key parameters
    tracing::info!("  ACWR danger threshold: {}", params.injury.acwr_danger_threshold);
    tracing::info!("  Base injury probability: {}", params.injury.base_injury_probability);
    tracing::info!("  CTL time constant: {} days", params.training.ctl_time_constant);

    // Setup progress tracking
    let pb = if !args.no_progress && !args.json_progress {
        let pb = ProgressBar::new(args.n_athletes as u64);
        pb.set_style(
            ProgressStyle::default_bar()
                .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} athletes ({eta})")?
                .progress_chars("#>-")
        );
        Some(pb)
    } else {
        None
    };

    let json_progress = args.json_progress;
    let completed = Arc::new(AtomicUsize::new(0));
    let total = args.n_athletes;

    // Configure simulation
    let config = SimulationConfig {
        n_athletes: args.n_athletes,
        year: args.year,
        seed: args.seed,
        threads: args.threads,
        params,
    };

    // Run generation with progress callback
    let pb_clone = pb.clone();
    let completed_clone = completed.clone();

    let result = generate_dataset_parallel(&config, Some(move |current, _total| {
        if let Some(ref pb) = pb_clone {
            pb.set_position(current as u64);
        }

        if json_progress {
            let prev = completed_clone.fetch_add(1, Ordering::SeqCst);
            if prev + 1 != current {
                completed_clone.store(current, Ordering::SeqCst);
            }
            eprintln!(r#"{{"progress": {}, "total": {}}}"#, current, total);
        }
    }))?;

    if let Some(pb) = pb {
        pb.finish_with_message("Generation complete");
    }

    // Write output
    tracing::info!("Writing output files...");
    std::fs::create_dir_all(&args.output_dir)?;
    write_to_parquet(&result, &args.output_dir)?;

    // Print summary
    println!("\nGeneration complete!");
    println!("  Athletes: {}", result.results.len());
    println!("  Daily records: {}", result.total_daily_records());
    println!("  Activities: {}", result.total_activities());
    println!("  Injury rate: {:.2}%", result.injury_rate());
    println!("  Output: {}", args.output_dir.display());

    Ok(())
}

/// Build SimulationParams from CLI arguments.
fn build_params_from_args(args: &Args) -> SimulationParams {
    use datagen_core::{InjuryModelConfig, TrainingModelConfig, AthleteConfig};

    SimulationParams {
        injury: InjuryModelConfig {
            acwr_danger_threshold: args.acwr_danger,
            acwr_caution_threshold: args.acwr_caution,
            acwr_undertrained_threshold: args.acwr_undertrained,
            base_injury_probability: args.base_injury_prob,
            max_injury_probability: args.max_injury_prob,
            ..InjuryModelConfig::default()
        },
        training: TrainingModelConfig {
            ctl_time_constant: args.ctl_days,
            atl_time_constant: args.atl_days,
            acwr_acute_window: args.acwr_acute_window,
            acwr_chronic_window: args.acwr_chronic_window,
            ..TrainingModelConfig::default()
        },
        athlete: AthleteConfig {
            min_age: args.min_age,
            max_age: args.max_age,
            min_weekly_hours: args.min_hours,
            max_weekly_hours: args.max_hours,
            female_probability: args.female_prob,
        },
    }
}
