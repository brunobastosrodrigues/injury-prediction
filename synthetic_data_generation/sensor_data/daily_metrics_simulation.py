import random
import numpy as np

# Random seed for reproducibility
np.random.seed(42)
random.seed(42)

class AthleteMetricsSimulator:
    """Simulates morning wearable recovery data based on previous training loads and athlete metrics."""
    
    def __init__(self):
        self.MIN_SLEEP_HOURS = 4.0
        self.IDEAL_SLEEP_PROPORTIONS = {
            'deep': 0.20,
            'rem': 0.25,
            'light': 0.55
        }
    
    def simulate_morning_data(self, athlete, date, prev_day, recovery_days_remaining, max_daily_tss, 
                              tss_history=None, acwr=None):
        """
        Simulate morning wearable recovery data based on previous training loads
        
        Parameters:
        - athlete: Dictionary containing athlete baseline metrics
        - date: Current date for simulation
        - prev_day: Previous day's metrics
        - recovery_days_remaining: Days remaining until injury is healed (0-10 scale)
        - max_daily_tss: Maximum sustainable daily training stress for this athlete
        - tss_history: List of TSS values for the past 28 days (optional)
        - acwr: Acute:Chronic Workload Ratio (optional)
        """
        # Initialize daily metrics
        daily_data = self._initialize_daily_data(athlete, date)
        
        # Calculate base recovery parameters
        recovery_params = self._calculate_recovery_parameters(
            athlete, prev_day, recovery_days_remaining, max_daily_tss, tss_history, acwr
        )
        
        # Simulate sleep metrics
        sleep_metrics = self._simulate_sleep_metrics(
            athlete, 
            recovery_params['fatigue_factor'], 
            recovery_params['injury_effect'], 
            recovery_params['stress_factor'],
            athlete['sleep_time_norm']
        )
        
        # Calculate morning physiological metrics
        morning_metrics = self._calculate_morning_metrics(
            athlete, prev_day, sleep_metrics, recovery_params, max_daily_tss
        )
        
        # Update daily data with all calculated metrics
        daily_data.update({**sleep_metrics, **morning_metrics})
        
        return daily_data
    
    def simulate_evening_data(self, athlete, daily_data, fatigue, current_hour=22):
        """
        Simulate evening wearable sensor data based on day's activity and fatigue
        
        Parameters:
        - athlete: Dictionary containing athlete baseline metrics
        - daily_data: Dictionary containing morning metrics and day's activity
        - fatigue: Current fatigue level (0-100 scale)
        - current_hour: Current hour of day (24-hour format)
        
        Returns:
        - Updated daily data with evening metrics
        """
        # Calculate stress factors
        stress = self._calculate_stress_factors(athlete, fatigue, daily_data)
        
        # Calculate evening body battery
        body_battery_evening = self._calculate_evening_body_battery(daily_data, stress, fatigue, current_hour)
        
        # Update daily data with evening metrics
        daily_data.update({
            'stress': round(stress, 1),
            'body_battery_evening': body_battery_evening
        })
        
        return daily_data
    
    def _initialize_daily_data(self, athlete, date):
        """Initialize the daily data structure with default values."""
        return {
            'athlete_id': athlete['id'],
            'date': date,
            'resting_hr': None,
            'hrv': None,
            'sleep_hours': None,
            'deep_sleep': None,
            'light_sleep': None,
            'rem_sleep': None,
            'sleep_quality': None,
            'body_battery_morning': None,
            'stress': None,
            'body_battery_evening': None,
            'workout_data': None,
            'injury': 0
        }
    
    def _calculate_recovery_parameters(self, athlete, prev_day, recovery_days_remaining, 
                                      max_daily_tss, tss_history, acwr):
        """Calculate base recovery parameters needed for simulations."""
        stress_level_yesterday = prev_day['stress'] if prev_day else 30
        fatigue = prev_day['fatigue'] if prev_day else 30
        recovery_rate = athlete['recovery_rate']
        
        # Calculate total fatigue
        total_fatigue = self._calculate_total_fatigue(fatigue, tss_history, recovery_rate)
        
        # Calculate recovery score (0-1 scale, higher is better recovery)
        recovery_score = max(0, 1 - (total_fatigue / 150))
        
        # Calculate injury effect (0-1 scale)
        injury_effect = self._calculate_injury_effect(recovery_days_remaining, recovery_rate)
        
        # Calculate derived factors
        fatigue_factor = min(total_fatigue / 100, 1)  # Normalize fatigue effect
        stress_factor = min(stress_level_yesterday / 100, 1)  # Normalize stress effect
        acwr_effect = self._check_acwr_effect(acwr)
        chronic_adaptation = self._check_chronic_adaptation(tss_history, max_daily_tss)
        consecutive_high_load_days = self._check_consecutive_high_load_days(tss_history, max_daily_tss)
        
        return {
            'total_fatigue': total_fatigue,
            'recovery_score': recovery_score,
            'injury_effect': injury_effect,
            'fatigue_factor': fatigue_factor,
            'stress_factor': stress_factor,
            'acwr_effect': acwr_effect,
            'chronic_adaptation': chronic_adaptation,
            'consecutive_high_load_days': consecutive_high_load_days,
            'stress_level_yesterday': stress_level_yesterday
        }
    
    def _simulate_sleep_metrics(self, athlete, fatigue_factor, injury_effect, stress_factor, sleep_norm):
        """Simulate sleep metrics based on fatigue, injury, and stress factors."""
        # Calculate sleep hours
        sleep_hours = self._calculate_sleep_hours(fatigue_factor, injury_effect, stress_factor, sleep_norm)
        
        # Calculate sleep distribution
        deep_sleep, rem_sleep, light_sleep = self._calculate_sleep_distribution(
            sleep_hours, fatigue_factor, injury_effect, stress_factor
        )
        
        # Calculate sleep quality
        sleep_quality = self._calculate_sleep_quality(sleep_hours, deep_sleep, light_sleep, rem_sleep)
        
        return {
            'sleep_hours': sleep_hours,
            'deep_sleep': deep_sleep,
            'light_sleep': light_sleep,
            'rem_sleep': rem_sleep,
            'sleep_quality': sleep_quality
        }
    
    def _calculate_morning_metrics(self, athlete, prev_day, sleep_metrics, recovery_params, max_daily_tss):
        """Calculate morning physiological metrics based on sleep and recovery parameters."""
        # Calculate baseline sleep
        baseline_sleep = athlete['sleep_time_norm'] * athlete['sleep_quality']
        if athlete['sleep_quality'] > 0.85:
            baseline_sleep *= 0.85  # 100 sleep score is very rare so we account for it
        
        # Calculate sleep debt
        night_sleep = sleep_metrics['sleep_hours'] * sleep_metrics['sleep_quality']
        sleep_debt = max(0, baseline_sleep - night_sleep)
        
        # Calculate status flags
        flags = self._check_flags(prev_day, max_daily_tss)
        
        # Calculate physiological metrics
        rhr = self._calculate_resting_hr(
            athlete, prev_day, recovery_params, sleep_debt, sleep_metrics['sleep_quality'], 
            flags, max_daily_tss
        )
        
        hrv = self._calculate_hrv(
            prev_day, athlete['hrv_baseline'], sleep_debt, sleep_metrics['sleep_quality'], 
            recovery_params, flags, max_daily_tss
        )
        
        body_battery = self._calculate_morning_body_battery(
            athlete, prev_day, sleep_metrics['sleep_quality'], sleep_metrics['sleep_hours'], 
            hrv, rhr, recovery_params['stress_level_yesterday'], recovery_params['recovery_score'], 
            recovery_params['injury_effect']
        )
        
        return {
            'resting_hr': rhr,
            'hrv': hrv,
            'body_battery_morning': body_battery
        }
    
    def _calculate_total_fatigue(self, fatigue, tss_history, recovery_rate):
        """Calculate total fatigue including delayed effects."""
        # Calculate delayed fatigue effects (24-72 hour window)
        delayed_fatigue = 0
        if tss_history and len(tss_history) >= 3:
            # Get training stress from 1, 2, and 3 days ago
            day_minus_1_tss = tss_history[-1]
            day_minus_2_tss = tss_history[-2]
            day_minus_3_tss = tss_history[-3]
            
            # Apply delayed impact factors (highest impact 24-48 hours after workout)
            delayed_fatigue = (day_minus_1_tss * 0.3) + (day_minus_2_tss * 0.15) + (day_minus_3_tss * 0.05)
        
        # Apply recovery rate to fatigue and delayed effects
        adjusted_fatigue = fatigue / recovery_rate
        adjusted_delayed_fatigue = delayed_fatigue / recovery_rate
        
        # Calculate total effective fatigue (immediate + delayed)
        return adjusted_fatigue + adjusted_delayed_fatigue
    
    def _calculate_injury_effect(self, recovery_days_remaining, recovery_rate):
        """Calculate injury effect on a 0-1 scale."""
        if recovery_days_remaining <= 0:
            return 0
            
        # Apply recovery rate to injury recovery speed
        adjusted_recovery_days = recovery_days_remaining / recovery_rate
        # Stronger effect when recovery_days_remaining is closer to 10 (maximum)
        return adjusted_recovery_days / 10
    
    def _check_consecutive_high_load_days(self, tss_history, max_daily_tss):
        """Track consecutive high load days."""
        consecutive_high_load_days = 0
        if tss_history:
            for day in reversed(tss_history):
                if day > max_daily_tss:
                    consecutive_high_load_days += 1
                else:
                    break
        return consecutive_high_load_days
    
    def _check_acwr_effect(self, acwr):
        """Apply ACWR effects if available."""
        if acwr is None:
            return 0
            
        if acwr > 1.3:
            # High acute:chronic ratio - increased injury risk
            return 0.1
        elif acwr < 0.8:
            # Low acute:chronic ratio - detraining risk
            return 0.05
        return 0
    
    def _check_chronic_adaptation(self, tss_history, max_daily_tss):
        """Check for chronic training adaptations."""
        if not tss_history or len(tss_history) < 28:
            return 0
            
        # Calculate average loading over past month
        avg_monthly_tss = sum(tss_history) / len(tss_history)
        
        # Higher chronic load = more adaptation (up to a point)
        if avg_monthly_tss > max_daily_tss * 0.7:
            # Long-term adaptation reduces impact of similar training loads
            return min((avg_monthly_tss / max_daily_tss) * 0.2, 0.2)
        return 0
    
    def _check_flags(self, prev_day, max_daily_tss):
        """Check for various training status flags."""
        if not prev_day:
            return {
                'overtraining_risk': False,
                'excessive_fatigue': False,
                'high_load': False,
                'peaking': False,
                'high_stress': False
            }
            
        excessive_fatigue = prev_day['form'] < -20
        high_load = prev_day['training_stress'] > max_daily_tss
        overtraining_risk = excessive_fatigue and high_load
        peaking = 35 > prev_day['form'] > 20
        high_stress = prev_day['stress'] > 50
        
        return {
            'overtraining_risk': overtraining_risk,
            'excessive_fatigue': excessive_fatigue,
            'high_load': high_load,
            'peaking': peaking,
            'high_stress': high_stress
        }
    
    def _calculate_sleep_hours(self, fatigue_factor, injury_effect, stress_factor, sleep_norm):
        """Calculate sleep hours based on fatigue, injury, and stress factors."""
        fatigue_sleep_effect = 0.1 * fatigue_factor - 0.2 * injury_effect
        stress_effect = 0.1 * stress_factor
        sleep_hours = sleep_norm + fatigue_sleep_effect - stress_effect + random.normalvariate(0, 0.5)
        return max(sleep_hours, self.MIN_SLEEP_HOURS)
    
    def _calculate_sleep_distribution(self, sleep_hours, fatigue_factor, injury_effect, stress_factor):
        """Calculate the distribution of deep, REM, and light sleep."""
        # Adjust sleep stages based on fatigue, injury, and stress
        deep_sleep_pct = self.IDEAL_SLEEP_PROPORTIONS['deep'] - (0.05 * fatigue_factor) - (0.07 * injury_effect) - (0.03 * stress_factor)
        rem_sleep_pct = self.IDEAL_SLEEP_PROPORTIONS['rem'] - (0.03 * fatigue_factor) - (0.05 * injury_effect) - (0.02 * stress_factor)
        
        # Ensure sleep percentages are physiologically plausible
        deep_sleep_pct = max(0.08, min(deep_sleep_pct, 0.25))
        rem_sleep_pct = max(0.15, min(rem_sleep_pct, 0.25))
        light_sleep_pct = 1 - deep_sleep_pct - rem_sleep_pct
        
        # Calculate actual sleep times
        deep_sleep = sleep_hours * deep_sleep_pct
        rem_sleep = sleep_hours * rem_sleep_pct
        light_sleep = sleep_hours * light_sleep_pct
        
        return deep_sleep, rem_sleep, light_sleep
    
    def _calculate_sleep_quality(self, sleep_hours, deep_sleep, light_sleep, rem_sleep):
        """Calculate sleep quality score between 0-1."""
        # duration scoring
        def duration_scoring(hours):
            if hours < 5:
                return max(0, 0.1 - (5 - hours) * 0.05)  # Stronger penalty for <5 hours
            elif hours < 6:
                return 0.2  # Slightly reduced generosity
            elif hours < 7:
                return 0.4
            elif hours < 8:
                return 0.7
            elif hours <= 9:
                return 0.9  # Peak range remains
            elif hours <= 10:
                return 0.7
            else:
                return max(0, 0.6 - (hours - 10) * 0.07)  # Faster decline after 10 hours
        
        # stage quality assessment
        def stage_quality(actual, ideal):
            deviation = abs(actual - ideal)
            if deviation <= 0.03:  # Very close to ideal
                return 1.0
            elif deviation <= 0.08:
                return 0.9
            elif deviation <= 0.12:
                return 0.75
            elif deviation <= 0.8:
                return 0.65
            else:
                return max(0, 0.6 - (deviation - 0.18) * 2)
        
        # Calculate percentages
        total_sleep = max(0.1, sleep_hours)
        deep_sleep_percent = deep_sleep / total_sleep
        light_sleep_percent = light_sleep / total_sleep
        rem_sleep_percent = rem_sleep / total_sleep
        
        # Individual stage scores
        deep_score = stage_quality(deep_sleep_percent, self.IDEAL_SLEEP_PROPORTIONS['deep'])
        rem_score = stage_quality(rem_sleep_percent, self.IDEAL_SLEEP_PROPORTIONS['rem'])
        light_score = stage_quality(light_sleep_percent, self.IDEAL_SLEEP_PROPORTIONS['light'])
        
        # Weighted stage score (more emphasis on deep and REM)
        stage_quality_score = (
            deep_score * 0.45 +
            rem_score * 0.35 +
            light_score * 0.20
        )
        
        # Combine duration and stage quality
        if sleep_hours < 6:
            final_score = (duration_scoring(sleep_hours) * 0.6 + stage_quality_score * 0.4)
        else:
            final_score = (duration_scoring(sleep_hours) * 0.4 + stage_quality_score * 0.6)
        
        return min(1.0, max(0.0, final_score))
    
    def _calculate_resting_hr(self, athlete, prev_day, recovery_params, sleep_debt, sleep_quality, flags, max_daily_tss):
        """Calculate resting heart rate based on recovery parameters."""
        # Calculate resting heart rate deviation
        rhr_deviation = (
            0.6 * sleep_debt +                                     # Sleep debt impact
            0.08 * recovery_params['injury_effect'] * athlete['resting_hr'] +  # Injury impact
            0.1 * recovery_params['fatigue_factor'] * athlete['resting_hr'] -  # Fatigue impact
            0.03 * recovery_params['recovery_score'] * athlete['resting_hr'] - # Recovery benefit
            0.02 * max(0, sleep_quality - 0.7) * athlete['resting_hr'] +       # Sleep benefit
            0.08 * recovery_params['acwr_effect'] * athlete['resting_hr'] -    # ACWR impact
            recovery_params['chronic_adaptation'] * athlete['resting_hr']      # Long-term adaptation
        )
        
        # Apply conditional factors with nonlinear responses
        if flags['overtraining_risk']:
            # Significant nonlinear increase when both fatigued and high load
            rhr_deviation += 0.08 * athlete['resting_hr']
        elif flags['excessive_fatigue']:
            rhr_deviation += 0.08 * athlete['resting_hr']
        elif flags['high_load']:
            rhr_deviation += 0.07 * athlete['resting_hr']
        elif recovery_params['consecutive_high_load_days'] >= 3:
            # Delayed rise in RHR after consecutive high loads
            rhr_deviation += 0.05 * athlete['resting_hr']
        elif flags['peaking']:
            rhr_deviation -= 0.05 * athlete['resting_hr']
        elif flags['high_stress']:
            rhr_deviation += 0.05 * athlete['resting_hr']
        
        # Add day-to-day variability (smaller for RHR than HRV)
        rhr_deviation += random.normalvariate(0, 0.02 * athlete['resting_hr'])
        
        # Add temporal correlation (if previous day exists)
        if prev_day and 'resting_hr' in prev_day:
            yesterday_rhr_deviation = prev_day['resting_hr'] - athlete['resting_hr']
            rhr_deviation = 0.7 * rhr_deviation + 0.3 * yesterday_rhr_deviation
        
        # Calculate final RHR
        rhr = athlete['resting_hr'] + rhr_deviation 
        
        # Ensure RHR stays within physiological bounds
        min_rhr = athlete['resting_hr'] * 0.85
        max_rhr = athlete['resting_hr'] * 1.15
        return max(min_rhr, min(rhr, max_rhr))
    
    def _calculate_hrv(self, prev_day, hrv_baseline, sleep_debt, sleep_quality, recovery_params, flags, max_daily_tss):
        """Calculate heart rate variability based on recovery parameters."""
        # Expand boundaries for extreme conditions
        expanded_boundaries = flags['excessive_fatigue'] or (prev_day and prev_day['training_stress'] > max_daily_tss * 1.2)
        
        if expanded_boundaries:
            min_hrv = hrv_baseline * 0.6  # Allow wider range when excessively fatigued
            max_hrv = hrv_baseline * 1.4
        else:
            min_hrv = hrv_baseline * 0.85
            max_hrv = hrv_baseline * 1.15
        
        # HRV supracompensation phenomenon (temporary increase before crash)
        supracompensation = 0
        if recovery_params['consecutive_high_load_days'] == 3:
            # Brief HRV increase before collapse (happens in some athletes)
            supracompensation = 0.08 * hrv_baseline
        elif recovery_params['consecutive_high_load_days'] >= 4:
            # Followed by sharp decline
            supracompensation = -0.15 * hrv_baseline
        
        hrv_deviation = (
            -3.0 * sleep_debt -                                    # Sleep debt impact (negative)
            0.25 * recovery_params['injury_effect'] * hrv_baseline -  # Injury impact (negative)
            0.15 * recovery_params['fatigue_factor'] * hrv_baseline +  # Fatigue impact (negative)
            0.1 * recovery_params['recovery_score'] * hrv_baseline +  # Recovery benefit (positive)
            0.05 * max(0, sleep_quality - 0.7) * hrv_baseline -    # Sleep benefit (positive)
            0.12 * recovery_params['acwr_effect'] * hrv_baseline +  # ACWR impact (negative)
            recovery_params['chronic_adaptation'] * hrv_baseline +  # Long-term adaptation benefit (positive)
            supracompensation                                      # Supracompensation effect (variable)
        )
        
        # Apply conditional factors with nonlinear responses
        if flags['overtraining_risk']:
            # Significant decrease when both fatigued and high load
            hrv_deviation -= 0.20 * hrv_baseline
        elif flags['excessive_fatigue']:
            hrv_deviation -= 0.12 * hrv_baseline
        elif flags['high_load']:
            # Highly nonlinear response to extreme loads
            if prev_day and prev_day['training_stress'] > max_daily_tss * 1.5:
                hrv_deviation -= 0.25 * hrv_baseline
            else:
                hrv_deviation -= 0.10 * hrv_baseline
        elif flags['peaking']:
            hrv_deviation += 0.08 * hrv_baseline
        elif flags['high_stress']:
            hrv_deviation -= 0.07 * hrv_baseline
        
        # Add day-to-day variability (higher for HRV than RHR)
        hrv_deviation += random.normalvariate(0, 0.05 * hrv_baseline)
        
        # Add temporal correlation (if previous day exists)
        if prev_day and 'hrv' in prev_day:
            yesterday_hrv_deviation = prev_day['hrv'] - hrv_baseline
            hrv_deviation = 0.6 * hrv_deviation + 0.4 * yesterday_hrv_deviation  # HRV has less day-to-day stability than RHR
        
        # Calculate final HRV
        hrv = hrv_baseline + hrv_deviation 
        
        # Ensure HRV stays within physiological bounds
        return max(min_hrv, min(hrv, max_hrv))
    
    def _calculate_morning_body_battery(self, athlete, prev_day, sleep_quality, sleep_hours, hrv, rhr, 
                                      stress_level_yesterday, recovery_score, injury_effect):
        """Calculate morning body battery based on recovery parameters."""
        # Start with previous evening's body battery value (if available)
        # Otherwise start at a reasonable default
        last_body_battery = prev_day['body_battery_evening'] if prev_day and 'body_battery_evening' in prev_day else 30
        
        # Calculate recharge amount based on sleep quality and duration
        sleep_norm = athlete['sleep_time_norm']
        
        # Sleep recharge (higher quality and longer duration = more recharge)
        max_recharge = 120 - last_body_battery 
        sleep_efficiency = sleep_quality * (min(sleep_hours / sleep_norm, 1.3))  # Cap benefit at 130% of normal
        
        if sleep_hours < 6:
            # Sleep deprivation reduces recharge
            sleep_efficiency *= max(0.5, 0.9 - (6 - sleep_hours) * 0.1)
        elif 9 >= sleep_hours >= 8:
            # optimal sleep hours increase recharge
            sleep_efficiency *= 1.1
        
        sleep_recharge = max_recharge * sleep_efficiency
        
        # Recovery adjustments
        hrv_factor = hrv / athlete['hrv_baseline']  # Normalized HRV (1.0 = baseline)
        rhr_factor = athlete['resting_hr'] / rhr   
        
        # Adjust recharge based on physiological recovery markers
        recovery_multiplier = (0.6 * hrv_factor + 0.4 * rhr_factor) * recovery_score * 2
        adjusted_recharge = sleep_recharge * recovery_multiplier
        
        # Drain factors from previous day (if available)
        previous_drain = 0
        if prev_day:
            # Stress drains body battery
            stress_drain = stress_level_yesterday * 0.15
            
            # Training stress drains body battery
            training_drain = prev_day.get('training_stress', 0) * 0.1
            
            previous_drain = stress_drain + training_drain
        
        # Calculate new body battery
        new_body_battery = last_body_battery + adjusted_recharge - previous_drain
        
        # Apply diminishing returns as we approach 100
        if new_body_battery > 80:
            # Dampen recharge as we get closer to 100
            excess = new_body_battery - 80
            new_body_battery = 80 + (excess * 0.8)
        elif new_body_battery < 70:
            boost_factor = (70 - new_body_battery) / 20  # boost increases as battery decreases
            new_body_battery += adjusted_recharge * boost_factor
        
        # Apply floor and ceiling
        new_body_battery = max(min(new_body_battery, 100), 60)
        
        # Round to nearest whole number
        return round(new_body_battery)
    
    def _calculate_stress_factors(self, athlete, fatigue, daily_data):
        """Calculate stress factors based on lifestyle, biometrics, and recovery."""
        factors = {
            'smoking': athlete.get('smoking_factor', 0),
            'alcohol': athlete.get('drinking_factor', 0),
            'life_stress': athlete.get('stress_factor', 0),
            'hrv': max(0, min(1, (athlete['hrv_baseline'] - daily_data['hrv']) / athlete['hrv_baseline'] * 2)),
            'hr': max(0, min(1, (daily_data['resting_hr'] - athlete['resting_hr']) / (athlete['resting_hr'] * 0.15))),
            'sleep': max(0, min(1, (100 - daily_data['sleep_quality'] * 100) / 100)),
            'battery': max(0, min(1, (100 - daily_data['body_battery_morning']) / 100)),
            'fatigue': max(0, min(1, fatigue / 100))
        }
        
        # Exponential scaling for critical cases
        if daily_data['hrv'] < athlete['hrv_baseline'] * 0.8:
            factors['hrv'] **= 1.5
        if daily_data['resting_hr'] > athlete['resting_hr'] * 1.1:
            factors['hr'] **= 1.5
            
        weights = {
            'smoking': 15,
            'alcohol': 15,
            'life_stress': 20,
            'hrv': 15,
            'hr': 10,
            'sleep': 10,
            'battery': 10,
            'fatigue': 5
        }
        
        stress = sum(factors[k] * weights[k] for k in factors) + np.random.normal(0, 3)  # Add variability
        return min(max(stress, 0), 100)
    
    def _calculate_evening_body_battery(self, daily_data, stress, fatigue, current_hour):
        """Calculate evening body battery considering various drains."""
        hour_factor = abs((current_hour - 15) / 12)
        base_decay = 25 + 5 * hour_factor
        
        if daily_data['body_battery_morning'] > 80:
            decay_modifier = 1.4
        elif daily_data['body_battery_morning'] < 40:
            decay_modifier = 0.8
        elif daily_data.get('actual_tss', 0) < 40:
            decay_modifier = 1.3
        else:
            decay_modifier = 1.0
            
        training_stress = daily_data.get('actual_tss', 0)
        workout_drain = training_stress * (0.085 + (training_stress / 400) * 0.1) if training_stress > 0 else 0
        stress_drain = (stress / 100) ** 1.2 * 25
        fatigue_drain = fatigue * 0.12
        
        total_drain = (base_decay * decay_modifier) + workout_drain + stress_drain + fatigue_drain + np.random.normal(0, 2)
        
        return round(min(max(daily_data['body_battery_morning'] - total_drain, 5), daily_data['body_battery_morning'] - 40), 1)

# Backward compatibility
def simulate_morning_sensor_data(athlete, date, prev_day, recovery_days_remaining, max_daily_tss, tss_history=None, acwr=None):
    """Wrapper function to maintain backward compatibility."""
    simulator = AthleteMetricsSimulator()
    return simulator.simulate_morning_data(athlete, date, prev_day, recovery_days_remaining, max_daily_tss, tss_history, acwr)

def simulate_evening_sensor_data(athlete, fatigue, daily_data, current_hour=22):
    """Wrapper function to maintain backward compatibility."""
    simulator = AthleteMetricsSimulator()
    return simulator.simulate_evening_data(athlete, daily_data, fatigue, current_hour)

def inject_realistic_injury_patterns(athlete, daily_data_list, injury_day_index, lookback_days=14):
    """
    Inject realistic physiological patterns before injuries with appropriate noise and variability.
    
    Parameters:
    -----------
    athlete : dict
        Athlete profile with baseline metrics
    daily_data_list : list
        List of daily data dictionaries
    injury_day_index : int
        Index of the day when injury occurs
    lookback_days : int
        Number of days before injury to modify data
    """
    # Ensure we don't go beyond the beginning of the data
    start_idx = max(0, injury_day_index - lookback_days)
    
    # Get the relevant data slice leading to injury
    pre_injury_period = daily_data_list[start_idx:injury_day_index+1]
    period_length = len(pre_injury_period)
    
    # Calculate baseline values from athlete profile
    baseline_hrv = athlete['hrv_baseline']
    baseline_rhr = athlete['resting_hr']
    
    # Add some athlete-specific variability to pattern strength (some athletes show stronger patterns)
    pattern_strength_modifier = random.uniform(0.7, 1.3)
    
    # Add some randomness to the pattern onset (not all patterns start at the same time)
    pattern_start_point = random.randint(1, min(5, period_length//3))
    effective_days = period_length - pattern_start_point
    
    # Decide which patterns this athlete will exhibit (not all athletes show all patterns)
    show_hrv_pattern = random.random() < 0.85  # 85% show HRV decline
    show_rhr_pattern = random.random() < 0.80  # 80% show RHR increase
    show_sleep_pattern = random.random() < 0.70  # 70% show sleep quality decline
    show_bb_pattern = random.random() < 0.75  # 75% show body battery decline

    hrv_sensitivity = athlete['recovery_signature']['hrv_sensitivity']
    rhr_sensitivity = athlete['recovery_signature']['rhr_sensitivity'] 
    sleep_sensitivity = athlete['recovery_signature']['sleep_sensitivity']
    stress_sensitivity = athlete['recovery_signature']['stress_sensitivity']
    
    # Sometimes injuries happen with minimal warning (acute injuries)
    is_acute_injury = random.random() < 0.15  # 15% of injuries are acute with minimal warning
    if is_acute_injury:
        # For acute injuries, only modify 1-3 days before injury
        pattern_start_point = period_length - random.randint(1, 3)
    
    # Create a recent history of the athlete's data
    if len(daily_data_list) > 3:
        # Get recent history for temporal effects
        recent_history = daily_data_list[max(0, injury_day_index-3):injury_day_index]
    else:
        recent_history = None

    # Create pattern alterations with realistic noise
    for i, day_data in enumerate(pre_injury_period):
        # Skip early days before pattern starts
        if i < pattern_start_point:
            continue
            
        # Calculate progression factor (0 to 1) - how close to injury day
        progression = (i - pattern_start_point) / (period_length - pattern_start_point) if (period_length - pattern_start_point) > 0 else 0
        
        # Add day-to-day variability (good days even during overall decline)
        daily_variability = random.normalvariate(0, 0.2)  # Higher variability

        # Calculate cross-stress multipliers
        cross_stress_mults = calculate_cross_stress_effects(day_data, recent_history)
        
        # 1. Modify HRV if this athlete shows HRV pattern
        if show_hrv_pattern:
            # Base decline factor - more subtle max decline (25%)
            hrv_decline_factor = min(0.25, 0.05 + progression * 0.20) * pattern_strength_modifier * hrv_sensitivity * cross_stress_mults['hrv']
            
            # Add daily variability - some days HRV might improve slightly despite overall decline
            daily_hrv_adjustment = daily_variability * baseline_hrv * 0.15
            
            # Calculate new HRV with realistic noise
            new_hrv = baseline_hrv * (1 - hrv_decline_factor * (progression ** 1.2)) + daily_hrv_adjustment
            
            # Ensure within physiological limits (don't let it drop too low)
            day_data['hrv'] = max(baseline_hrv * 0.65, min(baseline_hrv * 1.1, new_hrv))
        
        if show_hrv_pattern and random.random() < 0.3:  # 30% chance of non-linear pattern
            # Sometimes HRV improves briefly before crashing (false recovery)
            if 0.5 < progression < 0.8 and random.random() < 0.4:
                # Temporary improvement in HRV (false recovery)
                hrv_decline_factor = hrv_decline_factor * 0.3
        
        # 2. Modify resting heart rate if this athlete shows RHR pattern
        if show_rhr_pattern:
            # Base increase factor - more subtle (12% max)
            rhr_increase_factor = min(0.12, 0.02 + progression * 0.10) * pattern_strength_modifier * rhr_sensitivity * cross_stress_mults['rhr']
            
            # Add daily variability
            daily_rhr_adjustment = -daily_variability * baseline_rhr * 0.08  # Negative because lower is better for RHR
            
            # Calculate new RHR with realistic noise
            new_rhr = baseline_rhr * (1 + rhr_increase_factor * (progression ** 1.1)) + daily_rhr_adjustment
            
            # Ensure within physiological limits
            day_data['resting_hr'] = max(baseline_rhr * 0.92, min(baseline_rhr * 1.15, new_rhr))
        
        # 3. Modify sleep quality if this athlete shows sleep pattern
        if show_sleep_pattern and progression > 0.3:  # Sleep issues often start later
            # More subtle sleep reduction
            sleep_reduction = min(0.2, (progression - 0.3) * 0.3) * pattern_strength_modifier * sleep_sensitivity * cross_stress_mults['sleep']
            
            # Add daily variability - some nights are better than others
            daily_sleep_adjustment = daily_variability * 0.15  # Some nights are better/worse
            
            # Apply changes with noise
            new_sleep_quality = day_data['sleep_quality'] * (1 - sleep_reduction) + daily_sleep_adjustment
            
            # Ensure within limits
            day_data['sleep_quality'] = max(0.4, min(0.95, new_sleep_quality))
            
            # Also adjust sleep stages
            deep_sleep_reduction = sleep_reduction * (1.0 + random.uniform(-0.3, 0.3))
            rem_sleep_reduction = sleep_reduction * (0.8 + random.uniform(-0.3, 0.3))
            
            day_data['deep_sleep'] = day_data['deep_sleep'] * (1 - deep_sleep_reduction)
            day_data['rem_sleep'] = day_data['rem_sleep'] * (1 - rem_sleep_reduction)
            day_data['light_sleep'] = day_data['sleep_hours'] - day_data['deep_sleep'] - day_data['rem_sleep']
        
        # 4. Modify body battery metrics if this athlete shows that pattern
        if show_bb_pattern and 'body_battery_morning' in day_data:
            # More subtle battery reduction
            bb_reduction = min(0.25, 0.05 + progression * 0.10) * pattern_strength_modifier * cross_stress_mults['body_battery']
            
            # Add daily variability
            daily_bb_adjustment = daily_variability * 8  # Some days feel better than others
            
            # Apply to morning body battery
            new_bb_morning = day_data['body_battery_morning'] * (1 - bb_reduction * (progression ** 1.0)) + daily_bb_adjustment
            day_data['body_battery_morning'] = max(40, min(100, new_bb_morning))
            
            # Apply to evening body battery
            if 'body_battery_evening' in day_data:
                new_bb_evening = day_data['body_battery_evening'] * (1 - bb_reduction * (progression ** 1.1)) + daily_bb_adjustment * 0.5
                day_data['body_battery_evening'] = max(15, min(60, new_bb_evening))
        
        # 5. Increase stress levels as injury approaches - most athletes show this
        stress_increase = min(20, progression * 30 * pattern_strength_modifier) * stress_sensitivity * cross_stress_mults['stress']
        stress_daily_variability = random.normalvariate(0, 8)  # High daily stress variability
        
        new_stress = day_data['stress'] + stress_increase + stress_daily_variability
        day_data['stress'] = min(95, max(20, new_stress))  # Keep within range

    return daily_data_list


def create_false_alarm_patterns(athlete, daily_data_list, start_index, pattern_days=10):
    """
    Create false alarm patterns that look like injury warnings but don't result in injury.
    This makes the data more realistic by including "close calls" that the model needs to distinguish.
    
    Parameters:
    -----------
    athlete : dict
        Athlete profile with baseline metrics
    daily_data_list : list
        List of daily data dictionaries
    start_index : int
        Index to start inserting false alarm patterns
    pattern_days : int
        Duration of the false alarm pattern
    """
    # Ensure we have enough days to work with
    if start_index + pattern_days >= len(daily_data_list):
        return daily_data_list
    
    if random.random() < 0.3:  # 30% of false alarms are "strong" 
        pattern_strength = random.uniform(0.8, 1.1)
    else:
        pattern_strength = random.uniform(0.4, 0.8)
    
    # Baseline values
    baseline_hrv = athlete['hrv_baseline']
    baseline_rhr = athlete['resting_hr']
    hrv_sensitivity = athlete['recovery_signature']['hrv_sensitivity']
    rhr_sensitivity = athlete['recovery_signature']['rhr_sensitivity'] 
    sleep_sensitivity = athlete['recovery_signature']['sleep_sensitivity']
    stress_sensitivity = athlete['recovery_signature']['stress_sensitivity']
    
    # Decide which patterns to show (usually fewer than real injury patterns)
    show_hrv_pattern = random.random() < 0.7
    show_rhr_pattern = random.random() < 0.6
    show_sleep_pattern = random.random() < 0.5

    # Create a recent history of the athlete's data
    # Create a recent history of the athlete's data
    if len(daily_data_list) > 3:
        # Get recent history for temporal effects
        recent_history = daily_data_list[max(0, start_index-3):start_index]
    else:
        recent_history = None
    
    # Create mild warning patterns that resolve without injury
    for i in range(pattern_days):
        day_index = start_index + i
        day_data = daily_data_list[day_index]
        
        # Calculate progression factor: rises then falls (peak in the middle)
        if i < pattern_days // 2:
            # First half - metrics worsen
            progression = i / (pattern_days // 2)
        else:
            # Second half - metrics improve (pattern resolves)
            progression = 1.0 - ((i - pattern_days // 2) / (pattern_days - pattern_days // 2))
        
        # Add daily variability
        daily_variability = random.normalvariate(0, 0.25)

        # Calculate cross-stress multipliers
        cross_stress_mults = calculate_cross_stress_effects(day_data, recent_history)
        
        # 1. HRV modification
        if show_hrv_pattern:
            hrv_change_factor = 0.15 * progression * pattern_strength * hrv_sensitivity * cross_stress_mults['hrv']
            daily_hrv_adjustment = daily_variability * baseline_hrv * 0.1
            
            new_hrv = baseline_hrv * (1 - hrv_change_factor) + daily_hrv_adjustment
            day_data['hrv'] = max(baseline_hrv * 0.75, min(baseline_hrv * 1.1, new_hrv))
        
        # 2. RHR modification
        if show_rhr_pattern:
            rhr_change_factor = 0.08 * progression * pattern_strength * rhr_sensitivity * cross_stress_mults['rhr']
            daily_rhr_adjustment = -daily_variability * baseline_rhr * 0.05
            
            new_rhr = baseline_rhr * (1 + rhr_change_factor) + daily_rhr_adjustment
            day_data['resting_hr'] = max(baseline_rhr * 0.95, min(baseline_rhr * 1.1, new_rhr))
        
        # 3. Sleep quality modification
        if show_sleep_pattern and i > pattern_days // 3:  # Start sleep issues later
            sleep_reduction = 0.1 * progression * pattern_strength * sleep_sensitivity * cross_stress_mults['sleep']
            daily_sleep_adjustment = daily_variability * 0.12
            
            new_sleep_quality = day_data['sleep_quality'] * (1 - sleep_reduction) + daily_sleep_adjustment
            day_data['sleep_quality'] = max(0.6, min(0.95, new_sleep_quality))
            
            # Mild sleep stage adjustments
            deep_sleep_reduction = sleep_reduction * (1.0 + random.uniform(-0.2, 0.2))
            day_data['deep_sleep'] = day_data['deep_sleep'] * (1 - deep_sleep_reduction)
            day_data['light_sleep'] = day_data['sleep_hours'] - day_data['deep_sleep'] - day_data['rem_sleep']
        
        # 4. Mild stress increase
        stress_increase = min(20, progression * 25 * pattern_strength) * stress_sensitivity * cross_stress_mults['stress']
        stress_daily_variability = random.normalvariate(0, 6)
        
        new_stress = day_data['stress'] + stress_increase + stress_daily_variability
        day_data['stress'] = min(85, max(20, new_stress))
    
    return daily_data_list

def calculate_cross_stress_effects(metrics, history=None):
    """
    Calculate multiplicative effects between different stressors.
    
    Args:
        metrics: Dictionary of current day's metrics
        history: Optional list of previous days' metrics
    
    Returns:
        Dictionary of interaction multipliers for various metrics
    """
    multipliers = {
        'hrv': 1.0,
        'rhr': 1.0,
        'sleep': 1.0,
        'stress': 1.0,
        'body_battery': 1.0
    }
    
    # Sleep and stress interaction (poor sleep + high stress = worse effect)
    if metrics['sleep_quality'] < 0.6 and metrics['stress'] > 70:
        multipliers['hrv'] *= 1.4  # 40% stronger HRV impact
        multipliers['rhr'] *= 1.3  # 30% stronger RHR impact
    
    # High fatigue and poor sleep interaction
    if 'fatigue' in metrics and metrics['fatigue'] > 75 and metrics['sleep_quality'] < 0.7:
        multipliers['hrv'] *= 1.5
        multipliers['body_battery'] *= 1.4
    
    # Temporal sequence effects (if we have history)
    if history and len(history) >= 3:
        # High stress followed by high training load
        if (history[-3]['stress'] > 70 and 
            history[-2]['stress'] > 70 and 
            history[-1]['actual_tss'] > history[-1]['planned_tss'] * 1.1):
            multipliers['hrv'] *= 1.6
            multipliers['sleep'] *= 1.3
    
    return multipliers