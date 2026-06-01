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

    if "market_timestamp" in header:
        return

    updated_header = header + [
        "market_timestamp"
    ]

    updated_rows = [
        updated_header
    ]

    for row in rows[1:]:

        updated_rows.append(
            row + [
                ""
            ]
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
        ])
