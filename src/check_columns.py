import pandas as pd

df = pd.read_parquet("outputs/clean_data.parquet")

print(df.columns.tolist())
print(df["activity_level"].value_counts())
