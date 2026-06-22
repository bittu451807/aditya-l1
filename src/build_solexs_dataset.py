import os
import gzip
import zipfile
import shutil
import pandas as pd
from astropy.io import fits

BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)

RAW_DIR = os.path.join(
    BASE_DIR,
    "raw_zip",
    "solexs"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data_stream",
    "AL1_SOLEXS.csv"
)

TEMP_DIR = os.path.join(
    BASE_DIR,
    "temp_solexs"
)

os.makedirs(
    TEMP_DIR,
    exist_ok=True
)

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

    extract_dir = os.path.join(
        TEMP_DIR,
        zip_name.replace(
            ".zip",
            ""
        )
    )

    if os.path.exists(
        extract_dir
    ):
        shutil.rmtree(
            extract_dir,
            ignore_errors=True
        )

    os.makedirs(
        extract_dir,
        exist_ok=True
    )

    with zipfile.ZipFile(
        zip_path
    ) as z:

        z.extractall(
            extract_dir
        )

    for root, dirs, files in os.walk(
        extract_dir
    ):

        for file in files:

            if not file.endswith(
                ".lc.gz"
            ):
                continue

            gz_path = os.path.join(
                root,
                file
            )

            lc_path = gz_path[:-3]

            with gzip.open(
                gz_path,
                "rb"
            ) as fin:

                with open(
                    lc_path,
                    "wb"
                ) as fout:

                    fout.write(
                        fin.read()
                    )

            with fits.open(
                lc_path,
                memmap=False
            ) as hdul:

                data = hdul[1].data

                df = pd.DataFrame(
                    data
                )

            cols = []

            for c in [
                "TIME",
                "COUNTS",
                "COUNT_RATE",
                "QUALITY"
            ]:
                if c in df.columns:
                    cols.append(c)

            df = df[cols]

            all_days.append(
                df
            )

            try:
                os.remove(
                    lc_path
                )
            except:
                pass


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

print(
    "Saved:",
    OUTPUT_FILE
)

print(
    "Rows:",
    len(big_df)
)

shutil.rmtree(
    TEMP_DIR,
    ignore_errors=True
)
