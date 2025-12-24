class MenstrualCycleModel:
    """
    Simulates the physiological effects of the menstrual cycle on athletic metrics.
    Focuses on RHR, HRV, and Temperature modulation.
    """
    
    PHASES = {
        'FOLLICULAR': 'follicular',  # Days 1-13 (Low hormones)
        'OVULATION': 'ovulation',    # Day 14 (Estrogen peak)
        'LUTEAL': 'luteal',          # Days 15-28 (High Progesterone)
        'MENSTRUATION': 'menstruation' # Days 1-5 (subset of Follicular)
    }

    @classmethod
    def get_phase(cls, day_in_cycle, cycle_length, luteal_length):
        """Determine the current phase based on the day in cycle."""
        # Standardize day to cycle
        day = day_in_cycle % cycle_length
        if day == 0: day = cycle_length
        
        ovulation_day = cycle_length - luteal_length
        
        if day <= 5:
            return cls.PHASES['MENSTRUATION'] # Also part of follicular
        elif day < ovulation_day:
            return cls.PHASES['FOLLICULAR']
        elif day == ovulation_day:
            return cls.PHASES['OVULATION']
        else:
            return cls.PHASES['LUTEAL']

    @classmethod
    def calculate_modulations(cls, phase, day_in_cycle):
        """
        Return modulation factors for RHR, HRV, and Readiness.
        Reference: High progesterone in Luteal phase increases RHR and body temp, lowers HRV.
        """
        effects = {
            'rhr_modifier': 0.0,      # Additive (bpm)
            'hrv_multiplier': 1.0,    # Multiplicative
            'readiness_factor': 1.0,  # Multiplicative (recovery score)
            'injury_risk_modifier': 1.0 # Multiplicative
        }
        
        if phase == cls.PHASES['LUTEAL']:
            # Luteal Phase: Higher RHR, Lower HRV, Higher Temp
            effects['rhr_modifier'] = 1.5  # +1.5 bpm on average
            effects['hrv_multiplier'] = 0.94 # -6% HRV
            effects['readiness_factor'] = 0.95 # Slightly reduced readiness
            
            # Late luteal (PMS) - intensified effects
            if day_in_cycle > 24: # Assuming 28 day cycle logic scaled
                effects['rhr_modifier'] = 2.0
                effects['hrv_multiplier'] = 0.90
                effects['readiness_factor'] = 0.90

        elif phase == cls.PHASES['OVULATION']:
            # Ovulation: Estrogen peak can be performance enhancing but higher ACL risk
            effects['rhr_modifier'] = 0.5
            effects['hrv_multiplier'] = 1.02 # Slight bump
            effects['injury_risk_modifier'] = 1.2 # Ligament laxity hypothesis

        elif phase == cls.PHASES['MENSTRUATION']:
            # Menstruation: Relief from Progesterone, but potential discomfort
            effects['rhr_modifier'] = -0.5
            effects['hrv_multiplier'] = 1.0
            effects['readiness_factor'] = 0.92 # Symptom-based reduction

        # Follicular (non-menstruation) is baseline (no changes)
        
        return effects
