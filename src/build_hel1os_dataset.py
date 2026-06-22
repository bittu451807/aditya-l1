import os
import zipfile
import shutil
import tempfile
import pandas as pd
from astropy.io import fits

BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)

RAW_DIR = os.path.join(
    BASE_DIR,
    "raw_zip",
    "hel1os"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data_stream",
    "AL1_HEL1OS.csv"
)


def read_lightcurve(path):

    with fits.open(
        path,
        memmap=False
    ) as hdul:

        data = hdul[1].data

        return pd.DataFrame(data)


def find_time_column(df):

    possible = [
        "TIME",
        "MET",
        "TIME_SEC",
        "TIME_UTC",
        "DATE"
    ]

    for c in possible:
        if c in df.columns:
            return c

    # use first column if nothing matches
    return df.columns[0]


all_days = []

for zip_name in sorted(
    os.listdir(RAW_DIR)
):

    if not zip_name.endswith(".zip"):
        continue

    print(
        "Reading:",
        zip_name
    )

    zip_path = os.path.join(
        RAW_DIR,
        zip_name
    )

    extract_dir = tempfile.mkdtemp()

    with zipfile.ZipFile(
        zip_path
    ) as z:

        z.extractall(
            extract_dir
        )

    detector_data = {}

    try:

        for root, dirs, files in os.walk(
            extract_dir
        ):

            for file in files:

                name = file.lower()

                if (
                    "lightcurve"
                    not in name
                ):
                    continue

                if not name.endswith(
                    ".fits"
                ):
                    continue

                full_path = os.path.join(
                    root,
                    file
                )

                print(
                    "   ",
                    file
                )

                detector_data[
                    name
                ] = read_lightcurve(
                    full_path
                )

        if (
            "lightcurve_czt1.fits"
            not in detector_data
        ):
            continue

        final = pd.DataFrame()

        czt1 = detector_data[
            "lightcurve_czt1.fits"
        ]

        print(
            "Columns found:"
        )
        print(
            czt1.columns.tolist()
        )

        time_col = find_time_column(
            czt1
        )

        print(
            "Using time column:",
            time_col
        )

        final["TIME"] = (
            czt1[time_col]
        )

        final[
            "CZT1_RATE_CPS"
        ] = (
            czt1.iloc[:, -1]
        )

        if (
            "lightcurve_czt2.fits"
            in detector_data
        ):

            final[
                "CZT2_RATE_CPS"
            ] = (
                detector_data[
                    "lightcurve_czt2.fits"
                ].iloc[:, -1]
            )

        if (
            "lightcurve_cdte1.fits"
            in detector_data
        ):

            final[
                "CDTE1_RATE_CPS"
            ] = (
                detector_data[
                    "lightcurve_cdte1.fits"
                ].iloc[:, -1]
            )

        if (
            "lightcurve_cdte2.fits"
            in detector_data
        ):

            final[
                "CDTE2_RATE_CPS"
            ] = (
                detector_data[
                    "lightcurve_cdte2.fits"
                ].iloc[:, -1]
            )

        all_days.append(
            final
        )

    finally:

        shutil.rmtree(
            extract_dir,
            ignore_errors=True
        )


if len(all_days) == 0:

    raise Exception(
        "No HEL1OS data found."
    )


big_df = pd.concat(
    all_days,
    ignore_index=True
)

big_df = (
    big_df
    .drop_duplicates(
        subset="TIME"
    )
    .sort_values(
        "TIME"
    )
)

os.makedirs(
    os.path.dirname(
        OUTPUT_FILE
    ),
    exist_ok=True
)

big_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print(
    "Saved:",
    OUTPUT_FILE
)
print(
    "Rows:",
    len(big_df)
)
print(
    "Columns:",
    big_df.columns.tolist()
)
