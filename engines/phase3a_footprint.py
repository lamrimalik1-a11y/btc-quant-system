def process_footprint(
    row_data,
    orderbook_data
):

    footprint_data = {
        "footprint_delta": 0,
        "stacked_imbalance": False,
        "delta_divergence": False,
        "failed_auction": False,
    }

    return footprint_data