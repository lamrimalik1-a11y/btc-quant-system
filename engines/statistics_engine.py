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

            "price_variance": row.get("price_variance"),
            "volume_variance": row.get("volume_variance"),
            "delta_variance": row.get("delta_variance"),
            "velocity_variance": row.get("velocity_variance"),

            "volatility_ratio": row.get("volatility_ratio"),
            "volatility_regime": row.get("volatility_regime"),
            "volatility_transition": row.get("volatility_transition"),
            "volatility_persistence": row.get("volatility_persistence"),
            "volatility_acceleration": row.get("volatility_acceleration"),

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