import asyncio
import json
from collections import deque, defaultdict

import websockets


SYMBOL = "btcusdt"

TRADE_URL = f"wss://stream.binance.com:9443/ws/{SYMBOL}@trade"
DEPTH_URL = f"wss://stream.binance.com:9443/ws/{SYMBOL}@depth5@100ms"

ROW_SIZE = 500

MIN_ROLLING_WINDOW = 10
DEFAULT_ROLLING_WINDOW = 20
MAX_ROLLING_WINDOW = 50

RVI_PERIOD = 14

SPREAD_WINDOW = 50
SIZE_WINDOW = 100

WALL_MULTIPLIER = 2.0
WHALE_ZSCORE_THRESHOLD = 2.5

RENKO_BRICK_SIZE = 10.0

PSY_LEVEL_STEP = 100
PSY_LEVEL_TOLERANCE = 20

PREVIOUS_HIGH_LOW_WINDOW = 100
PREVIOUS_HIGH_LOW_TOLERANCE = 15

VOLUME_CLUSTER_BUCKET = 50
VOLUME_CLUSTER_MULTIPLIER = 1.5
VOLUME_PROFILE_WINDOW = 300

ZONE_TOUCH_TOLERANCE = 20

FOOTPRINT_BUCKET_SIZE = 10

STACKED_IMBALANCE_MIN_LEVELS = 3
STACKED_IMBALANCE_RATIO = 2.0

DIVERGENCE_WINDOW = 10

FAILED_AUCTION_CLOSE_BACK_RATIO = 0.5
FAILED_AUCTION_FOOTPRINT_RATIO = 1.5

ABSORPTION_LEVEL_RATIO = 1.5
ABSORPTION_LEVEL_MIN_VOLUME = 0.01


last_trade_id = None

tick_buffer = []
row_history = deque(maxlen=500)

rvi_values = deque(maxlen=RVI_PERIOD)

spread_history = deque(maxlen=SPREAD_WINDOW)
size_history = deque(maxlen=SIZE_WINDOW)

volume_profile = defaultdict(float)
volume_profile_queue = deque(maxlen=VOLUME_PROFILE_WINDOW)

zone_touch_count = defaultdict(int)
active_zone_key = None

footprint_data = defaultdict(lambda: {
    "buy": 0.0,
    "sell": 0.0,
    "delta": 0.0,
    "total_volume": 0.0
})

recent_stacked_imbalance_history = deque(maxlen=10)

price_history_div = deque(maxlen=50)
delta_history_div = deque(maxlen=50)
cvd_history_div = deque(maxlen=50)
divergence_events = deque(maxlen=20)
global_cvd = 0.0

failed_auction_events = deque(maxlen=20)
auction_attempts = defaultdict(lambda: {
    "high": 0,
    "low": 0,
    "sweeps": 0,
    "failures": 0
})

absorption_level_events = deque(maxlen=20)

renko_state = {
    "last_renko_close": None,
    "direction": "FLAT",
    "bricks": 0,
    "event": "NO_RENKO_EVENT"
}

orderbook_state = {
    "best_bid": None,
    "best_ask": None,
    "spread": 0,
    "spread_zscore": 0,
    "imbalance": 0,
    "whale_detected": False,
    "whale_zscore": 0,
    "bid_wall": None,
    "ask_wall": None,
    "market_state": "NEUTRAL",
    "execution_state": "NORMAL_EXECUTION"
}


def calculate_mean(values):
    if len(values) == 0:
        return 0
    return sum(values) / len(values)


def calculate_std(values):
    if len(values) < 2:
        return 0

    mean = calculate_mean(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return variance ** 0.5


def calculate_zscore(value, values, min_window):
    if len(values) < min_window:
        return 0

    mean = calculate_mean(values)
    std = calculate_std(values)

    if std == 0:
        return 0

    return (value - mean) / std


# ==================================================
# PHASE 3A1 — BID/ASK FOOTPRINT PER TICK
# ==================================================

def get_price_level(price):
    return int(price / FOOTPRINT_BUCKET_SIZE) * FOOTPRINT_BUCKET_SIZE


def update_footprint(trade):
    price = trade["price"]
    quantity = trade["quantity"]
    side = trade["side"]

    level = get_price_level(price)

    if side == "BUY":
        footprint_data[level]["buy"] += quantity
        footprint_data[level]["delta"] += quantity
    else:
        footprint_data[level]["sell"] += quantity
        footprint_data[level]["delta"] -= quantity

    footprint_data[level]["total_volume"] += quantity


def reset_footprint():
    footprint_data.clear()


def get_footprint_summary():
    return {
        level: {
            "buy": data["buy"],
            "sell": data["sell"],
            "delta": data["delta"],
            "total_volume": data["total_volume"]
        }
        for level, data in footprint_data.items()
    }


def get_dominant_footprint_levels(top_n=5):
    levels = [
        {
            "level": level,
            "buy": data["buy"],
            "sell": data["sell"],
            "delta": data["delta"],
            "total_volume": data["total_volume"]
        }
        for level, data in footprint_data.items()
    ]

    levels.sort(key=lambda x: x["total_volume"], reverse=True)
    return levels[:top_n]


def get_max_delta_footprint_level():
    if not footprint_data:
        return None

    level, data = max(
        footprint_data.items(),
        key=lambda item: abs(item[1]["delta"])
    )

    return {
        "level": level,
        "buy": data["buy"],
        "sell": data["sell"],
        "delta": data["delta"],
        "total_volume": data["total_volume"]
    }


def get_max_volume_footprint_level():
    if not footprint_data:
        return None

    level, data = max(
        footprint_data.items(),
        key=lambda item: item[1]["total_volume"]
    )

    return {
        "level": level,
        "buy": data["buy"],
        "sell": data["sell"],
        "delta": data["delta"],
        "total_volume": data["total_volume"]
    }


# ==================================================
# PHASE 3A2 — STACKED IMBALANCES
# ==================================================

def classify_level_imbalance(data, ratio_threshold=STACKED_IMBALANCE_RATIO):
    buy = data["buy"]
    sell = data["sell"]
    total_volume = data["total_volume"]

    if total_volume <= 0:
        return {
            "direction": "NEUTRAL",
            "ratio": 0
        }

    if sell == 0 and buy > 0:
        return {
            "direction": "BUY_IMBALANCE",
            "ratio": ratio_threshold
        }

    if buy == 0 and sell > 0:
        return {
            "direction": "SELL_IMBALANCE",
            "ratio": ratio_threshold
        }

    if sell > 0 and buy / sell >= ratio_threshold:
        return {
            "direction": "BUY_IMBALANCE",
            "ratio": buy / sell
        }

    if buy > 0 and sell / buy >= ratio_threshold:
        return {
            "direction": "SELL_IMBALANCE",
            "ratio": sell / buy
        }

    return {
        "direction": "NEUTRAL",
        "ratio": 0
    }


def detect_stacked_imbalance(
    footprint_summary,
    min_levels=STACKED_IMBALANCE_MIN_LEVELS,
    ratio_threshold=STACKED_IMBALANCE_RATIO
):
    if len(footprint_summary) < min_levels:
        return {
            "detected": False,
            "direction": "NONE",
            "levels": [],
            "length": 0,
            "avg_ratio": 0,
            "strength": 0
        }

    sorted_levels = sorted(footprint_summary.items(), key=lambda x: x[0])

    current_streak = []
    all_streaks = []
    current_direction = None

    for level, data in sorted_levels:
        imbalance = classify_level_imbalance(data, ratio_threshold)
        level_direction = imbalance["direction"]
        ratio = imbalance["ratio"]

        if level_direction == "NEUTRAL":
            if len(current_streak) >= min_levels:
                all_streaks.append({
                    "direction": current_direction,
                    "levels": current_streak.copy(),
                    "length": len(current_streak),
                    "avg_ratio": calculate_mean([x["ratio"] for x in current_streak])
                })

            current_streak = []
            current_direction = None
            continue

        if level_direction == current_direction:
            current_streak.append({
                "level": level,
                "buy": data["buy"],
                "sell": data["sell"],
                "delta": data["delta"],
                "total_volume": data["total_volume"],
                "ratio": ratio
            })

        else:
            if len(current_streak) >= min_levels:
                all_streaks.append({
                    "direction": current_direction,
                    "levels": current_streak.copy(),
                    "length": len(current_streak),
                    "avg_ratio": calculate_mean([x["ratio"] for x in current_streak])
                })

            current_direction = level_direction
            current_streak = [{
                "level": level,
                "buy": data["buy"],
                "sell": data["sell"],
                "delta": data["delta"],
                "total_volume": data["total_volume"],
                "ratio": ratio
            }]

    if len(current_streak) >= min_levels:
        all_streaks.append({
            "direction": current_direction,
            "levels": current_streak.copy(),
            "length": len(current_streak),
            "avg_ratio": calculate_mean([x["ratio"] for x in current_streak])
        })

    if not all_streaks:
        return {
            "detected": False,
            "direction": "NONE",
            "levels": [],
            "length": 0,
            "avg_ratio": 0,
            "strength": 0
        }

    best_streak = max(
        all_streaks,
        key=lambda x: (x["length"], x["avg_ratio"])
    )

    strength = min(
        10,
        best_streak["length"] * 2 + best_streak["avg_ratio"]
    )

    result = {
        "detected": True,
        "direction": best_streak["direction"],
        "levels": [x["level"] for x in best_streak["levels"]],
        "length": best_streak["length"],
        "avg_ratio": round(best_streak["avg_ratio"], 2),
        "strength": round(strength, 2)
    }

    recent_stacked_imbalance_history.append(result)

    return result


def get_stacked_imbalance_trend(window=5):
    if len(recent_stacked_imbalance_history) < window:
        return {
            "trend": "INSUFFICIENT_DATA",
            "buy_count": 0,
            "sell_count": 0,
            "avg_strength": 0
        }

    recent = list(recent_stacked_imbalance_history)[-window:]

    buy_count = sum(
        1 for item in recent
        if item["direction"] == "BUY_IMBALANCE"
    )

    sell_count = sum(
        1 for item in recent
        if item["direction"] == "SELL_IMBALANCE"
    )

    avg_strength = calculate_mean(
        [item["strength"] for item in recent]
    )

    if buy_count >= 4 and avg_strength >= 6:
        trend = "STRONG_BUY_STACKED_IMBALANCE"

    elif sell_count >= 4 and avg_strength >= 6:
        trend = "STRONG_SELL_STACKED_IMBALANCE"

    elif buy_count > sell_count:
        trend = "WEAK_BUY_STACKED_IMBALANCE"

    elif sell_count > buy_count:
        trend = "WEAK_SELL_STACKED_IMBALANCE"

    else:
        trend = "NEUTRAL_STACKED_IMBALANCE"

    return {
        "trend": trend,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "avg_strength": round(avg_strength, 2)
    }


# ==================================================
# PHASE 3A3 — DELTA / CVD DIVERGENCE
# ==================================================

def update_global_cvd(delta):
    global global_cvd
    global_cvd += delta
    return global_cvd


def calculate_divergence(price_series, delta_series, window=DIVERGENCE_WINDOW):
    if len(price_series) < window * 2 or len(delta_series) < window * 2:
        return "NO_DIVERGENCE", 0

    recent_price = list(price_series)[-window:]
    older_price = list(price_series)[-window * 2:-window]

    recent_delta = list(delta_series)[-window:]
    older_delta = list(delta_series)[-window * 2:-window]

    price_change = recent_price[-1] - older_price[-1]
    delta_change = recent_delta[-1] - older_delta[-1]

    price_higher_high = max(recent_price) > max(older_price)
    price_lower_low = min(recent_price) < min(older_price)

    delta_higher_high = max(recent_delta) > max(older_delta)
    delta_lower_low = min(recent_delta) < min(older_delta)

    if price_lower_low and not delta_lower_low and delta_change > 0:
        strength = min(10, abs(delta_change) / (abs(price_change) + 0.01))
        return "BULLISH_DIVERGENCE", round(strength, 2)

    if price_higher_high and not delta_higher_high and delta_change < 0:
        strength = min(10, abs(delta_change) / (abs(price_change) + 0.01))
        return "BEARISH_DIVERGENCE", round(strength, 2)

    if not price_lower_low and delta_lower_low and price_change > 0:
        strength = min(10, abs(delta_change) / (abs(price_change) + 0.01))
        return "HIDDEN_BULLISH_DIVERGENCE", round(strength, 2)

    if not price_higher_high and delta_higher_high and price_change < 0:
        strength = min(10, abs(delta_change) / (abs(price_change) + 0.01))
        return "HIDDEN_BEARISH_DIVERGENCE", round(strength, 2)

    return "NO_DIVERGENCE", 0


def detect_cvd_divergence(price_series, cvd_series, window=DIVERGENCE_WINDOW):
    if len(price_series) < window or len(cvd_series) < window:
        return "NO_CVD_DIVERGENCE", 0

    recent_price = list(price_series)[-window:]
    recent_cvd = list(cvd_series)[-window:]

    price_change = recent_price[-1] - recent_price[0]
    cvd_change = recent_cvd[-1] - recent_cvd[0]

    if price_change <= 0 and cvd_change > 0:
        strength = min(10, abs(cvd_change) / (abs(price_change) + 0.01))
        return "CVD_BULLISH_DIVERGENCE", round(strength, 2)

    if price_change >= 0 and cvd_change < 0:
        strength = min(10, abs(cvd_change) / (abs(price_change) + 0.01))
        return "CVD_BEARISH_DIVERGENCE", round(strength, 2)

    return "NO_CVD_DIVERGENCE", 0


def detect_all_divergences(trade_row):
    price = trade_row["close"]
    delta = trade_row["delta"]
    cvd = update_global_cvd(delta)

    price_history_div.append(price)
    delta_history_div.append(delta)
    cvd_history_div.append(cvd)

    div_type, div_strength = calculate_divergence(
        price_history_div,
        delta_history_div
    )

    cvd_div_type, cvd_div_strength = detect_cvd_divergence(
        price_history_div,
        cvd_history_div
    )

    if div_type != "NO_DIVERGENCE" and div_strength > 3:
        divergence_events.append({
            "type": div_type,
            "strength": div_strength,
            "price": price,
            "delta": delta,
            "cvd": cvd
        })

    if cvd_div_type != "NO_CVD_DIVERGENCE" and cvd_div_strength > 3:
        divergence_events.append({
            "type": cvd_div_type,
            "strength": cvd_div_strength,
            "price": price,
            "delta": delta,
            "cvd": cvd
        })

    recent_events = list(divergence_events)[-5:]

    bullish_count = sum(
        1 for event in recent_events
        if "BULLISH" in event["type"]
    )

    bearish_count = sum(
        1 for event in recent_events
        if "BEARISH" in event["type"]
    )

    if bullish_count > bearish_count + 2:
        divergence_trend = "BULLISH_DIVERGENCE_TREND"

    elif bearish_count > bullish_count + 2:
        divergence_trend = "BEARISH_DIVERGENCE_TREND"

    elif bullish_count > bearish_count:
        divergence_trend = "WEAK_BULLISH_DIVERGENCE_TREND"

    elif bearish_count > bullish_count:
        divergence_trend = "WEAK_BEARISH_DIVERGENCE_TREND"

    else:
        divergence_trend = "NEUTRAL_DIVERGENCE"

    return {
        "global_cvd": cvd,
        "regular_divergence": {
            "type": div_type,
            "strength": div_strength
        },
        "cvd_divergence": {
            "type": cvd_div_type,
            "strength": cvd_div_strength
        },
        "divergence_trend": divergence_trend,
        "recent_divergence_count": len(recent_events),
        "has_active_divergence": (
            div_type != "NO_DIVERGENCE"
            or cvd_div_type != "NO_CVD_DIVERGENCE"
        )
    }


def get_divergence_alignment(divergence_result, zone_context, absorption_state):
    div_type = divergence_result["regular_divergence"]["type"]
    cvd_div_type = divergence_result["cvd_divergence"]["type"]
    cvd_div_strength = divergence_result["cvd_divergence"]["strength"]

    alignment_score = 0
    alignment_desc = ""

    if "BULLISH" in div_type and absorption_state in [
        "BUYER_ABSORPTION",
        "POSSIBLE_BUYER_ABSORPTION"
    ]:
        alignment_score += 3
        alignment_desc += "Bullish divergence + buyer absorption. "

    if "BULLISH" in div_type and "LOW" in zone_context.get("statistical_zone", ""):
        alignment_score += 2
        alignment_desc += "Bullish divergence + low statistical zone. "

    if "BEARISH" in div_type and absorption_state in [
        "SELLER_ABSORPTION",
        "POSSIBLE_SELLER_ABSORPTION"
    ]:
        alignment_score += 3
        alignment_desc += "Bearish divergence + seller absorption. "

    if "BEARISH" in div_type and "HIGH" in zone_context.get("statistical_zone", ""):
        alignment_score += 2
        alignment_desc += "Bearish divergence + high statistical zone. "

    if cvd_div_type != "NO_CVD_DIVERGENCE" and cvd_div_strength > 5:
        alignment_score += 2
        alignment_desc += "CVD divergence confirmation. "

    if alignment_score >= 5:
        alignment = "STRONG_DIVERGENCE_ALIGNMENT"

    elif alignment_score >= 3:
        alignment = "MODERATE_DIVERGENCE_ALIGNMENT"

    elif alignment_score >= 1:
        alignment = "WEAK_DIVERGENCE_ALIGNMENT"

    else:
        alignment = "NO_DIVERGENCE_ALIGNMENT"

    return {
        "alignment": alignment,
        "alignment_score": alignment_score,
        "alignment_desc": alignment_desc.strip()
    }


# ==================================================
# PHASE 3A4 — FAILED AUCTIONS
# ==================================================

def detect_failed_auction(
    full_row_context,
    footprint_summary,
    stacked_imbalance,
    current_orderbook_state
):
    current_price = full_row_context["close"]
    open_price = full_row_context["open"]
    high = full_row_context["high"]
    low = full_row_context["low"]

    delta_z = full_row_context["delta_zscore"]
    velocity_z = full_row_context["velocity_zscore"]

    previous_high = full_row_context.get("previous_high")
    previous_low = full_row_context.get("previous_low")

    bid_wall = current_orderbook_state.get("bid_wall")
    ask_wall = current_orderbook_state.get("ask_wall")

    candle_range = high - low

    if candle_range <= 0:
        return {
            "detected": False,
            "type": "NO_FAILED_AUCTION",
            "level": None,
            "strength": 0,
            "direction": "NONE"
        }

    close_position = (current_price - low) / candle_range

    close_back_from_high = close_position < FAILED_AUCTION_CLOSE_BACK_RATIO
    close_back_from_low = close_position > FAILED_AUCTION_CLOSE_BACK_RATIO

    upward_reference = previous_high
    downward_reference = previous_low

    if ask_wall is not None:
        if upward_reference is None:
            upward_reference = ask_wall["price"]
        else:
            upward_reference = max(upward_reference, ask_wall["price"])

    if bid_wall is not None:
        if downward_reference is None:
            downward_reference = bid_wall["price"]
        else:
            downward_reference = min(downward_reference, bid_wall["price"])

    upward_failed = False
    downward_failed = False
    upward_level = None
    downward_level = None

    if upward_reference is not None:
        swept_up = high > upward_reference
        failed_back_down = current_price < upward_reference or close_back_from_high
        weak_follow_through = delta_z < 0.5 or velocity_z < 0.5

        if swept_up and failed_back_down and weak_follow_through:
            upward_failed = True
            upward_level = upward_reference

            auction_attempts[upward_level]["high"] += 1
            auction_attempts[upward_level]["sweeps"] += 1
            auction_attempts[upward_level]["failures"] += 1

    if downward_reference is not None:
        swept_down = low < downward_reference
        failed_back_up = current_price > downward_reference or close_back_from_low
        weak_follow_through = delta_z > -0.5 or velocity_z < 0.5

        if swept_down and failed_back_up and weak_follow_through:
            downward_failed = True
            downward_level = downward_reference

            auction_attempts[downward_level]["low"] += 1
            auction_attempts[downward_level]["sweeps"] += 1
            auction_attempts[downward_level]["failures"] += 1

    footprint_failure = False
    footprint_level = None
    footprint_direction = "NONE"

    if footprint_summary:
        sorted_levels = sorted(footprint_summary.items(), key=lambda x: x[0])

        lowest_level, lowest_data = sorted_levels[0]
        highest_level, highest_data = sorted_levels[-1]

        highest_sell_absorption = (
            highest_data["sell"] > highest_data["buy"] * FAILED_AUCTION_FOOTPRINT_RATIO
            and current_price < highest_level
        )

        lowest_buy_absorption = (
            lowest_data["buy"] > lowest_data["sell"] * FAILED_AUCTION_FOOTPRINT_RATIO
            and current_price > lowest_level
        )

        if highest_sell_absorption:
            footprint_failure = True
            footprint_level = highest_level
            footprint_direction = "BEARISH_REVERSAL"

            auction_attempts[footprint_level]["high"] += 1
            auction_attempts[footprint_level]["failures"] += 1

        elif lowest_buy_absorption:
            footprint_failure = True
            footprint_level = lowest_level
            footprint_direction = "BULLISH_REVERSAL"

            auction_attempts[footprint_level]["low"] += 1
            auction_attempts[footprint_level]["failures"] += 1

    trapped_orderflow = False
    trapped_type = "NONE"

    if stacked_imbalance and stacked_imbalance["detected"]:
        if stacked_imbalance["direction"] == "BUY_IMBALANCE" and current_price < open_price:
            trapped_orderflow = True
            trapped_type = "BUYERS_TRAPPED_AFTER_BUY_IMBALANCE"

        elif stacked_imbalance["direction"] == "SELL_IMBALANCE" and current_price > open_price:
            trapped_orderflow = True
            trapped_type = "SELLERS_TRAPPED_AFTER_SELL_IMBALANCE"

    if upward_failed:
        result = {
            "detected": True,
            "type": "FAILED_UPSWEEP",
            "level": upward_level,
            "strength": min(10, 5 + abs(delta_z)),
            "direction": "BEARISH_REVERSAL"
        }

    elif downward_failed:
        result = {
            "detected": True,
            "type": "FAILED_DOWNSWEEP",
            "level": downward_level,
            "strength": min(10, 5 + abs(delta_z)),
            "direction": "BULLISH_REVERSAL"
        }

    elif footprint_failure:
        result = {
            "detected": True,
            "type": "FOOTPRINT_FAILED_AUCTION",
            "level": footprint_level,
            "strength": 6,
            "direction": footprint_direction
        }

    elif trapped_orderflow:
        result = {
            "detected": True,
            "type": trapped_type,
            "level": None,
            "strength": 7,
            "direction": "REVERSAL_POSSIBLE"
        }

    else:
        result = {
            "detected": False,
            "type": "NO_FAILED_AUCTION",
            "level": None,
            "strength": 0,
            "direction": "NONE"
        }

    if result["detected"]:
        failed_auction_events.append({
            "type": result["type"],
            "strength": result["strength"],
            "price": current_price,
            "level": result["level"]
        })

    return result


def get_auction_failure_rate(level=None):
    if level is not None and level in auction_attempts:
        data = auction_attempts[level]
        total = data["high"] + data["low"]
        failures = data["failures"]

        return {
            "level": level,
            "total_attempts": total,
            "failures": failures,
            "failure_rate": round(failures / total, 2) if total > 0 else 0,
            "high_attempts": data["high"],
            "low_attempts": data["low"]
        }

    total_attempts = sum(
        data["high"] + data["low"]
        for data in auction_attempts.values()
    )

    total_failures = sum(
        data["failures"]
        for data in auction_attempts.values()
    )

    return {
        "total_attempts": total_attempts,
        "failures": total_failures,
        "failure_rate": round(total_failures / total_attempts, 2) if total_attempts > 0 else 0,
        "levels_tracked": len(auction_attempts)
    }


def get_failed_auction_trend(window=5):
    if len(failed_auction_events) < window:
        return {
            "trend": "INSUFFICIENT_DATA",
            "recent_count": len(failed_auction_events),
            "avg_strength": 0
        }

    recent = list(failed_auction_events)[-window:]

    failed_up_count = sum(
        1 for event in recent
        if event["type"] == "FAILED_UPSWEEP"
    )

    failed_down_count = sum(
        1 for event in recent
        if event["type"] == "FAILED_DOWNSWEEP"
    )

    trapped_count = sum(
        1 for event in recent
        if "TRAPPED" in event["type"]
    )

    avg_strength = calculate_mean(
        [event["strength"] for event in recent]
    )

    if failed_down_count > failed_up_count + 1:
        trend = "BULLISH_FAILED_AUCTION_TREND"

    elif failed_up_count > failed_down_count + 1:
        trend = "BEARISH_FAILED_AUCTION_TREND"

    elif trapped_count >= 2:
        trend = "TRAPPED_ORDERFLOW_TREND"

    elif avg_strength >= 7:
        trend = "HIGH_CONFIDENCE_FAILED_AUCTIONS"

    else:
        trend = "MIXED_FAILED_AUCTIONS"

    return {
        "trend": trend,
        "failed_up_count": failed_up_count,
        "failed_down_count": failed_down_count,
        "trapped_count": trapped_count,
        "avg_strength": round(avg_strength, 2),
        "total_recent": len(recent)
    }


# ==================================================
# PHASE 3A5 — ABSORPTION PER PRICE LEVEL
# ==================================================

def detect_absorption_per_level(footprint_summary, trade_row):
    if not footprint_summary:
        return {
            "detected": False,
            "type": "NO_LEVEL_ABSORPTION",
            "level": None,
            "strength": 0,
            "direction": "NONE",
            "absorbed_side": "NONE"
        }

    current_price = trade_row["close"]

    sorted_levels = sorted(footprint_summary.items(), key=lambda x: x[0])

    absorption_candidates = []

    for level, data in sorted_levels:
        buy = data["buy"]
        sell = data["sell"]
        delta = data["delta"]
        total_volume = data["total_volume"]

        if total_volume < ABSORPTION_LEVEL_MIN_VOLUME:
            continue

        seller_absorption = (
            buy > sell * ABSORPTION_LEVEL_RATIO
            and delta > 0
            and current_price <= level
        )

        buyer_absorption = (
            sell > buy * ABSORPTION_LEVEL_RATIO
            and delta < 0
            and current_price >= level
        )

        if seller_absorption:
            strength = min(10, (buy / max(sell, 0.00001)) + total_volume)

            absorption_candidates.append({
                "type": "SELLER_ABSORPTION_LEVEL",
                "level": level,
                "strength": round(strength, 2),
                "direction": "BEARISH_REVERSAL_POSSIBLE",
                "absorbed_side": "BUYERS",
                "buy": buy,
                "sell": sell,
                "delta": delta,
                "total_volume": total_volume
            })

        if buyer_absorption:
            strength = min(10, (sell / max(buy, 0.00001)) + total_volume)

            absorption_candidates.append({
                "type": "BUYER_ABSORPTION_LEVEL",
                "level": level,
                "strength": round(strength, 2),
                "direction": "BULLISH_REVERSAL_POSSIBLE",
                "absorbed_side": "SELLERS",
                "buy": buy,
                "sell": sell,
                "delta": delta,
                "total_volume": total_volume
            })

    if not absorption_candidates:
        return {
            "detected": False,
            "type": "NO_LEVEL_ABSORPTION",
            "level": None,
            "strength": 0,
            "direction": "NONE",
            "absorbed_side": "NONE"
        }

    best_absorption = max(
        absorption_candidates,
        key=lambda x: x["strength"]
    )

    absorption_level_events.append(best_absorption)

    return {
        "detected": True,
        **best_absorption
    }


def get_absorption_level_trend(window=5):
    if len(absorption_level_events) < window:
        return {
            "trend": "INSUFFICIENT_DATA",
            "recent_count": len(absorption_level_events),
            "avg_strength": 0
        }

    recent = list(absorption_level_events)[-window:]

    buyer_absorption_count = sum(
        1 for event in recent
        if event["type"] == "BUYER_ABSORPTION_LEVEL"
    )

    seller_absorption_count = sum(
        1 for event in recent
        if event["type"] == "SELLER_ABSORPTION_LEVEL"
    )

    avg_strength = calculate_mean(
        [event["strength"] for event in recent]
    )

    if buyer_absorption_count > seller_absorption_count + 1:
        trend = "BULLISH_LEVEL_ABSORPTION_TREND"

    elif seller_absorption_count > buyer_absorption_count + 1:
        trend = "BEARISH_LEVEL_ABSORPTION_TREND"

    elif avg_strength >= 7:
        trend = "STRONG_MIXED_LEVEL_ABSORPTION"

    else:
        trend = "MIXED_LEVEL_ABSORPTION"

    return {
        "trend": trend,
        "buyer_absorption_count": buyer_absorption_count,
        "seller_absorption_count": seller_absorption_count,
        "avg_strength": round(avg_strength, 2),
        "recent_count": len(recent)
    }


# ==================================================
# PHASE 3A6 — FOOTPRINT FINAL SCORE
# ==================================================

def calculate_footprint_final_score(
    stacked_imbalance,
    divergence_result,
    failed_auction,
    level_absorption,
    trade_row
):
    bullish_score = 0
    bearish_score = 0
    notes = []

    if stacked_imbalance and stacked_imbalance["detected"]:
        if stacked_imbalance["direction"] == "BUY_IMBALANCE":
            bullish_score += stacked_imbalance["strength"] * 0.25
            notes.append("Buy stacked imbalance")

        elif stacked_imbalance["direction"] == "SELL_IMBALANCE":
            bearish_score += stacked_imbalance["strength"] * 0.25
            notes.append("Sell stacked imbalance")

    regular_div = divergence_result["regular_divergence"]
    cvd_div = divergence_result["cvd_divergence"]

    if "BULLISH" in regular_div["type"]:
        bullish_score += regular_div["strength"] * 0.25
        notes.append("Bullish regular divergence")

    if "BEARISH" in regular_div["type"]:
        bearish_score += regular_div["strength"] * 0.25
        notes.append("Bearish regular divergence")

    if "BULLISH" in cvd_div["type"]:
        bullish_score += cvd_div["strength"] * 0.25
        notes.append("Bullish CVD divergence")

    if "BEARISH" in cvd_div["type"]:
        bearish_score += cvd_div["strength"] * 0.25
        notes.append("Bearish CVD divergence")

    if failed_auction and failed_auction["detected"]:
        if failed_auction["direction"] == "BULLISH_REVERSAL":
            bullish_score += failed_auction["strength"] * 0.30
            notes.append("Bullish failed auction")

        elif failed_auction["direction"] == "BEARISH_REVERSAL":
            bearish_score += failed_auction["strength"] * 0.30
            notes.append("Bearish failed auction")

        elif failed_auction["direction"] == "REVERSAL_POSSIBLE":
            bullish_score += failed_auction["strength"] * 0.10
            bearish_score += failed_auction["strength"] * 0.10
            notes.append("Possible trapped orderflow")

    if level_absorption and level_absorption["detected"]:
        if level_absorption["type"] == "BUYER_ABSORPTION_LEVEL":
            bullish_score += level_absorption["strength"] * 0.30
            notes.append("Buyer absorption per level")

        elif level_absorption["type"] == "SELLER_ABSORPTION_LEVEL":
            bearish_score += level_absorption["strength"] * 0.30
            notes.append("Seller absorption per level")

    max_delta_level = trade_row.get("max_delta_footprint_level")

    if max_delta_level:
        distance = abs(trade_row["close"] - max_delta_level["level"])

        if distance <= FOOTPRINT_BUCKET_SIZE * 2:
            if max_delta_level["delta"] > 0:
                bullish_score += 0.75
                notes.append("Positive max delta near close")

            elif max_delta_level["delta"] < 0:
                bearish_score += 0.75
                notes.append("Negative max delta near close")

    bullish_score = min(10, round(bullish_score, 2))
    bearish_score = min(10, round(bearish_score, 2))

    score_diff = abs(bullish_score - bearish_score)

    if bullish_score >= 6 and score_diff >= 2:
        final_state = "FOOTPRINT_BULLISH_REVERSAL_OR_CONTINUATION"

    elif bearish_score >= 6 and score_diff >= 2:
        final_state = "FOOTPRINT_BEARISH_REVERSAL_OR_CONTINUATION"

    elif bullish_score >= 4 and bearish_score >= 4:
        final_state = "FOOTPRINT_CONFLICT"

    elif bullish_score >= 3:
        final_state = "WEAK_BULLISH_FOOTPRINT"

    elif bearish_score >= 3:
        final_state = "WEAK_BEARISH_FOOTPRINT"

    else:
        final_state = "FOOTPRINT_NEUTRAL"

    return {
        "final_state": final_state,
        "bullish_score": bullish_score,
        "bearish_score": bearish_score,
        "score_diff": round(score_diff, 2),
        "notes": notes
    }


# ==================================================
# PHASE 1 + ZONES + ORDERBOOK
# ==================================================

def get_adaptive_window():
    if len(row_history) < DEFAULT_ROLLING_WINDOW:
        return DEFAULT_ROLLING_WINDOW

    recent_rows = list(row_history)[-DEFAULT_ROLLING_WINDOW:]
    recent_velocities = [row["velocity"] for row in recent_rows]

    current_velocity = recent_velocities[-1]
    avg_velocity = calculate_mean(recent_velocities)

    if avg_velocity == 0:
        return DEFAULT_ROLLING_WINDOW

    velocity_ratio = current_velocity / avg_velocity

    if velocity_ratio > 1.5:
        return MIN_ROLLING_WINDOW

    if velocity_ratio < 0.7:
        return MAX_ROLLING_WINDOW

    return DEFAULT_ROLLING_WINDOW


def classify_statistical_zone(price_zscore):
    if price_zscore > 2.5:
        return "EXTREME_HIGH_ZONE"

    if price_zscore > 2:
        return "HIGH_STATISTICAL_ZONE"

    if price_zscore < -2.5:
        return "EXTREME_LOW_ZONE"

    if price_zscore < -2:
        return "LOW_STATISTICAL_ZONE"

    if -1 <= price_zscore <= 1:
        return "NORMAL_ZONE"

    return "TRANSITION_ZONE"


def update_renko(price):
    global renko_state

    if renko_state["last_renko_close"] is None:
        renko_state["last_renko_close"] = price
        renko_state["direction"] = "FLAT"
        renko_state["bricks"] = 0
        renko_state["event"] = "RENKO_INITIALIZED"
        return renko_state

    last_close = renko_state["last_renko_close"]
    price_move = price - last_close

    bricks = int(abs(price_move) // RENKO_BRICK_SIZE)

    if bricks == 0:
        renko_state["event"] = "NO_RENKO_EVENT"
        renko_state["bricks"] = 0
        return renko_state

    if price_move > 0:
        new_direction = "RENKO_UP"
        renko_state["last_renko_close"] = last_close + bricks * RENKO_BRICK_SIZE
    else:
        new_direction = "RENKO_DOWN"
        renko_state["last_renko_close"] = last_close - bricks * RENKO_BRICK_SIZE

    if renko_state["direction"] != new_direction and renko_state["direction"] != "FLAT":
        renko_event = "RENKO_REVERSAL"
    else:
        renko_event = "RENKO_CONTINUATION"

    renko_state["direction"] = new_direction
    renko_state["bricks"] = bricks
    renko_state["event"] = renko_event

    return renko_state


def validate_trade(data):
    required_fields = ["t", "p", "q", "T", "m"]

    for field in required_fields:
        if field not in data:
            return None

    price = float(data["p"])
    quantity = float(data["q"])

    if price <= 0 or quantity <= 0:
        return None

    side = "SELL" if data["m"] else "BUY"

    return {
        "trade_id": data["t"],
        "price": price,
        "quantity": quantity,
        "timestamp": data["T"],
        "side": side
    }


def is_duplicate(trade):
    global last_trade_id

    if trade["trade_id"] == last_trade_id:
        return True

    last_trade_id = trade["trade_id"]
    return False


def calculate_wilder_rvi(raw_rvi):
    rvi_values.append(raw_rvi)

    if len(rvi_values) < RVI_PERIOD:
        return raw_rvi

    return sum(rvi_values) / len(rvi_values)


def build_trade_row(trades):
    prices = [trade["price"] for trade in trades]

    open_price = prices[0]
    high_price = max(prices)
    low_price = min(prices)
    close_price = prices[-1]

    total_volume = sum(trade["quantity"] for trade in trades)

    buy_volume = sum(
        trade["quantity"]
        for trade in trades
        if trade["side"] == "BUY"
    )

    sell_volume = sum(
        trade["quantity"]
        for trade in trades
        if trade["side"] == "SELL"
    )

    delta = buy_volume - sell_volume
    delta_ratio = abs(delta) / total_volume if total_volume > 0 else 0

    duration_seconds = (trades[-1]["timestamp"] - trades[0]["timestamp"]) / 1000

    if duration_seconds <= 0:
        duration_seconds = 0.001

    velocity = total_volume / duration_seconds

    raw_rvi = len(trades) / duration_seconds
    rvi = calculate_wilder_rvi(raw_rvi)

    adaptive_window = get_adaptive_window()
    previous_rows = list(row_history)[-adaptive_window:]

    close_history = [row["close"] for row in previous_rows]
    delta_history = [row["delta"] for row in previous_rows]
    delta_ratio_history = [row["delta_ratio"] for row in previous_rows]
    velocity_history = [row["velocity"] for row in previous_rows]
    volume_history = [row["volume"] for row in previous_rows]

    price_mean = calculate_mean(close_history)
    price_std = calculate_std(close_history)

    price_zscore = calculate_zscore(
        close_price,
        close_history,
        adaptive_window
    )

    statistical_zone = classify_statistical_zone(price_zscore)

    footprint_summary = get_footprint_summary()
    dominant_footprint_levels = get_dominant_footprint_levels(top_n=5)
    max_delta_footprint_level = get_max_delta_footprint_level()
    max_volume_footprint_level = get_max_volume_footprint_level()

    stacked_imbalance = detect_stacked_imbalance(footprint_summary)
    stacked_imbalance_trend = get_stacked_imbalance_trend()

    return {
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,

        "adaptive_window": adaptive_window,
        "price_mean": price_mean,
        "price_std": price_std,
        "price_zscore": price_zscore,
        "statistical_zone": statistical_zone,

        "volume": total_volume,
        "buy_volume": buy_volume,
        "sell_volume": sell_volume,

        "delta": delta,
        "delta_ratio": delta_ratio,

        "velocity": velocity,
        "rvi": rvi,
        "duration_seconds": duration_seconds,
        "tick_count": len(trades),

        "delta_zscore": calculate_zscore(delta, delta_history, adaptive_window),
        "delta_ratio_zscore": calculate_zscore(delta_ratio, delta_ratio_history, adaptive_window),
        "velocity_zscore": calculate_zscore(velocity, velocity_history, adaptive_window),
        "volume_zscore": calculate_zscore(total_volume, volume_history, adaptive_window),

        "footprint_summary": footprint_summary,
        "dominant_footprint_levels": dominant_footprint_levels,
        "max_delta_footprint_level": max_delta_footprint_level,
        "max_volume_footprint_level": max_volume_footprint_level,
        "stacked_imbalance": stacked_imbalance,
        "stacked_imbalance_trend": stacked_imbalance_trend
    }


def calculate_average_size(levels):
    sizes = [float(level[1]) for level in levels]

    if len(sizes) == 0:
        return 0

    return sum(sizes) / len(sizes)


def detect_main_wall(levels, average_size):
    walls = []

    for level in levels:
        price = float(level[0])
        size = float(level[1])

        if average_size > 0 and size > WALL_MULTIPLIER * average_size:
            walls.append({
                "price": price,
                "size": size
            })

    if not walls:
        return None

    return max(walls, key=lambda wall: wall["size"])


def update_orderbook_state(data):
    bids = data["bids"]
    asks = data["asks"]

    best_bid_price = float(bids[0][0])
    best_bid_size = float(bids[0][1])

    best_ask_price = float(asks[0][0])
    best_ask_size = float(asks[0][1])

    spread = best_ask_price - best_bid_price
    spread_history.append(spread)

    spread_zscore = calculate_zscore(
        spread,
        list(spread_history),
        SPREAD_WINDOW
    )

    total_size = best_bid_size + best_ask_size
    size_history.append(total_size)

    whale_zscore = calculate_zscore(
        total_size,
        list(size_history),
        30
    )

    whale_detected = whale_zscore > WHALE_ZSCORE_THRESHOLD

    imbalance = (
        (best_bid_size - best_ask_size) / total_size
        if total_size > 0
        else 0
    )

    avg_bid_size = calculate_average_size(bids)
    avg_ask_size = calculate_average_size(asks)

    bid_wall = detect_main_wall(bids, avg_bid_size)
    ask_wall = detect_main_wall(asks, avg_ask_size)

    if imbalance > 0.3:
        market_state = "BUY_PRESSURE"

    elif imbalance < -0.3:
        market_state = "SELL_PRESSURE"

    else:
        market_state = "NEUTRAL"

    if spread_zscore > 2:
        execution_state = "BAD_EXECUTION"

    elif spread_zscore > 1:
        execution_state = "WIDE_SPREAD"

    else:
        execution_state = "NORMAL_EXECUTION"

    orderbook_state["best_bid"] = best_bid_price
    orderbook_state["best_ask"] = best_ask_price
    orderbook_state["spread"] = spread
    orderbook_state["spread_zscore"] = spread_zscore
    orderbook_state["imbalance"] = imbalance
    orderbook_state["whale_detected"] = whale_detected
    orderbook_state["whale_zscore"] = whale_zscore
    orderbook_state["bid_wall"] = bid_wall
    orderbook_state["ask_wall"] = ask_wall
    orderbook_state["market_state"] = market_state
    orderbook_state["execution_state"] = execution_state


def nearest_psychological_level(price):
    level = round(price / PSY_LEVEL_STEP) * PSY_LEVEL_STEP
    distance = price - level
    inside = abs(distance) <= PSY_LEVEL_TOLERANCE

    return {
        "level": level,
        "distance": distance,
        "inside": inside
    }


def detect_previous_high_low_zone(price):
    if len(row_history) < 5:
        return {
            "near_previous_high": False,
            "near_previous_low": False,
            "previous_high": None,
            "previous_low": None
        }

    recent_rows = list(row_history)[-PREVIOUS_HIGH_LOW_WINDOW:]

    previous_high = max(row["high"] for row in recent_rows)
    previous_low = min(row["low"] for row in recent_rows)

    near_high = abs(price - previous_high) <= PREVIOUS_HIGH_LOW_TOLERANCE
    near_low = abs(price - previous_low) <= PREVIOUS_HIGH_LOW_TOLERANCE

    return {
        "near_previous_high": near_high,
        "near_previous_low": near_low,
        "previous_high": previous_high,
        "previous_low": previous_low
    }


def update_volume_profile(price, volume):
    bucket = round(price / VOLUME_CLUSTER_BUCKET) * VOLUME_CLUSTER_BUCKET

    if len(volume_profile_queue) == volume_profile_queue.maxlen:
        old_bucket, old_volume = volume_profile_queue.popleft()

        volume_profile[old_bucket] -= old_volume

        if volume_profile[old_bucket] <= 0:
            del volume_profile[old_bucket]

    volume_profile[bucket] += volume
    volume_profile_queue.append((bucket, volume))

    return bucket


def detect_volume_cluster_zone(current_bucket):
    if len(volume_profile) < 5:
        return {
            "inside_volume_cluster": False,
            "volume_cluster_level": current_bucket,
            "bucket_volume": volume_profile[current_bucket]
        }

    volumes = list(volume_profile.values())
    average_volume = calculate_mean(volumes)
    bucket_volume = volume_profile[current_bucket]

    inside = (
        average_volume > 0
        and bucket_volume > average_volume * VOLUME_CLUSTER_MULTIPLIER
    )

    return {
        "inside_volume_cluster": inside,
        "volume_cluster_level": current_bucket,
        "bucket_volume": bucket_volume
    }


def detect_liquidity_zone():
    bid_wall = orderbook_state["bid_wall"]
    ask_wall = orderbook_state["ask_wall"]

    has_bid_wall = bid_wall is not None
    has_ask_wall = ask_wall is not None

    if has_bid_wall and has_ask_wall:
        return "BID_AND_ASK_LIQUIDITY"

    if has_bid_wall:
        return "BID_LIQUIDITY_ZONE"

    if has_ask_wall:
        return "ASK_LIQUIDITY_ZONE"

    return "NO_LIQUIDITY_ZONE"


def detect_rejection_zone(trade_row, absorption_state, trap_state):
    candle_range = trade_row["high"] - trade_row["low"]

    if candle_range <= 0:
        return "NO_REJECTION"

    close_position = (trade_row["close"] - trade_row["low"]) / candle_range

    upper_rejection = close_position < 0.35
    lower_rejection = close_position > 0.65

    if upper_rejection and absorption_state in [
        "SELLER_ABSORPTION",
        "POSSIBLE_SELLER_ABSORPTION"
    ]:
        return "UPPER_REJECTION_ZONE"

    if lower_rejection and absorption_state in [
        "BUYER_ABSORPTION",
        "POSSIBLE_BUYER_ABSORPTION"
    ]:
        return "LOWER_REJECTION_ZONE"

    if trap_state != "NO_TRAP":
        return "TRAP_REJECTION_ZONE"

    return "NO_REJECTION"


def get_zone_key(price):
    return round(price / ZONE_TOUCH_TOLERANCE) * ZONE_TOUCH_TOLERANCE


def update_zone_lifecycle(price):
    global active_zone_key

    zone_key = get_zone_key(price)

    if active_zone_key != zone_key:
        zone_touch_count[zone_key] += 1
        active_zone_key = zone_key

    touches = zone_touch_count[zone_key]

    if touches == 1:
        lifecycle = "FRESH"

    elif 2 <= touches <= 3:
        lifecycle = "TESTING"

    else:
        lifecycle = "CONSUMED"

    return {
        "zone_key": zone_key,
        "touches": touches,
        "lifecycle": lifecycle
    }


def calculate_zone_rank(zone_context):
    score = 0

    if zone_context["inside_psychological_zone"]:
        score += 1.5

    if zone_context["near_previous_high"] or zone_context["near_previous_low"]:
        score += 1.5

    if zone_context["inside_volume_cluster"]:
        score += 1.5

    if zone_context["statistical_zone"] in [
        "HIGH_STATISTICAL_ZONE",
        "LOW_STATISTICAL_ZONE"
    ]:
        score += 1.0

    if zone_context["statistical_zone"] in [
        "EXTREME_HIGH_ZONE",
        "EXTREME_LOW_ZONE"
    ]:
        score += 2.0

    if zone_context["liquidity_zone"] != "NO_LIQUIDITY_ZONE":
        score += 1.5

    if zone_context["rejection_zone"] != "NO_REJECTION":
        score += 1.5

    if zone_context["zone_lifecycle"] == "FRESH":
        score += 1.0

    elif zone_context["zone_lifecycle"] == "TESTING":
        score += 0.5

    elif zone_context["zone_lifecycle"] == "CONSUMED":
        score -= 1.0

    if score < 0:
        score = 0

    if score > 10:
        score = 10

    return round(score, 2)


def build_zone_context(trade_row, absorption_state, trap_state):
    price = trade_row["close"]

    psychological = nearest_psychological_level(price)
    previous_high_low = detect_previous_high_low_zone(price)

    current_bucket = update_volume_profile(
        price,
        trade_row["volume"]
    )

    volume_cluster = detect_volume_cluster_zone(current_bucket)
    liquidity_zone = detect_liquidity_zone()

    rejection_zone = detect_rejection_zone(
        trade_row,
        absorption_state,
        trap_state
    )

    lifecycle = update_zone_lifecycle(price)

    zone_context = {
        "nearest_psychological_level": psychological["level"],
        "distance_to_psychological_level": psychological["distance"],
        "inside_psychological_zone": psychological["inside"],

        "previous_high": previous_high_low["previous_high"],
        "previous_low": previous_high_low["previous_low"],
        "near_previous_high": previous_high_low["near_previous_high"],
        "near_previous_low": previous_high_low["near_previous_low"],

        "inside_volume_cluster": volume_cluster["inside_volume_cluster"],
        "volume_cluster_level": volume_cluster["volume_cluster_level"],
        "volume_cluster_volume": volume_cluster["bucket_volume"],

        "statistical_zone": trade_row["statistical_zone"],
        "price_zscore": trade_row["price_zscore"],

        "liquidity_zone": liquidity_zone,
        "rejection_zone": rejection_zone,

        "zone_key": lifecycle["zone_key"],
        "zone_touches": lifecycle["touches"],
        "zone_lifecycle": lifecycle["lifecycle"]
    }

    zone_rank = calculate_zone_rank(zone_context)

    if zone_rank >= 7:
        zone_priority = "HIGH_PRIORITY_ZONE"

    elif zone_rank >= 4:
        zone_priority = "MEDIUM_PRIORITY_ZONE"

    elif zone_rank >= 2:
        zone_priority = "LOW_PRIORITY_ZONE"

    else:
        zone_priority = "NO_IMPORTANT_ZONE"

    zone_context["zone_rank"] = zone_rank
    zone_context["zone_priority"] = zone_priority

    return zone_context


def classify_behavior(trade_row):
    price_change = trade_row["close"] - trade_row["open"]

    delta_z = trade_row["delta_zscore"]
    velocity_z = trade_row["velocity_zscore"]
    imbalance = orderbook_state["imbalance"]

    if delta_z > 2 and velocity_z > 1.5 and price_change > 0 and imbalance > 0:
        return "BUY_AGGRESSION"

    if delta_z < -2 and velocity_z > 1.5 and price_change < 0 and imbalance < 0:
        return "SELL_AGGRESSION"

    if abs(delta_z) < 1 and abs(velocity_z) < 1:
        return "NEUTRAL"

    return "UNDEFINED"


def detect_absorption(trade_row):
    price_change = trade_row["close"] - trade_row["open"]

    delta_z = trade_row["delta_zscore"]
    velocity_z = trade_row["velocity_zscore"]
    imbalance = orderbook_state["imbalance"]

    small_price_move = abs(price_change) < 5
    fast_market = velocity_z > 1.5

    strong_buying = delta_z > 2
    strong_selling = delta_z < -2

    if strong_buying and fast_market and small_price_move:
        return "SELLER_ABSORPTION"

    if strong_selling and fast_market and small_price_move:
        return "BUYER_ABSORPTION"

    if strong_buying and imbalance < 0:
        return "POSSIBLE_SELLER_ABSORPTION"

    if strong_selling and imbalance > 0:
        return "POSSIBLE_BUYER_ABSORPTION"

    return "NO_ABSORPTION"


def detect_zone_absorption(zone_rank, zone_priority, absorption_state):
    if absorption_state == "NO_ABSORPTION":
        return "NO_ZONE_ABSORPTION"

    strong_absorption = absorption_state in [
        "BUYER_ABSORPTION",
        "SELLER_ABSORPTION"
    ]

    possible_absorption = absorption_state in [
        "POSSIBLE_BUYER_ABSORPTION",
        "POSSIBLE_SELLER_ABSORPTION"
    ]

    if zone_rank >= 7 and strong_absorption:
        return "HIGH_QUALITY_ZONE_ABSORPTION"

    if zone_rank >= 7 and possible_absorption:
        return "POSSIBLE_HIGH_QUALITY_ZONE_ABSORPTION"

    if zone_rank >= 4 and strong_absorption:
        return "VALID_ZONE_ABSORPTION"

    if zone_rank >= 4 and possible_absorption:
        return "POSSIBLE_ZONE_ABSORPTION"

    if zone_priority == "LOW_PRIORITY_ZONE":
        return "WEAK_ZONE_ABSORPTION"

    return "ABSORPTION_OUTSIDE_IMPORTANT_ZONE"


def confirm_zone_reaction(row):
    if row["zone_absorption_state"] in [
        "HIGH_QUALITY_ZONE_ABSORPTION",
        "VALID_ZONE_ABSORPTION"
    ]:
        if row["rejection_zone"] != "NO_REJECTION":
            return "ABSORPTION_CONFIRMED_BY_REJECTION"

        if row["liquidity_zone"] != "NO_LIQUIDITY_ZONE":
            return "ABSORPTION_SUPPORTED_BY_LIQUIDITY"

        return "ABSORPTION_WAIT_CONFIRMATION"

    if row["trap_state"] != "NO_TRAP":
        return "TRAP_REACTION"

    return "NO_CONFIRMED_REACTION"


def detect_exhaustion(trade_row):
    price_change = trade_row["close"] - trade_row["open"]

    delta_z = trade_row["delta_zscore"]
    velocity_z = trade_row["velocity_zscore"]

    if delta_z > 2 and velocity_z < 0 and price_change < 5:
        return "BUYER_EXHAUSTION"

    if delta_z < -2 and velocity_z < 0 and price_change > -5:
        return "SELLER_EXHAUSTION"

    return "NO_EXHAUSTION"


def detect_trap(trade_row, absorption_state, exhaustion_state):
    price_change = trade_row["close"] - trade_row["open"]
    delta_z = trade_row["delta_zscore"]

    if absorption_state == "SELLER_ABSORPTION" and price_change <= 0:
        return "BUYERS_TRAPPED"

    if absorption_state == "BUYER_ABSORPTION" and price_change >= 0:
        return "SELLERS_TRAPPED"

    if exhaustion_state == "BUYER_EXHAUSTION" and delta_z > 2:
        return "LATE_BUYERS_AT_RISK"

    if exhaustion_state == "SELLER_EXHAUSTION" and delta_z < -2:
        return "LATE_SELLERS_AT_RISK"

    return "NO_TRAP"


def get_watch_mode(zone_rank):
    if zone_rank >= 7:
        return "HIGH_ALERT"

    if zone_rank >= 4:
        return "WATCH_MODE"

    return "IGNORE"


def build_combined_row(trade_row):
    renko = update_renko(trade_row["close"])

    behavior_state = classify_behavior(trade_row)
    absorption_state = detect_absorption(trade_row)
    exhaustion_state = detect_exhaustion(trade_row)

    trap_state = detect_trap(
        trade_row,
        absorption_state,
        exhaustion_state
    )

    zone_context = build_zone_context(
        trade_row,
        absorption_state,
        trap_state
    )

    zone_absorption_state = detect_zone_absorption(
        zone_context["zone_rank"],
        zone_context["zone_priority"],
        absorption_state
    )

    divergence_result = detect_all_divergences(trade_row)

    divergence_alignment = get_divergence_alignment(
        divergence_result,
        zone_context,
        absorption_state
    )

    full_row_context = {
        **trade_row,
        **zone_context
    }

    failed_auction = detect_failed_auction(
        full_row_context,
        trade_row["footprint_summary"],
        trade_row["stacked_imbalance"],
        orderbook_state
    )

    failed_auction_trend = get_failed_auction_trend()
    auction_failure_rate = get_auction_failure_rate(
        failed_auction["level"]
    )

    level_absorption = detect_absorption_per_level(
        trade_row["footprint_summary"],
        trade_row
    )

    level_absorption_trend = get_absorption_level_trend()

    footprint_final_score = calculate_footprint_final_score(
        trade_row["stacked_imbalance"],
        divergence_result,
        failed_auction,
        level_absorption,
        trade_row
    )

    temp_row = {
        **trade_row,

        "renko_close": renko["last_renko_close"],
        "renko_direction": renko["direction"],
        "renko_bricks": renko["bricks"],
        "renko_event": renko["event"],

        "best_bid": orderbook_state["best_bid"],
        "best_ask": orderbook_state["best_ask"],
        "spread": orderbook_state["spread"],
        "spread_zscore": orderbook_state["spread_zscore"],
        "imbalance": orderbook_state["imbalance"],
        "whale_detected": orderbook_state["whale_detected"],
        "whale_zscore": orderbook_state["whale_zscore"],
        "bid_wall": orderbook_state["bid_wall"],
        "ask_wall": orderbook_state["ask_wall"],
        "orderbook_state": orderbook_state["market_state"],
        "execution_state": orderbook_state["execution_state"],

        "behavior_state": behavior_state,
        "absorption_state": absorption_state,
        "zone_absorption_state": zone_absorption_state,
        "exhaustion_state": exhaustion_state,
        "trap_state": trap_state,

        "global_cvd": divergence_result["global_cvd"],
        "regular_divergence": divergence_result["regular_divergence"],
        "cvd_divergence": divergence_result["cvd_divergence"],
        "divergence_trend": divergence_result["divergence_trend"],
        "recent_divergence_count": divergence_result["recent_divergence_count"],
        "has_active_divergence": divergence_result["has_active_divergence"],
        "divergence_alignment": divergence_alignment,

        "failed_auction": failed_auction,
        "failed_auction_trend": failed_auction_trend,
        "auction_failure_rate": auction_failure_rate,

        "level_absorption": level_absorption,
        "level_absorption_trend": level_absorption_trend,

        "footprint_final_score": footprint_final_score,

        **zone_context
    }

    temp_row["zone_reaction_confirmation"] = confirm_zone_reaction(temp_row)

    return temp_row


def print_clean_output(row):
    watch_mode = get_watch_mode(row["zone_rank"])

    print("\n==============================")
    print("MARKET CONTEXT")
    print("==============================")

    print(f"PRICE        : {row['close']}")
    print(f"ZONE PRIORITY: {row['zone_priority']}")
    print(f"ZONE RANK    : {row['zone_rank']}")
    print(f"WATCH MODE   : {watch_mode}")

    print("\n--- PHASE 1 DATA ---")
    print(f"Open         : {row['open']}")
    print(f"High         : {row['high']}")
    print(f"Low          : {row['low']}")
    print(f"Close        : {row['close']}")
    print(f"Volume       : {round(row['volume'], 5)}")
    print(f"Buy Volume   : {round(row['buy_volume'], 5)}")
    print(f"Sell Volume  : {round(row['sell_volume'], 5)}")
    print(f"Delta        : {round(row['delta'], 5)}")
    print(f"Delta Ratio  : {round(row['delta_ratio'], 4)}")
    print(f"Velocity     : {round(row['velocity'], 4)}")
    print(f"RVI          : {round(row['rvi'], 4)}")
    print(f"Duration     : {round(row['duration_seconds'], 3)}s")
    print(f"Tick Count   : {row['tick_count']}")

    print("\n--- FOOTPRINT 3A1 ---")
    print(f"Max Delta Level  : {row['max_delta_footprint_level']}")
    print(f"Max Volume Level : {row['max_volume_footprint_level']}")
    print(f"Dominant Levels  : {row['dominant_footprint_levels']}")

    print("\n--- STACKED IMBALANCE 3A2 ---")
    print(f"Stacked Imb.     : {row['stacked_imbalance']}")
    print(f"Stacked Trend    : {row['stacked_imbalance_trend']}")

    print("\n--- DIVERGENCE 3A3 ---")
    print(f"Global CVD    : {round(row['global_cvd'], 5)}")
    print(f"Regular Div   : {row['regular_divergence']}")
    print(f"CVD Div       : {row['cvd_divergence']}")
    print(f"Div Trend     : {row['divergence_trend']}")
    print(f"Div Align     : {row['divergence_alignment']}")

    print("\n--- FAILED AUCTION 3A4 ---")
    print(f"Failed Auction : {row['failed_auction']}")
    print(f"Failure Trend  : {row['failed_auction_trend']}")
    print(f"Failure Rate   : {row['auction_failure_rate']}")

    print("\n--- ABSORPTION LEVEL 3A5 ---")
    print(f"Level Absorp. : {row['level_absorption']}")
    print(f"Absorp Trend  : {row['level_absorption_trend']}")

    print("\n--- FOOTPRINT SCORE 3A6 ---")
    print(f"FP State      : {row['footprint_final_score']['final_state']}")
    print(f"Bullish Score : {row['footprint_final_score']['bullish_score']}")
    print(f"Bearish Score : {row['footprint_final_score']['bearish_score']}")
    print(f"FP Notes      : {row['footprint_final_score']['notes']}")

    print("\n--- ZONE INFO ---")
    print(f"Psych Level  : {row['nearest_psychological_level']}")
    print(f"Distance     : {round(row['distance_to_psychological_level'], 2)}")
    print(f"Inside Psych : {row['inside_psychological_zone']}")
    print(f"Prev High    : {row['previous_high']}")
    print(f"Prev Low     : {row['previous_low']}")
    print(f"Near High    : {row['near_previous_high']}")
    print(f"Near Low     : {row['near_previous_low']}")
    print(f"Volume Zone  : {row['inside_volume_cluster']}")
    print(f"Volume Level : {row['volume_cluster_level']}")
    print(f"Liquidity    : {row['liquidity_zone']}")
    print(f"Lifecycle    : {row['zone_lifecycle']} | Touches: {row['zone_touches']}")

    print("\n--- STATISTICS ---")
    print(f"Stat Zone    : {row['statistical_zone']}")
    print(f"Price Z      : {round(row['price_zscore'], 2)}")
    print(f"Delta Z      : {round(row['delta_zscore'], 2)}")
    print(f"Velocity Z   : {round(row['velocity_zscore'], 2)}")
    print(f"Volume Z     : {round(row['volume_zscore'], 2)}")
    print(f"Window       : {row['adaptive_window']}")

    print("\n--- ORDERFLOW ---")
    print(f"Behavior     : {row['behavior_state']}")
    print(f"Absorption   : {row['absorption_state']}")
    print(f"Zone Absorp. : {row['zone_absorption_state']}")
    print(f"Reaction     : {row['zone_reaction_confirmation']}")
    print(f"Exhaustion   : {row['exhaustion_state']}")
    print(f"Trap         : {row['trap_state']}")

    print("\n--- RENKO ---")
    print(f"Renko Close  : {row['renko_close']}")
    print(f"Direction    : {row['renko_direction']}")
    print(f"Bricks       : {row['renko_bricks']}")
    print(f"Event        : {row['renko_event']}")

    print("\n--- EXECUTION ---")
    print(f"Best Bid     : {row['best_bid']}")
    print(f"Best Ask     : {row['best_ask']}")
    print(f"Spread       : {row['spread']}")
    print(f"Spread Z     : {round(row['spread_zscore'], 2)}")
    print(f"Imbalance    : {round(row['imbalance'], 3)}")
    print(f"Whale        : {row['whale_detected']} | Z: {round(row['whale_zscore'], 2)}")
    print(f"Bid Wall     : {row['bid_wall']}")
    print(f"Ask Wall     : {row['ask_wall']}")
    print(f"Execution    : {row['execution_state']}")
    print(f"Orderbook    : {row['orderbook_state']}")


async def trade_stream():
    global tick_buffer

    async with websockets.connect(TRADE_URL) as ws:
        print("TRADE STREAM CONNECTED")

        while True:
            message = await ws.recv()
            data = json.loads(message)

            trade = validate_trade(data)

            if trade is None:
                continue

            if is_duplicate(trade):
                continue

            tick_buffer.append(trade)
            update_footprint(trade)

            if len(tick_buffer) >= ROW_SIZE:
                trade_row = build_trade_row(tick_buffer)
                combined_row = build_combined_row(trade_row)

                row_history.append(combined_row)

                print_clean_output(combined_row)

                tick_buffer = []
                reset_footprint()


async def orderbook_stream():
    async with websockets.connect(DEPTH_URL) as ws:
        print("ORDER BOOK STREAM CONNECTED")

        while True:
            message = await ws.recv()
            data = json.loads(message)

            update_orderbook_state(data)


async def main():
    await asyncio.gather(
        trade_stream(),
        orderbook_stream()
    )


asyncio.run(main())