"""
Configuration management for synthetic data generation.

Provides centralized access to all simulation parameters through the SimConfig class.
Parameters are loaded from YAML configuration files and can be overridden at runtime.
"""

import os
import yaml
from typing import Any, Dict, Optional
from functools import lru_cache


class SimConfig:
    """
    Centralized configuration for synthetic data generation.

    Usage:
        from config import SimConfig

        # Access parameters using dot notation
        threshold = SimConfig.get('injury_model.acwr_thresholds.undertrained')

        # Or get entire sections
        injury_config = SimConfig.get('injury_model')

        # Override for specific experiments
        SimConfig.override('injury_model.physiological.base_daily_risk', 0.01)
    """

    _config: Optional[Dict[str, Any]] = None
    _overrides: Dict[str, Any] = {}
    _config_path: Optional[str] = None

    @classmethod
    def _load_config(cls) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if cls._config is not None:
            return cls._config

        # Find config file
        if cls._config_path:
            config_path = cls._config_path
        else:
            # Default path relative to this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, 'simulation_config.yaml')

        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                "Please ensure simulation_config.yaml exists in the config directory."
            )

        with open(config_path, 'r') as f:
            cls._config = yaml.safe_load(f)

        return cls._config

    @classmethod
    def set_config_path(cls, path: str) -> None:
        """Set custom configuration file path."""
        cls._config_path = path
        cls._config = None  # Force reload

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Dot-separated path to the config value (e.g., 'injury_model.acwr_thresholds.undertrained')
            default: Default value if key not found

        Returns:
            The configuration value or default
        """
        # Check overrides first
        if key in cls._overrides:
            return cls._overrides[key]

        config = cls._load_config()

        # Navigate the nested dict
        keys = key.split('.')
        value = config

        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                elif isinstance(value, list) and k.isdigit():
                    value = value[int(k)]
                else:
                    return default
            return value
        except (KeyError, IndexError, TypeError):
            return default

    @classmethod
    def get_section(cls, section: str) -> Dict[str, Any]:
        """Get an entire configuration section."""
        return cls.get(section, {})

    @classmethod
    def override(cls, key: str, value: Any) -> None:
        """
        Override a configuration value at runtime.
        Useful for experiments with different parameters.

        Args:
            key: Dot-separated path to the config value
            value: New value to use
        """
        cls._overrides[key] = value

    @classmethod
    def reset_overrides(cls) -> None:
        """Clear all runtime overrides."""
        cls._overrides = {}

    @classmethod
    def reload(cls) -> None:
        """Force reload of configuration from file."""
        cls._config = None
        cls._load_config()

    # =========================================================================
    # CONVENIENCE METHODS FOR COMMON PARAMETER ACCESS
    # =========================================================================

    @classmethod
    def injury_model(cls) -> Dict[str, Any]:
        """Get injury model configuration."""
        return cls.get_section('injury_model')

    @classmethod
    def acwr_thresholds(cls) -> Dict[str, float]:
        """Get ACWR zone thresholds."""
        return cls.get('injury_model.acwr_thresholds', {
            'undertrained': 0.8,
            'optimal_upper': 1.3,
            'danger_zone': 1.5
        })

    @classmethod
    def wellness_weights(cls) -> Dict[str, float]:
        """Get wellness vulnerability component weights."""
        return cls.get('wellness_vulnerability.weights', {
            'sleep_deficit': 0.25,
            'poor_sleep_quality': 0.15,
            'high_stress': 0.20,
            'low_recovery': 0.15,
            'fatigue': 0.15,
            'negative_form': 0.10
        })

    @classmethod
    def load_spike_config(cls, spike_type: str) -> Dict[str, Any]:
        """Get configuration for a specific load spike type."""
        return cls.get(f'load_spikes.{spike_type}', {})

    @classmethod
    def training_model(cls) -> Dict[str, Any]:
        """Get training model configuration."""
        return cls.get_section('training_model')

    @classmethod
    def athlete_profiles(cls) -> Dict[str, Any]:
        """Get athlete profile generation configuration."""
        return cls.get_section('athlete_profiles')

    @classmethod
    def preinjury_patterns(cls) -> Dict[str, Any]:
        """Get pre-injury pattern configuration."""
        return cls.get_section('preinjury_patterns')

    @classmethod
    def hrv_model(cls) -> Dict[str, Any]:
        """Get HRV simulation configuration."""
        return cls.get_section('hrv_model')

    @classmethod
    def rhr_model(cls) -> Dict[str, Any]:
        """Get RHR simulation configuration."""
        return cls.get_section('rhr_model')

    @classmethod
    def sleep_model(cls) -> Dict[str, Any]:
        """Get sleep simulation configuration."""
        return cls.get_section('sleep_model')

    @classmethod
    def stress_model(cls) -> Dict[str, Any]:
        """Get stress simulation configuration."""
        return cls.get_section('stress_model')

    @classmethod
    def body_battery(cls) -> Dict[str, Any]:
        """Get body battery simulation configuration."""
        return cls.get_section('body_battery')


# Shorthand alias
cfg = SimConfig
