import os
import numpy as np
import pandas as pd


class NowcastingEngine:

    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.dirname(__file__))
        self.data_path = os.path.join(self.BASE_DIR, "outputs", "clean_data.parquet")
        self.catalogue_path = os.path.join(self.BASE_DIR, "outputs", "event_catalogue.csv")

    def sanitize_and_reconstruct(self, df):
        """Space-Grade Dropout Guard & Sensor Saturation Reconstructor."""
        df = df.copy()
        
        # 1. Clean Dropouts & Cosmic Spikes
        for col in ["soft_flux", "hard_flux"]:
            if col in df.columns:
                df[col] = df[col].replace([-999, -9999, np.inf, -np.inf], np.nan)
                rolling_median = df[col].rolling(window=11, min_periods=1, center=True).median()
                rolling_std = df[col].rolling(window=11, min_periods=1, center=True).std().fillna(0)
                spike_mask = (df[col] - rolling_median).abs() > (5 * rolling_std + 1e-9)
                df.loc[spike_mask, col] = rolling_median
                df[col] = df[col].ffill().bfill().fillna(1e-9)

        # 2. Sensor Saturation Reconstruction Algorithm
        df['soft_diff'] = df['soft_flux'].diff().fillna(0)
        df['hard_diff'] = df['hard_flux'].diff().fillna(0)
        
        high_flux_threshold = df['soft_flux'].quantile(0.99)
        saturation_mask = (df['soft_flux'] > high_flux_threshold) & (df['soft_diff'].abs() < 1e-12)
        
        if saturation_mask.sum() > 0:
            scale_factor = (df['soft_flux'].mean() / (df['hard_flux'].mean() + 1e-9)) * 0.5
            reconstructed_values = df['soft_flux'].shift(1) + (df['hard_diff'] * scale_factor)
            df.loc[saturation_mask, 'soft_flux'] = reconstructed_values.loc[saturation_mask]
            df['soft_diff'] = df['soft_flux'].diff().fillna(0)

        return df

    def detect_activity(self, df):
        df = df.copy()
        df = self.sanitize_and_reconstruct(df)

        # Macro-Background Subtraction (1-hour rolling baseline)
        df['soft_bg'] = df['soft_flux'].rolling(window=360, min_periods=1).min()
        df['hard_bg'] = df['hard_flux'].rolling(window=360, min_periods=1).min()
        
        df['soft_flux_net'] = df['soft_flux'] - df['soft_bg']
        df['hard_flux_net'] = df['hard_flux'] - df['hard_bg']

        # Astrophyics Variables
        df["neupert_proxy"] = df["hard_flux_net"].rolling(window=30, min_periods=1).sum()
        df["hardness_ratio"] = df["hard_flux_net"] / (df["soft_flux_net"] + 1e-9)
        
        df["soft_std"] = df["soft_flux_net"].rolling(15, min_periods=1).std().fillna(0)
        df["hard_std"] = df["hard_flux_net"].rolling(15, min_periods=1).std().fillna(0)
        
        df["z_soft"] = (df["soft_flux_net"] - df["soft_flux_net"].rolling(180, min_periods=1).mean()) / (df["soft_flux_net"].rolling(180, min_periods=1).std() + 1e-9)
        df["z_hard"] = (df["hard_flux_net"] - df["hard_flux_net"].rolling(180, min_periods=1).mean()) / (df["hard_flux_net"].rolling(180, min_periods=1).std() + 1e-9)

        score = (
            0.35 * df["z_soft"] +
            0.25 * df["z_hard"] +
            0.15 * df["hardness_ratio"].clip(0, 10) +
            0.15 * (df["soft_diff"].fillna(0) / (df["soft_std"] + 1e-6)) +
            0.10 * (df["hard_diff"].fillna(0) / (df["hard_std"] + 1e-6))
        )
        df["activity_score"] = score

        q1, q2, q3 = score.quantile(0.90), score.quantile(0.97), score.quantile(0.995)

        df["activity_level"] = 0
        df.loc[score >= q1, "activity_level"] = 1  
        df.loc[score >= q2, "activity_level"] = 2  
        df.loc[score >= q3, "activity_level"] = 3  

        df["flare_now"] = (df["activity_level"] >= 2).astype(int)
        
        df.drop(columns=['soft_bg', 'hard_bg', 'soft_flux_net', 'hard_flux_net'], inplace=True, errors='ignore')
        
        return df

    def confidence(self, peak_score):
        return min(99, max(50, int(50 + peak_score * 8)))

    def create_catalogue(self, df):
        active = df[df["activity_level"] >= 1].copy()
        if len(active) == 0:
            return pd.DataFrame(columns=["start_time", "end_time", "peak_time", "peak_flux", "activity_level", "confidence", "duration_minutes"])

        active["group"] = (active["activity_level"] != active["activity_level"].shift()).cumsum()
        events = []
        for _, g in active.groupby("group"):
            peak_idx = g["activity_score"].idxmax()
            peak_score = float(g.loc[peak_idx, "activity_score"])
            duration = (g["time"].iloc[-1] - g["time"].iloc[0]).total_seconds() / 60.0

            events.append({
                "start_time": g["time"].iloc[0],
                "end_time": g["time"].iloc[-1],
                "peak_time": g.loc[peak_idx, "time"],
                "peak_flux": float(g["soft_flux"].max()),
                "activity_level": int(g["activity_level"].max()),
                "confidence": self.confidence(peak_score),
                "duration_minutes": round(duration, 2)
            })

        events = pd.DataFrame(events)
        return events.sort_values("peak_time")

    def run(self):
        print("🚀 Executing Pro-Grade Nowcasting Core...")
        df = pd.read_parquet(self.data_path)
        df["time"] = pd.to_datetime(df["time"])

        df = self.detect_activity(df)
        catalogue = self.create_catalogue(df)

        df.to_parquet(self.data_path, index=False)
        catalogue.to_csv(self.catalogue_path, index=False)
        print("✅ Feature engineering and catalog generation completed.")


if __name__ == "__main__":
    NowcastingEngine().run()
