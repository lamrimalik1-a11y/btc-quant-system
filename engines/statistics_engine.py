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

        adaptive_window = row.get(
            "adaptive_window",
            20
        )

        row = add_zscores(

            row,

            list(price_history)[
                -adaptive_window:
            ],

            list(volume_history)[
                -adaptive_window:
            ],

            list(delta_history)[
                -adaptive_window:
            ],

            list(velocity_history)[
                -adaptive_window:
            ],
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