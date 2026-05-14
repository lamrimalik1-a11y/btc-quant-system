CONFIG = {

    # =========================================
    # MARKET
    # =========================================

    "SYMBOL":
        "btcusdt",

    "ROW_SIZE":
        500,

    "RECONNECT_DELAY":
        5,


    # =========================================
    # DISTRIBUTION
    # =========================================

    "DISTRIBUTION_WINDOW":
        30,

    "PERCENTILE_HIGH":
        90,

    "PERCENTILE_LOW":
        10,


    # =========================================
    # ZSCORE
    # =========================================

    "ZSCORE_WINDOW":
        20,

    "EXTREME_ZSCORE":
        2.5,

    "HIGH_ZSCORE":
        2.0,


    # =========================================
    # RVI
    # =========================================

    "RVI_PERIOD":
        14,


    # =========================================
    # RENKO
    # =========================================

    "RENKO_BRICK_SIZE":
        10,


    # =========================================
    # PSYCHOLOGICAL LEVELS
    # =========================================

    "PSYCHOLOGICAL_STEP":
        100,

    "PSYCHOLOGICAL_TOLERANCE":
        20,


    # =========================================
    # PREVIOUS LEVELS
    # =========================================

    "PREVIOUS_LEVEL_WINDOW":
        100,

    "PREVIOUS_LEVEL_TOLERANCE":
        15,


    # =========================================
    # LIQUIDITY
    # =========================================

    "IMBALANCE_THRESHOLD":
        0.30,

    "WALL_MULTIPLIER":
        2.0,


    # =========================================
    # ADAPTIVE WINDOW
    # =========================================

    "MIN_WINDOW":
        10,

    "DEFAULT_WINDOW":
        20,

    "MAX_WINDOW":
        50,
}


def get_config(
    key,
    default=None
):

    return CONFIG.get(
        key,
        default
    )