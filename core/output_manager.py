# ==================================================
# OUTPUT MANAGER
# ==================================================

class OutputManager:

    def print_row_summary(self, context):
        row = self._get(context, "row")
        market = self._get(context, "market", {})
        statistics = self._get(context, "statistics", {})
        renko = self._get(context, "renko", {})
        zone = self._get(context, "zone", {})
        history = self._get(context, "history", [])
        active_engines = self._get(context, "active_engines", [])

        print("\n" + "=" * 70)
        print("NEW ROW CREATED")
        print("=" * 70)

        # ==================================================
        # ROW DATA
        # ==================================================

        if row:
            print(f"CLOSE: {self._get(row, 'close')}")
            print(f"VOLUME: {self._get(row, 'volume')}")
            print(f"DELTA: {self._get(row, 'delta')}")
            print(f"VELOCITY: {self._get(row, 'velocity')}")

        # ==================================================
        # MARKET CONTEXT
        # ==================================================

        print("\n--- MARKET CONTEXT ---")
        print(f"SESSION: {self._get(market, 'session')}")
        print(f"SPREAD: {self._get(market, 'spread')}")
        print(f"IMBALANCE: {self._get(market, 'imbalance')}")
        print(f"TRADE/DEPTH DELAY: {self._get(market, 'trade_depth_delay_ms')} ms")

        # ==================================================
        # STATISTICS
        # ==================================================

        print("\n--- STATISTICS ---")
        print(f"PRICE ZONE: {self._get(statistics, 'price_zone')}")
        print(f"VOLUME ZONE: {self._get(statistics, 'volume_zone')}")
        print(f"DELTA ZONE: {self._get(statistics, 'delta_zone')}")
        print(f"VELOCITY ZONE: {self._get(statistics, 'velocity_zone')}")
        print(f"PRICE PERCENTILE: {self._get(statistics, 'price_percentile')}")
        print(f"PERCENTILE ZONE: {self._get(statistics, 'percentile_zone')}")

        # ==================================================
        # RENKO
        # ==================================================

        print("\n--- RENKO ---")
        print(f"RVI: {self._get(renko, 'rvi')}")
        print(f"RVI STATE: {self._get(renko, 'rvi_state')}")
        print(f"RENKO DIRECTION: {self._get(renko, 'direction')}")
        print(f"RENKO EVENT: {self._get(renko, 'event')}")
        print(f"RENKO BRICKS: {self._get(renko, 'bricks')}")

        # ==================================================
        # ZONE ENGINE
        # ==================================================

        print("\n--- ZONE ENGINE ---")

        psychological = self._get(zone, "psychological", {})
        previous_levels = self._get(zone, "previous_levels", {})
        volume_cluster = self._get(zone, "volume_cluster", {})
        liquidity_zone = self._get(zone, "liquidity_zone", {})
        rejection = self._get(zone, "rejection", {})

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

        print(f"VOLUME CLUSTER: {self._get(volume_cluster, 'active')}")
        print(f"LIQUIDITY ZONE: {self._get(liquidity_zone, 'active')}")
        print(f"REJECTION: {self._get(rejection, 'active')}")

        # ==================================================
        # SYSTEM STATE
        # ==================================================

        print("\n--- SYSTEM STATE ---")

        try:
            history_size = len(history)
        except Exception:
            history_size = None

        print(f"HISTORY SIZE: {history_size}")
        print(f"ACTIVE ENGINES: {active_engines}")

    # ==================================================
    # SAFE GETTER
    # ==================================================

    def _get(self, source, key, default=None):
        if source is None:
            return default

        if isinstance(source, dict):
            return source.get(key, default)

        return getattr(source, key, default)


# ==================================================
# BACKWARD COMPATIBILITY FUNCTION
# stream_manager.py imports this function
# ==================================================

def print_row_summary(context):
    manager = OutputManager()
    manager.print_row_summary(context)