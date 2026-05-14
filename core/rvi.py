RVI_PERIOD = 14


def calculate_rvi(
    current_velocity,
    velocity_history
):

    if len(velocity_history) < RVI_PERIOD:

        return 0

    recent_velocities = list(
        velocity_history
    )[-RVI_PERIOD:]

    average_velocity = (
        sum(recent_velocities)
        / len(recent_velocities)
    )

    if average_velocity <= 0:

        return 0

    rvi = (
        current_velocity
        / average_velocity
    )

    return rvi


def classify_rvi(rvi):

    if rvi >= 2:

        return "EXTREME_VELOCITY"

    elif rvi >= 1.5:

        return "HIGH_VELOCITY"

    elif rvi <= 0.5:

        return "LOW_VELOCITY"

    else:

        return "NORMAL_VELOCITY"


def add_rvi(
    row,
    velocity_history
):

    rvi = calculate_rvi(
        row["velocity"],
        velocity_history
    )

    row["rvi"] = rvi

    row["rvi_state"] = classify_rvi(
        rvi
    )

    return row