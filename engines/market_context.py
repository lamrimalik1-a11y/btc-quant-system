def build_market_context(
    phase1_data,
    statistics_data,
    zones_data,
    liquidity_data,
    footprint_data,
    microstructure_data,
    execution_data,
    states_data
):

    market_context = {
        "phase1": phase1_data,
        "statistics": statistics_data,
        "zones": zones_data,
        "liquidity": liquidity_data,
        "footprint": footprint_data,
        "microstructure": microstructure_data,
        "execution": execution_data,
        "states": states_data,
    }

    return market_context