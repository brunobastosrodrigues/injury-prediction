//! Training plan generation and fitness-fatigue model.

mod types;
mod plan;
mod metrics;

pub use types::*;
pub use plan::generate_annual_plan;
pub use metrics::*;
