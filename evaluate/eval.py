import pandas as pd
from sklearn.metrics import (
    confusion_matrix, 
    accuracy_score, 
    precision_score, 
    recall_score, 
    f1_score, 
    classification_report,
    roc_auc_score,
    average_precision_score
)

def calculate_metrics(csv_path):
    # 读取CSV文件
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {csv_path}")
        return
    
    # 确保必需的列存在
    if 'label' not in df.columns or 'prediction' not in df.columns:
        raise ValueError("CSV文件中必须包含 'label' 和 'prediction' 列")
        
    y_true = df['label']
    y_pred = df['prediction']
    
    # 计算混淆矩阵
    # confusion_matrix 针对二分类返回的结果扁平化后依次为: TN, FP, FN, TP
    # (假设你的数据标签是0和1)
    cm = confusion_matrix(y_true, y_pred)
    
    # 处理可能只有单一类别导致解包报错的特殊情况
    if cm.size == 4:
        tn, fp, fn, tp = cm.ravel()
    else:
        # 如果样本里全是对的预测，或者只有一个类别，混淆矩阵可能只有 1x1
        print("警告: 你的数据可能只有单一类别，混淆矩阵维度不足 2x2。")
        tn, fp, fn, tp = (cm[0][0], 0, 0, 0) if y_true.iloc[0] == 0 else (0, 0, 0, cm[0][0])
    
    # 计算核心指标
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    # 打印基础结果
    print("=" * 40)
    print("📊 混淆矩阵统计 (Confusion Matrix):")
    print(f" True Positives (TP) : {tp}")
    print(f" True Negatives (TN) : {tn}")
    print(f" False Positives (FP): {fp}")
    print(f" False Negatives (FN): {fn}")
    print("-" * 40)
    print("📈 基础评估指标 (Evaluation Metrics):")
    print(f" Accuracy  (准确率): {accuracy:.4f}")
    print(f" Precision (精确率): {precision:.4f}")
    print(f" Recall    (召回率): {recall:.4f}")
    print(f" F1 Score  (F1 值):  {f1:.4f}")
    print("=" * 40)
    
    # 打印其他重要的统计值：使用分类报告
    print("\n📑 详细分类报告 (Classification Report):")
    # classification_report 会列出每个类别的 precision, recall, f1-score 和 support（样本数）
    print(classification_report(y_true, y_pred, zero_division=0))
    
    # 在你的深度学习或机器学习项目中，ROC-AUC 也是评估分类器能力非常重要的指标
    try:
        roc_auc = roc_auc_score(y_true, y_pred)
        pr_auc = average_precision_score(y_true, y_pred)
        print(f"🚀 ROC AUC Score: {roc_auc:.4f}")
        print(f"🚀 PR AUC Score: {pr_auc:.4f}")
    except ValueError:
        print("🚀 ROC AUC Score: 无法计算 (数据中可能只包含一个类别，比如全为0)")

if __name__ == "__main__":
    # 替换为你实际存放数据的 CSV 文件路径
    # 如果你在 WSL 的 fish shell 里运行，确保路径对应正确
    csv_file_path = "../data/predict/psi_douyin_20260301_213426_predict.csv" 
    
    calculate_metrics(csv_file_path)