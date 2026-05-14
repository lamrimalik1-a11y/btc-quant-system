def process_liquidity(
    orderbook_data,
    zones_data
):

    liquidity_data = {
        "bid_wall": None,
        "ask_wall": None,
        "liquidity_sweep": False,
        "spoofing_detected": False,
        "iceberg_detected": False,
    }

    return liquidity_data