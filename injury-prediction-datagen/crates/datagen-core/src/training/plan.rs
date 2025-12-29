//! Training plan generation.

use chrono::{NaiveDate, Datelike};
use rand::prelude::*;
use rand_chacha::ChaCha8Rng;

use crate::athlete::Athlete;
use super::types::*;

/// Generate an annual training plan for an athlete.
pub fn generate_annual_plan(athlete: &Athlete, year: i32, seed: u64) -> AnnualPlan {
    let mut rng = ChaCha8Rng::seed_from_u64(seed.wrapping_add(athlete.id.as_bytes()[0] as u64));

    let start_date = NaiveDate::from_ymd_opt(year, 1, 1).unwrap();
    let end_date = NaiveDate::from_ymd_opt(year, 12, 31).unwrap();

    // Generate race dates (2-4 races per year)
    let n_races = rng.gen_range(2..=4);
    let mut race_dates = generate_race_dates(&mut rng, year, n_races);
    race_dates.sort();

    let mut days = Vec::with_capacity(366);
    let mut current_date = start_date;

    while current_date <= end_date {
        let day_of_week = current_date.weekday().num_days_from_monday() as u8;
        let week_number = current_date.iso_week().week() as u8;

        // Determine training phase based on proximity to races
        let phase = determine_phase(current_date, &race_dates);

        // Calculate TSS for the day
        let (total_tss, is_rest_day) = calculate_daily_tss(
            &mut rng,
            athlete,
            phase,
            day_of_week,
        );

        let is_race_day = race_dates.contains(&current_date);

        // Distribute TSS across sports
        let (swim_tss, bike_tss, run_tss, strength_tss) = distribute_tss(
            &mut rng,
            athlete,
            total_tss,
            phase,
            is_rest_day,
        );

        // Generate workout specs
        let swim_workout = if swim_tss > 0.0 {
            Some(generate_workout_spec(&mut rng, Sport::Swim, swim_tss, phase))
        } else {
            None
        };

        let bike_workout = if bike_tss > 0.0 {
            Some(generate_workout_spec(&mut rng, Sport::Bike, bike_tss, phase))
        } else {
            None
        };

        let run_workout = if run_tss > 0.0 {
            Some(generate_workout_spec(&mut rng, Sport::Run, run_tss, phase))
        } else {
            None
        };

        let strength_workout = if strength_tss > 0.0 {
            Some(generate_workout_spec(&mut rng, Sport::Strength, strength_tss, phase))
        } else {
            None
        };

        days.push(TrainingDay {
            date: current_date,
            day_of_week,
            week_number,
            phase,
            total_tss,
            swim_tss,
            bike_tss,
            run_tss,
            strength_tss,
            swim_workout,
            bike_workout,
            run_workout,
            strength_workout,
            is_rest_day,
            is_race_day,
        });

        current_date = current_date.succ_opt().unwrap();
    }

    AnnualPlan { days, race_dates }
}

/// Generate race dates spread throughout the year.
fn generate_race_dates<R: Rng>(rng: &mut R, year: i32, n_races: usize) -> Vec<NaiveDate> {
    let mut dates = Vec::with_capacity(n_races);

    // Typical race months: May, June, July, August, September
    let race_months = [5, 6, 7, 8, 9];

    for _ in 0..n_races {
        let month = race_months[rng.gen_range(0..race_months.len())];
        let day = rng.gen_range(1..=28); // Safe for all months

        if let Some(date) = NaiveDate::from_ymd_opt(year, month, day) {
            if !dates.contains(&date) {
                dates.push(date);
            }
        }
    }

    dates
}

/// Determine training phase based on date and race schedule.
fn determine_phase(date: NaiveDate, race_dates: &[NaiveDate]) -> TrainingPhase {
    // Find days until next race
    let days_to_race = race_dates
        .iter()
        .filter(|&&r| r >= date)
        .map(|&r| (r - date).num_days())
        .min();

    let month = date.month();

    match days_to_race {
        Some(0) => TrainingPhase::Race,
        Some(1..=3) => TrainingPhase::RacePrep,
        Some(4..=14) => TrainingPhase::Taper,
        Some(15..=42) => TrainingPhase::Peak,
        Some(43..=84) => TrainingPhase::Build,
        _ => {
            // Off-season in Dec-Jan, Base in Feb-Mar
            match month {
                12 | 1 => TrainingPhase::OffSeason,
                2 | 3 => TrainingPhase::Base,
                10 | 11 => TrainingPhase::Recovery,
                _ => TrainingPhase::Build,
            }
        }
    }
}

/// Calculate daily TSS based on athlete, phase, and day of week.
fn calculate_daily_tss<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    phase: TrainingPhase,
    day_of_week: u8,
) -> (f64, bool) {
    // Weekly TSS based on training hours (rough estimate: ~60 TSS/hour average)
    let weekly_tss = athlete.weekly_training_hours * 60.0;

    // Phase multiplier
    let phase_mult = match phase {
        TrainingPhase::Base => 0.85,
        TrainingPhase::Build => 1.0,
        TrainingPhase::Peak => 1.1,
        TrainingPhase::Taper => 0.5,
        TrainingPhase::RacePrep => 0.3,
        TrainingPhase::Race => 0.0,
        TrainingPhase::Recovery => 0.4,
        TrainingPhase::OffSeason => 0.3,
        TrainingPhase::Transition => 0.6,
    };

    // Day distribution (higher on weekends)
    let day_mult = match day_of_week {
        0 => 0.15, // Monday - recovery
        1 => 0.14, // Tuesday
        2 => 0.16, // Wednesday
        3 => 0.12, // Thursday - easy
        4 => 0.13, // Friday - easy
        5 => 0.16, // Saturday - long
        6 => 0.14, // Sunday
        _ => 0.14,
    };

    // Rest day (Monday or one random day)
    let is_rest_day = day_of_week == 0 || (rng.gen::<f64>() < 0.1);

    let base_tss = weekly_tss * day_mult * phase_mult;

    // Add some variation
    let variation = rng.gen_range(0.8..1.2);
    let total_tss = if is_rest_day { 0.0 } else { base_tss * variation };

    (total_tss.max(0.0), is_rest_day)
}

/// Distribute TSS across sports based on athlete specialization.
fn distribute_tss<R: Rng>(
    rng: &mut R,
    athlete: &Athlete,
    total_tss: f64,
    phase: TrainingPhase,
    is_rest_day: bool,
) -> (f64, f64, f64, f64) {
    if is_rest_day || total_tss < 10.0 {
        return (0.0, 0.0, 0.0, 0.0);
    }

    // Base distribution (roughly 25/35/30/10 for swim/bike/run/strength)
    let mut swim_pct = 0.25;
    let mut bike_pct = 0.35;
    let mut run_pct = 0.30;
    let mut strength_pct = 0.10;

    // Adjust based on specialization
    match athlete.specialization {
        crate::athlete::Specialization::SwimStrong => {
            swim_pct += 0.05;
            bike_pct -= 0.025;
            run_pct -= 0.025;
        }
        crate::athlete::Specialization::BikeStrong => {
            bike_pct += 0.05;
            swim_pct -= 0.025;
            run_pct -= 0.025;
        }
        crate::athlete::Specialization::RunStrong => {
            run_pct += 0.05;
            swim_pct -= 0.025;
            bike_pct -= 0.025;
        }
        crate::athlete::Specialization::Balanced => {}
    }

    // Less strength in peak/race phases
    if matches!(phase, TrainingPhase::Peak | TrainingPhase::Taper | TrainingPhase::RacePrep) {
        strength_pct *= 0.5;
        let extra = strength_pct * 0.5;
        bike_pct += extra / 2.0;
        run_pct += extra / 2.0;
    }

    // Add variation
    let swim_var = rng.gen_range(0.8..1.2);
    let bike_var = rng.gen_range(0.8..1.2);
    let run_var = rng.gen_range(0.8..1.2);

    // Randomly skip some sports on any given day
    let do_swim = rng.gen::<f64>() < 0.6;
    let do_strength = rng.gen::<f64>() < 0.3;

    let swim_tss = if do_swim { total_tss * swim_pct * swim_var } else { 0.0 };
    let bike_tss = total_tss * bike_pct * bike_var;
    let run_tss = total_tss * run_pct * run_var;
    let strength_tss = if do_strength { total_tss * strength_pct } else { 0.0 };

    (swim_tss, bike_tss, run_tss, strength_tss)
}

/// Generate a workout specification.
fn generate_workout_spec<R: Rng>(
    rng: &mut R,
    sport: Sport,
    tss: f64,
    phase: TrainingPhase,
) -> WorkoutSpec {
    // Intensity factor based on phase
    let base_if = match phase {
        TrainingPhase::Base => 0.65,
        TrainingPhase::Build => 0.75,
        TrainingPhase::Peak => 0.85,
        TrainingPhase::Taper => 0.70,
        _ => 0.70,
    };

    let intensity_factor: f64 = base_if + rng.gen_range(-0.05..0.05);

    // TSS = IF^2 * hours * 100
    // hours = TSS / (IF^2 * 100)
    let hours = tss / (intensity_factor.powi(2) * 100.0);
    let duration_minutes = (hours * 60.0).clamp(20.0, 300.0);

    let tss_per_hour = if hours > 0.0 { tss / hours } else { 50.0 };

    let name = match (sport, phase) {
        (Sport::Swim, TrainingPhase::Base) => "Endurance Swim",
        (Sport::Swim, TrainingPhase::Build) => "Threshold Swim",
        (Sport::Swim, _) => "Swim Session",
        (Sport::Bike, TrainingPhase::Base) => "Endurance Ride",
        (Sport::Bike, TrainingPhase::Build) => "Tempo Ride",
        (Sport::Bike, TrainingPhase::Peak) => "Interval Ride",
        (Sport::Bike, _) => "Bike Session",
        (Sport::Run, TrainingPhase::Base) => "Easy Run",
        (Sport::Run, TrainingPhase::Build) => "Tempo Run",
        (Sport::Run, TrainingPhase::Peak) => "Interval Run",
        (Sport::Run, _) => "Run Session",
        (Sport::Strength, _) => "Strength Training",
    };

    WorkoutSpec {
        name: name.to_string(),
        sport,
        duration_minutes,
        tss_per_hour,
        intensity_factor,
    }
}
