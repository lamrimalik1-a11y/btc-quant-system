MIN_WINDOW = 10

DEFAULT_WINDOW = 20

MAX_WINDOW = 50


def calculate_adaptive_window(
    current_velocity,
    velocity_history
):

    if len(velocity_history) < 10:
        return DEFAULT_WINDOW

    average_velocity = (
        sum(velocity_history)
        / len(velocity_history)
    )

    if average_velocity <= 0:
        return DEFAULT_WINDOW

    velocity_ratio = (
        current_velocity
        / average_velocity
    )

    # Fast Market
    if velocity_ratio >= 1.5:

        return MIN_WINDOW

    # Slow Market
    elif velocity_ratio <= 0.7:

        return MAX_WINDOW

    # Normal Market
    else:

        return DEFAULT_WINDOW