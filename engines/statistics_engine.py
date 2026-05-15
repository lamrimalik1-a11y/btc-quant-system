# ==================================================
# STATISTICS ENGINE
# ==================================================

from engines.base_engine import (
    BaseEngine
)

from core.statistics import (

    add_zscores,

    add_statistical_zones,

    add_distribution_features,
)

from core.state import (

    price_history,

    volume_history,

    delta_history,

    velocity_history,
)


class StatisticsEngine(
    BaseEngine
):

    ENGINE_NAME = (
        "statistics_engine"
    )

    PRIORITY = 10


    def process(
        self,
        context
    ):

        row = context.row

        row = add_zscores(

            row,

            list(price_history),

            list(volume_history),

            list(delta_history),

            list(velocity_history),
        )

        row = add_statistical_zones(
            row
        )

        row = add_distribution_features(
            row
        )

        context.row = row

        self.output = {

            "price_zscore":
                row.get(
                    "price_zscore"
                ),

            "volume_zscore":
                row.get(
                    "volume_zscore"
                ),

            "delta_zscore":
                row.get(
                    "delta_zscore"
                ),

            "velocity_zscore":
                row.get(
                    "velocity_zscore"
                ),

            "fast_price_zscore":
                row.get(
                    "fast_price_zscore"
                ),

            "medium_price_zscore":
                row.get(
                    "medium_price_zscore"
                ),

            "slow_price_zscore":
                row.get(
                    "slow_price_zscore"
                ),

            "price_variance":
                row.get(
                    "price_variance"
                ),

            "volume_variance":
                row.get(
                    "volume_variance"
                ),

            "delta_variance":
                row.get(
                    "delta_variance"
                ),

            "velocity_variance":
                row.get(
                    "velocity_variance"
                ),

            "distribution_ready":
                row.get(
                    "distribution_ready"
                ),

            "price_percentile":
                row.get(
                    "price_percentile"
                ),

            "price_percentile_zone":
                row.get(
                    "price_percentile_zone"
                ),
        }

        return self.output