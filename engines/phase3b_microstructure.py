def process_microstructure(
    orderbook_data,
    footprint_data
):

    microstructure_data = {
        "microstructure_state": "NEUTRAL",
        "bullish_score": 0,
        "bearish_score": 0,
        "risk_score": 0,
        "iceberg": False,
        "spoofing": False,
        "hidden_liquidity": False,
        "liquidity_vacuum": False,
    }

    return microstructure_data