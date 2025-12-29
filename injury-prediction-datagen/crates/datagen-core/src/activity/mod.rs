//! Activity simulation and wearable data generation.

mod types;
mod generator;
mod physics;
mod timeseries;

pub use types::*;
pub use generator::generate_activities;
pub use physics::solve_cycling_speed;
