import matplotlib.pyplot as plt
import pandas as pd

# 中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为 SimHei
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 读取CSV文件
df_predict = pd.read_csv("../data/predict/psi_douyin_20260301_213426_predict.csv")
df_raw = pd.read_csv("../data/processed/psi_douyin_20260301_213426_processed.csv")

# 将df_predict按window_index排序
df_predict = df_predict.sort_values(by="window_index").reset_index(drop=True)

# 确保必需的列存在
if 'full_delta' not in df_raw.columns:
    raise ValueError("CSV文件中必须包含 'full_delta' 列")

# 2. 创建画布
# 设置一个较宽的比例，方便观察时间序列的趋势
plt.figure(figsize=(14, 6))

# 3. 绘制折线图
# 直接使用 DataFrame 的 index 作为 X 轴，代表采样步进
plt.plot(df_raw.index, df_raw['full_delta'], 
            color='#1f77b4',       # 曲线颜色
            linewidth=1.5,         # 线宽
            label='full_delta')

# 在纵轴20000处添加水平参考线，帮助观察数值变化
plt.axhline(y=20000, color='red', linestyle='--', linewidth=1, label='Spike 阈值 (20000)')

# 4. 图表装饰与排版
plt.xlabel('Sampling Steps (Index)', fontsize=12)
plt.ylabel('full_delta Value', fontsize=12)

# 添加网格线，方便对齐数值
plt.grid(True, linestyle='--', alpha=0.6) 
plt.legend(loc='upper right')

# 去除所有边框线，突出数据线条
plt.gca().spines['top'].set_visible(False)
plt.gca().spines['bottom'].set_visible(False)
plt.gca().spines['right'].set_visible(False)
plt.gca().spines['left'].set_visible(False)

# 去除左右留白，使图表更紧凑
plt.gca().margins(x=0, y=0)



# 5. 调整布局并保存
plt.tight_layout()

plt.show()

output_image = "./output/plot.svg"
plt.savefig(output_image, dpi=300)
print(f"✅ 图表已成功生成并保存至当前目录: {output_image}")

print("预测结果预览:")
print(df_predict.head(80))
