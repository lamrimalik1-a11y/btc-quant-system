from engines.phase1_engine import process_phase1
from engines.phase1b_statistics import process_phase1b
from engines.decision_engine import make_decision


def run_pipeline():

    sample_row = {
        "open": 100,
        "high": 110,
        "low": 95,
        "close": 108,

        "volume": 2500,

        "buy_volume": 1600,
        "sell_volume": 900,

        "delta": 700,
        "delta_ratio": 0.28,

        "velocity": 12.5,
        "rvi": 58,

        "duration_seconds": 5,
        "tick_count": 500,
    }

    phase1_result = process_phase1(sample_row)

    phase1b_result = process_phase1b(phase1_result)

    final_context = {
        **phase1_result,
        **phase1b_result,
    }

    decision = make_decision(final_context)

    return {
        "phase1": phase1_result,
        "phase1b": phase1b_result,
        "decision": decision,
    }