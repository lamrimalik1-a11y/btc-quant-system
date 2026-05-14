def build_trade_row(trades):

    prices = [trade["price"] for trade in trades]
    quantities = [trade["quantity"] for trade in trades]

    open_price = prices[0]
    high_price = max(prices)
    low_price = min(prices)
    close_price = prices[-1]

    total_volume = sum(quantities)

    buy_volume = sum(
        trade["quantity"]
        for trade in trades
        if trade["is_buyer_maker"] is False
    )

    sell_volume = sum(
        trade["quantity"]
        for trade in trades
        if trade["is_buyer_maker"] is True
    )

    delta = buy_volume - sell_volume

    delta_ratio = 0

    if total_volume > 0:
        delta_ratio = abs(delta) / total_volume

    duration_seconds = (
        trades[-1]["timestamp"] - trades[0]["timestamp"]
    ) / 1000

    velocity = 0

    if duration_seconds > 0:
        velocity = total_volume / duration_seconds

    rvi = velocity

    return {

        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,

        "volume": total_volume,
        "buy_volume": buy_volume,
        "sell_volume": sell_volume,

        "delta": delta,
        "delta_ratio": delta_ratio,

        "velocity": velocity,
        "rvi": rvi,

        "duration_seconds": duration_seconds,
        "tick_count": len(trades),
    }


def process_phase1(row_data):

    return {

        "open": row_data.get("open"),
        "high": row_data.get("high"),
        "low": row_data.get("low"),
        "close": row_data.get("close"),

        "volume": row_data.get("volume"),
        "buy_volume": row_data.get("buy_volume"),
        "sell_volume": row_data.get("sell_volume"),

        "delta": row_data.get("delta"),
        "delta_ratio": row_data.get("delta_ratio"),

        "velocity": row_data.get("velocity"),
        "rvi": row_data.get("rvi"),

        "duration_seconds": row_data.get("duration_seconds"),
        "tick_count": row_data.get("tick_count"),
    }