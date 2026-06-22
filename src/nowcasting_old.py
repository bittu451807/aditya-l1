import os
import numpy as np
import pandas as pd


class NowcastingEngine:

    def __init__(self):

        self.BASE_DIR = os.path.dirname(
            os.path.dirname(__file__)
        )

        self.data_path = os.path.join(
            self.BASE_DIR,
            "outputs",
            "clean_data.parquet"
        )

        self.catalogue_path = os.path.join(
            self.BASE_DIR,
            "outputs",
            "event_catalogue.csv"
        )

    # ----------------------------------
    # DETECT FLARES
    # ----------------------------------

    def detect_flares(
        self,
        df
    ):

        df = df.copy()

        soft_mean = df["soft_flux"].mean()
        soft_std = df["soft_flux"].std()

        hard_mean = df["hard_flux"].mean()
        hard_std = df["hard_flux"].std()

        df["z_soft"] = (
            df["soft_flux"] -
            soft_mean
        ) / (
            soft_std + 1e-8
        )

        df["z_hard"] = (
            df["hard_flux"] -
            hard_mean
        ) / (
            hard_std + 1e-8
        )

        df["flare_score"] = (
            0.7 * df["z_soft"] +
            0.3 * df["z_hard"]
        )

        threshold = (
            df["flare_score"]
            .mean()
            +
            3 *
            df["flare_score"]
            .std()
        )

        df["flare_now"] = (
            df["flare_score"]
            >
            threshold
        )

        return df

    # ----------------------------------
    # CLASSIFICATION
    # ----------------------------------

    def classify(
        self,
        value
    ):

        if value < 1:
            return "A"

        elif value < 2:
            return "B"

        elif value < 4:
            return "C"

        elif value < 8:
            return "M"

        else:
            return "X"

    # ----------------------------------
    # EVENT CATALOGUE
    # ----------------------------------

    def create_catalogue(
        self,
        df
    ):

        flare_df = df[
            df["flare_now"]
        ].copy()

        if len(flare_df) == 0:

            return pd.DataFrame(
                columns=[
                    "start_time",
                    "end_time",
                    "peak_time",
                    "peak_flux",
                    "flare_class"
                ]
            )

        flare_df[
            "group"
        ] = (
            flare_df["flare_now"]
            !=
            flare_df["flare_now"]
            .shift()
        ).cumsum()

        events = []

        for _, g in flare_df.groupby(
            "group"
        ):

            peak_idx = (
                g["soft_flux"]
                .idxmax()
            )

            peak_flux = (
                g.loc[
                    peak_idx,
                    "soft_flux"
                ]
            )

            events.append(

                {

                    "start_time":
                    g["time"].iloc[0],

                    "end_time":
                    g["time"].iloc[-1],

                    "peak_time":
                    g.loc[
                        peak_idx,
                        "time"
                    ],

                    "peak_flux":
                    peak_flux,

                    "flare_class":
                    self.classify(
                        peak_flux
                    )
                }
            )

        return pd.DataFrame(
            events
        )

    # ----------------------------------
    # RUN
    # ----------------------------------

    def run(self):

        print(
            "Loading data..."
        )

        df = pd.read_parquet(
            self.data_path
        )

        print(
            "Detecting flares..."
        )

        df = self.detect_flares(
            df
        )

        print(
            "Creating catalogue..."
        )

        catalogue = (
            self.create_catalogue(
                df
            )
        )

        df.to_parquet(
            self.data_path,
            index=False
        )

        catalogue.to_csv(
            self.catalogue_path,
            index=False
        )

        print()

        print(
            "Flare points:",
            int(
                df[
                    "flare_now"
                ].sum()
            )
        )

        print(
            "Events:",
            len(
                catalogue
            )
        )

        print(
            "Saved:"
        )

        print(
            self.catalogue_path
        )


if __name__ == "__main__":

    NowcastingEngine().run()