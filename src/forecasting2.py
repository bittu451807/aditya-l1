import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler


LOOKBACK = 30
BATCH_SIZE = 256
EPOCHS = 8
LR = 0.001

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


class SolarDataset(Dataset):

    def __init__(self, X, y):

        self.X = X
        self.y = y

    def __len__(self):

        return len(self.X)

    def __getitem__(self, idx):

        return (
            torch.tensor(
                self.X[idx],
                dtype=torch.float32
            ),
            torch.tensor(
                self.y[idx],
                dtype=torch.long
            )
        )


class GRUClassifier(nn.Module):

    def __init__(
        self,
        input_size,
        num_classes=4
    ):

        super().__init__()

        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=64,
            num_layers=2,
            batch_first=True,
            dropout=0.2
        )

        self.fc = nn.Sequential(

            nn.Linear(
                64,
                32
            ),

            nn.ReLU(),

            nn.Dropout(
                0.2
            ),

            nn.Linear(
                32,
                num_classes
            )
        )

    def forward(
        self,
        x
    ):

        out, _ = self.gru(x)

        out = out[:, -1, :]

        return self.fc(out)


class ForecastEngine:

    def __init__(self):

        self.BASE_DIR = os.path.dirname(
            os.path.dirname(__file__)
        )

        self.data_path = os.path.join(
            self.BASE_DIR,
            "outputs",
            "clean_data.parquet"
        )

        self.model_path = os.path.join(
            self.BASE_DIR,
            "models",
            "activity_model.pth"
        )

    def load_data(self):

        df = pd.read_parquet(
            self.data_path
        )

        df = df.iloc[::5].reset_index(
            drop=True
        )

        df = df.iloc[:300000]

        return df

    def create_targets(
        self,
        df
    ):

        df = df.copy()

        df["target"] = (
            df["activity_level"]
            .shift(-15)
            .fillna(0)
            .astype(int)
        )

        return df

    def build_sequences(
        self,
        df
    ):

        feature_cols = [

            c

            for c in df.columns

            if c not in [

                "time",
                "target"
            ]
        ]

        scaler = StandardScaler()

        X_data = scaler.fit_transform(

            df[
                feature_cols
            ].fillna(0)
        )

        y_data = df[
            "target"
        ].values

        X = []
        y = []

        for i in range(

            LOOKBACK,
            len(df),
            3
        ):

            X.append(

                X_data[
                    i-LOOKBACK:i
                ]
            )

            y.append(
                y_data[i]
            )

        return (

            np.array(X),

            np.array(y),

            feature_cols
        )

    def split(
        self,
        X,
        y
    ):

        split = int(
            len(X) * 0.8
        )

        return (

            X[:split],

            X[split:],

            y[:split],

            y[split:]
        )

    def train_model(

        self,

        X_train,

        y_train
    ):

        loader = DataLoader(

            SolarDataset(
                X_train,
                y_train
            ),

            batch_size=BATCH_SIZE,

            shuffle=True
        )

        model = GRUClassifier(

            X_train.shape[2]

        ).to(device)

        criterion = nn.CrossEntropyLoss()

        optimizer = torch.optim.Adam(

            model.parameters(),

            lr=LR
        )

        print(
            "Training..."
        )

        for epoch in range(
            EPOCHS
        ):

            losses = []

            model.train()

            for xb, yb in loader:

                xb = xb.to(device)

                yb = yb.to(device)

                pred = model(xb)

                loss = criterion(
                    pred,
                    yb
                )

                optimizer.zero_grad()

                loss.backward()

                optimizer.step()

                losses.append(
                    loss.item()
                )

            print(

                f"Epoch {epoch+1}"

                f" Loss {np.mean(losses):.4f}"
            )

        os.makedirs(

            os.path.dirname(
                self.model_path
            ),

            exist_ok=True
        )

        torch.save(

            model.state_dict(),

            self.model_path
        )

        print(
            "Model Saved"
        )

        return model

    def run(self):

        print(
            "Loading..."
        )

        df = self.load_data()

        df = self.create_targets(
            df
        )

        X, y, features = (

            self.build_sequences(
                df
            )
        )

        X_train, X_val, y_train, y_val = (

            self.split(
                X,
                y
            )
        )

        self.train_model(

            X_train,

            y_train
        )

        print()

        print(
            "Training Complete"
        )

        print(
            "Model:",
            self.model_path
        )


if __name__ == "__main__":

    ForecastEngine().run()
