MAX_ALLOWED_GAP_MS = 3000


last_timestamp = None


def detect_gap(trade):

    global last_timestamp

    result = {

        "gap_detected": False,

        "gap_size_ms": 0,
    }

    current_timestamp = trade["timestamp"]

    if last_timestamp is None:

        last_timestamp = current_timestamp

        return result

    gap = (
        current_timestamp -
        last_timestamp
    )

    result["gap_size_ms"] = gap

    if gap > MAX_ALLOWED_GAP_MS:

        result["gap_detected"] = True

    last_timestamp = current_timestamp

    return result