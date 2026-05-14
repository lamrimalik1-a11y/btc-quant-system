PSYCHOLOGICAL_STEP = 100
PSYCHOLOGICAL_TOLERANCE = 20

PREVIOUS_LEVEL_WINDOW = 100
PREVIOUS_LEVEL_TOLERANCE = 15

VOLUME_CLUSTER_THRESHOLD = 1.5


price_history_for_zones = []
volume_history_for_zones = []


def detect_psychological_levels(row):

    price = row["close"]

    nearest_level = round(
        price / PSYCHOLOGICAL_STEP
    ) * PSYCHOLOGICAL_STEP

    distance = abs(
        price - nearest_level
    )

    row["nearest_psychological_level"] = nearest_level

    row["distance_to_psychological_level"] = distance

    row["inside_psychological_zone"] = (
        distance <= PSYCHOLOGICAL_TOLERANCE
    )

    return row


def detect_previous_levels(row):

    price = row["close"]

    price_history_for_zones.append(
        price
    )

    recent_prices = price_history_for_zones[
        -PREVIOUS_LEVEL_WINDOW:
    ]

    if len(recent_prices) < 10:

        row["previous_high"] = None

        row["previous_low"] = None

        row["near_previous_high"] = False

        row["near_previous_low"] = False

        return row

    previous_high = max(
        recent_prices
    )

    previous_low = min(
        recent_prices
    )

    row["previous_high"] = previous_high

    row["previous_low"] = previous_low

    row["near_previous_high"] = (
        abs(price - previous_high)
        <= PREVIOUS_LEVEL_TOLERANCE
    )

    row["near_previous_low"] = (
        abs(price - previous_low)
        <= PREVIOUS_LEVEL_TOLERANCE
    )

    return row


def detect_volume_clusters(row):

    volume = row["volume"]

    volume_history_for_zones.append(
        volume
    )

    if len(volume_history_for_zones) < 20:

        row["average_volume_zone"] = None

        row["inside_volume_cluster"] = False

        return row

    recent_volume = volume_history_for_zones[
        -50:
    ]

    average_volume = sum(
        recent_volume
    ) / len(recent_volume)

    row["average_volume_zone"] = average_volume

    row["inside_volume_cluster"] = (
        volume >= average_volume
        * VOLUME_CLUSTER_THRESHOLD
    )

    return row


def detect_liquidity_zones(row):

    imbalance = row.get(
        "imbalance",
        0
    )

    spread = row.get(
        "spread",
        None
    )

    row["liquidity_zone_detected"] = False

    if spread is None:

        return row

    if abs(imbalance) >= 0.30:

        row["liquidity_zone_detected"] = True

    return row


def detect_rejection_zones(row):

    high = row["high"]

    low = row["low"]

    close = row["close"]

    candle_range = high - low

    if candle_range == 0:

        row["rejection_detected"] = False

        row["upper_rejection"] = False

        row["lower_rejection"] = False

        return row

    close_position = (
        close - low
    ) / candle_range

    upper_rejection = (
        close_position <= 0.30
    )

    lower_rejection = (
        close_position >= 0.70
    )

    row["upper_rejection"] = upper_rejection

    row["lower_rejection"] = lower_rejection

    row["rejection_detected"] = (
        upper_rejection
        or lower_rejection
    )

    return row


def calculate_zone_score(row):

    score = 0

    if row.get(
        "inside_psychological_zone"
    ):

        score += 1.5

    if row.get(
        "near_previous_high"
    ):

        score += 1.5

    if row.get(
        "near_previous_low"
    ):

        score += 1.5

    if row.get(
        "inside_volume_cluster"
    ):

        score += 1.5

    if row.get(
        "liquidity_zone_detected"
    ):

        score += 1.5

    if row.get(
        "rejection_detected"
    ):

        score += 1.5

    price_zone = row.get(
        "price_zone"
    )

    if price_zone in [
        "HIGH_STATISTICAL_ZONE",
        "LOW_STATISTICAL_ZONE",
    ]:

        score += 1.0

    if price_zone in [
        "EXTREME_HIGH_ZONE",
        "EXTREME_LOW_ZONE",
    ]:

        score += 2.0

    row["zone_score"] = score

    return row


def classify_zone_priority(row):

    score = row.get(
        "zone_score",
        0
    )

    if score >= 7:

        priority = "HIGH_PRIORITY_ZONE"

    elif score >= 4:

        priority = "MEDIUM_PRIORITY_ZONE"

    elif score >= 2:

        priority = "LOW_PRIORITY_ZONE"

    else:

        priority = "NO_PRIORITY_ZONE"

    row["zone_priority"] = priority

    return row