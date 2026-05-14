from engines.base_engine import (
    BaseEngine
)


class ContextEngine(
    BaseEngine
):

    ENGINE_NAME = (
        "context_engine"
    )

    PRIORITY = 1


    def process(
        self,
        context
    ):

        row = context.row

        self.output = {

            "row_close":
                row.get(
                    "close"
                ),

            "row_volume":
                row.get(
                    "volume"
                ),

            "market_session":
                context.session,

            "spread":
                row.get(
                    "spread"
                ),

            "imbalance":
                row.get(
                    "imbalance"
                ),

            "adaptive_window":
                row.get(
                    "adaptive_window"
                ),
        }

        return self.output