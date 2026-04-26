import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import joblib

# 1. 讀取數據
df = pd.read_csv("data/gesture_data.csv", header=None)
X = df.iloc[:, 1:]  # 座標特徵 (42 個值)
y = df.iloc[:, 0]   # 標籤

# 2. 分割數據 (80% 訓練, 20% 測試)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. 訓練模型
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# 4. 評估與圖表
y_pred = model.predict(X_test)
score = model.score(X_test, y_test)
print(f"=== 模型測試結果 ===")
print(f"測試集準確率 (Accuracy): {score * 100:.2f}%\n")
print("詳細分類報告 (Classification Report):")
print(classification_report(y_test, y_pred))

# 繪製混淆矩陣
cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=model.classes_)
fig, ax = plt.subplots(figsize=(8, 6))
disp.plot(cmap=plt.cm.Blues, ax=ax)
plt.title("Gesture Classification Confusion Matrix")

# 儲存圖表
chart_path = "data/confusion_matrix.png"
plt.savefig(chart_path)
print(f"已成功將混淆矩陣圖表儲存至：{chart_path}")

# 5. 儲存模型
joblib.dump(model, "assets/models/gesture_classifier.pkl")