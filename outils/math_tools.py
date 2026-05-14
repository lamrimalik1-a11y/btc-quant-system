def calculate_mean(values):
    if len(values) == 0:
        return 0

    return sum(values) / len(values)


def calculate_std(values):
    if len(values) < 2:
        return 0

    mean = calculate_mean(values)

    variance = (
        sum((value - mean) ** 2 for value in values)
        / len(values)
    )

    return variance ** 0.5


def calculate_zscore(value, values, min_window):
    if len(values) < min_window:
        return 0

    mean = calculate_mean(values)
    std = calculate_std(values)

    if std == 0:
        return 0

    return (value - mean) / std