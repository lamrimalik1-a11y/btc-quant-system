import time


market_clock = {

    "last_trade_timestamp": None,

    "last_depth_timestamp": None,

    "trade_depth_delay_ms": 0,

    "clock_drift_ms": 0,
}


def update_trade_clock(
    timestamp
):

    market_clock[
        "last_trade_timestamp"
    ] = timestamp

    update_delay()


def update_depth_clock():

    current_time_ms = int(
        time.time() * 1000
    )

    market_clock[
        "last_depth_timestamp"
    ] = current_time_ms

    update_delay()


def update_delay():

    trade_ts = market_clock[
        "last_trade_timestamp"
    ]

    depth_ts = market_clock[
        "last_depth_timestamp"
    ]

    if (
        trade_ts is None
        or
        depth_ts is None
    ):
        return

    delay = abs(
        trade_ts - depth_ts
    )

    market_clock[
        "trade_depth_delay_ms"
    ] = delay


def get_market_clock():

    return market_clock