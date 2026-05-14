import csv
import os


OUTPUT_FOLDER = "outputs"

ORDERBOOK_FILE = (
    "outputs/orderbook.csv"
)


def initialize_orderbook_storage():

    if not os.path.exists(
        OUTPUT_FOLDER
    ):

        os.makedirs(
            OUTPUT_FOLDER
        )

    if not os.path.exists(
        ORDERBOOK_FILE
    ):

        with open(

            ORDERBOOK_FILE,

            mode="w",

            newline=""
        ) as file:

            writer = csv.writer(
                file
            )

            writer.writerow([

                "best_bid_price",

                "best_bid_size",

                "best_ask_price",

                "best_ask_size",

                "spread",

                "total_bid_volume",

                "total_ask_volume",

                "imbalance",
            ])


def save_orderbook(
    orderbook
):

    if orderbook is None:
        return

    with open(

        ORDERBOOK_FILE,

        mode="a",

        newline=""
    ) as file:

        writer = csv.writer(
            file
        )

        writer.writerow([

            orderbook[
                "best_bid_price"
            ],

            orderbook[
                "best_bid_size"
            ],

            orderbook[
                "best_ask_price"
            ],

            orderbook[
                "best_ask_size"
            ],

            orderbook[
                "spread"
            ],

            orderbook[
                "total_bid_volume"
            ],

            orderbook[
                "total_ask_volume"
            ],

            orderbook[
                "imbalance"
            ],
        ])