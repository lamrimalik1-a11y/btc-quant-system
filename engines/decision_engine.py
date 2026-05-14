def make_decision(context):

    zscore = context.get("zscore", 0)
    delta_ratio = context.get("delta_ratio", 0)

    if zscore > 2 and delta_ratio > 0.2:

        return {
            "action": "BUY",
            "confidence": 0.8,
            "reason": "Strong bullish statistical pressure"
        }

    if zscore < -2 and delta_ratio < -0.2:

        return {
            "action": "SELL",
            "confidence": 0.8,
            "reason": "Strong bearish statistical pressure"
        }

    return {
        "action": "NO_TRADE",
        "confidence": 0,
        "reason": "No conditions met"
    }