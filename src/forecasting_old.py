import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler

# ----------------------------
# CONFIG
# ----------------------------
LOOKBACK = 30
BATCH_SIZE = 128
EPOCHS = 6
LR = 0.001

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ----------------------------
# DATASET (FIXED)
# ----------------------------
class FlareDataset(Dataset):
    def __init__(self, X, y):
        self.X = X
        self.y = y

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return (
            torch.tensor(self.X[idx], dtype=torch.float32),
            torch.tensor(self.y[idx], dtype=torch.float32),
        )


# ----------------------------
# MODEL
# ----------------------------
class GRUModel(nn.Module):
    def __init__(self, input_size):
        super().__init__()

        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=48,
            num_layers=1,
            batch_first=True
        )

        self.fc = nn.Sequential(
            nn.Linear(48, 24),
            nn.ReLU(),
            nn.Linear(24, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        out, _ = self.gru(x)
        out = out[:, -1, :]
        return self.fc(out).squeeze()


# ----------------------------
# ENGINE
# ----------------------------
class ForecastEngine:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.dirname(__file__))

        self.data_path = os.path.join(self.BASE_DIR, "outputs", "clean_data.parquet")
        self.model_path = os.path.join(self.BASE_DIR, "models", "flare_model.pth")

    # ----------------------------
    # LOAD + SPEED REDUCTION
    # ----------------------------
    def load_data(self):
        df = pd.read_parquet(self.data_path)

        # 🔥 FAST MODE (critical)
        df = df.iloc[::3].reset_index(drop=True)   # downsample
        df = df.iloc[:200000]                      # cap size

        return df

    # ----------------------------
    # TARGET CREATION
    # ----------------------------
    def create_targets(self, df):
        df = df.copy()

        # 15-step future prediction
        df["target"] = df["flare_now"].shift(-15).fillna(0).astype(int)

        return df

    # ----------------------------
    # SEQUENCE BUILDER
    # ----------------------------
    def build_sequences(self, df):

        feature_cols = [
            c for c in df.columns
            if c not in ["time", "target"]
        ]

        scaler = StandardScaler()
        features = scaler.fit_transform(df[feature_cols].fillna(0))

        y = df["target"].values

        X_seq, y_seq = [], []

        for i in range(LOOKBACK, len(df), 2):  # stride = speed boost
            X_seq.append(features[i-LOOKBACK:i])
            y_seq.append(y[i])

        return np.array(X_seq), np.array(y_seq), scaler, feature_cols

    # ----------------------------
    # SPLIT
    # ----------------------------
    def split(self, X, y):
        split = int(len(X) * 0.8)

        return (
            X[:split], X[split:],
            y[:split], y[split:]
        )

    # ----------------------------
    # TRAIN
    # ----------------------------
    def train(self, X_train, y_train):

        loader = DataLoader(
            FlareDataset(X_train, y_train),
            batch_size=BATCH_SIZE,
            shuffle=False
        )

        model = GRUModel(X_train.shape[2]).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=LR)
        loss_fn = nn.BCELoss()

        print("🚀 Training started...")

        for epoch in range(EPOCHS):
            losses = []

            for xb, yb in loader:
                xb, yb = xb.to(device), yb.to(device)

                pred = model(xb)
                loss = loss_fn(pred, yb)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                losses.append(loss.item())

            print(f"Epoch {epoch+1} | Loss: {np.mean(losses):.4f}")

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        torch.save(model.state_dict(), self.model_path)

        return model

    # ----------------------------
    # RUN
    # ----------------------------
    def run(self):

        df = self.load_data()
        df = self.create_targets(df)

        X, y, scaler, features = self.build_sequences(df)
        X_train, X_val, y_train, y_val = self.split(X, y)

        self.train(X_train, y_train)

        print("✔ Training Complete")


if __name__ == "__main__":
    ForecastEngine().run()