import os
import numpy as np
import pandas as pd


class DataPipeline:

    def __init__(self):

        self.BASE_DIR = os.path.dirname(
            os.path.dirname(__file__)
        )

        self.soft_path = os.path.join(
            self.BASE_DIR,
            "data_stream",
            "AL1_SOLEXS.csv"
        )

        self.hard_path = os.path.join(
            self.BASE_DIR,
            "data_stream",
            "AL1_HEL1OS.csv"
        )

        self.output_path = os.path.join(
            self.BASE_DIR,
            "outputs",
            "clean_data.parquet"
        )

    # ------------------------
    # LOAD
    # ------------------------

    def load(self):

        print("Loading SoLEXS...")
        soft = pd.read_csv(
            self.soft_path
        )

        print("Loading HEL1OS...")
        hard = pd.read_csv(
            self.hard_path
        )

        return soft, hard

    # ------------------------
    # SOLEXS
    # ------------------------

    def process_solexs(
        self,
        df
    ):

        df = df.copy()

        if "TIME" in df.columns:

            df["time"] = pd.to_datetime(
                df["TIME"],
                unit="s",
                origin="unix",
                errors="coerce"
            )

        elif "MJD" in df.columns:

            df["time"] = pd.to_datetime(
                df["MJD"],
                unit="D",
                origin="1858-11-17",
                errors="coerce"
            )

        else:
            raise Exception(
                "No time column in SoLEXS."
            )

        if "COUNT_RATE" in df.columns:
            flux = "COUNT_RATE"

        elif "RATE_CPS" in df.columns:
            flux = "RATE_CPS"

        elif "COUNTS" in df.columns:
            flux = "COUNTS"

        else:

            numeric = df.select_dtypes(
                include=np.number
            )

            flux = numeric.columns[-1]

        df = df[
            [
                "time",
                flux
            ]
        ]

        df.columns = [
            "time",
            "soft_flux"
        ]

        return df

    # ------------------------
    # HEL1OS
    # ------------------------

    def process_hel1os(
        self,
        df
    ):

        df = df.copy()

        if "TIME" in df.columns:

            # TIME column contains MJD
            df["time"] = pd.to_datetime(
                df["TIME"],
                unit="D",
                origin="1858-11-17",
                errors="coerce"
            )

        else:
            raise Exception(
                "TIME column missing."
            )

        detector_cols = []

        for c in [

            "CZT1_RATE_CPS",
            "CZT2_RATE_CPS",
            "CDTE1_RATE_CPS",
            "CDTE2_RATE_CPS"

        ]:

            if c in df.columns:
                detector_cols.append(c)

        df["hard_flux"] = (
            df[
                detector_cols
            ]
            .mean(axis=1)
        )

        return df[
            [
                "time",
                "hard_flux"
            ]
        ]

    # ------------------------
    # MERGE
    # ------------------------

    def merge(
        self,
        soft,
        hard
    ):

        soft["time"] = pd.to_datetime(
            soft["time"]
        ).astype(
            "datetime64[ns]"
        )

        hard["time"] = pd.to_datetime(
            hard["time"]
        ).astype(
            "datetime64[ns]"
        )

        soft = (
            soft
            .dropna(
                subset=["time"]
            )
            .sort_values(
                "time"
            )
        )

        hard = (
            hard
            .dropna(
                subset=["time"]
            )
            .sort_values(
                "time"
            )
        )

        print(
            "Soft range:",
            soft["time"].min(),
            "->",
            soft["time"].max()
        )

        print(
            "Hard range:",
            hard["time"].min(),
            "->",
            hard["time"].max()
        )

        df = pd.merge_asof(
            soft,
            hard,
            on="time",
            direction="nearest",
            tolerance=pd.Timedelta(
                "5min"
            )
        )

        return df

    # ------------------------
    # FEATURES
    # ------------------------

    def add_features(
        self,
        df
    ):

        df = df.copy()

        for w in [
            5,
            15,
            30
        ]:

            df[
                f"soft_mean_{w}"
            ] = (
                df["soft_flux"]
                .rolling(
                    w,
                    min_periods=1
                )
                .mean()
            )

            df[
                f"hard_mean_{w}"
            ] = (
                df["hard_flux"]
                .rolling(
                    w,
                    min_periods=1
                )
                .mean()
            )

        df["soft_std"] = (
            df["soft_flux"]
            .rolling(
                30,
                min_periods=1
            )
            .std()
        )

        df["hard_std"] = (
            df["hard_flux"]
            .rolling(
                30,
                min_periods=1
            )
            .std()
        )

        df["soft_diff"] = (
            df["soft_flux"]
            .diff()
        )

        df["hard_diff"] = (
            df["hard_flux"]
            .diff()
        )

        for lag in [
            1,
            5,
            15,
            30
        ]:

            df[
                f"soft_lag_{lag}"
            ] = (
                df["soft_flux"]
                .shift(lag)
            )

            df[
                f"hard_lag_{lag}"
            ] = (
                df["hard_flux"]
                .shift(lag)
            )

        return df

    # ------------------------
    # CLEAN
    # ------------------------

    def clean(
        self,
        df
    ):

        df = (
            df
            .dropna(
                subset=["time"]
            )
            .sort_values(
                "time"
            )
        )

        df["soft_flux"] = (
            df["soft_flux"]
            .interpolate()
        )

        df["hard_flux"] = (
            df["hard_flux"]
            .interpolate()
        )

        df = df.fillna(0)

        return df

    # ------------------------
    # RUN
    # ------------------------

    def run(self):

        soft, hard = self.load()

        print(
            "Processing SoLEXS..."
        )
        soft = self.process_solexs(
            soft
        )

        print(
            "Processing HEL1OS..."
        )
        hard = self.process_hel1os(
            hard
        )

        print(
            "Merging..."
        )
        df = self.merge(
            soft,
            hard
        )

        print(
            "Cleaning..."
        )
        df = self.clean(
            df
        )

        print(
            "Creating features..."
        )
        df = self.add_features(
            df
        )

        os.makedirs(
            os.path.dirname(
                self.output_path
            ),
            exist_ok=True
        )

        df.to_parquet(
            self.output_path,
            index=False
        )

        print()
        print(
            "Rows:",
            len(df)
        )

        print(
            "Columns:",
            len(df.columns)
        )

        print(
            "Saved:",
            self.output_path
        )


if __name__ == "__main__":
    DataPipeline().run()