"""
Budget Optimization Engine for MarketingROITracker.

This module analyzes channel performance metrics to suggest optimal budget 
reallocations. It moves beyond simple reporting by providing actionable 
insights based on relative efficiency scores, helping marketing managers 
maximize ROI across their portfolio.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from config.settings import ChannelName


@dataclass(slots=True)
class OptimizationResult:
    """Bundles the output of the optimization analysis."""
    suggested_allocations: dict[str, float]
    comparison_df: pd.DataFrame
    narrative: list[str]


def suggest_reallocation(
    df: pd.DataFrame, 
    total_budget: float | None = None
) -> dict[str, float]:
    """
    Proposes a new budget allocation percentage per channel based on 
    relative efficiency_score.
    
    Logic:
    1. Channels with higher efficiency scores receive proportionally more budget.
    2. A minimum floor (5%) is applied to all channels to ensure no channel 
       is completely starved, acknowledging brand/awareness value not captured 
       by last-click ROAS.
    3. The result is normalized to sum to 100%.
    """
    if 'efficiency_score' not in df.columns:
        raise ValueError(
            "Input dataframe must contain an 'efficiency_score' column. "
            "Please run analytics.metrics.compute_efficiency_score first."
        )

    # Handle single channel edge case
    if (n_channels := len(df)) == 1:
        return {df.iloc[0]['channel']: 1.0}

    # Extract scores and channels
    channels = df['channel'].tolist()
    scores = df['efficiency_score'].to_numpy(dtype=float)
    
    # Handle case where all scores are 0 or NaN (fallback to equal distribution)
    if np.all(scores == 0) or np.isnan(scores).all():
        return {ch: 1.0 / n_channels for ch in channels}

    # Calculate raw weights based on efficiency
    total_score = scores.sum()
    raw_weights = scores / total_score if total_score > 0 else np.ones(n_channels) / n_channels
    
    # Apply minimum floor (5%)
    min_allocation = 0.05
    capped_weights = np.maximum(raw_weights, min_allocation)
    
    # Normalize to ensure sum is exactly 1.0
    final_allocations = capped_weights / capped_weights.sum()
    
    return dict(zip(channels, final_allocations))


def compute_current_vs_suggested(
    df: pd.DataFrame, 
    suggested_allocations: dict[str, float]
) -> pd.DataFrame:
    """
    Generates a comparison dataframe showing current vs. suggested budget 
    allocation in both percentages and absolute dollars.
    """
    if df.empty:
        return pd.DataFrame()

    total_current_spend = df['spend'].sum()
    
    # Create a copy to avoid SettingWithCopyWarning
    comp_df = df[['channel', 'spend', 'roas', 'efficiency_score']].copy()
    
    # Current metrics
    comp_df['current_pct'] = comp_df['spend'] / total_current_spend if total_current_spend > 0 else 0.0
    comp_df['current_spend'] = comp_df['spend']
    
    # Suggested metrics
    comp_df['suggested_pct'] = comp_df['channel'].map(suggested_allocations).fillna(0.0)
    # Calculate suggested dollars based on total current spend (assuming fixed budget scenario)
    comp_df['suggested_spend'] = comp_df['suggested_pct'] * total_current_spend
    
    # Deltas
    comp_df['delta_pct'] = comp_df['suggested_pct'] - comp_df['current_pct']
    comp_df['delta_spend'] = comp_df['suggested_spend'] - comp_df['current_spend']
    
    # Sort by suggested allocation descending for better readability
    return comp_df.sort_values(by='suggested_pct', ascending=False)


def generate_optimization_narrative(comparison_df: pd.DataFrame) -> list[str]:
    """
    Generates plain-English, professional insights based on the optimization 
    comparison data.
    """
    if comparison_df.empty:
        return ["No data available for optimization insights."]

    insights: list[str] = []
    
    # 1. Identify the biggest gainer
    if (max_gain_row := comparison_df.loc[comparison_df['delta_spend'].idxmax()])['delta_spend'] > 0:
        channel = max_gain_row['channel']
        delta = max_gain_row['delta_spend']
        pct = max_gain_row['delta_pct'] * 100
        insights.append(
            f"**{channel.replace('_', ' ').title()}** shows the highest efficiency potential; "
            f"increasing its budget by ${delta:,.0f} ({pct:+.1f}%) is recommended to capitalize on its performance."
        )
        
    # 2. Identify the biggest loser (optimization opportunity)
    if (max_loss_row := comparison_df.loc[comparison_df['delta_spend'].idxmin()])['delta_spend'] < 0:
        channel = max_loss_row['channel']
        delta = abs(max_loss_row['delta_spend'])
        insights.append(
            f"**{channel.replace('_', ' ').title()}** is currently over-funded relative to its efficiency score; "
            f"reallocating ${delta:,.0f} from this channel will improve overall portfolio ROI."
        )
        
    # 3. General efficiency observation
    avg_efficiency = comparison_df['efficiency_score'].mean()
    if avg_efficiency > 70:
        insights.append("Overall portfolio efficiency is strong, suggesting current allocations are well-optimized.")
    elif avg_efficiency < 40:
        insights.append("Portfolio efficiency indicates significant room for improvement; consider reviewing campaign-level tactics alongside budget shifts.")

    return insights


def run_optimization(
    df: pd.DataFrame, 
    total_budget: float | None = None
) -> OptimizationResult:
    """
    Top-level convenience function that executes the full optimization pipeline:
    1. Suggests reallocation percentages.
    2. Computes current vs. suggested comparison.
    3. Generates narrative insights.
    """
    suggested_allocations = suggest_reallocation(df, total_budget)
    comparison_df = compute_current_vs_suggested(df, suggested_allocations)
    narrative = generate_optimization_narrative(comparison_df)
    
    return OptimizationResult(
        suggested_allocations=suggested_allocations,
        comparison_df=comparison_df,
        narrative=narrative
    )
