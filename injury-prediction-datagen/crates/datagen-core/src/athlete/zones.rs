//! Heart rate and power zone calculations.

use super::types::{HeartRateZones, PowerZones};

/// Calculate heart rate zones based on LTHR, resting HR, and max HR.
pub fn calculate_hr_zones(lthr: f64, resting_hr: f64, max_hr: f64) -> HeartRateZones {
    HeartRateZones {
        z1: (resting_hr * 1.5, 0.80 * lthr),  // Recovery
        z2: (0.80 * lthr, 0.90 * lthr),        // Endurance
        z3: (0.90 * lthr, 0.95 * lthr),        // Tempo
        z4: (0.95 * lthr, 1.02 * lthr),        // Threshold
        z5: (1.02 * lthr, 1.06 * lthr),        // VO2 Max
        z6: (1.06 * lthr, max_hr),             // Anaerobic
    }
}

/// Calculate power zones based on FTP.
pub fn calculate_power_zones(ftp: f64) -> PowerZones {
    PowerZones {
        z1: (0.0, 0.55 * ftp),          // Active Recovery
        z2: (0.56 * ftp, 0.75 * ftp),   // Endurance
        z3: (0.76 * ftp, 0.90 * ftp),   // Tempo
        z4: (0.91 * ftp, 1.05 * ftp),   // Threshold
        z5: (1.06 * ftp, 1.20 * ftp),   // VO2 Max
        z6: (1.21 * ftp, f64::INFINITY), // Anaerobic Capacity
    }
}
