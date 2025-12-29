//! Menstrual cycle effects on performance.

use crate::athlete::MenstrualCycleConfig;

/// Calculate the current phase of menstrual cycle.
pub fn get_cycle_phase(day_of_year: u32, config: &MenstrualCycleConfig) -> CyclePhase {
    let day_in_cycle = (day_of_year % config.cycle_length as u32) as u8;

    if day_in_cycle < 5 {
        CyclePhase::Menstrual
    } else if day_in_cycle < 14 {
        CyclePhase::Follicular
    } else if day_in_cycle < 17 {
        CyclePhase::Ovulatory
    } else {
        CyclePhase::Luteal
    }
}

/// Menstrual cycle phases.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CyclePhase {
    Menstrual,   // Days 1-5
    Follicular,  // Days 6-14
    Ovulatory,   // Days 14-17
    Luteal,      // Days 17-28
}

/// Performance modifiers based on cycle phase.
pub fn get_phase_modifiers(phase: CyclePhase) -> PhaseModifiers {
    match phase {
        CyclePhase::Menstrual => PhaseModifiers {
            energy: 0.90,
            recovery: 0.95,
            hrv: 0.95,
            injury_risk: 1.10,
        },
        CyclePhase::Follicular => PhaseModifiers {
            energy: 1.05,
            recovery: 1.05,
            hrv: 1.02,
            injury_risk: 0.95,
        },
        CyclePhase::Ovulatory => PhaseModifiers {
            energy: 1.10,
            recovery: 1.00,
            hrv: 1.00,
            injury_risk: 1.05, // Ligament laxity increases
        },
        CyclePhase::Luteal => PhaseModifiers {
            energy: 0.95,
            recovery: 0.92,
            hrv: 0.98,
            injury_risk: 1.02,
        },
    }
}

/// Performance modifiers for a cycle phase.
#[derive(Debug, Clone, Copy)]
pub struct PhaseModifiers {
    pub energy: f64,
    pub recovery: f64,
    pub hrv: f64,
    pub injury_risk: f64,
}

impl Default for PhaseModifiers {
    fn default() -> Self {
        Self {
            energy: 1.0,
            recovery: 1.0,
            hrv: 1.0,
            injury_risk: 1.0,
        }
    }
}
