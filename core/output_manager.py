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

        print(f"PRICE STD: {self._get(statistics, 'price_std')}")
        print(f"WEIGHTED STD: {self._get(statistics, 'price_weighted_std')}")
        print(f"ROBUST STD: {self._get(statistics, 'price_robust_std')}")
        print(f"EWMA STD: {self._get(statistics, 'price_ewma_std')}")
        print(f"VOLATILITY WEIGHTED STD: {self._get(statistics, 'price_volatility_weighted_std')}")
        print(f"ADAPTIVE STD: {self._get(statistics, 'price_adaptive_std')}")
        print(f"STD INSTABILITY: {self._get(statistics, 'std_instability_state')}")

        print(f"VOLUME ADAPTIVE STD: {self._get(statistics, 'volume_adaptive_std')}")
        print(f"DELTA ADAPTIVE STD: {self._get(statistics, 'delta_adaptive_std')}")
        print(f"VELOCITY ADAPTIVE STD: {self._get(statistics, 'velocity_adaptive_std')}")
        print(f"ADAPTIVE DISTRIBUTION WINDOW: {self._get(statistics, 'adaptive_distribution_window')}")

        print("\n--- VOLUME STATISTICS ---")
        print(f"VOLUME MEAN: {self._get(statistics, 'volume_mean')}")
        print(f"VOLUME STD: {self._get(statistics, 'volume_std')}")
        print(f"VOLUME STATE: {self._get(statistics, 'volume_state')}")
        print(f"VOLUME EXPANSION: {self._get(statistics, 'volume_expansion')}")
        print(f"VOLUME COMPRESSION: {self._get(statistics, 'volume_compression')}")
        print(f"ABNORMAL VOLUME: {self._get(statistics, 'abnormal_volume')}")
        print(f"CLIMACTIC VOLUME: {self._get(statistics, 'climactic_volume')}")

        print("\n--- SPREAD STATISTICS ---")
        print(f"SPREAD MEAN: {self._get(statistics, 'spread_mean')}")
        print(f"SPREAD STD: {self._get(statistics, 'spread_std')}")
        print(f"SPREAD ZSCORE: {self._get(statistics, 'spread_zscore')}")
        print(f"SPREAD STATE: {self._get(statistics, 'spread_state')}")
        print(f"SPREAD EXPANSION: {self._get(statistics, 'spread_expansion')}")
        print(f"SPREAD COMPRESSION: {self._get(statistics, 'spread_compression')}")
        print(f"ABNORMAL SPREAD: {self._get(statistics, 'abnormal_spread')}")
        print(f"EXECUTION QUALITY: {self._get(statistics, 'execution_quality')}")

        print("\n--- VELOCITY STATISTICS ---")
        print(f"VELOCITY MEAN: {self._get(statistics, 'velocity_mean')}")
        print(f"VELOCITY STD: {self._get(statistics, 'velocity_std')}")
        print(f"VELOCITY STATE: {self._get(statistics, 'velocity_state')}")
        print(f"VELOCITY EXPANSION: {self._get(statistics, 'velocity_expansion')}")
        print(f"VELOCITY COMPRESSION: {self._get(statistics, 'velocity_compression')}")
        print(f"ABNORMAL VELOCITY: {self._get(statistics, 'abnormal_velocity')}")
        print(f"VELOCITY CHANGE: {self._get(statistics, 'velocity_change')}")
        print(f"VELOCITY ACCELERATION: {self._get(statistics, 'velocity_acceleration')}")
        print(f"VELOCITY ACCELERATION STATE: {self._get(statistics, 'velocity_acceleration_state')}")
        print(f"VELOCITY DECELERATION: {self._get(statistics, 'velocity_deceleration')}")
        print(f"VELOCITY SHOCK: {self._get(statistics, 'velocity_shock')}")
        print(f"VELOCITY EXHAUSTION: {self._get(statistics, 'velocity_exhaustion')}")
        print(f"VELOCITY EXHAUSTION STATE: {self._get(statistics, 'velocity_exhaustion_state')}")
        print(f"EXHAUSTION STRENGTH: {self._get(statistics, 'exhaustion_strength')}")

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

        print("\n--- VARIANCE ---")
        print(f"PRICE VARIANCE: {self._get(row, 'price_variance')}")
        print(f"VOLUME VARIANCE: {self._get(row, 'volume_variance')}")
        print(f"DELTA VARIANCE: {self._get(row, 'delta_variance')}")
        print(f"VELOCITY VARIANCE: {self._get(row, 'velocity_variance')}")

        print("\n--- DISTRIBUTION ZONES ---")
        print(f"PRICE ZONE: {self._get(row, 'price_zone')}")
        print(f"VOLUME ZONE: {self._get(row, 'volume_zone')}")
        print(f"DELTA ZONE: {self._get(row, 'delta_zone')}")
        print(f"VELOCITY ZONE: {self._get(row, 'velocity_zone')}")

        print("\n--- VOLATILITY REGIME ---")
        print(f"VOLATILITY RATIO: {self._get(statistics, 'volatility_ratio')}")
        print(f"VOLATILITY REGIME: {self._get(statistics, 'volatility_regime')}")
        print(f"VOLATILITY TRANSITION: {self._get(statistics, 'volatility_transition')}")
        print(f"VOLATILITY PERSISTENCE: {self._get(statistics, 'volatility_persistence')}")
        print(f"VOLATILITY ACCELERATION: {self._get(statistics, 'volatility_acceleration')}")

        print("\n--- DISTRIBUTION SHIFT ---")
        print(f"PRICE MEAN SHIFT: {self._get(statistics, 'price_mean_shift')}")
        print(f"PRICE STD SHIFT: {self._get(statistics, 'price_std_shift')}")
        print(f"DISTRIBUTION SHIFT: {self._get(statistics, 'distribution_shift')}")
        print(f"DISTRIBUTION SHIFT STATE: {self._get(statistics, 'distribution_shift_state')}")
        print(f"DISTRIBUTION SHIFT STRENGTH: {self._get(statistics, 'distribution_shift_strength')}")

        print("\n--- DELTA STATISTICS ---")
        print(f"CUMULATIVE DELTA: {self._get(statistics, 'cumulative_delta')}")
        print(f"DELTA DOMINATION: {self._get(statistics, 'delta_domination')}")
        print(f"AGGRESSIVE FLOW: {self._get(statistics, 'aggressive_flow')}")
        print(f"DELTA PRESSURE: {self._get(statistics, 'delta_pressure')}")
        print(f"DELTA PRESSURE STATE: {self._get(statistics, 'delta_pressure_state')}")
        print(f"DELTA ACCELERATION: {self._get(statistics, 'delta_acceleration')}")
        print(f"DELTA ACCELERATION STATE: {self._get(statistics, 'delta_acceleration_state')}")
        print(f"DELTA EXHAUSTION: {self._get(statistics, 'delta_exhaustion')}")
        print(f"IMBALANCE STATE: {self._get(statistics, 'imbalance_state')}")

        print("\n--- TAIL DETECTION ---")
        print(f"PRICE TAIL SIDE: {self._get(statistics, 'price_tail_side')}")
        print(f"PRICE TAIL STRENGTH: {self._get(statistics, 'price_tail_strength')}")
        print(f"PRICE TAIL RISK: {self._get(statistics, 'price_tail_risk')}")
        print(f"PRICE TAIL PERSISTENCE: {self._get(statistics, 'price_tail_persistence')}")
        print(f"PRICE TAIL EXHAUSTION: {self._get(statistics, 'price_tail_exhaustion')}")

        print("\n--- RENKO ---")
        print(f"RVI: {self._get(renko, 'rvi')}")
        print(f"RVI STATE: {self._get(renko, 'rvi_state')}")
        print(f"RENKO DIRECTION: {self._get(renko, 'renko_direction')}")
        print(f"RENKO EVENT: {self._get(renko, 'renko_event')}")
        print(f"RENKO BRICKS: {self._get(renko, 'renko_bricks')}")

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

        active_engines = list(engine_outputs.keys())
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
