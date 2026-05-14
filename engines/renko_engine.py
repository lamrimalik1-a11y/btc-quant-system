from engines.base_engine import (
    BaseEngine
)

from core.rvi import (
    add_rvi,
)

from core.renko import (
    process_renko,
)

from core.state import (
    velocity_history
)


class RenkoEngine(
    BaseEngine
):

    ENGINE_NAME = (
        "renko_engine"
    )

    PRIORITY = 20


    def process(
        self,
        context
    ):

        row = context.row

        row = add_rvi(
            row,
            velocity_history
        )

        row = process_renko(
            row
        )

        context.row = row

        self.output = {

            "rvi":
                row.get(
                    "rvi"
                ),

            "rvi_state":
                row.get(
                    "rvi_state"
                ),

            "renko_direction":
                row.get(
                    "renko_direction"
                ),

            "renko_event":
                row.get(
                    "renko_event"
                ),

            "renko_bricks":
                row.get(
                    "renko_bricks"
                ),
        }

        return self.output