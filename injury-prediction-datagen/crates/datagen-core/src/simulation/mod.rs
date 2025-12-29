//! Simulation orchestration module.

mod types;
mod daily;
mod year;

pub use types::*;
pub use daily::{simulate_daily_metrics, simulate_daily_metrics_with_config};
pub use year::{simulate_full_year, simulate_full_year_with_config};
