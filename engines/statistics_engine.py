# ==================================================
# STATISTICS ENGINE
# ==================================================

from engines.base_engine import BaseEngine
from core.statistics import add_distribution_features


class StatisticsEngine(BaseEngine):

    ENGINE_NAME = "statistics_engine"
    PRIORITY = 10

    def process(self, context):

        row = context.row

        row = add_distribution_features(row)

        context.row = row

        self.output = {

            "price_zscore": row.get("price_zscore"),
            "volume_zscore": row.get("volume_zscore"),
            "delta_zscore": row.get("delta_zscore"),
            "velocity_zscore": row.get("velocity_zscore"),

            "fast_price_zscore": row.get("fast_price_zscore"),
            "medium_price_zscore": row.get("medium_price_zscore"),
            "slow_price_zscore": row.get("slow_price_zscore"),

            "price_std": row.get("price_std"),
            "price_weighted_std": row.get("price_weighted_std"),
            "price_robust_std": row.get("price_robust_std"),
            "price_ewma_std": row.get("price_ewma_std"),
            "price_volatility_weighted_std": row.get("price_volatility_weighted_std"),
            "price_adaptive_std": row.get("price_adaptive_std"),
            "std_instability_state": row.get("std_instability_state"),

            "volume_adaptive_std": row.get("volume_adaptive_std"),
            "delta_adaptive_std": row.get("delta_adaptive_std"),
            "velocity_adaptive_std": row.get("velocity_adaptive_std"),
            "volume_mean": row.get("volume_mean"),
            "volume_std": row.get("volume_std"),
            "volume_state": row.get("volume_state"),
            "volume_expansion": row.get("volume_expansion"),
            "volume_compression": row.get("volume_compression"),
            "abnormal_volume": row.get("abnormal_volume"),
            "climactic_volume": row.get("climactic_volume"),
            "spread_mean": row.get("spread_mean"),
            "spread_std": row.get("spread_std"),
            "spread_zscore": row.get("spread_zscore"),
            "spread_state": row.get("spread_state"),
            "spread_expansion": row.get("spread_expansion"),
            "spread_compression": row.get("spread_compression"),
            "abnormal_spread": row.get("abnormal_spread"),
            "execution_quality": row.get("execution_quality"),
            "velocity_mean": row.get("velocity_mean"),
            "velocity_std": row.get("velocity_std"),
            "velocity_state": row.get("velocity_state"),
            "velocity_expansion": row.get("velocity_expansion"),
            "velocity_compression": row.get("velocity_compression"),
            "abnormal_velocity": row.get("abnormal_velocity"),
            "velocity_change": row.get("velocity_change"),
            "velocity_acceleration": row.get("velocity_acceleration"),
            "velocity_acceleration_state": row.get("velocity_acceleration_state"),
            "velocity_deceleration": row.get("velocity_deceleration"),
            "velocity_shock": row.get("velocity_shock"),
            "velocity_exhaustion": row.get("velocity_exhaustion"),
            "velocity_exhaustion_state": row.get("velocity_exhaustion_state"),
            "exhaustion_strength": row.get("exhaustion_strength"),

            "price_variance": row.get("price_variance"),
            "volume_variance": row.get("volume_variance"),
            "delta_variance": row.get("delta_variance"),
            "velocity_variance": row.get("velocity_variance"),

            "volatility_ratio": row.get("volatility_ratio"),
            "volatility_regime": row.get("volatility_regime"),
            "volatility_transition": row.get("volatility_transition"),
            "volatility_persistence": row.get("volatility_persistence"),
            "volatility_acceleration": row.get("volatility_acceleration"),
            "price_mean_shift": row.get("price_mean_shift"),
            "price_std_shift": row.get("price_std_shift"),
            "distribution_shift": row.get("distribution_shift"),
            "distribution_shift_state": row.get("distribution_shift_state"),
            "distribution_shift_strength": row.get("distribution_shift_strength"),
            "price_gaussian_prob": row.get("price_gaussian_prob"),
            "gaussian_zone": row.get("gaussian_zone"),
            "gaussian_tail": row.get("gaussian_tail"),
            "gaussian_extreme": row.get("gaussian_extreme"),
            "gaussian_confidence": row.get("gaussian_confidence"),
            "price_extreme_event": row.get("price_extreme_event"),
            "volume_extreme_event": row.get("volume_extreme_event"),
            "delta_extreme_event": row.get("delta_extreme_event"),
            "velocity_extreme_event": row.get("velocity_extreme_event"),
            "gaussian_extreme_event": row.get("gaussian_extreme_event"),
            "spread_extreme_event": row.get("spread_extreme_event"),
            "global_extreme_event": row.get("global_extreme_event"),
            "extreme_event_score": row.get("extreme_event_score"),
            "extreme_event_state": row.get("extreme_event_state"),
            "extreme_event_context": row.get("extreme_event_context"),
            "extreme_event_origin": row.get("extreme_event_origin"),

            "adaptive_distribution_window": row.get("adaptive_distribution_window"),

            "distribution_ready": row.get("distribution_ready"),

            "price_percentile": row.get("price_percentile"),
            "volume_percentile": row.get("volume_percentile"),
            "delta_percentile": row.get("delta_percentile"),
            "velocity_percentile": row.get("velocity_percentile"),

            "price_percentile_zone": row.get("price_percentile_zone"),

            "price_tail_side": row.get("price_tail_side"),
            "price_tail_strength": row.get("price_tail_strength"),
            "price_tail_risk": row.get("price_tail_risk"),
            "price_tail_persistence": row.get("price_tail_persistence"),
            "price_tail_exhaustion": row.get("price_tail_exhaustion"),

            "cumulative_delta": row.get("cumulative_delta"),
            "delta_domination": row.get("delta_domination"),
            "aggressive_flow": row.get("aggressive_flow"),
            "delta_pressure": row.get("delta_pressure"),
            "delta_pressure_state": row.get("delta_pressure_state"),
            "delta_acceleration": row.get("delta_acceleration"),
            "delta_acceleration_state": row.get("delta_acceleration_state"),
            "delta_exhaustion": row.get("delta_exhaustion"),
            "imbalance_state": row.get("imbalance_state"),
        }

        return self.output
