BRICK_SIZE = 10

EXPANSION_BRICK_THRESHOLD = 3


renko_state = {

    "last_brick_close": None,

    "direction": "NEUTRAL",

    "brick_count": 0,
}


def process_renko(row):

    current_price = row["close"]

    if renko_state["last_brick_close"] is None:

        renko_state["last_brick_close"] = current_price

        row["renko_direction"] = "NEUTRAL"

        row["renko_event"] = "INITIALIZATION"

        row["renko_bricks"] = 0

        row["renko_expansion"] = False

        return row

    last_close = renko_state["last_brick_close"]

    price_move = current_price - last_close

    bricks = int(
        abs(price_move) / BRICK_SIZE
    )

    if bricks == 0:

        row["renko_direction"] = renko_state["direction"]

        row["renko_event"] = "COMPRESSION"

        row["renko_bricks"] = 0

        row["renko_expansion"] = False

        return row

    if price_move > 0:

        new_direction = "UP"

    else:

        new_direction = "DOWN"

    if (
        renko_state["direction"] != "NEUTRAL"
        and new_direction != renko_state["direction"]
    ):

        event = "REVERSAL"

    else:

        event = "CONTINUATION"

    renko_expansion = (
        bricks >= EXPANSION_BRICK_THRESHOLD
    )

    if renko_expansion:

        event = "EXPANSION"

    renko_state["direction"] = new_direction

    renko_state["brick_count"] += bricks

    if new_direction == "UP":

        renko_state["last_brick_close"] = (
            last_close + BRICK_SIZE * bricks
        )

    else:

        renko_state["last_brick_close"] = (
            last_close - BRICK_SIZE * bricks
        )

    row["renko_direction"] = new_direction

    row["renko_event"] = event

    row["renko_bricks"] = bricks

    row["renko_expansion"] = renko_expansion

    return row