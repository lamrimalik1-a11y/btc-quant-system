def validate_trade(trade):
    required_fields = [
        "price",
        "quantity",
        "timestamp",
        "is_buyer_maker"
    ]

    for field in required_fields:
        if field not in trade:
            return False

    return True


def validate_orderbook(orderbook):
    if "bids" not in orderbook:
        return False

    if "asks" not in orderbook:
        return False

    return True


def is_duplicate_trade(trade_id, cache):
    if trade_id in cache:
        return True

    cache.add(trade_id)
    return False