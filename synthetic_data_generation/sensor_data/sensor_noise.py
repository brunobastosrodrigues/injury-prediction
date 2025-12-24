import random
import numpy as np

class SensorNoiseModel:
    """
    Simulates noise profiles for different types of wearable sensors.
    Can be used to add realism to idealized physiological and activity data.
    """

    @staticmethod
    def apply_hr_spikes(hr_value, probability=0.01, spike_magnitude=(10, 30)):
        """
        Simulates occasional heart rate spikes (common in chest straps with poor contact 
        or optical sensors with light leakage).
        """
        if random.random() < probability:
            spike = random.uniform(*spike_magnitude)
            # 80% chance of upward spike, 20% chance of downward dropout
            if random.random() < 0.8:
                return hr_value + spike
            else:
                return max(40, hr_value - spike)
        return hr_value

    @staticmethod
    def apply_optical_noise(hr_value, intensity_factor, noise_base=2.0):
        """
        Simulates noise in optical heart rate sensors (vulnerable to motion artifacts).
        Noise increases with intensity.
        """
        # Noise scales with intensity (higher movement = more artifacts)
        noise_std = noise_base + (intensity_factor ** 2) * 5.0
        noise = random.normalvariate(0, noise_std)
        return max(40, hr_value + noise)

    @staticmethod
    def apply_gps_noise(distance_km, quality_factor=1.0):
        """
        Simulates GPS inaccuracies in distance calculation.
        quality_factor: 1.0 is good, >1.0 is worse.
        """
        # Typical GPS error is 1-3%
        error_percent = random.normalvariate(0, 0.01 * quality_factor)
        return max(0, distance_km * (1 + error_percent))

    @classmethod
    def apply_garmin_profile(cls, activity_data):
        """
        Profile: Generally high quality but with occasional HR spikes.
        """
        # Apply occasional spikes to avg and max HR
        if 'avg_hr' in activity_data:
            activity_data['avg_hr'] = cls.apply_hr_spikes(activity_data['avg_hr'], probability=0.05)
        if 'max_hr' in activity_data:
            activity_data['max_hr'] = cls.apply_hr_spikes(activity_data['max_hr'], probability=0.1)
        
        # Minor GPS noise
        if 'distance_km' in activity_data:
            activity_data['distance_km'] = cls.apply_gps_noise(activity_data['distance_km'], quality_factor=0.8)
            
        return activity_data

    @classmethod
    def apply_optical_profile(cls, activity_data):
        """
        Profile: Generic optical sensor with significant noise during high intensity.
        """
        intensity = activity_data.get('intensity_factor', 0.7)
        
        if 'avg_hr' in activity_data:
            activity_data['avg_hr'] = cls.apply_optical_noise(activity_data['avg_hr'], intensity)
        if 'max_hr' in activity_data:
            activity_data['max_hr'] = cls.apply_optical_noise(activity_data['max_hr'], intensity, noise_base=4.0)
            
        # Slightly worse GPS noise typically found in budget watches
        if 'distance_km' in activity_data:
            activity_data['distance_km'] = cls.apply_gps_noise(activity_data['distance_km'], quality_factor=1.5)
            
        return activity_data

    @classmethod
    def apply_daily_noise(cls, daily_data):
        """
        Apply noise to daily physiological metrics (RHR, HRV).
        """
        # Resting HR noise (minor)
        if 'resting_hr' in daily_data and daily_data['resting_hr'] is not None:
            daily_data['resting_hr'] += random.normalvariate(0, 0.5)
            
        # HRV noise (HRV measurements are very sensitive to movement/breathing)
        if 'hrv' in daily_data and daily_data['hrv'] is not None:
            daily_data['hrv'] += random.normalvariate(0, 2.0)
            
        # Sleep hours noise (watches often overestimate or underestimate sleep start/end)
        if 'sleep_hours' in daily_data and daily_data['sleep_hours'] is not None:
            daily_data['sleep_hours'] = max(0, daily_data['sleep_hours'] + random.normalvariate(0, 0.25))
            
        return daily_data
