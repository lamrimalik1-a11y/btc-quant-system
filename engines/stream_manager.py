import asyncio
import json

import websockets

from core.config_manager import (
    get_config,
)

from core.row_builder import (
    build_trade_row,
)

from core.adaptive_window import (
    calculate_adaptive_window,
)

from core.data_validator import (
    validate_trade,
)

from core.gap_detector import (
    detect_gap,
)

from core.storage import (
    initialize_storage,
    save_row,
)

from core.orderbook import (
    process_orderbook,
)

from core.orderbook_storage import (
    initialize_orderbook_storage,
    save_orderbook,
)

from core.market_clock import (
    update_trade_clock,
    update_depth_clock,
    get_market_clock,
)

from core.session_manager import (
    get_market_session,
)

from core.market_context import (
    MarketContext,
)

from core.state import (
    update_history,
    price_history,
    velocity_history,
)

from core.output_manager import (
    print_row_summary,
)

from engines.engine_registry import (
    EngineRegistry,
)


SYMBOL = get_config("SYMBOL")
ROW_SIZE = get_config("ROW_SIZE")
RECONNECT_DELAY = get_config("RECONNECT_DELAY")

TRADE_URL = (
    f"wss://stream.binance.com:9443/ws/{SYMBOL}@trade"
)

DEPTH_URL = (
    f"wss://stream.binance.com:9443/ws/{SYMBOL}@depth5@100ms"
)

tick_buffer = []
latest_orderbook = None

engine_registry = EngineRegistry()
engine_registry.discover_engines()

print("\nDISCOVERED ENGINES:")

for engine_name in engine_registry.list_engines():
    print("-", engine_name)


async def process_depth_stream():

    global latest_orderbook

    print("[DEPTH STREAM CONNECTING]")

    async with websockets.connect(
        DEPTH_URL
    ) as websocket:

        print("[DEPTH STREAM CONNECTED]")

        async for message in websocket:

            update_depth_clock()

            data = json.loads(message)

            if (
                "b" not in data
                or
                "a" not in data
            ):
                continue

            depth_data = {
                "bids": data.get("b", []),
                "asks": data.get("a", []),
            }

            processed_orderbook = process_orderbook(
                depth_data
            )

            if processed_orderbook is None:
                continue

            latest_orderbook = processed_orderbook

            save_orderbook(
                latest_orderbook
            )


async def process_trade_stream():

    global latest_orderbook

    print("[TRADE STREAM CONNECTING]")

    async with websockets.connect(
        TRADE_URL
    ) as websocket:

        print("[TRADE STREAM CONNECTED]\n")

        async for message in websocket:

            data = json.loads(message)

            required_keys = [
                "p",
                "q",
                "m",
                "T",
                "t",
            ]

            if not all(
                key in data
                for key in required_keys
            ):
                continue

            price = float(data["p"])
            quantity = float(data["q"])
            is_sell = data["m"]
            timestamp = int(data["T"])

            update_trade_clock(timestamp)

            trade = {
                "trade_id": data["t"],
                "price": price,
                "quantity": quantity,
                "timestamp": timestamp,
                "side": (
                    "SELL"
                    if is_sell
                    else "BUY"
                ),
            }

            validation = validate_trade(trade)

            if not validation["is_valid"]:

                if validation["reasons"]:
                    print(
                        "INVALID TRADE:",
                        validation["reasons"]
                    )

                continue

            gap_result = detect_gap(trade)

            if gap_result["gap_detected"]:

                print("\n[DATA GAP DETECTED]")

                print(
                    "GAP SIZE:",
                    gap_result["gap_size_ms"],
                    "ms"
                )

            tick_buffer.append(trade)

            if len(tick_buffer) < ROW_SIZE:
                continue

            row = build_trade_row(tick_buffer)

            tick_buffer.clear()

            update_history(row)

            adaptive_window = calculate_adaptive_window(
                row["velocity"],
                velocity_history
            )

            row["adaptive_window"] = adaptive_window

            if latest_orderbook is not None:

                row["spread"] = latest_orderbook.get("spread")
                row["imbalance"] = latest_orderbook.get(
                    "imbalance",
                    0
                )
                row["best_bid"] = latest_orderbook.get(
                    "best_bid_price"
                )
                row["best_ask"] = latest_orderbook.get(
                    "best_ask_price"
                )
                row["best_bid_size"] = latest_orderbook.get(
                    "best_bid_size"
                )
                row["best_ask_size"] = latest_orderbook.get(
                    "best_ask_size"
                )
                row["bid_wall_price"] = latest_orderbook.get(
                    "bid_wall_price"
                )
                row["bid_wall_size"] = latest_orderbook.get(
                    "bid_wall_size"
                )
                row["ask_wall_price"] = latest_orderbook.get(
                    "ask_wall_price"
                )
                row["ask_wall_size"] = latest_orderbook.get(
                    "ask_wall_size"
                )
                row["liquidity_strength"] = latest_orderbook.get(
                    "liquidity_strength"
                )

            else:

                row["spread"] = None
                row["imbalance"] = 0
                row["best_bid"] = None
                row["best_ask"] = None
                row["best_bid_size"] = None
                row["best_ask_size"] = None
                row["bid_wall_price"] = None
                row["bid_wall_size"] = None
                row["ask_wall_price"] = None
                row["ask_wall_size"] = None
                row["liquidity_strength"] = None

            market_clock = get_market_clock()

            row["trade_depth_delay_ms"] = market_clock[
                "trade_depth_delay_ms"
            ]

            row["market_session"] = get_market_session()

            context = MarketContext(
                row=row,
                orderbook=latest_orderbook,
                market_clock=market_clock,
                session=row["market_session"],
            )

            engine_outputs = engine_registry.process_all(
                context
            )

            context.set_engine_outputs(
                engine_outputs
            )

            save_row(row)

            context.active_engines = (
                engine_registry.list_engines()
            )

            context.history = price_history

            print_row_summary(context)


async def start_stream():

    initialize_storage()
    initialize_orderbook_storage()

    while True:

        try:

            await asyncio.gather(
                process_trade_stream(),
                process_depth_stream(),
            )

        except Exception as error:

            print("\n[CONNECTION LOST]")
            print("ERROR:", error)

            print(
                f"\n[RECONNECTING IN {RECONNECT_DELAY} SECONDS]"
            )

            await asyncio.sleep(RECONNECT_DELAY)


async def main():

    await start_stream()


if __name__ == "__main__":

    asyncio.run(main())