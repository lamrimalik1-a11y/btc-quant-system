from datetime import datetime


def get_market_session():

    current_hour = (
        datetime.utcnow().hour
    )

    if 0 <= current_hour < 7:

        return "ASIA"

    elif 7 <= current_hour < 13:

        return "LONDON"

    elif 13 <= current_hour < 17:

        return "NY_OPEN"

    elif 17 <= current_hour < 22:

        return "NEW_YORK"

    else:

        return "CLOSING"