import csv
import os


OUTPUT_FOLDER = "outputs"

OUTPUT_FILE = "outputs/market_rows.csv"


def initialize_storage():

    if not os.path.exists(
        OUTPUT_FOLDER
    ):

        os.makedirs(
            OUTPUT_FOLDER
        )

    if not os.path.exists(
        OUTPUT_FILE
    ):

        with open(
            OUTPUT_FILE,
            mode="w",
            newline=""
        ) as file:

            writer = csv.writer(
                file
            )

            writer.writerow([

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
            ])


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
        ])