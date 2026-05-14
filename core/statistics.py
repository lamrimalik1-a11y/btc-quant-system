import math
import statistics
from collections import deque


MIN_HISTORY_SIZE = 10

DISTRIBUTION_WINDOW = 200


price_distribution = deque(
    maxlen=DISTRIBUTION_WINDOW
)

volume_distribution = deque(
    maxlen=DISTRIBUTION_WINDOW
)

delta_distribution = deque(
    maxlen=DISTRIBUTION_WINDOW
)

velocity_distribution = deque(
    maxlen=DISTRIBUTION_WINDOW
)


def calculate_mean(values):

    if len(values) == 0:
        return 0

    return sum(values) / len(values)


def calculate_std(values):

    if len(values) < 2:
        return 0

    mean = calculate_mean(
        values
    )

    variance = sum(

        (value - mean) ** 2

        for value in values

    ) / len(values)

    return math.sqrt(
        variance
    )


def calculate_zscore(
    value,
    history
):

    if len(history) < MIN_HISTORY_SIZE:
        return 0

    mean = calculate_mean(
        history
    )

    std = calculate_std(
        history
    )

    if std == 0:
        return 0

    return (
        value - mean
    ) / std


def calculate_percentile(
    value,
    distribution
):

    if len(distribution) == 0:

        return 0

    count = sum(

        sample <= value

        for sample in distribution
    )

    percentile = (
        count / len(distribution)
    ) * 100

    return percentile


def classify_statistical_zone(
    zscore
):

    if zscore >= 2.5:

        return "EXTREME_HIGH_ZONE"

    elif zscore >= 2:

        return "HIGH_STATISTICAL_ZONE"

    elif zscore <= -2.5:

        return "EXTREME_LOW_ZONE"

    elif zscore <= -2:

        return "LOW_STATISTICAL_ZONE"

    elif -1 <= zscore <= 1:

        return "NORMAL_ZONE"

    else:

        return "TRANSITION_ZONE"


def classify_percentile_zone(
    percentile
):

    if percentile >= 97:

        return "EXTREME_TOP_TAIL"

    elif percentile >= 90:

        return "HIGH_TAIL"

    elif percentile <= 3:

        return "EXTREME_BOTTOM_TAIL"

    elif percentile <= 10:

        return "LOW_TAIL"

    else:

        return "NORMAL_DISTRIBUTION"
    

def add_zscores(
    row,
    price_history,
    volume_history,
    delta_history,
    velocity_history
):

    row["price_zscore"] = calculate_zscore(

        row["close"],

        price_history
    )

    row["volume_zscore"] = calculate_zscore(

        row["volume"],

        volume_history
    )

    row["delta_zscore"] = calculate_zscore(

        row["delta"],

        delta_history
    )

    row["velocity_zscore"] = calculate_zscore(

        row["velocity"],

        velocity_history
    )

    return row


def add_statistical_zones(
    row
):

    row["price_zone"] = classify_statistical_zone(
        row["price_zscore"]
    )

    row["volume_zone"] = classify_statistical_zone(
        row["volume_zscore"]
    )

    row["delta_zone"] = classify_statistical_zone(
        row["delta_zscore"]
    )

    row["velocity_zone"] = classify_statistical_zone(
        row["velocity_zscore"]
    )

    return row


def update_distributions(
    row
):

    price_distribution.append(
        row["close"]
    )

    volume_distribution.append(
        row["volume"]
    )

    delta_distribution.append(
        row["delta"]
    )

    velocity_distribution.append(
        row["velocity"]
    )


def distribution_snapshot():

    if len(price_distribution) < 30:

        return {

            "ready": False,
        }

    snapshot = {

        "ready": True,

        "price_min":
            min(price_distribution),

        "price_max":
            max(price_distribution),

        "price_mean":
            statistics.mean(
                price_distribution
            ),

        "price_median":
            statistics.median(
                price_distribution
            ),

        "volume_mean":
            statistics.mean(
                volume_distribution
            ),

        "delta_mean":
            statistics.mean(
                delta_distribution
            ),

        "velocity_mean":
            statistics.mean(
                velocity_distribution
            ),
    }

    return snapshot


def add_distribution_features(
    row
):

    update_distributions(
        row
    )

    distribution = distribution_snapshot()

    row["distribution_ready"] = (
        distribution["ready"]
    )

    if not distribution["ready"]:

        row["price_distribution_mean"] = None

        row["price_distribution_median"] = None

        row["distribution_range"] = None

        row["price_percentile"] = None

        row["volume_percentile"] = None

        row["delta_percentile"] = None

        row["velocity_percentile"] = None

        row["price_percentile_zone"] = None

        return row

    row["price_distribution_mean"] = (
        distribution["price_mean"]
    )

    row["price_distribution_median"] = (
        distribution["price_median"]
    )

    row["distribution_range"] = (

        distribution["price_max"]
        -
        distribution["price_min"]
    )

    row["price_percentile"] = (
        calculate_percentile(
            row["close"],
            price_distribution
        )
    )

    row["volume_percentile"] = (
        calculate_percentile(
            row["volume"],
            volume_distribution
        )
    )

    row["delta_percentile"] = (
        calculate_percentile(
            row["delta"],
            delta_distribution
        )
    )

    row["velocity_percentile"] = (
        calculate_percentile(
            row["velocity"],
            velocity_distribution
        )
    )

    row["price_percentile_zone"] = (
        classify_percentile_zone(
            row["price_percentile"]
        )
    )

    return row