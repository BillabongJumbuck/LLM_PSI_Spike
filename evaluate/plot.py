import matplotlib.pyplot as plt
import pandas as pd

# 读取CSV文件
df_predict = pd.read_csv("../data/predict/psi_douyin_20260301_213426_predict.csv")
df_raw = pd.read_csv("../data/processed/psi_douyin_20260301_213426_processed.csv")

# 将df_predict按window_index排序
df_predict = df_predict.sort_values(by="window_index").reset_index(drop=True)

print("预测结果预览:")
print(df_predict.head(80))
