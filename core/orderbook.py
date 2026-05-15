# ==================================================
# ORDERBOOK PROCESSOR
# ==================================================

def process_orderbook(depth_data):

    if depth_data is None:
        return None

    bids = (
        depth_data.get("bids")
        or depth_data.get("b")
        or []
    )

    asks = (
        depth_data.get("asks")
        or depth_data.get("a")
        or []
    )

    if len(bids) == 0 or len(asks) == 0:
        return None

    try:
        best_bid_price = float(bids[0][0])
        best_bid_size = float(bids[0][1])

        best_ask_price = float(asks[0][0])
        best_ask_size = float(asks[0][1])

    except Exception:
        return None

    spread = best_ask_price - best_bid_price

    total_bid_volume = sum(
        float(level[1])
        for level in bids
    )

    total_ask_volume = sum(
        float(level[1])
        for level in asks
    )

    total_volume = total_bid_volume + total_ask_volume

    if total_volume > 0:
        imbalance = (
            total_bid_volume - total_ask_volume
        ) / total_volume
    else:
        imbalance = 0

    largest_bid_level = max(
        bids,
        key=lambda level: float(level[1])
    )

    largest_ask_level = max(
        asks,
        key=lambda level: float(level[1])
    )

    bid_wall_price = float(largest_bid_level[0])
    bid_wall_size = float(largest_bid_level[1])

    ask_wall_price = float(largest_ask_level[0])
    ask_wall_size = float(largest_ask_level[1])

    liquidity_strength = (
        total_bid_volume + total_ask_volume
    )

    return {
        "best_bid_price": best_bid_price,
        "best_bid_size": best_bid_size,
        "best_ask_price": best_ask_price,
        "best_ask_size": best_ask_size,
        "spread": spread,
        "total_bid_volume": total_bid_volume,
        "total_ask_volume": total_ask_volume,
        "imbalance": imbalance,
        "bid_wall_price": bid_wall_price,
        "bid_wall_size": bid_wall_size,
        "ask_wall_price": ask_wall_price,
        "ask_wall_size": ask_wall_size,
        "liquidity_strength": liquidity_strength,
        "bid_levels": bids,
        "ask_levels": asks,
    }