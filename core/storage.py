import csv
import os


OUTPUT_FOLDER = "outputs"

OUTPUT_FILE = "outputs/market_rows.csv"

MARKET_ROW_COLUMNS = [
    "close",
    "volume",
    "delta",
    "velocity",
    "rvi",
    "adaptive_window",
    "price_zone",
    "volume_zone",
    "delta_zone",
    "velocity_zone",
    "renko_direction",
    "renko_event",
    "renko_bricks",
    "market_timestamp",
    # OHLC persistence (ADDITIVE). open/high/low are already computed by
    # build_trade_row(); appended AFTER all existing columns so "close" and
    # every prior column keep their exact byte positions. LIVE going forward
    # only — does not retroactively populate already-written rows.
    "open",
    "high",
    "low",
]


def initialize_storage():

    if not os.path.exists(
        OUTPUT_FOLDER
    ):

        os.makedirs(
            OUTPUT_FOLDER
        )

    if os.path.exists(
        OUTPUT_FILE
    ):

        ensure_market_timestamp_column()

    else:

        with open(
            OUTPUT_FILE,
            mode="w",
            newline=""
        ) as file:

            writer = csv.writer(
                file
            )

            writer.writerow(
                MARKET_ROW_COLUMNS
            )


def ensure_market_timestamp_column():

    with open(
        OUTPUT_FILE,
        mode="r",
        newline=""
    ) as file:

        reader = csv.reader(
            file
        )

        rows = list(
            reader
        )

    if not rows:

        with open(
            OUTPUT_FILE,
            mode="w",
            newline=""
        ) as file:

            writer = csv.writer(
                file
            )

            writer.writerow(
                MARKET_ROW_COLUMNS
            )

        return

    header = rows[0]

    # Append ANY MARKET_ROW_COLUMNS missing from the on-disk header (ADDITIVE
    # migration). Originally market_timestamp-only; generalized so newly-added
    # trailing columns (open/high/low) are migrated onto existing files too.
    # New columns are only ever appended at the end of MARKET_ROW_COLUMNS, so
    # existing column positions are preserved; already-written rows receive
    # empty trailing cells for the new columns.
    missing = [
        column
        for column in MARKET_ROW_COLUMNS
        if column not in header
    ]

    if not missing:
        return

    updated_header = header + missing

    updated_rows = [
        updated_header
    ]

    pad = [""] * len(missing)

    for row in rows[1:]:

        updated_rows.append(
            row + pad
        )

    with open(
        OUTPUT_FILE,
        mode="w",
        newline=""
    ) as file:

        writer = csv.writer(
            file
        )

        writer.writerows(
            updated_rows
        )


def save_row(row):

    with open(
        OUTPUT_FILE,
        mode="a",
        newline=""
    ) as file:

        writer = csv.writer(
            file
        )

        writer.writerow([

            row["close"],

            row["volume"],

            row["delta"],

            row["velocity"],

            row["rvi"],

            row["adaptive_window"],

            row["price_zone"],

            row["volume_zone"],

            row["delta_zone"],

            row["velocity_zone"],

            row["renko_direction"],

            row["renko_event"],

            row["renko_bricks"],

            row.get(
                "market_timestamp",
                row.get(
                    "end_ts",
                    ""
                )
            ),

            row["open"],

            row["high"],

            row["low"],
        ])
