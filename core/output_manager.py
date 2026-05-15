# ==================================================
# OUTPUT MANAGER
# ==================================================

from core.state import (
    price_history,
    system_state,
)


class OutputManager:

    def print_row_summary(self, context):

        row = self._get(context, "row", {})
        engine_outputs = self._get(context, "engine_outputs", {})

        statistics = engine_outputs.get("statistics_engine", {})
        renko = engine_outputs.get("renko_engine", {})
        zone = engine_outputs.get("zone_engine", {})

        print("\n" + "=" * 70)
        print("NEW ROW CREATED")
        print("=" * 70)

        print(f"ROW COUNTER: {system_state['row_counter']}")

        print("\n--- ROW OHLC ---")
        print(f"OPEN: {self._get(row, 'open')}")
        print(f"HIGH: {self._get(row, 'high')}")
        print(f"LOW: {self._get(row, 'low')}")
        print(f"CLOSE: {self._get(row, 'close')}")

        print("\n--- ROW FLOW ---")
        print(f"VOLUME: {self._get(row, 'volume')}")
        print(f"BUY VOLUME: {self._get(row, 'buy_volume')}")
        print(f"SELL VOLUME: {self._get(row, 'sell_volume')}")
        print(f"DELTA: {self._get(row, 'delta')}")
        print(f"DELTA RATIO: {self._get(row, 'delta_ratio')}")
        print(f"VELOCITY: {self._get(row, 'velocity')}")
        print(f"DURATION SEC: {self._get(row, 'duration_sec')}")
        print(f"DURATION MS: {self._get(row, 'duration_ms')}")
        print(f"TICK COUNT: {self._get(row, 'tick_count')}")
        print(f"ADAPTIVE WINDOW: {self._get(row, 'adaptive_window')}")

        print("\n--- MARKET CONTEXT / LATENCY ---")
        print(f"SESSION: {self._get(context, 'session')}")
        print(f"SPREAD: {self._get(row, 'spread')}")
        print(f"IMBALANCE: {self._get(row, 'imbalance')}")
        print(f"BEST BID: {self._get(row, 'best_bid')}")
        print(f"BEST ASK: {self._get(row, 'best_ask')}")
        print(f"TRADE/DEPTH DELAY: {self._get(row, 'trade_depth_delay_ms')} ms")

        print("\n--- STATISTICS / NORMAL DISTRIBUTION ---")
        print(f"PRICE ZSCORE: {self._get(statistics, 'price_zscore')}")
        print(f"FAST PRICE ZSCORE: {self._get(statistics, 'fast_price_zscore')}")
        print(f"MEDIUM PRICE ZSCORE: {self._get(statistics, 'medium_price_zscore')}")
        print(f"SLOW PRICE ZSCORE: {self._get(statistics, 'slow_price_zscore')}")
        print(f"VOLUME ZSCORE: {self._get(statistics, 'volume_zscore')}")
        print(f"DELTA ZSCORE: {self._get(statistics, 'delta_zscore')}")
        print(f"VELOCITY ZSCORE: {self._get(statistics, 'velocity_zscore')}")
        print(f"PRICE ZONE: {self._get(row, 'price_zone')}")
        print(f"VOLUME ZONE: {self._get(row, 'volume_zone')}")
        print(f"DELTA ZONE: {self._get(row, 'delta_zone')}")
        print(f"VELOCITY ZONE: {self._get(row, 'velocity_zone')}")

        print("\n--- VARIANCE ---")
        print(f"PRICE VARIANCE: {self._get(row, 'price_variance')}")
        print(f"VOLUME VARIANCE: {self._get(row, 'volume_variance')}")
        print(f"DELTA VARIANCE: {self._get(row, 'delta_variance')}")
        print(f"VELOCITY VARIANCE: {self._get(row, 'velocity_variance')}")

        print("\n--- DISTRIBUTION SNAPSHOT ---")
        print(f"DISTRIBUTION READY: {self._get(row, 'distribution_ready')}")
        print(f"PRICE DISTRIBUTION MEAN: {self._get(row, 'price_distribution_mean')}")
        print(f"PRICE DISTRIBUTION MEDIAN: {self._get(row, 'price_distribution_median')}")
        print(f"DISTRIBUTION RANGE: {self._get(row, 'distribution_range')}")
        print(f"PRICE PERCENTILE: {self._get(row, 'price_percentile')}")
        print(f"VOLUME PERCENTILE: {self._get(row, 'volume_percentile')}")
        print(f"DELTA PERCENTILE: {self._get(row, 'delta_percentile')}")
        print(f"VELOCITY PERCENTILE: {self._get(row, 'velocity_percentile')}")
        print(f"PRICE PERCENTILE ZONE: {self._get(row, 'price_percentile_zone')}")

        print("\n--- RENKO ---")
        print(f"RVI: {self._get(renko, 'rvi')}")
        print(f"RVI STATE: {self._get(renko, 'rvi_state')}")
        print(f"RENKO DIRECTION: {self._get(renko, 'renko_direction')}")
        print(f"RENKO EVENT: {self._get(renko, 'renko_event')}")
        print(f"RENKO BRICKS: {self._get(renko, 'renko_bricks')}")
        print(f"RENKO EXPANSION: {self._get(row, 'renko_expansion')}")

        print("\n--- ZONE ENGINE ---")

        psychological = self._get(zone, "psychological", {})
        previous_levels = self._get(zone, "previous_levels", {})

        print(f"ZONE SCORE: {self._get(zone, 'score')}")
        print(f"ZONE PRIORITY: {self._get(zone, 'priority')}")
        print(f"PSYCHOLOGICAL: {self._get(psychological, 'classification')}")
        print(f"PSYCHOLOGICAL LEVEL: {self._get(psychological, 'nearest_level')}")
        print(f"PSYCHOLOGICAL DISTANCE: {self._get(psychological, 'distance')}")
        print(f"PSYCHOLOGICAL STRENGTH: {self._get(psychological, 'strength')}")
        print(f"INSIDE PSYCHOLOGICAL ZONE: {self._get(psychological, 'inside_zone')}")
        print(f"PREVIOUS HIGH: {self._get(previous_levels, 'previous_high')}")
        print(f"PREVIOUS LOW: {self._get(previous_levels, 'previous_low')}")
        print(f"NEAR PREVIOUS HIGH: {self._get(previous_levels, 'near_previous_high')}")
        print(f"NEAR PREVIOUS LOW: {self._get(previous_levels, 'near_previous_low')}")

        print("\n--- SYSTEM STATE ---")
        print(f"HISTORY SIZE: {len(price_history)}")
        print(f"ROW COUNTER: {system_state['row_counter']}")

        if isinstance(engine_outputs, dict):
            active_engines = list(engine_outputs.keys())
        else:
            active_engines = []

        print(f"ACTIVE ENGINES: {active_engines}")

    def display(self, context):
        self.print_row_summary(context)

    def _get(self, source, key, default=None):

        if source is None:
            return default

        if isinstance(source, dict):
            return source.get(key, default)

        return getattr(source, key, default)


# ==================================================
# BACKWARD COMPATIBILITY
# ==================================================

def print_row_summary(context):

    manager = OutputManager()
    manager.print_row_summary(context)