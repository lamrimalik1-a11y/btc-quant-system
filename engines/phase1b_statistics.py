PRICE_HISTORY = []


def update_price_history(price, max_size=200):

    PRICE_HISTORY.append(price)

    if len(PRICE_HISTORY) > max_size:
        PRICE_HISTORY.pop(0)


def calculate_mean(values):

    if len(values) == 0:
        return 0

    return sum(values) / len(values)


def calculate_std(values):

    if len(values) < 2:
        return 0

    mean = calculate_mean(values)

    variance = sum(
        (value - mean) ** 2
        for value in values
    ) / len(values)

    return variance ** 0.5


def calculate_zscore(price):

    if len(PRICE_HISTORY) < 20:
        return 0

    mean = calculate_mean(PRICE_HISTORY)

    std = calculate_std(PRICE_HISTORY)

    if std == 0:
        return 0

    return (price - mean) / std


def classify_statistical_zone(zscore):

    if zscore >= 2.5:
        return "EXTREME_HIGH_ZONE"

    if zscore >= 2:
        return "HIGH_STATISTICAL_ZONE"

    if zscore <= -2.5:
        return "EXTREME_LOW_ZONE"

    if zscore <= -2:
        return "LOW_STATISTICAL_ZONE"

    if -1 <= zscore <= 1:
        return "NORMAL_ZONE"

    return "TRANSITION_ZONE"


def process_phase1b(row_data):

    close_price = row_data.get("close")

    update_price_history(close_price)

    zscore = calculate_zscore(close_price)

    statistical_zone = classify_statistical_zone(zscore)

    return {

        "zscore": zscore,
        "statistical_zone": statistical_zone,
        "history_size": len(PRICE_HISTORY),
    }