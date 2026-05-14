def process_engine_states(
    statistics_data,
    execution_data
):

    states_data = {
        "market_mode": "NORMAL",
        "engine_state": "ACTIVE",
        "risk_state": "NORMAL",
        "kill_switch": False,
    }

    return states_data