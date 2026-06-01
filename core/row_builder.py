def build_trade_row(tick_buffer):

    prices = [
        trade["price"]
        for trade in tick_buffer
    ]

    buy_volume = sum(
        trade["quantity"]
        for trade in tick_buffer
        if trade["side"] == "BUY"
    )

    sell_volume = sum(
        trade["quantity"]
        for trade in tick_buffer
        if trade["side"] == "SELL"
    )

    total_volume = buy_volume + sell_volume

    delta = buy_volume - sell_volume

    delta_ratio = (
        abs(delta) / total_volume
        if total_volume > 0
        else 0
    )

    start_ts = tick_buffer[0]["timestamp"]

    end_ts = tick_buffer[-1]["timestamp"]

    duration_ms = max(
        end_ts - start_ts,
        1
    )

    duration_sec = duration_ms / 1000

    velocity = (
        total_volume / duration_sec
        if duration_sec > 0
        else 0
    )

    row = {

        "open": prices[0],

        "high": max(prices),

        "low": min(prices),

        "close": prices[-1],

        "volume": total_volume,

        "buy_volume": buy_volume,

        "sell_volume": sell_volume,

        "delta": delta,

        "delta_ratio": delta_ratio,

        "tick_count": len(tick_buffer),

        "start_ts": start_ts,

        "end_ts": end_ts,

        "market_timestamp": end_ts,

        "duration_ms": duration_ms,

        "duration_sec": duration_sec,

        "velocity": velocity,
    }

    return row
