import asyncio
import json
from collections import deque

import websockets


SYMBOL = "btcusdt"

DEPTH_URL = f"wss://stream.binance.com:9443/ws/{SYMBOL}@depth5@100ms"

WALL_MULTIPLIER = 2.0
PULL_STACK_THRESHOLD = 1.0

SPREAD_WINDOW = 50
SIZE_WINDOW = 100
WHALE_ZSCORE_THRESHOLD = 2.5

STRONG_IMBALANCE = 0.75

WALL_PRICE_TOLERANCE = 0.01
WALL_SIZE_CHANGE_THRESHOLD = 1.0

last_bid_size = None
last_ask_size = None

last_whale_state = False
last_market_state = "NEUTRAL"

last_bid_wall_price = None
last_bid_wall_size = None

last_ask_wall_price = None
last_ask_wall_size = None

spread_history = deque(maxlen=SPREAD_WINDOW)
size_history = deque(maxlen=SIZE_WINDOW)


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


def calculate_average_size(levels):
    sizes = [float(level[1]) for level in levels]

    if len(sizes) == 0:
        return 0

    return sum(sizes) / len(sizes)


def detect_liquidity_walls(levels, average_size):
    walls = []

    for level in levels:
        price = float(level[0])
        size = float(level[1])

        if average_size > 0 and size > WALL_MULTIPLIER * average_size:
            walls.append({
                "price": price,
                "size": size
            })

    return walls


def get_main_wall(walls):
    if not walls:
        return None

    return max(walls, key=lambda wall: wall["size"])


def wall_changed(current_wall, last_price, last_size):
    if current_wall is None and last_price is None:
        return False

    if current_wall is None and last_price is not None:
        return True

    if current_wall is not None and last_price is None:
        return True

    price_changed = abs(current_wall["price"] - last_price) > WALL_PRICE_TOLERANCE
    size_changed = abs(current_wall["size"] - last_size) > WALL_SIZE_CHANGE_THRESHOLD

    return price_changed or size_changed


def detect_pull_stack(current_bid_size, current_ask_size):
    global last_bid_size
    global last_ask_size

    events = []

    if last_bid_size is not None and last_ask_size is not None:
        bid_change = current_bid_size - last_bid_size
        ask_change = current_ask_size - last_ask_size

        if bid_change > PULL_STACK_THRESHOLD:
            events.append("BID STACKING")

        elif bid_change < -PULL_STACK_THRESHOLD:
            events.append("BID PULLING")

        if ask_change > PULL_STACK_THRESHOLD:
            events.append("ASK STACKING")

        elif ask_change < -PULL_STACK_THRESHOLD:
            events.append("ASK PULLING")

    last_bid_size = current_bid_size
    last_ask_size = current_ask_size

    return events


def detect_whale(size, history):
    whale_zscore = calculate_zscore(
        size,
        list(history),
        30
    )

    if whale_zscore > WHALE_ZSCORE_THRESHOLD:
        return True, whale_zscore

    return False, whale_zscore


def get_market_state(imbalance):
    if imbalance > 0.3:
        return "BUY PRESSURE"

    if imbalance < -0.3:
        return "SELL PRESSURE"

    return "NEUTRAL"


def print_event(title, data):
    print("\n==============================")
    print(title)
    print("==============================")

    for key, value in data.items():
        print(f"{key}: {value}")


async def stream_order_book():
    global last_whale_state
    global last_market_state

    global last_bid_wall_price
    global last_bid_wall_size
    global last_ask_wall_price
    global last_ask_wall_size

    async with websockets.connect(DEPTH_URL) as ws:
        print("ORDER BOOK CONNECTED")
        print("EVENT MODE + WALL MEMORY ENABLED")

        while True:
            message = await ws.recv()
            data = json.loads(message)

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

            whale_detected, whale_zscore = detect_whale(
                total_size,
                size_history
            )

            if total_size > 0:
                imbalance = (
                    (best_bid_size - best_ask_size)
                    /
                    total_size
                )
            else:
                imbalance = 0

            market_state = get_market_state(imbalance)

            avg_bid_size = calculate_average_size(bids)
            avg_ask_size = calculate_average_size(asks)

            bid_walls = detect_liquidity_walls(
                bids,
                avg_bid_size
            )

            ask_walls = detect_liquidity_walls(
                asks,
                avg_ask_size
            )

            main_bid_wall = get_main_wall(bid_walls)
            main_ask_wall = get_main_wall(ask_walls)

            pull_stack_events = detect_pull_stack(
                best_bid_size,
                best_ask_size
            )

            if whale_detected and not last_whale_state:
                print_event(
                    "WHALE DETECTED",
                    {
                        "Best Bid": best_bid_price,
                        "Bid Size": best_bid_size,
                        "Best Ask": best_ask_price,
                        "Ask Size": best_ask_size,
                        "Whale Z": round(whale_zscore, 2),
                        "Imbalance": round(imbalance, 4),
                        "State": market_state
                    }
                )

            last_whale_state = whale_detected

            if abs(imbalance) >= STRONG_IMBALANCE:
                print_event(
                    "STRONG IMBALANCE",
                    {
                        "Imbalance": round(imbalance, 4),
                        "State": market_state,
                        "Bid Size": best_bid_size,
                        "Ask Size": best_ask_size
                    }
                )

            if market_state != last_market_state:
                print_event(
                    "MARKET STATE CHANGE",
                    {
                        "From": last_market_state,
                        "To": market_state,
                        "Imbalance": round(imbalance, 4)
                    }
                )

            last_market_state = market_state

            if spread_zscore > 2:
                print_event(
                    "BAD EXECUTION / SPREAD EXPANSION",
                    {
                        "Spread": spread,
                        "Spread Z": round(spread_zscore, 2)
                    }
                )

            if pull_stack_events:
                print_event(
                    "PULLING / STACKING EVENT",
                    {
                        "Events": ", ".join(pull_stack_events),
                        "Bid Size": best_bid_size,
                        "Ask Size": best_ask_size,
                        "Imbalance": round(imbalance, 4)
                    }
                )

            bid_wall_has_changed = wall_changed(
                main_bid_wall,
                last_bid_wall_price,
                last_bid_wall_size
            )

            ask_wall_has_changed = wall_changed(
                main_ask_wall,
                last_ask_wall_price,
                last_ask_wall_size
            )

            if bid_wall_has_changed or ask_wall_has_changed:
                wall_data = {}

                if main_bid_wall is not None:
                    wall_data["Main Bid Wall"] = (
                        f"{main_bid_wall['price']} | {main_bid_wall['size']}"
                    )
                else:
                    wall_data["Main Bid Wall"] = "REMOVED"

                if main_ask_wall is not None:
                    wall_data["Main Ask Wall"] = (
                        f"{main_ask_wall['price']} | {main_ask_wall['size']}"
                    )
                else:
                    wall_data["Main Ask Wall"] = "REMOVED"

                print_event(
                    "LIQUIDITY WALL CHANGE",
                    wall_data
                )

            if main_bid_wall is not None:
                last_bid_wall_price = main_bid_wall["price"]
                last_bid_wall_size = main_bid_wall["size"]
            else:
                last_bid_wall_price = None
                last_bid_wall_size = None

            if main_ask_wall is not None:
                last_ask_wall_price = main_ask_wall["price"]
                last_ask_wall_size = main_ask_wall["size"]
            else:
                last_ask_wall_price = None
                last_ask_wall_size = None


asyncio.run(stream_order_book())