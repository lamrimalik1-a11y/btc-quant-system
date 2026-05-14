import time
from collections import deque


MAX_ALLOWED_LATENCY_MS = 5000

MAX_PRICE_JUMP_PERCENT = 5.0

MAX_QTY = 1000

RECENT_TRADE_IDS_MAXLEN = 5000


recent_trade_ids = deque(
    maxlen=RECENT_TRADE_IDS_MAXLEN
)

recent_trade_ids_set = set()

last_price = None


def remember_trade_id(trade_id):

    if trade_id is None:
        return

    if len(recent_trade_ids) >= RECENT_TRADE_IDS_MAXLEN:

        old_trade_id = recent_trade_ids.popleft()

        recent_trade_ids_set.discard(
            old_trade_id
        )

    recent_trade_ids.append(
        trade_id
    )

    recent_trade_ids_set.add(
        trade_id
    )


def validate_trade(trade):

    global last_price

    validation_result = {

        "is_valid": True,

        "reasons": [],

        "latency_ms": None,
    }

    trade_id = trade.get(
        "trade_id"
    )

    price = trade.get(
        "price"
    )

    quantity = trade.get(
        "quantity"
    )

    timestamp = trade.get(
        "timestamp"
    )

    if trade_id is None:

        validation_result["is_valid"] = False

        validation_result["reasons"].append(
            "MISSING_TRADE_ID"
        )

    if trade_id in recent_trade_ids_set:

        validation_result["is_valid"] = False

        return validation_result

    if price is None or price <= 0:

        validation_result["is_valid"] = False

        validation_result["reasons"].append(
            "INVALID_PRICE"
        )

    if quantity is None or quantity <= 0:

        validation_result["is_valid"] = False

        validation_result["reasons"].append(
            "INVALID_QUANTITY"
        )

    if quantity is not None and quantity > MAX_QTY:

        validation_result["is_valid"] = False

        validation_result["reasons"].append(
            "QTY_OUTLIER"
        )

    if timestamp is None:

        validation_result["is_valid"] = False

        validation_result["reasons"].append(
            "MISSING_TIMESTAMP"
        )

    if (
        last_price is not None
        and price is not None
        and last_price > 0
    ):

        price_jump_percent = (

            abs(price - last_price)

            / last_price

            * 100
        )

        if price_jump_percent > MAX_PRICE_JUMP_PERCENT:

            validation_result["is_valid"] = False

            validation_result["reasons"].append(
                "PRICE_OUTLIER"
            )

    if timestamp is not None:

        current_time_ms = int(
            time.time() * 1000
        )

        latency_ms = (
            current_time_ms - timestamp
        )

        validation_result["latency_ms"] = (
            latency_ms
        )

        if latency_ms > MAX_ALLOWED_LATENCY_MS:

            validation_result["reasons"].append(
                "HIGH_LATENCY"
            )

    if validation_result["is_valid"]:

        remember_trade_id(
            trade_id
        )

        last_price = price

    return validation_result