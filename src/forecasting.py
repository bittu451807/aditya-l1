import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix

LOOKBACK = 30
BATCH_SIZE = 256
EPOCHS = 10 
LR = 0.001

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class SolarDataset(Dataset):
    def __init__(self, X, y):
        self.X = X
        self.y = y

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return (
            torch.tensor(self.X[idx], dtype=torch.float32),
            torch.tensor(self.y[idx], dtype=torch.long)
        )

# 🚀 HACKATHON WINNER BACKEND: ATTENTION-ENHANCED GRU
class AttentionGRU(nn.Module):
    def __init__(self, input_size, hidden_dim=64, num_classes=4):
        super(AttentionGRU, self).__init__()
        self.hidden_dim = hidden_dim
        self.gru = nn.GRU(input_size=input_size, hidden_size=hidden_dim, 
                          num_layers=2, batch_first=True, dropout=0.3)
        self.attention_weights = nn.Linear(hidden_dim, 1)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, num_classes)
        )

    def forward(self, x):
        gru_out, _ = self.gru(x)
        attention_scores = self.attention_weights(gru_out) 
        attention_weights = F.softmax(attention_scores, dim=1) 
        context_vector = torch.sum(attention_weights * gru_out, dim=1) 
        return self.fc(context_vector)

class ForecastEngine:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.dirname(__file__))
        self.data_path = os.path.join(self.BASE_DIR, "outputs", "clean_data.parquet")
        self.model_path = os.path.join(self.BASE_DIR, "models", "activity_model.pth")

    def load_data(self):
        df = pd.read_parquet(self.data_path)
        return df.iloc[:300000].reset_index(drop=True)

    def create_targets(self, df):
        df = df.copy()
        df["target"] = df["activity_level"].shift(-15).fillna(0).astype(int)
        return df

    def build_sequences(self, df):
        feature_cols = [c for c in df.columns if c not in ["time", "target"]]
        X_raw = df[feature_cols].fillna(0).values
        y_raw = df["target"].values

        split_idx = int(len(df) * 0.8)
        X_raw_train, X_raw_val = X_raw[:split_idx], X_raw[split_idx:]
        y_train_raw, y_val_raw = y_raw[:split_idx], y_raw[split_idx:]
        
        scaler = StandardScaler()
        X_scaled_train = scaler.fit_transform(X_raw_train)
        X_scaled_val = scaler.transform(X_raw_val)
        
        X_train, y_train = [], []
        for i in range(LOOKBACK, len(X_scaled_train), 3):
            X_train.append(X_scaled_train[i-LOOKBACK:i])
            y_train.append(y_train_raw[i])
            
        X_val, y_val = [], []
        for i in range(LOOKBACK, len(X_scaled_val), 3):
            X_val.append(X_scaled_val[i-LOOKBACK:i])
            y_val.append(y_val_raw[i])

        return np.array(X_train), np.array(X_val), np.array(y_train), np.array(y_val), feature_cols

    def train_model(self, X_train, y_train, X_val, y_val):
        loader = DataLoader(SolarDataset(X_train, y_train), batch_size=BATCH_SIZE, shuffle=True)
        val_loader = DataLoader(SolarDataset(X_val, y_val), batch_size=BATCH_SIZE, shuffle=False)
        
        model = AttentionGRU(input_size=X_train.shape[2], num_classes=4).to(device)
        
        class_counts = np.bincount(y_train, minlength=4)
        class_counts = np.where(class_counts == 0, 1, class_counts)
        weights = len(y_train) / (4.0 * class_counts)
        class_weights = torch.tensor(weights, dtype=torch.float32).to(device)
        
        criterion = nn.CrossEntropyLoss(weight=class_weights)
        optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)

        print("🔮 Optimizing Advanced Attention-GRU Network...")
        best_tss = -1.0
        
        for epoch in range(EPOCHS):
            model.train()
            for xb, yb in loader:
                xb, yb = xb.to(device), yb.to(device)
                pred = model(xb)
                loss = criterion(pred, yb)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
            model.eval()
            all_preds, all_trues = [], []
            with torch.no_grad():
                for xb_val, yb_val in val_loader:
                    xb_val = xb_val.to(device)
                    preds = torch.argmax(model(xb_val), dim=1).cpu().numpy()
                    all_preds.extend(preds)
                    all_trues.extend(yb_val.numpy())
            
            y_true_bin = (np.array(all_trues) >= 2).astype(int)
            y_pred_bin = (np.array(all_preds) >= 2).astype(int)
            
            try:
                tn, fp, fn, tp = confusion_matrix(y_true_bin, y_pred_bin, labels=[0, 1]).ravel()
                tpr = tp / (tp + fn + 1e-9)
                fpr = fp / (fp + tn + 1e-9)
                tss = tpr - fpr
            except ValueError:
                tss = 0.0
                
            print(f"Epoch {epoch+1}/{EPOCHS} | Validation TSS: {tss:.4f} (TPR: {tpr:.2f}, FPR: {fpr:.2f})")
            
            if tss >= best_tss:
                best_tss = tss
                os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
                torch.save(model.state_dict(), self.model_path)

        print(f"✅ State-of-the-Art Attention-GRU saved. Best TSS: {best_tss:.4f}")
        return model

    def run(self):
        df = self.load_data()
        df = self.create_targets(df)
        X_train, X_val, y_train, y_val, features = self.build_sequences(df)
        self.train_model(X_train, y_train, X_val, y_val)

if __name__ == "__main__":
    ForecastEngine().run()
