from collections import deque


market_state = {

    "last_price": None,

    "last_trade": None,

    "current_row": None,

    "orderbook": {},

    "signals": [],

    "zones": [],

    "execution_state": {},
}


statistics_state = {

    "price_history": deque(maxlen=500),

    "volume_history": deque(maxlen=500),

    "delta_history": deque(maxlen=500),

    "velocity_history": deque(maxlen=500),

    "spread_history": deque(maxlen=500),
}


microstructure_state = {

    "icebergs": [],

    "spoofing_events": [],

    "sweeps": [],

    "imbalances": [],
}


engine_state = {

    "current_regime": None,

    "entropy_state": None,

    "risk_state": None,
}


system_state = {

    "row_counter": 0,
}


price_history = statistics_state["price_history"]

volume_history = statistics_state["volume_history"]

delta_history = statistics_state["delta_history"]

velocity_history = statistics_state["velocity_history"]


def update_history(row):

    price_history.append(
        row["close"]
    )

    volume_history.append(
        row["volume"]
    )

    delta_history.append(
        row["delta"]
    )

    velocity_history.append(
        row["velocity"]
    )

    system_state["row_counter"] += 1