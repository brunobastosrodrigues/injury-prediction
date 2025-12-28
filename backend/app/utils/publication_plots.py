"""
Publication-quality visualization utilities for validation studies.

Generates high-impact plots for scientific papers demonstrating:
1. Statistical Fidelity (Raincloud plots)
2. Causal Fidelity (Risk Landscape, Causal Asymmetry)
3. Transferability (ROC curves with confidence intervals)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import io
import base64


def calculate_raincloud_data(
    df_synth: pd.DataFrame,
    df_real: pd.DataFrame,
    feature: str
) -> Dict[str, Any]:
    """
    Prepare data for raincloud plot visualization.
    Returns summary statistics and density data for frontend rendering.
    """
    if feature not in df_synth.columns or feature not in df_real.columns:
        return {'error': f'Feature {feature} not found in data'}

    synth_values = df_synth[feature].dropna().values
    real_values = df_real[feature].dropna().values

    # Calculate density estimates using histogram bins
    bins = np.linspace(
        min(synth_values.min(), real_values.min()),
        max(synth_values.max(), real_values.max()),
        50
    )

    synth_hist, _ = np.histogram(synth_values, bins=bins, density=True)
    real_hist, _ = np.histogram(real_values, bins=bins, density=True)

    bin_centers = (bins[:-1] + bins[1:]) / 2

    # Box plot statistics
    def calc_box_stats(values):
        return {
            'min': float(np.min(values)),
            'q1': float(np.percentile(values, 25)),
            'median': float(np.percentile(values, 50)),
            'q3': float(np.percentile(values, 75)),
            'max': float(np.max(values)),
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'n': len(values)
        }

    return {
        'feature': feature,
        'synthetic': {
            'density_x': bin_centers.tolist(),
            'density_y': synth_hist.tolist(),
            'box_stats': calc_box_stats(synth_values),
            'sample_points': np.random.choice(
                synth_values,
                size=min(500, len(synth_values)),
                replace=False
            ).tolist()
        },
        'real': {
            'density_x': bin_centers.tolist(),
            'density_y': real_hist.tolist(),
            'box_stats': calc_box_stats(real_values),
            'sample_points': np.random.choice(
                real_values,
                size=min(500, len(real_values)),
                replace=False
            ).tolist()
        }
    }


def calculate_risk_landscape(
    df: pd.DataFrame,
    chronic_col: str = 'chronic_load',
    acute_col: str = 'acute_load',
    injury_col: str = 'injury',
    grid_size: int = 50
) -> Dict[str, Any]:
    """
    Calculate 2D injury risk landscape for contour visualization.
    X: Chronic Load (Fitness), Y: Acute Load, Z: Injury Probability
    """
    # If we have actual_tss but not acute/chronic, calculate them
    if chronic_col not in df.columns and 'actual_tss' in df.columns:
        # Calculate rolling averages per athlete
        df = df.sort_values(['athlete_id', 'date'])
        df['acute_load'] = df.groupby('athlete_id')['actual_tss'].transform(
            lambda x: x.rolling(7, min_periods=1).mean()
        )
        df['chronic_load'] = df.groupby('athlete_id')['actual_tss'].transform(
            lambda x: x.rolling(28, min_periods=1).mean()
        )
        chronic_col = 'chronic_load'
        acute_col = 'acute_load'

    if chronic_col not in df.columns or acute_col not in df.columns:
        return {'error': 'Required load columns not found'}

    # Filter valid data
    valid_df = df[[chronic_col, acute_col, injury_col]].dropna()

    # Define grid
    chronic_min, chronic_max = valid_df[chronic_col].quantile([0.01, 0.99])
    acute_min, acute_max = valid_df[acute_col].quantile([0.01, 0.99])

    chronic_bins = np.linspace(chronic_min, chronic_max, grid_size)
    acute_bins = np.linspace(acute_min, acute_max, grid_size)

    # Calculate empirical injury rate in each bin
    risk_grid = np.zeros((grid_size - 1, grid_size - 1))
    count_grid = np.zeros((grid_size - 1, grid_size - 1))

    for i in range(grid_size - 1):
        for j in range(grid_size - 1):
            mask = (
                (valid_df[chronic_col] >= chronic_bins[i]) &
                (valid_df[chronic_col] < chronic_bins[i + 1]) &
                (valid_df[acute_col] >= acute_bins[j]) &
                (valid_df[acute_col] < acute_bins[j + 1])
            )
            if mask.sum() > 0:
                risk_grid[j, i] = valid_df.loc[mask, injury_col].mean()
                count_grid[j, i] = mask.sum()

    # Smooth the grid using a simple average filter for visualization
    from scipy.ndimage import gaussian_filter
    try:
        risk_grid_smooth = gaussian_filter(risk_grid, sigma=2)
    except ImportError:
        risk_grid_smooth = risk_grid

    # Calculate ACWR lines for overlay
    chronic_centers = (chronic_bins[:-1] + chronic_bins[1:]) / 2
    acute_centers = (acute_bins[:-1] + acute_bins[1:]) / 2

    return {
        'chronic_values': chronic_centers.tolist(),
        'acute_values': acute_centers.tolist(),
        'risk_grid': risk_grid_smooth.tolist(),
        'count_grid': count_grid.tolist(),
        'acwr_lines': {
            'x': chronic_centers.tolist(),
            'acwr_0.8': (chronic_centers * 0.8).tolist(),
            'acwr_1.3': (chronic_centers * 1.3).tolist(),
            'acwr_1.5': (chronic_centers * 1.5).tolist()
        },
        'statistics': {
            'total_observations': int(count_grid.sum()),
            'total_injuries': int((valid_df[injury_col] == 1).sum()),
            'overall_injury_rate': float(valid_df[injury_col].mean())
        }
    }


def calculate_causal_asymmetry(
    df: pd.DataFrame,
    acwr_col: str = 'acwr',
    injury_col: str = 'injury',
    load_col: str = 'actual_tss'
) -> Dict[str, Any]:
    """
    Calculate injury risk per unit of load by ACWR zone.
    Proves the "Asymmetric ACWR" hypothesis: undertrained athletes have
    higher risk PER LOAD UNIT than overtrained athletes.
    """
    if acwr_col not in df.columns:
        return {'error': f'ACWR column {acwr_col} not found'}

    # Filter valid data
    valid_df = df[[acwr_col, injury_col, load_col]].dropna()
    valid_df = valid_df[valid_df[load_col] > 0]  # Only count training days

    # Define ACWR zones based on scientific literature
    zones = {
        'Undertrained': (0, 0.8),
        'Optimal': (0.8, 1.3),
        'Elevated': (1.3, 1.5),
        'High Risk': (1.5, float('inf'))
    }

    zone_stats = []
    for zone_name, (low, high) in zones.items():
        mask = (valid_df[acwr_col] >= low) & (valid_df[acwr_col] < high)
        zone_data = valid_df[mask]

        if len(zone_data) > 0:
            total_load = zone_data[load_col].sum()
            total_injuries = zone_data[injury_col].sum()
            total_days = len(zone_data)

            # Risk per 10,000 TSS units (normalized)
            risk_per_load = (total_injuries / total_load) * 10000 if total_load > 0 else 0

            # Also calculate injury rate per day for comparison
            injury_rate_pct = (total_injuries / total_days) * 100

            zone_stats.append({
                'zone': zone_name,
                'acwr_range': f'{low:.1f} - {high:.1f}' if high != float('inf') else f'> {low:.1f}',
                'risk_per_load': round(risk_per_load, 2),
                'injury_rate_pct': round(injury_rate_pct, 2),
                'total_injuries': int(total_injuries),
                'total_days': int(total_days),
                'total_load': round(total_load, 0),
                'avg_load_per_day': round(total_load / total_days, 1) if total_days > 0 else 0
            })

    # Calculate relative risk compared to optimal zone
    optimal_risk = next(
        (z['risk_per_load'] for z in zone_stats if z['zone'] == 'Optimal'),
        1.0
    )
    for stat in zone_stats:
        stat['relative_risk'] = round(
            stat['risk_per_load'] / optimal_risk if optimal_risk > 0 else 0,
            2
        )

    return {
        'zones': zone_stats,
        'summary': {
            'undertrained_vs_optimal': next(
                (z['relative_risk'] for z in zone_stats if z['zone'] == 'Undertrained'),
                0
            ),
            'high_risk_vs_optimal': next(
                (z['relative_risk'] for z in zone_stats if z['zone'] == 'High Risk'),
                0
            ),
            'interpretation': _generate_interpretation(zone_stats)
        }
    }


def _generate_interpretation(zone_stats: List[Dict]) -> str:
    """Generate scientific interpretation of the causal asymmetry results."""
    undertrained = next((z for z in zone_stats if z['zone'] == 'Undertrained'), None)
    optimal = next((z for z in zone_stats if z['zone'] == 'Optimal'), None)
    high_risk = next((z for z in zone_stats if z['zone'] == 'High Risk'), None)

    if not all([undertrained, optimal, high_risk]):
        return "Insufficient data across ACWR zones for interpretation."

    ut_ratio = undertrained['relative_risk']
    hr_ratio = high_risk['relative_risk']

    if ut_ratio > hr_ratio and ut_ratio > 1.5:
        return (
            f"Strong evidence of PHYSIOLOGICAL VULNERABILITY in undertrained state. "
            f"Athletes with ACWR < 0.8 show {ut_ratio:.1f}x higher injury risk per load unit "
            f"compared to optimal zone, while high ACWR (>1.5) shows only {hr_ratio:.1f}x. "
            f"This supports the detraining-tissue fragility hypothesis."
        )
    elif hr_ratio > ut_ratio:
        return (
            f"Data suggests EXPOSURE-DOMINANT risk pattern. "
            f"High load periods (ACWR > 1.5) show {hr_ratio:.1f}x risk vs optimal, "
            f"exceeding undertrained risk ({ut_ratio:.1f}x). "
            f"Consider recalibrating physiological mechanism weights."
        )
    else:
        return (
            f"Balanced risk profile detected. Undertrained: {ut_ratio:.1f}x, "
            f"High-risk: {hr_ratio:.1f}x relative to optimal zone."
        )


def calculate_wellness_vulnerability_analysis(
    df: pd.DataFrame,
    wellness_col: str = 'wellness_vulnerability',
    injury_col: str = 'injury'
) -> Dict[str, Any]:
    """
    Analyze the relationship between wellness vulnerability score and injuries.
    """
    if wellness_col not in df.columns:
        return {'error': f'Wellness vulnerability column not found'}

    valid_df = df[[wellness_col, injury_col]].dropna()

    # Bin wellness vulnerability into deciles
    valid_df['wellness_decile'] = pd.qcut(
        valid_df[wellness_col],
        q=10,
        labels=False,
        duplicates='drop'
    )

    decile_stats = valid_df.groupby('wellness_decile').agg({
        wellness_col: ['mean', 'min', 'max', 'count'],
        injury_col: ['sum', 'mean']
    }).reset_index()

    decile_stats.columns = [
        'decile', 'wellness_mean', 'wellness_min', 'wellness_max',
        'count', 'injuries', 'injury_rate'
    ]

    return {
        'deciles': decile_stats.to_dict('records'),
        'correlation': float(valid_df[wellness_col].corr(valid_df[injury_col])),
        'summary': {
            'high_vulnerability_injury_rate': float(
                valid_df[valid_df[wellness_col] > 0.7][injury_col].mean()
            ),
            'low_vulnerability_injury_rate': float(
                valid_df[valid_df[wellness_col] < 0.3][injury_col].mean()
            )
        }
    }


def calculate_load_scenario_analysis(
    df: pd.DataFrame,
    scenario_col: str = 'load_scenario',
    injury_col: str = 'injury'
) -> Dict[str, Any]:
    """
    Analyze injury rates by training load scenario (camp, return, overreach, etc.)
    """
    if scenario_col not in df.columns:
        return {'error': f'Load scenario column not found'}

    valid_df = df[[scenario_col, injury_col]].dropna()

    scenario_stats = valid_df.groupby(scenario_col).agg({
        injury_col: ['count', 'sum', 'mean']
    }).reset_index()

    scenario_stats.columns = ['scenario', 'days', 'injuries', 'injury_rate']
    scenario_stats = scenario_stats.sort_values('injury_rate', ascending=False)

    return {
        'scenarios': scenario_stats.to_dict('records'),
        'highest_risk_scenario': scenario_stats.iloc[0]['scenario'] if len(scenario_stats) > 0 else None,
        'lowest_risk_scenario': scenario_stats.iloc[-1]['scenario'] if len(scenario_stats) > 0 else None
    }


def calculate_injury_type_breakdown(
    df: pd.DataFrame,
    injury_type_col: str = 'injury_type',
    injury_col: str = 'injury'
) -> Dict[str, Any]:
    """
    Break down injuries by causal mechanism (physiological, exposure, baseline).
    """
    if injury_type_col not in df.columns:
        return {'error': f'Injury type column not found'}

    # Only consider actual injury days
    injury_df = df[df[injury_col] == 1]

    if len(injury_df) == 0:
        return {'error': 'No injuries found in data'}

    type_counts = injury_df[injury_type_col].value_counts()
    total_injuries = len(injury_df)

    breakdown = []
    for injury_type, count in type_counts.items():
        if injury_type and injury_type != 'recovery':
            breakdown.append({
                'type': str(injury_type),
                'count': int(count),
                'percentage': round(count / total_injuries * 100, 1)
            })

    return {
        'breakdown': breakdown,
        'total_injuries': total_injuries,
        'dominant_mechanism': breakdown[0]['type'] if breakdown else None
    }
