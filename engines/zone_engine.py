# ==================================================
# PHASE 2A — ZONE ENGINE
# STEP 2A-1 + STEP 2A-2 + ZONE SCORING
# ==================================================

from engines.base_engine import BaseEngine

from core.state import (
    price_history,
)


class ZoneEngine(BaseEngine):

    ENGINE_NAME = "zone_engine"
    NAME = "zone_engine"
    PRIORITY = 30

    def __init__(self):
        super().__init__()

        self.default_psych_step = 100.0
        self.default_tolerance = 20.0

        self.min_tolerance = 5.0
        self.max_tolerance = 100.0

        self.previous_window = 100
        self.previous_level_tolerance = 15.0

    def process(self, context):

        row = context.row

        if row is None:
            self.output = {}
            return self.output

        close_price = self._get_value(row, "close")

        if close_price is None:
            self.output = {}
            return self.output

        psychological_data = self._detect_psychological_level(
            price=close_price,
            context=context
        )

        previous_levels_data = self._detect_previous_levels(
            row=row
        )

        zone_score = self._calculate_zone_score(
            psychological_data=psychological_data,
            previous_levels_data=previous_levels_data
        )

        zone_priority = self._classify_zone_priority(
            zone_score=zone_score
        )

        context.zone = {
            "engine": self.NAME,
            "score": round(zone_score, 2),
            "priority": zone_priority,
            "psychological": psychological_data,
            "previous_levels": previous_levels_data,
        }

        self.output = context.zone

        return self.output

    # ==================================================
    # ZONE SCORING
    # ==================================================

    def _calculate_zone_score(
        self,
        psychological_data,
        previous_levels_data
    ):

        score = 0.0

        if psychological_data.get("inside_zone"):
            score += 2.0

        psychological_strength = psychological_data.get(
            "strength",
            0.0
        )

        score += psychological_strength * 2.0

        if previous_levels_data.get("near_previous_high"):
            score += 1.5

        if previous_levels_data.get("near_previous_low"):
            score += 1.5

        return score

    def _classify_zone_priority(self, zone_score):

        if zone_score >= 5.0:
            return "HIGH_PRIORITY_ZONE"

        if zone_score >= 3.0:
            return "MEDIUM_PRIORITY_ZONE"

        if zone_score >= 1.0:
            return "LOW_PRIORITY_ZONE"

        return "NO_PRIORITY_ZONE"

    # ==================================================
    # PSYCHOLOGICAL LEVEL LOGIC
    # ==================================================

    def _detect_psychological_level(self, price, context):

        step = self._get_adaptive_psych_step(price)
        tolerance = self._get_adaptive_tolerance(context=context)

        nearest_level = round(price / step) * step
        distance = price - nearest_level
        abs_distance = abs(distance)

        inside_zone = abs_distance <= tolerance

        strength = self._calculate_zone_strength(
            abs_distance=abs_distance,
            tolerance=tolerance
        )

        classification = (
            "PSYCHOLOGICAL_ZONE"
            if inside_zone
            else "NO_PSYCHOLOGICAL_ZONE"
        )

        return {
            "price": price,
            "step": step,
            "tolerance": tolerance,
            "nearest_level": nearest_level,
            "distance": distance,
            "abs_distance": abs_distance,
            "inside_zone": inside_zone,
            "strength": strength,
            "classification": classification,
        }

    def _get_adaptive_psych_step(self, price):

        if price >= 50000:
            return 100.0

        if price >= 10000:
            return 50.0

        if price >= 1000:
            return 10.0

        if price >= 100:
            return 5.0

        return 1.0

    def _get_adaptive_tolerance(self, context):

        base_tolerance = self.default_tolerance

        velocity_zscore = self._safe_context_get(
            context,
            "velocity_zscore"
        )

        price_zscore = self._safe_context_get(
            context,
            "price_zscore"
        )

        adaptive_multiplier = 1.0

        if velocity_zscore is not None:
            if abs(velocity_zscore) > 2:
                adaptive_multiplier += 0.50
            elif abs(velocity_zscore) > 1:
                adaptive_multiplier += 0.25

        if price_zscore is not None:
            if abs(price_zscore) > 2:
                adaptive_multiplier += 0.25

        tolerance = base_tolerance * adaptive_multiplier
        tolerance = max(self.min_tolerance, tolerance)
        tolerance = min(self.max_tolerance, tolerance)

        return tolerance

    def _calculate_zone_strength(self, abs_distance, tolerance):

        if tolerance <= 0:
            return 0.0

        strength = 1.0 - (abs_distance / tolerance)
        strength = max(0.0, min(1.0, strength))

        return round(strength, 4)

    # ==================================================
    # PREVIOUS HIGH / LOW LOGIC
    # ==================================================

    def _detect_previous_levels(self, row):

        close_price = self._get_value(row, "close")

        recent_prices = list(price_history)[
            -self.previous_window:
        ]

        if len(recent_prices) < 5:

            return {
                "previous_high": None,
                "previous_low": None,
                "distance_to_previous_high": None,
                "distance_to_previous_low": None,
                "near_previous_high": False,
                "near_previous_low": False,
            }

        previous_high = max(recent_prices)
        previous_low = min(recent_prices)

        distance_high = close_price - previous_high
        distance_low = close_price - previous_low

        near_previous_high = (
            abs(distance_high) <= self.previous_level_tolerance
        )

        near_previous_low = (
            abs(distance_low) <= self.previous_level_tolerance
        )

        return {
            "previous_high": previous_high,
            "previous_low": previous_low,
            "distance_to_previous_high": distance_high,
            "distance_to_previous_low": distance_low,
            "near_previous_high": near_previous_high,
            "near_previous_low": near_previous_low,
        }

    # ==================================================
    # SAFE HELPERS
    # ==================================================

    def _get_value(self, source, key, default=None):

        if source is None:
            return default

        if isinstance(source, dict):
            return source.get(key, default)

        return getattr(source, key, default)

    def _safe_context_get(self, context, key, default=None):

        if context is None:
            return default

        if hasattr(context, key):
            return getattr(context, key)

        row = getattr(context, "row", None)

        if isinstance(row, dict):
            return row.get(key, default)

        if row is not None and hasattr(row, key):
            return getattr(row, key)

        return default