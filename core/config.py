# ==================================================
# GLOBAL CONFIG
# ==================================================

SYMBOL = "btcusdt"

TRADE_STREAM = f"{SYMBOL}@trade"
DEPTH_STREAM = f"{SYMBOL}@depth5@100ms"

BINANCE_WS_BASE = "wss://stream.binance.com:9443/ws"

TRADE_URL = f"{BINANCE_WS_BASE}/{TRADE_STREAM}"
DEPTH_URL = f"{BINANCE_WS_BASE}/{DEPTH_STREAM}"


# ==================================================
# ROW / AGGREGATION CONFIG
# ==================================================

ROW_SIZE = 500

MIN_ROLLING_WINDOW = 10
DEFAULT_ROLLING_WINDOW = 20
MAX_ROLLING_WINDOW = 50

RVI_PERIOD = 14


# ==================================================
# ORDERBOOK CONFIG
# ==================================================

SPREAD_WINDOW = 50
SIZE_WINDOW = 100

WALL_MULTIPLIER = 2.0
WHALE_ZSCORE_THRESHOLD = 2.5


# ==================================================
# RENKO CONFIG
# ==================================================

RENKO_BRICK_SIZE = 10.0


# ==================================================
# ZONE CONFIG
# ==================================================

PSY_LEVEL_STEP = 100
PSY_LEVEL_TOLERANCE = 20

PREVIOUS_HIGH_LOW_WINDOW = 100
PREVIOUS_HIGH_LOW_TOLERANCE = 15

VOLUME_CLUSTER_BUCKET = 50
VOLUME_CLUSTER_MULTIPLIER = 1.5

ZONE_TOUCH_TOLERANCE = 20