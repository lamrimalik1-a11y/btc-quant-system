import math
import statistics
from collections import deque
from dataclasses import dataclass, field


MIN_HISTORY_SIZE = 10
DEFAULT_DISTRIBUTION_WINDOW = 200

FAST_WINDOW = 10
MEDIUM_WINDOW = 30
SLOW_WINDOW = 60

SHIFT_RECENT_WINDOW = 20
SHIFT_BASELINE_WINDOW = 100

DASHBOARD_V2_SEVERITY_RANKS = {
    None: 0,
    "": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "EXTREME": 4,
}

DASHBOARD_V2_LAYERS = [
    "distribution",
    "multi_zscore",
    "price_rarity",
    "volatility",
    "volume",
    "velocity",
    "delta",
    "spread_execution",
    "extreme_event",
]


@dataclass
class LayerResult:
    layer_name: str
    active: bool = False
    severity: str = None
    primary_condition: str = None
    supporting_conditions: list = field(default_factory=list)
    display_fields: list = field(default_factory=list)
    notes: str = ""

    def to_scalar_fields(self):
        return {
            "layer_name": self.layer_name,
            "active": self.active,
            "severity": self.severity,
            "primary_condition": self.primary_condition,
            "supporting_conditions": format_condition_list(
                self.supporting_conditions
            ),
            "display_fields": format_condition_list(
                self.display_fields
            ),
            "notes": self.notes or "",
        }


def severity_rank(severity):
    return DASHBOARD_V2_SEVERITY_RANKS.get(
        severity,
        0
    )


def max_severity(*severities):
    if (
        len(severities) == 1
        and isinstance(severities[0], (list, tuple, set))
    ):
        severities = tuple(severities[0])

    ranked_severities = [
        severity
        for severity in severities
        if severity_rank(severity) > 0
    ]

    if not ranked_severities:
        return None

    return max(
        ranked_severities,
        key=severity_rank
    )


def format_condition_list(values):
    if values is None:
        return ""

    if isinstance(values, str):
        return values

    if not isinstance(values, (list, tuple, set)):
        return str(values)

    return "|".join(
        str(value)
        for value in values
        if value is not None and str(value).strip() != ""
    )


def evaluate_distribution_layer(row):
    state = row.get("distribution_shift_state")
    strength = _safe_number(row.get("distribution_shift_strength"))
    mean_shift = _safe_number(row.get("price_mean_shift"))
    std_shift = _safe_number(row.get("price_std_shift"))
    supporting_conditions = []

    if strength is not None:
        supporting_conditions.append("DISTRIBUTION_SHIFT_STRENGTH")

    if mean_shift is not None:
        supporting_conditions.append("PRICE_MEAN_SHIFT")

    if std_shift is not None:
        supporting_conditions.append("PRICE_STD_SHIFT")

    active = (
        state == "MAJOR_DISTRIBUTION_SHIFT"
        or (strength is not None and strength >= 0.75)
        or (mean_shift is not None and mean_shift >= 2.5)
        or (
            std_shift is not None
            and (std_shift >= 2.0 or std_shift <= 0.50)
        )
    )
    severity = None
    primary_condition = None

    if active:
        primary_condition = state or "DISTRIBUTION_SHIFT"

        if state == "MAJOR_DISTRIBUTION_SHIFT":
            severity = "HIGH"

            if (
                (strength is not None and strength >= 0.85)
                or (mean_shift is not None and mean_shift >= 2.5)
                or (
                    std_shift is not None
                    and (std_shift >= 2.0 or std_shift <= 0.5)
                )
            ):
                severity = "EXTREME"

        elif (
            (strength is not None and strength >= 0.75)
            or (mean_shift is not None and mean_shift >= 2.5)
            or (
                std_shift is not None
                and (std_shift >= 2.0 or std_shift <= 0.50)
            )
        ):
            severity = "MEDIUM"
        else:
            severity = "LOW"

    return LayerResult(
        layer_name="distribution",
        active=active,
        severity=severity,
        primary_condition=primary_condition,
        supporting_conditions=supporting_conditions,
        display_fields=[
            "distribution_shift_strength",
            "price_mean_shift",
            "price_std_shift",
        ],
    )


def evaluate_multi_zscore_layer(row):
    zscore_fields = [
        "price_zscore",
        "volume_zscore",
        "velocity_zscore",
        "spread_zscore",
        "delta_zscore",
    ]

    active_zscores = []
    extreme_zscores = []

    for field_name in zscore_fields:
        value = _safe_number(row.get(field_name))

        if value is None:
            continue

        if abs(value) >= 2:
            active_zscores.append(field_name.upper())

        if abs(value) >= 3:
            extreme_zscores.append(field_name.upper())

    active = len(active_zscores) > 0
    severity = None
    primary_condition = None

    if active:
        delta_zscore = _safe_number(row.get("delta_zscore"))
        primary_condition = "MULTI_ZSCORE_CONTEXT"
        severity = "LOW"

        if delta_zscore is not None and abs(delta_zscore) >= 2:
            primary_condition = "DELTA_ZSCORE_EXTREME"
            severity = "MEDIUM"

        if len(active_zscores) >= 2:
            severity = max_severity(severity, "HIGH")

        if len(extreme_zscores) > 0 or len(active_zscores) >= 3:
            severity = "EXTREME"

    return LayerResult(
        layer_name="multi_zscore",
        active=active,
        severity=severity,
        primary_condition=primary_condition,
        supporting_conditions=active_zscores,
        display_fields=zscore_fields,
    )


def evaluate_price_rarity_layer(row):
    gaussian_zone = row.get("gaussian_zone")
    gaussian_extreme = row.get("gaussian_extreme") is True
    gaussian_confidence = row.get("gaussian_confidence")
    tail_risk = row.get("price_tail_risk")
    tail_persistence = row.get("price_tail_persistence")
    tail_exhaustion = row.get("price_tail_exhaustion")
    price_zscore = _safe_number(row.get("price_zscore"))
    strong_price_zscore = (
        price_zscore is not None
        and abs(price_zscore) >= 2
    )
    tail_risk_active = _is_active_label(tail_risk)

    supporting_conditions = []

    if _is_active_label(gaussian_confidence):
        supporting_conditions.append(f"GAUSSIAN_CONFIDENCE:{gaussian_confidence}")

    if tail_persistence is True or _is_active_label(tail_persistence):
        supporting_conditions.append("PRICE_TAIL_PERSISTENCE")

    active = (
        gaussian_extreme
        or (
            gaussian_zone == "GAUSSIAN_OUTER"
            and tail_risk_active
            and strong_price_zscore
        )
        or (
            tail_exhaustion is True
            and (
                tail_risk_active
                or strong_price_zscore
            )
        )
    )
    severity = None
    primary_condition = None

    if active:
        severity = "LOW"
        primary_condition = gaussian_zone or "PRICE_RARITY_CONTEXT"

        if gaussian_zone == "GAUSSIAN_OUTER" or tail_risk_active:
            severity = "MEDIUM"

        if gaussian_zone == "GAUSSIAN_EXTREME":
            severity = "HIGH"

        if (
            gaussian_zone == "GAUSSIAN_EXTREME"
            and (
                tail_risk_active
                or tail_exhaustion is True
            )
        ):
            severity = "EXTREME"

        if (
            tail_exhaustion is True
            and severity_rank(severity) < severity_rank("HIGH")
        ):
            severity = "HIGH"

    return LayerResult(
        layer_name="price_rarity",
        active=active,
        severity=severity,
        primary_condition=primary_condition,
        supporting_conditions=supporting_conditions,
        display_fields=[
            "gaussian_extreme",
            "gaussian_zone",
            "gaussian_confidence",
            "price_tail_risk",
            "price_tail_persistence",
            "price_tail_exhaustion",
        ],
    )


def evaluate_volatility_layer(row):
    transition = row.get("volatility_transition")
    regime = row.get("volatility_regime")
    acceleration = _safe_number(row.get("volatility_acceleration"))

    active = (
        _is_active_label(transition)
        or (
            acceleration is not None
            and abs(acceleration) >= 1.0
        )
    )
    severity = None
    primary_condition = None
    supporting_conditions = []

    if _is_active_label(regime):
        supporting_conditions.append(f"VOLATILITY_REGIME:{regime}")

    if acceleration is not None:
        supporting_conditions.append("VOLATILITY_ACCELERATION")

    if active:
        primary_condition = transition or "VOLATILITY_ACCELERATION"
        severity = "MEDIUM"

        if acceleration is not None and abs(acceleration) >= 0.5:
            severity = "HIGH"

        if acceleration is not None and abs(acceleration) >= 1.0:
            severity = "EXTREME"

    return LayerResult(
        layer_name="volatility",
        active=active,
        severity=severity,
        primary_condition=primary_condition,
        supporting_conditions=supporting_conditions,
        display_fields=[
            "volatility_regime",
            "volatility_transition",
            "volatility_acceleration",
        ],
    )


def evaluate_volume_layer(row):
    climactic_volume = row.get("climactic_volume") is True
    abnormal_volume = row.get("abnormal_volume") is True
    volume_state = row.get("volume_state")
    volume_expansion = row.get("volume_expansion") is True

    active = (
        climactic_volume
        or abnormal_volume
        or volume_state in ["HIGH_VOLUME", "EXTREME_VOLUME"]
        or volume_expansion
    )
    severity = None
    primary_condition = None
    supporting_conditions = []

    if volume_state is not None:
        supporting_conditions.append(f"VOLUME_STATE:{volume_state}")

    if volume_expansion:
        supporting_conditions.append("VOLUME_EXPANSION")

    if active:
        severity = "LOW"
        primary_condition = volume_state or "VOLUME_CONTEXT"

        if abnormal_volume:
            primary_condition = "ABNORMAL_VOLUME"
            severity = "MEDIUM"

        if climactic_volume:
            primary_condition = "CLIMACTIC_VOLUME"
            severity = "HIGH"

    return LayerResult(
        layer_name="volume",
        active=active,
        severity=severity,
        primary_condition=primary_condition,
        supporting_conditions=supporting_conditions,
        display_fields=[
            "volume_state",
            "volume_expansion",
            "abnormal_volume",
            "climactic_volume",
        ],
    )


def evaluate_velocity_layer(row):
    velocity_shock = row.get("velocity_shock") is True
    exhaustion_state = row.get("velocity_exhaustion_state")
    acceleration_state = row.get("velocity_acceleration_state")
    velocity_state = row.get("velocity_state")

    active = (
        velocity_shock
        or _is_active_label(exhaustion_state)
        or acceleration_state in [
            "VELOCITY_SHOCK",
            "ACCELERATING_VELOCITY",
            "DECELERATING_VELOCITY",
        ]
        or velocity_state in ["HIGH_VELOCITY", "EXTREME_VELOCITY"]
    )
    severity = None
    primary_condition = None
    supporting_conditions = []

    for label, value in [
        ("VELOCITY_STATE", velocity_state),
        ("VELOCITY_ACCELERATION_STATE", acceleration_state),
        ("VELOCITY_EXHAUSTION_STATE", exhaustion_state),
    ]:
        if _is_active_label(value):
            supporting_conditions.append(f"{label}:{value}")

    if active:
        severity = "LOW"
        primary_condition = velocity_state or "VELOCITY_CONTEXT"

        if velocity_shock:
            primary_condition = "VELOCITY_SHOCK"
            severity = "MEDIUM"

        if exhaustion_state == "VELOCITY_EXHAUSTION":
            primary_condition = exhaustion_state
            severity = max_severity(severity, "MEDIUM")

        if exhaustion_state == "STRONG_VELOCITY_EXHAUSTION":
            primary_condition = exhaustion_state
            severity = "HIGH"

        if exhaustion_state == "EXTREME_VELOCITY_EXHAUSTION":
            primary_condition = exhaustion_state
            severity = "EXTREME"

    return LayerResult(
        layer_name="velocity",
        active=active,
        severity=severity,
        primary_condition=primary_condition,
        supporting_conditions=supporting_conditions,
        display_fields=[
            "velocity_state",
            "velocity_acceleration_state",
            "velocity_deceleration",
            "velocity_exhaustion_state",
            "exhaustion_strength",
        ],
    )


def evaluate_delta_layer(row):
    pressure_state = row.get("delta_pressure_state")
    imbalance_state = row.get("imbalance_state")
    aggressive_flow = row.get("aggressive_flow")
    delta_zscore = _safe_number(row.get("delta_zscore"))
    delta_exhaustion = row.get("delta_exhaustion") is True
    acceleration_state = row.get("delta_acceleration_state")

    pressure_confirmed = (
        _is_active_label(pressure_state)
        and _is_active_label(aggressive_flow)
    )
    acceleration_confirmed = (
        _is_active_label(acceleration_state)
        and _is_active_label(aggressive_flow)
        and delta_zscore is not None
        and abs(delta_zscore) >= 2
    )
    exhaustion_confirmed = (
        delta_exhaustion
        and (
            _is_active_label(pressure_state)
            or _is_active_label(aggressive_flow)
        )
    )

    active = (
        pressure_confirmed
        or (delta_zscore is not None and abs(delta_zscore) >= 2.75)
        or exhaustion_confirmed
        or acceleration_confirmed
    )
    severity = None
    primary_condition = None
    supporting_conditions = []

    for label, value in [
        ("DELTA_PRESSURE_STATE", pressure_state),
        ("IMBALANCE_STATE", imbalance_state),
        ("AGGRESSIVE_FLOW", aggressive_flow),
        ("DELTA_ACCELERATION_STATE", acceleration_state),
    ]:
        if _is_active_label(value):
            supporting_conditions.append(f"{label}:{value}")

    if active:
        severity = "LOW"
        primary_condition = pressure_state or "DELTA_CONTEXT"

        if delta_zscore is not None and abs(delta_zscore) >= 2.75:
            primary_condition = "DELTA_ZSCORE_EXTREME"
            severity = "MEDIUM"

        if pressure_confirmed:
            primary_condition = pressure_state
            severity = max_severity(severity, "MEDIUM")

        if acceleration_confirmed:
            primary_condition = acceleration_state
            severity = max_severity(severity, "MEDIUM")

        if exhaustion_confirmed:
            primary_condition = "DELTA_EXHAUSTION"
            severity = "HIGH"

        if delta_zscore is not None and abs(delta_zscore) >= 3:
            severity = "EXTREME"

    return LayerResult(
        layer_name="delta",
        active=active,
        severity=severity,
        primary_condition=primary_condition,
        supporting_conditions=supporting_conditions,
        display_fields=[
            "delta_pressure_state",
            "delta_zscore",
            "delta_exhaustion",
            "imbalance_state",
            "aggressive_flow",
            "delta_acceleration_state",
        ],
    )


def evaluate_spread_execution_layer(row):
    abnormal_spread = row.get("abnormal_spread") is True
    execution_quality = row.get("execution_quality")
    spread_state = row.get("spread_state")

    active = (
        abnormal_spread
        or execution_quality in ["WIDE_EXECUTION", "BAD_EXECUTION"]
        or spread_state in ["WIDE_SPREAD", "EXTREME_SPREAD"]
    )
    severity = None
    primary_condition = None
    supporting_conditions = []

    if _is_active_label(spread_state):
        supporting_conditions.append(f"SPREAD_STATE:{spread_state}")

    if abnormal_spread:
        supporting_conditions.append("ABNORMAL_SPREAD")

    if active:
        severity = "LOW"
        primary_condition = spread_state or "SPREAD_EXECUTION_CONTEXT"

        if execution_quality == "WIDE_EXECUTION":
            primary_condition = execution_quality
            severity = "MEDIUM"

        if execution_quality == "BAD_EXECUTION" or abnormal_spread:
            primary_condition = execution_quality or "ABNORMAL_SPREAD"
            severity = "HIGH"

        if spread_state == "EXTREME_SPREAD" and (
            execution_quality == "BAD_EXECUTION"
            or abnormal_spread
        ):
            severity = "EXTREME"

    return LayerResult(
        layer_name="spread_execution",
        active=active,
        severity=severity,
        primary_condition=primary_condition,
        supporting_conditions=supporting_conditions,
        display_fields=[
            "abnormal_spread",
            "execution_quality",
            "spread_state",
            "spread_expansion",
            "spread_zscore",
        ],
    )


def evaluate_extreme_event_layer(row):
    state = row.get("extreme_event_state")
    extreme_fields = [
        "price_extreme_event",
        "volume_extreme_event",
        "delta_extreme_event",
        "velocity_extreme_event",
        "spread_extreme_event",
    ]
    active_extremes = [
        field_name.upper()
        for field_name in extreme_fields
        if row.get(field_name) is True
    ]

    active = (
        state is not None
        and state != "NO_EXTREME_EVENT"
    ) or len(active_extremes) > 0
    severity = None
    primary_condition = None

    if active:
        primary_condition = state or "EXTREME_EVENT_CONTEXT"
        severity = "LOW"

        if state == "MULTI_FACTOR_EXTREME":
            severity = "MEDIUM"

        if state == "CRITICAL_EXTREME_EVENT":
            severity = "HIGH"

        if state == "UNSTABLE_EXTREME_CONTEXT":
            severity = "EXTREME"

    return LayerResult(
        layer_name="extreme_event",
        active=active,
        severity=severity,
        primary_condition=primary_condition,
        supporting_conditions=active_extremes,
        display_fields=[
            "extreme_event_state",
            "extreme_event_context",
            "extreme_event_origin",
        ] + extreme_fields,
        notes="Escalation context only in Dashboard V2",
    )


def add_statistical_dashboard_v2_features(row):
    layer_results = [
        evaluate_distribution_layer(row),
        evaluate_multi_zscore_layer(row),
        evaluate_price_rarity_layer(row),
        evaluate_volatility_layer(row),
        evaluate_volume_layer(row),
        evaluate_velocity_layer(row),
        evaluate_delta_layer(row),
        evaluate_spread_execution_layer(row),
        evaluate_extreme_event_layer(row),
    ]

    counted_layers = [
        result
        for result in layer_results
        if _is_counted_dashboard_layer(result)
    ]
    extreme_layer = _find_layer_result(
        layer_results,
        "extreme_event"
    )

    layer_count = len(counted_layers)
    active_layers = [
        result.layer_name
        for result in counted_layers
    ]
    layer_severities = [
        result.severity
        for result in counted_layers
    ]
    strongest_severity = max_severity(layer_severities)

    if (
        extreme_layer is not None
        and extreme_layer.active
        and layer_count > 0
    ):
        strongest_severity = max_severity(
            strongest_severity,
            extreme_layer.severity
        )

    active = (
        layer_count >= 2
        or strongest_severity == "EXTREME"
    )

    primary_context = _select_primary_dashboard_context(
        counted_layers,
        extreme_layer
    )
    conditions = _collect_dashboard_conditions(
        counted_layers,
        extreme_layer
    )
    display_context = _collect_dashboard_display_context(
        layer_results
    )
    observation_confidence = _dashboard_v2_observation_confidence(
        row,
        layer_results
    )
    active = _apply_dashboard_v2_combination_filter(
        active,
        counted_layers,
        extreme_layer,
        observation_confidence,
    )
    state = _dashboard_v2_state(
        active=active,
        layer_count=layer_count,
        max_layer_severity=strongest_severity,
        observation_confidence=observation_confidence,
    )

    row["dashboard_v2_active"] = active
    row["dashboard_v2_state"] = state
    row["dashboard_v2_layer_count"] = layer_count
    row["dashboard_v2_active_layers"] = format_condition_list(
        active_layers
    )
    row["dashboard_v2_max_severity"] = strongest_severity
    row["dashboard_v2_primary_context"] = primary_context
    row["dashboard_v2_conditions"] = format_condition_list(
        conditions
    )
    row["dashboard_v2_display_context"] = format_condition_list(
        display_context
    )
    row["observation_confidence"] = observation_confidence

    _add_dashboard_v2_layer_fields(
        row,
        layer_results
    )

    return row


def _find_layer_result(layer_results, layer_name):
    for result in layer_results:
        if result.layer_name == layer_name:
            return result

    return None


def _add_dashboard_v2_layer_fields(row, layer_results):
    for result in layer_results:
        prefix = f"dashboard_v2_{result.layer_name}"

        row[f"{prefix}_active"] = result.active
        row[f"{prefix}_severity"] = result.severity
        row[f"{prefix}_primary_condition"] = result.primary_condition
        row[f"{prefix}_supporting_conditions"] = format_condition_list(
            result.supporting_conditions
        )


def _is_counted_dashboard_layer(result):
    if not result.active:
        return False

    if result.layer_name in [
        "extreme_event",
        "spread_execution",
    ]:
        return False

    if (
        result.layer_name == "multi_zscore"
        and len(result.supporting_conditions) < 2
    ):
        return False

    return True


def _count_active_dashboard_layers(layer_results):
    return len([
        result
        for result in layer_results
        if _is_counted_dashboard_layer(result)
    ])


def _apply_dashboard_v2_combination_filter(
    active,
    counted_layers,
    extreme_layer,
    observation_confidence,
):
    if not active:
        return False

    if len(counted_layers) != 2:
        return active

    active_layer_names = {
        result.layer_name
        for result in counted_layers
    }
    weak_context_layers = {
        "distribution",
        "volatility",
        "price_rarity",
    }

    if not active_layer_names.issubset(weak_context_layers):
        return active

    if observation_confidence == "UNSTABLE_STATISTICAL_CONTEXT":
        return active

    if (
        extreme_layer is not None
        and extreme_layer.active
        and severity_rank(extreme_layer.severity) >= severity_rank("HIGH")
    ):
        return active

    if any(
        severity_rank(result.severity) >= severity_rank("HIGH")
        for result in counted_layers
    ):
        return active

    return False


def _select_primary_dashboard_context(counted_layers, extreme_layer):
    if not counted_layers:
        return None

    strongest_layer = max(
        counted_layers,
        key=lambda result: severity_rank(result.severity)
    )

    if (
        extreme_layer is not None
        and extreme_layer.active
        and severity_rank(extreme_layer.severity)
        > severity_rank(strongest_layer.severity)
    ):
        return extreme_layer.primary_condition

    return strongest_layer.primary_condition


def _collect_dashboard_conditions(counted_layers, extreme_layer):
    conditions = []

    for result in counted_layers:
        if result.primary_condition:
            conditions.append(result.primary_condition)

        conditions.extend(result.supporting_conditions)

    if (
        extreme_layer is not None
        and extreme_layer.active
        and counted_layers
    ):
        if extreme_layer.primary_condition:
            conditions.append(extreme_layer.primary_condition)

        conditions.extend(extreme_layer.supporting_conditions)

    return _unique_condition_list(conditions)


def _collect_dashboard_display_context(layer_results):
    display_context = []

    for result in layer_results:
        if not result.active:
            continue

        display_context.append(
            ":".join(
                [
                    result.layer_name,
                    result.severity or "NONE",
                    result.primary_condition or "NONE",
                ]
            )
        )

    return display_context


def _unique_condition_list(values):
    unique_values = []
    seen = set()

    for value in values:
        if value is None:
            continue

        text = str(value).strip()

        if text == "" or text in seen:
            continue

        seen.add(text)
        unique_values.append(text)

    return unique_values


def _dashboard_v2_observation_confidence(row, layer_results):
    gaussian_confidence = row.get("gaussian_confidence")
    distribution_layer = _find_layer_result(
        layer_results,
        "distribution"
    )
    price_rarity_layer = _find_layer_result(
        layer_results,
        "price_rarity"
    )
    extreme_layer = _find_layer_result(
        layer_results,
        "extreme_event"
    )
    spread_layer = _find_layer_result(
        layer_results,
        "spread_execution"
    )

    if (
        (
            distribution_layer is not None
            and distribution_layer.active
            and price_rarity_layer is not None
            and price_rarity_layer.active
            and gaussian_confidence == "UNSTABLE_GAUSSIAN"
        )
        or (
            extreme_layer is not None
            and extreme_layer.primary_condition
            == "UNSTABLE_EXTREME_CONTEXT"
            and _count_active_dashboard_layers(layer_results) > 0
        )
    ):
        return "UNSTABLE_STATISTICAL_CONTEXT"

    if (
        spread_layer is not None
        and spread_layer.active
        and severity_rank(spread_layer.severity) >= severity_rank("HIGH")
    ):
        return "LOW_CONFIDENCE"

    if (
        spread_layer is not None
        and spread_layer.active
    ):
        return "MEDIUM_CONFIDENCE"

    return "HIGH_CONFIDENCE"


def _dashboard_v2_state(
    active,
    layer_count,
    max_layer_severity,
    observation_confidence,
):
    if not active:
        return "NO_CONFLUENCE"

    if observation_confidence == "UNSTABLE_STATISTICAL_CONTEXT":
        return "UNSTABLE_STATISTICAL_CONTEXT"

    if (
        max_layer_severity == "EXTREME"
        and layer_count >= 2
    ):
        return "EXTREME_LAYER_CONFLUENCE"

    if layer_count >= 4:
        return "EXTREME_LAYER_CONFLUENCE"

    if layer_count >= 3:
        return "STRONG_LAYER_CONFLUENCE"

    if layer_count == 2:
        return "MODERATE_LAYER_CONFLUENCE"

    return "WEAK_LAYER_CONFLUENCE"


def _safe_number(value):
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if math.isnan(number):
        return None

    return number


def _is_active_label(value):
    if value is None:
        return False

    if isinstance(value, bool):
        return value

    text = str(value).strip()

    return text not in [
        "",
        "None",
        "False",
        "false",
        "NO_PREVIOUS_REGIME",
        "NO_REGIME_CHANGE",
        "NO_EXTREME_EVENT",
        "NO_TAIL_RISK",
        "NORMAL",
        "NORMAL_TAIL",
        "NORMAL_VOLUME",
        "NORMAL_VELOCITY",
        "NORMAL_SPREAD",
        "NORMAL_VOLATILITY",
        "NORMAL_FLOW",
        "NEUTRAL_PRESSURE",
        "BALANCED_ORDERBOOK",
        "STABLE_VELOCITY",
        "STABLE_DELTA_SPEED",
    ]


price_distribution = deque(maxlen=DEFAULT_DISTRIBUTION_WINDOW)
volume_distribution = deque(maxlen=DEFAULT_DISTRIBUTION_WINDOW)
delta_distribution = deque(maxlen=DEFAULT_DISTRIBUTION_WINDOW)
velocity_distribution = deque(maxlen=DEFAULT_DISTRIBUTION_WINDOW)
spread_distribution = deque(maxlen=DEFAULT_DISTRIBUTION_WINDOW)

tail_history = deque(maxlen=10)

volatility_regime_history = deque(maxlen=20)
volatility_ratio_history = deque(maxlen=20)

cumulative_delta_history = deque(maxlen=200)
delta_pressure_history = deque(maxlen=50)
delta_acceleration_history = deque(maxlen=50)


# ==================================================
# BASIC STATISTICS
# ==================================================

def calculate_mean(values):
    values = list(values)

    if len(values) == 0:
        return 0

    return sum(values) / len(values)


def calculate_variance(values):
    values = list(values)

    if len(values) < 2:
        return 0

    mean = calculate_mean(values)

    return sum(
        (value - mean) ** 2
        for value in values
    ) / len(values)


def calculate_std(values):
    return math.sqrt(
        calculate_variance(values)
    )


# ==================================================
# ADVANCED STANDARD DEVIATION
# ==================================================

def calculate_weighted_mean(values):
    values = list(values)

    if len(values) == 0:
        return 0

    weights = list(range(1, len(values) + 1))

    weighted_sum = sum(
        value * weight
        for value, weight in zip(values, weights)
    )

    return weighted_sum / sum(weights)


def calculate_weighted_std(values):
    values = list(values)

    if len(values) < 2:
        return 0

    weighted_mean = calculate_weighted_mean(values)

    weights = list(range(1, len(values) + 1))

    weighted_variance = sum(
        weight * ((value - weighted_mean) ** 2)
        for value, weight in zip(values, weights)
    ) / sum(weights)

    return math.sqrt(weighted_variance)


def calculate_robust_std(values):
    values = list(values)

    if len(values) < 2:
        return 0

    median = statistics.median(values)

    absolute_deviations = [
        abs(value - median)
        for value in values
    ]

    mad = statistics.median(absolute_deviations)

    return mad * 1.4826


def calculate_ewma_std(values, alpha=0.20):
    values = list(values)

    if len(values) < 2:
        return 0

    ewma_mean = values[0]
    ewma_variance = 0

    for value in values[1:]:
        previous_mean = ewma_mean

        ewma_mean = (
            alpha * value
            +
            (1 - alpha) * ewma_mean
        )

        ewma_variance = (
            alpha * ((value - previous_mean) ** 2)
            +
            (1 - alpha) * ewma_variance
        )

    return math.sqrt(ewma_variance)


def calculate_volatility_weighted_std(values):
    values = list(values)

    if len(values) < 2:
        return 0

    changes = []

    for i in range(1, len(values)):
        changes.append(
            abs(values[i] - values[i - 1])
        )

    if len(changes) == 0:
        return 0

    weights = [
        max(change, 0.0001)
        for change in changes
    ]

    aligned_values = values[1:]

    weighted_mean = (
        sum(
            value * weight
            for value, weight in zip(aligned_values, weights)
        )
        /
        sum(weights)
    )

    weighted_variance = (
        sum(
            weight * ((value - weighted_mean) ** 2)
            for value, weight in zip(aligned_values, weights)
        )
        /
        sum(weights)
    )

    return math.sqrt(weighted_variance)


def detect_std_instability(
    basic_std,
    weighted_std,
    robust_std,
    ewma_std,
    volatility_weighted_std
):
    stds = [
        basic_std,
        weighted_std,
        robust_std,
        ewma_std,
        volatility_weighted_std,
    ]

    valid_stds = [
        value
        for value in stds
        if value > 0
    ]

    if len(valid_stds) < 2:
        return "UNKNOWN_INSTABILITY"

    max_std = max(valid_stds)
    min_std = min(valid_stds)

    if min_std == 0:
        return "EXTREME_INSTABILITY"

    ratio = max_std / min_std

    if ratio >= 3:
        return "EXTREME_INSTABILITY"

    elif ratio >= 2:
        return "HIGH_INSTABILITY"

    elif ratio >= 1.5:
        return "MODERATE_INSTABILITY"

    return "STABLE_STD"


def calculate_adaptive_std(values):
    values = list(values)

    if len(values) < 2:
        return 0

    basic_std = calculate_std(values)
    weighted_std = calculate_weighted_std(values)
    robust_std = calculate_robust_std(values)
    ewma_std = calculate_ewma_std(values)
    volatility_weighted_std = calculate_volatility_weighted_std(values)

    if robust_std == 0:
        robust_std = basic_std

    return (
        basic_std * 0.20
        +
        weighted_std * 0.20
        +
        robust_std * 0.20
        +
        ewma_std * 0.20
        +
        volatility_weighted_std * 0.20
    )


# ==================================================
# ZSCORE
# ==================================================

def calculate_zscore(value, history):
    history = list(history)

    if len(history) < MIN_HISTORY_SIZE:
        return 0

    mean = calculate_mean(history)
    std = calculate_adaptive_std(history)

    if std == 0:
        return 0

    return (value - mean) / std


def calculate_multizscore(value, history):
    history = list(history)

    scores = {
        "fast_zscore": 0,
        "medium_zscore": 0,
        "slow_zscore": 0,
    }

    if len(history) >= FAST_WINDOW:
        scores["fast_zscore"] = calculate_zscore(
            value,
            history[-FAST_WINDOW:]
        )

    if len(history) >= MEDIUM_WINDOW:
        scores["medium_zscore"] = calculate_zscore(
            value,
            history[-MEDIUM_WINDOW:]
        )

    if len(history) >= SLOW_WINDOW:
        scores["slow_zscore"] = calculate_zscore(
            value,
            history[-SLOW_WINDOW:]
        )

    return scores


# ==================================================
# ZONES / PERCENTILES
# ==================================================

def calculate_percentile(value, distribution):
    distribution = list(distribution)

    if len(distribution) == 0:
        return 0

    count = sum(
        sample <= value
        for sample in distribution
    )

    return (count / len(distribution)) * 100


def classify_statistical_zone(zscore):
    if zscore >= 2.5:
        return "EXTREME_HIGH_ZONE"

    elif zscore >= 2:
        return "HIGH_STATISTICAL_ZONE"

    elif zscore <= -2.5:
        return "EXTREME_LOW_ZONE"

    elif zscore <= -2:
        return "LOW_STATISTICAL_ZONE"

    elif -1 <= zscore <= 1:
        return "NORMAL_ZONE"

    else:
        return "TRANSITION_ZONE"


def classify_percentile_zone(percentile):
    if percentile is None:
        return None

    if percentile >= 97:
        return "EXTREME_TOP_TAIL"

    elif percentile >= 90:
        return "HIGH_TAIL"

    elif percentile <= 3:
        return "EXTREME_BOTTOM_TAIL"

    elif percentile <= 10:
        return "LOW_TAIL"

    return "NORMAL_DISTRIBUTION"


# ==================================================
# TAIL DETECTION
# ==================================================

def detect_tail_side(percentile):
    if percentile is None:
        return "UNKNOWN_TAIL"

    if percentile >= 97:
        return "EXTREME_RIGHT_TAIL"

    elif percentile >= 90:
        return "RIGHT_TAIL"

    elif percentile <= 3:
        return "EXTREME_LEFT_TAIL"

    elif percentile <= 10:
        return "LEFT_TAIL"

    return "DISTRIBUTION_BODY"


def detect_tail_strength(zscore, percentile):
    abs_zscore = abs(zscore)

    if percentile is None:
        return "UNKNOWN_TAIL_STRENGTH"

    if abs_zscore >= 3 or percentile >= 99 or percentile <= 1:
        return "EXTREME_TAIL_EVENT"

    elif abs_zscore >= 2.5 or percentile >= 97 or percentile <= 3:
        return "STRONG_TAIL_EVENT"

    elif abs_zscore >= 2 or percentile >= 90 or percentile <= 10:
        return "MODERATE_TAIL_EVENT"

    return "NO_TAIL_EVENT"


def detect_tail_risk(zscore, percentile, volatility_regime):
    tail_strength = detect_tail_strength(
        zscore,
        percentile
    )

    if tail_strength == "EXTREME_TAIL_EVENT":
        if volatility_regime in [
            "HIGH_VOLATILITY",
            "EXTREME_VOLATILITY",
        ]:
            return "CRITICAL_TAIL_RISK"

        return "HIGH_TAIL_RISK"

    if tail_strength == "STRONG_TAIL_EVENT":
        if volatility_regime in [
            "HIGH_VOLATILITY",
            "EXTREME_VOLATILITY",
        ]:
            return "HIGH_TAIL_RISK"

        return "MODERATE_TAIL_RISK"

    if tail_strength == "MODERATE_TAIL_EVENT":
        return "LOW_TAIL_RISK"

    return "NO_TAIL_RISK"


def detect_tail_persistence(current_tail_side, tail_history_values):
    if len(tail_history_values) < 5:
        return "INSUFFICIENT_TAIL_HISTORY"

    same_side_count = sum(
        side == current_tail_side
        for side in tail_history_values
    )

    ratio = same_side_count / len(tail_history_values)

    if ratio >= 0.80:
        return "PERSISTENT_TAIL"

    elif ratio >= 0.50:
        return "MODERATE_TAIL_PERSISTENCE"

    return "NON_PERSISTENT_TAIL"


def detect_tail_exhaustion(zscore, percentile, volatility_ratio):
    abs_zscore = abs(zscore)

    if (
        abs_zscore >= 3
        and
        (
            percentile >= 99
            or percentile <= 1
        )
        and
        volatility_ratio < 1
    ):
        return "TAIL_EXHAUSTION"

    elif (
        abs_zscore >= 2.5
        and volatility_ratio < 0.8
    ):
        return "POSSIBLE_EXHAUSTION"

    return "NO_EXHAUSTION"


# ==================================================
# VOLATILITY REGIME
# ==================================================

def classify_volatility_regime(volatility_ratio):
    if volatility_ratio >= 3.0:
        return "EXTREME_VOLATILITY"

    elif volatility_ratio >= 2.0:
        return "HIGH_VOLATILITY"

    elif volatility_ratio <= 0.50:
        return "COMPRESSION_REGIME"

    elif volatility_ratio <= 0.80:
        return "LOW_VOLATILITY"

    return "NORMAL_VOLATILITY"


def calculate_volatility_ratio():
    if len(price_distribution) < 30:
        return 1.0

    fast_window = list(price_distribution)[-20:]
    slow_window = list(price_distribution)[-100:]

    fast_std = calculate_adaptive_std(fast_window)
    slow_std = calculate_adaptive_std(slow_window)

    if slow_std == 0:
        return 1.0

    return fast_std / slow_std


def detect_volatility_transition(current_regime, previous_regime):
    if previous_regime is None:
        return "NO_PREVIOUS_REGIME"

    if current_regime == previous_regime:
        return "NO_REGIME_CHANGE"

    return f"{previous_regime}_TO_{current_regime}"


def detect_volatility_persistence(current_regime, regime_history_values):
    if len(regime_history_values) < 5:
        return "INSUFFICIENT_REGIME_HISTORY"

    same_count = sum(
        regime == current_regime
        for regime in regime_history_values
    )

    ratio = same_count / len(regime_history_values)

    if ratio >= 0.80:
        return "PERSISTENT_REGIME"

    elif ratio >= 0.50:
        return "MODERATE_REGIME_PERSISTENCE"

    return "UNSTABLE_REGIME"


def detect_volatility_acceleration(ratio_history_values):
    if len(ratio_history_values) < 6:
        return "INSUFFICIENT_RATIO_HISTORY"

    recent = list(ratio_history_values)[-3:]
    previous = list(ratio_history_values)[-6:-3]

    recent_mean = calculate_mean(recent)
    previous_mean = calculate_mean(previous)

    change = recent_mean - previous_mean

    if change >= 0.75:
        return "FAST_VOLATILITY_ACCELERATION"

    elif change >= 0.30:
        return "VOLATILITY_ACCELERATION"

    elif change <= -0.75:
        return "FAST_VOLATILITY_DECELERATION"

    elif change <= -0.30:
        return "VOLATILITY_DECELERATION"

    return "STABLE_VOLATILITY_SPEED"


# ==================================================
# DELTA STATISTICS
# ==================================================

def calculate_cumulative_delta():
    if len(cumulative_delta_history) == 0:
        return 0

    return sum(cumulative_delta_history)


def calculate_delta_pressure(delta, volume):
    if volume == 0:
        return 0

    return delta / volume


def detect_delta_domination(delta_pressure):
    if delta_pressure >= 0.80:
        return "EXTREME_BUYER_DOMINATION"

    elif delta_pressure >= 0.50:
        return "BUYER_DOMINATION"

    elif delta_pressure <= -0.80:
        return "EXTREME_SELLER_DOMINATION"

    elif delta_pressure <= -0.50:
        return "SELLER_DOMINATION"

    return "BALANCED_MARKET"


def detect_aggressive_flow(delta_zscore, velocity_zscore):
    if (
        delta_zscore >= 2
        and velocity_zscore >= 1.5
    ):
        return "AGGRESSIVE_BUYERS"

    elif (
        delta_zscore <= -2
        and velocity_zscore >= 1.5
    ):
        return "AGGRESSIVE_SELLERS"

    return "NORMAL_FLOW"


def detect_delta_pressure_state(pressure):
    if pressure >= 0.70:
        return "EXTREME_BUY_PRESSURE"

    elif pressure >= 0.40:
        return "BUY_PRESSURE"

    elif pressure <= -0.70:
        return "EXTREME_SELL_PRESSURE"

    elif pressure <= -0.40:
        return "SELL_PRESSURE"

    return "NEUTRAL_PRESSURE"


def calculate_delta_acceleration():
    if len(delta_pressure_history) < 6:
        return 0

    recent = list(delta_pressure_history)[-3:]
    previous = list(delta_pressure_history)[-6:-3]

    recent_mean = calculate_mean(recent)
    previous_mean = calculate_mean(previous)

    return recent_mean - previous_mean


def detect_delta_acceleration_state(acceleration):
    if acceleration >= 0.50:
        return "FAST_BUY_ACCELERATION"

    elif acceleration >= 0.20:
        return "BUY_ACCELERATION"

    elif acceleration <= -0.50:
        return "FAST_SELL_ACCELERATION"

    elif acceleration <= -0.20:
        return "SELL_ACCELERATION"

    return "STABLE_DELTA_SPEED"


def detect_delta_exhaustion(delta_zscore, velocity_zscore, pressure):
    if (
        abs(delta_zscore) >= 3
        and velocity_zscore < 1
        and abs(pressure) < 0.30
    ):
        return "DELTA_EXHAUSTION"

    elif (
        abs(delta_zscore) >= 2
        and abs(pressure) < 0.20
    ):
        return "POSSIBLE_DELTA_EXHAUSTION"

    return "NO_DELTA_EXHAUSTION"


def detect_imbalance_state(imbalance):
    if imbalance is None:
        imbalance = 0

    if imbalance >= 0.60:
        return "STRONG_BID_IMBALANCE"

    elif imbalance >= 0.30:
        return "BID_IMBALANCE"

    elif imbalance <= -0.60:
        return "STRONG_ASK_IMBALANCE"

    elif imbalance <= -0.30:
        return "ASK_IMBALANCE"

    return "BALANCED_ORDERBOOK"


# ==================================================
# DISTRIBUTION UPDATE
# ==================================================

def get_adaptive_distribution_window(row):
    velocity = row.get("velocity", 0)

    if velocity > 250:
        return 50

    elif velocity > 150:
        return 100

    elif velocity > 75:
        return 150

    return 200


def update_distributions(row):
    adaptive_window = get_adaptive_distribution_window(row)

    while len(price_distribution) > adaptive_window:
        price_distribution.popleft()

    while len(volume_distribution) > adaptive_window:
        volume_distribution.popleft()

    while len(delta_distribution) > adaptive_window:
        delta_distribution.popleft()

    while len(velocity_distribution) > adaptive_window:
        velocity_distribution.popleft()

    price_distribution.append(row["close"])
    volume_distribution.append(row["volume"])
    delta_distribution.append(row["delta"])
    velocity_distribution.append(row["velocity"])

    if row.get("spread") is not None:
        spread_distribution.append(row["spread"])

    row["adaptive_distribution_window"] = adaptive_window


def add_zscores(row):
    row["price_zscore"] = calculate_zscore(
        row["close"],
        price_distribution
    )

    row["volume_zscore"] = calculate_zscore(
        row["volume"],
        volume_distribution
    )

    row["delta_zscore"] = calculate_zscore(
        row["delta"],
        delta_distribution
    )

    row["velocity_zscore"] = calculate_zscore(
        row["velocity"],
        velocity_distribution
    )

    price_multi = calculate_multizscore(
        row["close"],
        price_distribution
    )

    row["fast_price_zscore"] = price_multi["fast_zscore"]
    row["medium_price_zscore"] = price_multi["medium_zscore"]
    row["slow_price_zscore"] = price_multi["slow_zscore"]

    return row


def add_statistical_zones(row):
    row["price_zone"] = classify_statistical_zone(
        row["price_zscore"]
    )

    row["volume_zone"] = classify_statistical_zone(
        row["volume_zscore"]
    )

    row["delta_zone"] = classify_statistical_zone(
        row["delta_zscore"]
    )

    row["velocity_zone"] = classify_statistical_zone(
        row["velocity_zscore"]
    )

    return row


def add_volume_statistical_foundation(row):
    if (
        not row.get("distribution_ready")
        or len(volume_distribution) < 30
    ):
        row["volume_mean"] = None
        row["volume_std"] = None
        row["volume_state"] = None
        row["volume_expansion"] = False
        row["volume_compression"] = False
        row["abnormal_volume"] = False
        row["climactic_volume"] = False

        return row

    volume_zscore = row.get("volume_zscore")

    if volume_zscore is None:
        row["volume_mean"] = None
        row["volume_std"] = None
        row["volume_state"] = None
        row["volume_expansion"] = False
        row["volume_compression"] = False
        row["abnormal_volume"] = False
        row["climactic_volume"] = False

        return row

    volume_mean = calculate_mean(volume_distribution)
    volume_std = calculate_std(volume_distribution)

    row["volume_mean"] = volume_mean
    row["volume_std"] = volume_std

    if volume_mean <= 0 or volume_std <= 0:
        row["volume_state"] = None
        row["volume_expansion"] = False
        row["volume_compression"] = False
        row["abnormal_volume"] = False
        row["climactic_volume"] = False

        return row

    if volume_zscore >= 2.5:
        row["volume_state"] = "EXTREME_VOLUME"
    elif volume_zscore >= 1.5:
        row["volume_state"] = "HIGH_VOLUME"
    elif volume_zscore <= -1:
        row["volume_state"] = "COMPRESSED_VOLUME"
    else:
        row["volume_state"] = "NORMAL_VOLUME"

    row["volume_expansion"] = volume_zscore >= 1.5
    row["volume_compression"] = volume_zscore <= -1
    row["abnormal_volume"] = abs(volume_zscore) >= 2
    row["climactic_volume"] = volume_zscore >= 2.5

    return row


def add_spread_statistical_foundation(row):
    spread = row.get("spread")

    if (
        spread is None
        or len(spread_distribution) < 30
    ):
        row["spread_mean"] = None
        row["spread_std"] = None
        row["spread_zscore"] = None
        row["spread_state"] = None
        row["spread_expansion"] = False
        row["spread_compression"] = False
        row["abnormal_spread"] = False
        row["execution_quality"] = None

        return row

    spread_mean = calculate_mean(spread_distribution)
    spread_std = calculate_std(spread_distribution)

    row["spread_mean"] = spread_mean
    row["spread_std"] = spread_std

    if spread_std <= 0:
        row["spread_zscore"] = None
        row["spread_state"] = None
        row["spread_expansion"] = False
        row["spread_compression"] = False
        row["abnormal_spread"] = False
        row["execution_quality"] = None

        return row

    spread_zscore = (spread - spread_mean) / spread_std

    row["spread_zscore"] = spread_zscore

    if spread_zscore >= 2.5:
        row["spread_state"] = "EXTREME_SPREAD"
    elif spread_zscore >= 1.5:
        row["spread_state"] = "WIDE_SPREAD"
    elif spread_zscore <= -1:
        row["spread_state"] = "TIGHT_SPREAD"
    else:
        row["spread_state"] = "NORMAL_SPREAD"

    row["spread_expansion"] = spread_zscore >= 1.5
    row["spread_compression"] = spread_zscore <= -1
    row["abnormal_spread"] = spread_zscore >= 2

    if spread_zscore >= 2:
        row["execution_quality"] = "BAD_EXECUTION"
    elif spread_zscore >= 1:
        row["execution_quality"] = "WIDE_EXECUTION"
    else:
        row["execution_quality"] = "GOOD_EXECUTION"

    return row


def add_velocity_statistical_foundation(row):
    if (
        not row.get("distribution_ready")
        or len(velocity_distribution) < MIN_HISTORY_SIZE
    ):
        row["velocity_mean"] = None
        row["velocity_std"] = None
        row["velocity_state"] = None
        row["velocity_expansion"] = False
        row["velocity_compression"] = False
        row["abnormal_velocity"] = False

        return row

    velocity_zscore = row.get("velocity_zscore")

    if velocity_zscore is None:
        row["velocity_mean"] = None
        row["velocity_std"] = None
        row["velocity_state"] = None
        row["velocity_expansion"] = False
        row["velocity_compression"] = False
        row["abnormal_velocity"] = False

        return row

    row["velocity_mean"] = calculate_mean(velocity_distribution)
    row["velocity_std"] = calculate_std(velocity_distribution)

    if velocity_zscore >= 2:
        row["velocity_state"] = "EXTREME_VELOCITY"
    elif velocity_zscore >= 1:
        row["velocity_state"] = "HIGH_VELOCITY"
    elif velocity_zscore <= -1:
        row["velocity_state"] = "COMPRESSED_VELOCITY"
    else:
        row["velocity_state"] = "NORMAL_VELOCITY"

    row["velocity_expansion"] = velocity_zscore >= 1.5
    row["velocity_compression"] = velocity_zscore <= -1
    row["abnormal_velocity"] = abs(velocity_zscore) >= 2

    return row


def add_velocity_acceleration_features(row):
    if (
        not row.get("distribution_ready")
        or len(velocity_distribution) < 3
    ):
        row["velocity_change"] = None
        row["velocity_acceleration"] = None
        row["velocity_acceleration_state"] = None
        row["velocity_deceleration"] = False
        row["velocity_shock"] = False

        return row

    velocity_values = list(velocity_distribution)

    current_velocity = velocity_values[-1]
    previous_velocity = velocity_values[-2]
    previous_previous_velocity = velocity_values[-3]

    velocity_change = current_velocity - previous_velocity
    previous_velocity_change = previous_velocity - previous_previous_velocity
    velocity_acceleration = velocity_change - previous_velocity_change

    row["velocity_change"] = velocity_change
    row["velocity_acceleration"] = velocity_acceleration

    baseline = row.get("velocity_adaptive_std")

    if baseline is None or baseline <= 0:
        baseline = row.get("velocity_std")

    if baseline is None or baseline <= 0:
        row["velocity_acceleration_state"] = None
        row["velocity_deceleration"] = False
        row["velocity_shock"] = False

        return row

    ratio = velocity_acceleration / baseline

    if abs(ratio) >= 2:
        row["velocity_acceleration_state"] = "VELOCITY_SHOCK"
    elif ratio >= 1:
        row["velocity_acceleration_state"] = "ACCELERATING_VELOCITY"
    elif ratio <= -1:
        row["velocity_acceleration_state"] = "DECELERATING_VELOCITY"
    else:
        row["velocity_acceleration_state"] = "STABLE_VELOCITY"

    row["velocity_deceleration"] = ratio <= -1
    row["velocity_shock"] = abs(ratio) >= 2

    return row


def add_velocity_exhaustion_features(row):
    # Velocity exhaustion is a baseline warning signal, not a confirmed reversal signal.
    row["velocity_exhaustion"] = False
    row["velocity_exhaustion_state"] = None
    row["exhaustion_strength"] = None

    if (
        not row.get("distribution_ready")
        or len(velocity_distribution) < MIN_HISTORY_SIZE
    ):
        return row

    velocity_zscore = row.get("velocity_zscore")
    velocity_state = row.get("velocity_state")
    velocity_acceleration = row.get("velocity_acceleration")
    velocity_deceleration = row.get("velocity_deceleration")
    abnormal_velocity = row.get("abnormal_velocity")

    if (
        velocity_zscore is None
        or velocity_acceleration is None
    ):
        return row

    baseline = row.get("velocity_adaptive_std")

    if baseline is None or baseline <= 0:
        baseline = row.get("velocity_std")

    if baseline is None or baseline <= 0:
        return row

    active_velocity_context = (
        velocity_state in [
            "HIGH_VELOCITY",
            "EXTREME_VELOCITY",
        ]
        or abnormal_velocity is True
        or velocity_zscore >= 1.25
    )

    if velocity_acceleration >= 0:
        return row

    collapse_ratio = abs(velocity_acceleration) / baseline

    velocity_exhaustion = (
        active_velocity_context is True
        and velocity_deceleration is True
        and collapse_ratio >= 1
    )

    row["velocity_exhaustion"] = velocity_exhaustion

    if not velocity_exhaustion:
        return row

    row["exhaustion_strength"] = min(
        collapse_ratio / 3,
        1
    )

    if (
        collapse_ratio >= 2
        and abnormal_velocity is True
    ):
        row["velocity_exhaustion_state"] = "EXTREME_VELOCITY_EXHAUSTION"
    elif collapse_ratio >= 1.5:
        row["velocity_exhaustion_state"] = "STRONG_VELOCITY_EXHAUSTION"
    elif collapse_ratio >= 1:
        row["velocity_exhaustion_state"] = "VELOCITY_EXHAUSTION"

    return row


def add_distribution_shift_features(row):
    # Distribution shift is a statistical warning, not a trading signal.
    row["price_mean_shift"] = None
    row["price_std_shift"] = None
    row["distribution_shift"] = False
    row["distribution_shift_state"] = None
    row["distribution_shift_strength"] = None

    if len(price_distribution) < SHIFT_BASELINE_WINDOW:
        return row

    values = list(price_distribution)

    recent_values = values[-SHIFT_RECENT_WINDOW:]
    baseline_values = values[-SHIFT_BASELINE_WINDOW:]

    recent_mean = calculate_mean(recent_values)
    baseline_mean = calculate_mean(baseline_values)

    recent_std = calculate_adaptive_std(recent_values)
    baseline_std = calculate_adaptive_std(baseline_values)

    if baseline_std <= 0:
        return row

    price_mean_shift = abs(
        recent_mean
        -
        baseline_mean
    ) / baseline_std

    price_std_shift = recent_std / baseline_std

    mean_shift_detected = price_mean_shift >= 1.5

    std_shift_detected = (
        price_std_shift >= 1.5
        or price_std_shift <= 0.65
    )

    row["price_mean_shift"] = price_mean_shift
    row["price_std_shift"] = price_std_shift
    row["distribution_shift"] = (
        mean_shift_detected
        or std_shift_detected
    )

    if (
        price_mean_shift >= 2.5
        or price_std_shift >= 2.0
    ):
        row["distribution_shift_state"] = "MAJOR_DISTRIBUTION_SHIFT"
    elif (
        price_mean_shift >= 1.5
        or price_std_shift >= 1.5
    ):
        row["distribution_shift_state"] = "DISTRIBUTION_SHIFT"
    elif price_std_shift <= 0.65:
        row["distribution_shift_state"] = "DISTRIBUTION_COMPRESSION_SHIFT"

    shift_score = max(
        price_mean_shift / 3,
        abs(price_std_shift - 1)
    )

    row["distribution_shift_strength"] = min(
        shift_score,
        1
    )

    return row


def add_gaussian_modeling_features(row):
    # Gaussian modeling is statistical rarity context only.
    row["price_gaussian_prob"] = None
    row["gaussian_zone"] = None
    row["gaussian_tail"] = None
    row["gaussian_extreme"] = False
    row["gaussian_confidence"] = None

    if (
        not row.get("distribution_ready")
        or len(price_distribution) < 30
    ):
        return row

    price = row.get("close")

    if price is None:
        return row

    price_mean = calculate_mean(price_distribution)
    price_std = row.get("price_std")

    if price_std is None:
        price_std = calculate_std(price_distribution)

    if (
        price_mean is None
        or price_std is None
        or price_std <= 0
    ):
        return row

    zscore = row.get("price_zscore")

    if zscore is None:
        zscore = (price - price_mean) / price_std

    probability_zscore = max(
        min(zscore, 8),
        -8
    )

    row["price_gaussian_prob"] = (
        1
        /
        (
            price_std
            *
            math.sqrt(2 * math.pi)
        )
    ) * math.exp(
        -0.5 * (probability_zscore ** 2)
    )

    abs_zscore = abs(zscore)

    if abs_zscore < 2:
        row["gaussian_zone"] = "GAUSSIAN_NORMAL"
    elif abs_zscore < 3:
        row["gaussian_zone"] = "GAUSSIAN_OUTER"
    else:
        row["gaussian_zone"] = "GAUSSIAN_EXTREME"

    if (
        abs_zscore >= 2
        and zscore > 0
    ):
        row["gaussian_tail"] = "UPPER_TAIL"
    elif (
        abs_zscore >= 2
        and zscore < 0
    ):
        row["gaussian_tail"] = "LOWER_TAIL"

    row["gaussian_extreme"] = abs_zscore >= 3

    if row.get("distribution_shift") is True:
        row["gaussian_confidence"] = "UNSTABLE_GAUSSIAN"
    elif row["gaussian_zone"] == "GAUSSIAN_NORMAL":
        row["gaussian_confidence"] = "HIGH_CONFIDENCE"
    elif row["gaussian_zone"] == "GAUSSIAN_OUTER":
        row["gaussian_confidence"] = "MEDIUM_CONFIDENCE"
    elif row["gaussian_zone"] == "GAUSSIAN_EXTREME":
        row["gaussian_confidence"] = "LOW_CONFIDENCE"

    return row


def add_extreme_event_detection_features(row):
    # Extreme event detection is a statistical abnormality classifier only.
    row["price_extreme_event"] = False
    row["volume_extreme_event"] = False
    row["delta_extreme_event"] = False
    row["velocity_extreme_event"] = False
    row["gaussian_extreme_event"] = False
    row["spread_extreme_event"] = False
    row["global_extreme_event"] = False
    row["extreme_event_score"] = 0
    row["extreme_event_state"] = "NO_EXTREME_EVENT"
    row["extreme_event_context"] = "NO_EXTREME_CONTEXT"
    row["extreme_event_origin"] = "NONE"

    if not row.get("distribution_ready"):
        return row

    price_zscore = row.get("price_zscore")
    volume_zscore = row.get("volume_zscore")
    delta_zscore = row.get("delta_zscore")
    velocity_zscore = row.get("velocity_zscore")

    row["price_extreme_event"] = (
        price_zscore is not None
        and abs(price_zscore) >= 3
    )

    row["volume_extreme_event"] = (
        row.get("climactic_volume") is True
        or (
            volume_zscore is not None
            and volume_zscore >= 2.5
        )
    )

    row["delta_extreme_event"] = (
        delta_zscore is not None
        and abs(delta_zscore) >= 2.5
    )

    row["velocity_extreme_event"] = (
        row.get("velocity_shock") is True
        or (
            velocity_zscore is not None
            and abs(velocity_zscore) >= 2.5
        )
    )

    row["gaussian_extreme_event"] = (
        row.get("gaussian_extreme") is True
        or row.get("gaussian_zone") == "GAUSSIAN_EXTREME"
    )

    row["spread_extreme_event"] = (
        row.get("abnormal_spread") is True
        or row.get("execution_quality") == "BAD_EXECUTION"
    )

    active_dimensions = sum([
        row["price_extreme_event"],
        row["volume_extreme_event"],
        row["delta_extreme_event"],
        row["velocity_extreme_event"],
        row["gaussian_extreme_event"],
        row["spread_extreme_event"],
    ])

    row["global_extreme_event"] = active_dimensions >= 2

    gaussian_weight = (
        0
        if row.get("gaussian_confidence") == "UNSTABLE_GAUSSIAN"
        else 0.20
    )

    extreme_event_score = 0

    if row["price_extreme_event"]:
        extreme_event_score += 0.20

    if row["gaussian_extreme_event"]:
        extreme_event_score += gaussian_weight

    if row["volume_extreme_event"]:
        extreme_event_score += 0.15

    if row["delta_extreme_event"]:
        extreme_event_score += 0.15

    if row["velocity_extreme_event"]:
        extreme_event_score += 0.15

    if row["spread_extreme_event"]:
        extreme_event_score += 0.15

    row["extreme_event_score"] = min(
        extreme_event_score,
        1
    )

    if (
        row.get("distribution_shift") is True
        and active_dimensions >= 2
    ):
        row["extreme_event_state"] = "UNSTABLE_EXTREME_CONTEXT"
    elif active_dimensions == 0:
        row["extreme_event_state"] = "NO_EXTREME_EVENT"
    elif active_dimensions == 1:
        row["extreme_event_state"] = "SINGLE_FACTOR_EXTREME"
    elif active_dimensions == 2:
        row["extreme_event_state"] = "MULTI_FACTOR_EXTREME"
    else:
        row["extreme_event_state"] = "CRITICAL_EXTREME_EVENT"

    if active_dimensions >= 2:
        row["extreme_event_origin"] = "MULTI_FACTOR_EXTREME"
    elif row["price_extreme_event"]:
        row["extreme_event_origin"] = "PRICE_DOMINATED"
    elif row["volume_extreme_event"]:
        row["extreme_event_origin"] = "VOLUME_DOMINATED"
    elif row["gaussian_extreme_event"]:
        row["extreme_event_origin"] = "GAUSSIAN_DOMINATED"
    elif row["velocity_extreme_event"]:
        row["extreme_event_origin"] = "VELOCITY_DOMINATED"
    elif row["spread_extreme_event"]:
        row["extreme_event_origin"] = "SPREAD_DOMINATED"
    elif row["delta_extreme_event"]:
        row["extreme_event_origin"] = "DELTA_DOMINATED"

    if row["extreme_event_state"] == "UNSTABLE_EXTREME_CONTEXT":
        row["extreme_event_context"] = "UNSTABLE_EXTREME_CONTEXT"
    elif (
        row["price_extreme_event"]
        and row["gaussian_extreme_event"]
    ):
        row["extreme_event_context"] = "PRICE_GAUSSIAN_EXTREME"
    elif (
        row["volume_extreme_event"]
        and row["velocity_extreme_event"]
    ):
        row["extreme_event_context"] = "VOLUME_VELOCITY_EXTREME"
    elif row["spread_extreme_event"]:
        row["extreme_event_context"] = "SPREAD_EXECUTION_RISK"
    elif active_dimensions >= 2:
        row["extreme_event_context"] = "MULTI_FACTOR_STATISTICAL_EVENT"

    return row


def add_statistical_dashboard_features(row):
    row["statistical_dashboard_score"] = 0
    row["statistical_dashboard_state"] = "NO_STRONG_CONFLUENCE"
    row["statistical_dashboard_conditions"] = []
    row["statistical_dashboard_active"] = False

    active_conditions = []

    if row.get("gaussian_extreme") is True:
        active_conditions.append("GAUSSIAN_EXTREME")

    if row.get("distribution_shift") is True:
        active_conditions.append("DISTRIBUTION_SHIFT")

    if row.get("climactic_volume") is True:
        active_conditions.append("CLIMACTIC_VOLUME")

    if row.get("velocity_shock") is True:
        active_conditions.append("VELOCITY_SHOCK")

    if row.get("velocity_exhaustion") is True:
        active_conditions.append("VELOCITY_EXHAUSTION")

    if row.get("abnormal_spread") is True:
        active_conditions.append("ABNORMAL_SPREAD_EXECUTION_RISK")

    delta_zscore = row.get("delta_zscore")

    if (
        delta_zscore is not None
        and abs(delta_zscore) >= 2
    ):
        active_conditions.append("DELTA_ZSCORE_EXTREME")

    score = len(active_conditions)

    row["statistical_dashboard_score"] = score
    row["statistical_dashboard_conditions"] = active_conditions
    row["statistical_dashboard_active"] = score >= 2

    if score <= 1:
        row["statistical_dashboard_state"] = "NO_STRONG_CONFLUENCE"
    elif score <= 3:
        row["statistical_dashboard_state"] = "WEAK_CONFLUENCE"
    elif score <= 5:
        row["statistical_dashboard_state"] = "MODERATE_CONFLUENCE"
    else:
        row["statistical_dashboard_state"] = "STRONG_CONFLUENCE"

    return row


# ==================================================
# MAIN FEATURE ADDER
# ==================================================

def add_distribution_features(row):
    update_distributions(row)

    row = add_zscores(row)
    row = add_statistical_zones(row)

    volatility_ratio = calculate_volatility_ratio()

    row["volatility_ratio"] = volatility_ratio
    row["volatility_regime"] = classify_volatility_regime(
        volatility_ratio
    )

    previous_regime = (
        volatility_regime_history[-1]
        if len(volatility_regime_history) > 0
        else None
    )

    volatility_regime_history.append(
        row["volatility_regime"]
    )

    volatility_ratio_history.append(
        row["volatility_ratio"]
    )

    row["volatility_transition"] = detect_volatility_transition(
        row["volatility_regime"],
        previous_regime
    )

    row["volatility_persistence"] = detect_volatility_persistence(
        row["volatility_regime"],
        list(volatility_regime_history)
    )

    row["volatility_acceleration"] = detect_volatility_acceleration(
        list(volatility_ratio_history)
    )

    row["price_variance"] = calculate_variance(price_distribution)
    row["volume_variance"] = calculate_variance(volume_distribution)
    row["delta_variance"] = calculate_variance(delta_distribution)
    row["velocity_variance"] = calculate_variance(velocity_distribution)

    row["price_std"] = calculate_std(price_distribution)
    row["price_weighted_std"] = calculate_weighted_std(price_distribution)
    row["price_robust_std"] = calculate_robust_std(price_distribution)
    row["price_ewma_std"] = calculate_ewma_std(price_distribution)
    row["price_volatility_weighted_std"] = calculate_volatility_weighted_std(
        price_distribution
    )
    row["price_adaptive_std"] = calculate_adaptive_std(price_distribution)

    row["std_instability_state"] = detect_std_instability(
        row["price_std"],
        row["price_weighted_std"],
        row["price_robust_std"],
        row["price_ewma_std"],
        row["price_volatility_weighted_std"],
    )

    row["volume_adaptive_std"] = calculate_adaptive_std(volume_distribution)
    row["delta_adaptive_std"] = calculate_adaptive_std(delta_distribution)
    row["velocity_adaptive_std"] = calculate_adaptive_std(velocity_distribution)

    row["distribution_ready"] = len(price_distribution) >= 30

    row = add_volume_statistical_foundation(row)
    row = add_spread_statistical_foundation(row)
    row = add_velocity_statistical_foundation(row)
    row = add_velocity_acceleration_features(row)
    row = add_velocity_exhaustion_features(row)
    row = add_distribution_shift_features(row)
    row = add_gaussian_modeling_features(row)
    row = add_extreme_event_detection_features(row)
    row = add_statistical_dashboard_features(row)

    if not row["distribution_ready"]:
        row["price_distribution_mean"] = None
        row["price_distribution_median"] = None
        row["distribution_range"] = None

        row["price_percentile"] = None
        row["volume_percentile"] = None
        row["delta_percentile"] = None
        row["velocity_percentile"] = None

        row["price_percentile_zone"] = None

        row["price_tail_side"] = None
        row["price_tail_strength"] = None
        row["price_tail_risk"] = None
        row["price_tail_persistence"] = None
        row["price_tail_exhaustion"] = None

    else:
        row["price_distribution_mean"] = statistics.mean(
            price_distribution
        )

        row["price_distribution_median"] = statistics.median(
            price_distribution
        )

        row["distribution_range"] = (
            max(price_distribution)
            -
            min(price_distribution)
        )

        row["price_percentile"] = calculate_percentile(
            row["close"],
            price_distribution
        )

        row["volume_percentile"] = calculate_percentile(
            row["volume"],
            volume_distribution
        )

        row["delta_percentile"] = calculate_percentile(
            row["delta"],
            delta_distribution
        )

        row["velocity_percentile"] = calculate_percentile(
            row["velocity"],
            velocity_distribution
        )

        row["price_percentile_zone"] = classify_percentile_zone(
            row["price_percentile"]
        )

        row["price_tail_side"] = detect_tail_side(
            row["price_percentile"]
        )

        tail_history.append(
            row["price_tail_side"]
        )

        row["price_tail_strength"] = detect_tail_strength(
            row["price_zscore"],
            row["price_percentile"]
        )

        row["price_tail_risk"] = detect_tail_risk(
            row["price_zscore"],
            row["price_percentile"],
            row["volatility_regime"]
        )

        row["price_tail_persistence"] = detect_tail_persistence(
            row["price_tail_side"],
            list(tail_history)
        )

        row["price_tail_exhaustion"] = detect_tail_exhaustion(
            row["price_zscore"],
            row["price_percentile"],
            row["volatility_ratio"]
        )

    # ==================================================
    # DELTA STATISTICS
    # ==================================================

    cumulative_delta_history.append(
        row["delta"]
    )

    row["cumulative_delta"] = calculate_cumulative_delta()

    delta_pressure = calculate_delta_pressure(
        row["delta"],
        row["volume"]
    )

    row["delta_pressure"] = delta_pressure

    row["delta_domination"] = detect_delta_domination(
        delta_pressure
    )

    row["aggressive_flow"] = detect_aggressive_flow(
        row["delta_zscore"],
        row["velocity_zscore"]
    )

    delta_pressure_history.append(
        delta_pressure
    )

    row["delta_pressure_state"] = detect_delta_pressure_state(
        delta_pressure
    )

    delta_acceleration = calculate_delta_acceleration()

    row["delta_acceleration"] = delta_acceleration

    delta_acceleration_history.append(
        delta_acceleration
    )

    row["delta_acceleration_state"] = detect_delta_acceleration_state(
        delta_acceleration
    )

    row["delta_exhaustion"] = detect_delta_exhaustion(
        row["delta_zscore"],
        row["velocity_zscore"],
        delta_pressure
    )

    row["imbalance_state"] = detect_imbalance_state(
        row.get("imbalance", 0)
    )

    row = add_statistical_dashboard_v2_features(row)

    return row
