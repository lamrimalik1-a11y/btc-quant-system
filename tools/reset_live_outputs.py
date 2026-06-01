import csv
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.observation_archive import FIELDNAMES as OBSERVATION_ROW_COLUMNS
from core.observation_logger import (
    DASHBOARD_EPISODES_FILE,
    EPISODE_FIELDNAMES,
    EVENT_FIELDNAMES,
    OBSERVATION_EVENTS_FILE,
)
from core.storage import MARKET_ROW_COLUMNS


OUTPUT_DIR = REPO_ROOT / "outputs"

LIVE_OUTPUTS = [
    (
        OUTPUT_DIR / "market_rows.csv",
        MARKET_ROW_COLUMNS,
    ),
    (
        OUTPUT_DIR / "observation_rows.csv",
        OBSERVATION_ROW_COLUMNS,
    ),
    (
        REPO_ROOT / OBSERVATION_EVENTS_FILE,
        EVENT_FIELDNAMES,
    ),
    (
        REPO_ROOT / DASHBOARD_EPISODES_FILE,
        EPISODE_FIELDNAMES,
    ),
]


def write_header(path, fieldnames):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open(
        mode="w",
        newline=""
    ) as file:

        writer = csv.writer(
            file
        )

        writer.writerow(
            fieldnames
        )


def reset_live_outputs():

    for path, fieldnames in LIVE_OUTPUTS:

        write_header(
            path,
            fieldnames
        )


def main():

    reset_live_outputs()

    print("LIVE OUTPUTS RESET COMPLETE")


if __name__ == "__main__":

    main()
