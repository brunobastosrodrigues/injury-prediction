//! Athlete profile generation module.
//!
//! Generates realistic physiological and performance profiles for synthetic athletes.

mod types;
mod generator;
mod lifestyle;
mod zones;

pub use types::*;
pub use generator::{generate_athlete_profile, generate_athlete_profile_with_config};
