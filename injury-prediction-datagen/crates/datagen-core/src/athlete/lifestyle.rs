//! Lifestyle profile generation.

use rand::prelude::*;
use rand_distr::{Distribution, Uniform};

use super::types::LifestyleProfile;

/// Lifestyle profile definitions with their characteristics.
struct LifestyleTemplate {
    name: &'static str,
    sleep_range: (f64, f64),
    sleep_quality_range: (f64, f64),
    nutrition_range: (f64, f64),
    drinking_range: (f64, f64),
    smoking_range: (f64, f64),
    stress_range: (f64, f64),
    exercise_range: (f64, f64),
}

const LIFESTYLE_TEMPLATES: [LifestyleTemplate; 6] = [
    LifestyleTemplate {
        name: "Highly Disciplined Athlete",
        sleep_range: (7.5, 9.0),
        sleep_quality_range: (0.9, 1.0),
        nutrition_range: (0.9, 1.0),
        drinking_range: (0.0, 0.1),
        smoking_range: (0.0, 0.0),
        stress_range: (0.0, 0.2),
        exercise_range: (0.9, 1.0),
    },
    LifestyleTemplate {
        name: "Balanced Competitor",
        sleep_range: (6.5, 8.0),
        sleep_quality_range: (0.7, 0.9),
        nutrition_range: (0.7, 0.9),
        drinking_range: (0.1, 0.2),
        smoking_range: (0.0, 0.0),
        stress_range: (0.2, 0.4),
        exercise_range: (0.7, 0.9),
    },
    LifestyleTemplate {
        name: "Weekend Socializer",
        sleep_range: (6.0, 7.5),
        sleep_quality_range: (0.6, 0.8),
        nutrition_range: (0.6, 0.8),
        drinking_range: (0.3, 0.6),
        smoking_range: (0.0, 0.1),
        stress_range: (0.3, 0.6),
        exercise_range: (0.6, 0.8),
    },
    LifestyleTemplate {
        name: "Sleep-Deprived Workaholic",
        sleep_range: (4.5, 6.5),
        sleep_quality_range: (0.4, 0.7),
        nutrition_range: (0.5, 0.8),
        drinking_range: (0.2, 0.4),
        smoking_range: (0.0, 0.0),
        stress_range: (0.6, 0.9),
        exercise_range: (0.6, 0.8),
    },
    LifestyleTemplate {
        name: "Under-Recovered Athlete",
        sleep_range: (5.0, 7.0),
        sleep_quality_range: (0.3, 0.6),
        nutrition_range: (0.4, 0.7),
        drinking_range: (0.2, 0.4),
        smoking_range: (0.0, 0.0),
        stress_range: (0.4, 0.8),
        exercise_range: (0.7, 0.9),
    },
    LifestyleTemplate {
        name: "Health-Conscious Athlete",
        sleep_range: (7.0, 8.5),
        sleep_quality_range: (0.8, 1.0),
        nutrition_range: (0.8, 1.0),
        drinking_range: (0.0, 0.2),
        smoking_range: (0.0, 0.0),
        stress_range: (0.1, 0.3),
        exercise_range: (0.8, 1.0),
    },
];

/// Weights for each lifestyle profile in competitive triathletes.
const LIFESTYLE_WEIGHTS: [f64; 6] = [0.30, 0.25, 0.12, 0.12, 0.11, 0.10];

/// Generate lifestyle factors for an athlete.
pub fn generate_lifestyle_factors<R: Rng>(rng: &mut R) -> LifestyleProfile {
    // Select lifestyle profile based on weights
    let roll: f64 = rng.gen();
    let mut cumulative = 0.0;
    let mut selected_idx = 0;

    for (i, &weight) in LIFESTYLE_WEIGHTS.iter().enumerate() {
        cumulative += weight;
        if roll < cumulative {
            selected_idx = i;
            break;
        }
    }

    let template = &LIFESTYLE_TEMPLATES[selected_idx];

    // Generate values within ranges
    let sleep_hours = Uniform::new(template.sleep_range.0, template.sleep_range.1)
        .sample(rng)
        .clamp(5.0, 9.0);

    let sleep_quality = Uniform::new(template.sleep_quality_range.0, template.sleep_quality_range.1)
        .sample(rng);

    let nutrition = Uniform::new(template.nutrition_range.0, template.nutrition_range.1)
        .sample(rng);

    let drinking = Uniform::new(template.drinking_range.0, template.drinking_range.1)
        .sample(rng);

    let smoking = if template.smoking_range.1 > 0.0 {
        Uniform::new(template.smoking_range.0, template.smoking_range.1).sample(rng)
    } else {
        0.0
    };

    let stress = Uniform::new(template.stress_range.0, template.stress_range.1)
        .sample(rng);

    let exercise = Uniform::new(template.exercise_range.0, template.exercise_range.1)
        .sample(rng);

    LifestyleProfile {
        name: template.name.to_string(),
        sleep_hours,
        sleep_quality,
        nutrition,
        stress,
        smoking,
        drinking,
        exercise,
    }
}
