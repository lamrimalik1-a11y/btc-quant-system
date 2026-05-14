def process_execution(
    orderbook_data,
    microstructure_data
):

    execution_data = {
        "execution_allowed": True,
        "execution_state": "NORMAL",
        "spread_state": "NORMAL_SPREAD",
        "slippage_risk": 0,
        "execution_score": 0,
    }

    return execution_data