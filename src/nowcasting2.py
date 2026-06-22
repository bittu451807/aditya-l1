
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

    # -----------------------------
    # ACTIVITY DETECTION
    # -----------------------------

    def detect_activity(
        self,
        df
    ):

        df = df.copy()

        score = (
            0.45 * df["z_soft"] +
            0.35 * df["z_hard"] +
            0.10 * (
                df["soft_diff"].fillna(0)
                /
                (
                    df["soft_std"].fillna(1)
                    + 1e-6
                )
            ) +
            0.10 * (
                df["hard_diff"].fillna(0)
                /
                (
                    df["hard_std"].fillna(1)
                    + 1e-6
                )
            )
        )

        df["activity_score"] = score

        q1 = score.quantile(0.90)
        q2 = score.quantile(0.97)
        q3 = score.quantile(0.995)

        df["activity_level"] = 0

        df.loc[
            score >= q1,
            "activity_level"
        ] = 1

        df.loc[
            score >= q2,
            "activity_level"
        ] = 2

        df.loc[
            score >= q3,
            "activity_level"
        ] = 3

        df["flare_now"] = (
            df["activity_level"] >= 2
        )

        return df

    # -----------------------------
    # CONFIDENCE
    # -----------------------------

    def confidence(
        self,
        peak_score
    ):

        c = min(
            99,
            max(
                50,
                int(
                    50 +
                    peak_score * 8
                )
            )
        )

        return c

    # -----------------------------
    # EVENT CATALOGUE
    # -----------------------------

    def create_catalogue(
        self,
        df
    ):

        active = df[
            df["activity_level"] >= 1
        ].copy()

        if len(active) == 0:

            return pd.DataFrame()

        active["group"] = (
            active["activity_level"]
            !=
            active["activity_level"]
            .shift()
        ).cumsum()

        events = []

        for _, g in active.groupby(
            "group"
        ):

            peak_idx = (
                g["activity_score"]
                .idxmax()
            )

            peak_score = float(
                g.loc[
                    peak_idx,
                    "activity_score"
                ]
            )

            duration = (
                (
                    g["time"].iloc[-1]
                    -
                    g["time"].iloc[0]
                )
                .total_seconds()
                /
                60
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
                    float(
                        g["soft_flux"].max()
                    ),

                    "activity_level":
                    int(
                        g[
                            "activity_level"
                        ].max()
                    ),

                    "confidence":
                    self.confidence(
                        peak_score
                    ),

                    "duration_minutes":
                    round(
                        duration,
                        2
                    )
                }
            )

        events = pd.DataFrame(
            events
        )

        return events.sort_values(
            "peak_time"
        )

    # -----------------------------
    # RUN
    # -----------------------------

    def run(self):

        print(
            "Loading data..."
        )

        df = pd.read_parquet(
            self.data_path
        )

        df["time"] = pd.to_datetime(
            df["time"]
        )

        print(
            "Detecting activity..."
        )

        df = self.detect_activity(
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
            "Activity Level Counts"
        )

        print(
            df[
                "activity_level"
            ].value_counts()
        )

        print()

        print(
            "Events:",
            len(
                catalogue
            )
        )

        print()

        print(
            "Saved:"
        )

        print(
            self.catalogue_path
        )


if __name__ == "__main__":

    NowcastingEngine().run()
