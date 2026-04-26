import cv2
import joblib
import numpy as np
from collections import deque, Counter
from game.gestures import HandTracker
from game.camera import CameraFeed

# 定義標籤對應的名稱
LABEL_NAMES = {
    0: "Sword (0)",
    1: "Fist (1)",
    2: "Stop (2)",
    3: "Speed Up (3)",
    4: "Skill (4)"
}

# 顏色對應（BGR）
LABEL_COLORS = {
    0: (0, 200, 255),    # 橘黃 = Sword
    1: (0, 255, 120),    # 綠   = Fist
    2: (200, 200, 200),  # 灰   = Stop
    3: (255, 100, 0),    # 藍   = Speed Up
    4: (200, 0, 255),    # 紫   = Skill
}

# 時間平滑的緩衝幀數（越大越穩定但反應越慢）
SMOOTH_WINDOW = 10

def test_realtime():
    print("載入模型中...")
    try:
        model = joblib.load("assets/models/gesture_classifier.pkl")
    except FileNotFoundError:
        print("錯誤：找不到模型檔案，請先確認已經執行過訓練腳本！")
        return

    tracker = HandTracker()
    camera = CameraFeed(640, 480)

    # 滑動視窗：儲存最近 SMOOTH_WINDOW 幀的原始預測
    prediction_buffer = deque(maxlen=SMOOTH_WINDOW)

    print(f"開始即時測試！時間平滑視窗: {SMOOTH_WINDOW} 幀 (按 Esc 鍵離開)")

    running = True
    while running:
        rgb = camera.read_rgb()
        if rgb is None: continue

        gesture = tracker.process(rgb, (640, 480))

        # 準備要顯示的影像
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        if gesture.tracking_points:
            # 計算相對座標 + 正規化
            wrist = gesture.tracking_points[0]
            features = []
            for pt in gesture.tracking_points:
                features.extend([pt[0] - wrist[0], pt[1] - wrist[1]])
            max_val = max(abs(f) for f in features) if features else 1.0
            if max_val == 0: max_val = 1.0
            features = [f / max_val for f in features]
            features_array = np.array(features).reshape(1, -1)

            # 原始預測（每幀）
            raw_pred = model.predict(features_array)[0]
            prediction_buffer.append(raw_pred)

            # 時間平滑：用滑動視窗的多數決 (majority vote)
            vote_counts = Counter(prediction_buffer)
            smooth_pred = vote_counts.most_common(1)[0][0]

            # 計算信心度（當前手勢在視窗中佔幾 %）
            confidence = vote_counts[smooth_pred] / len(prediction_buffer)

            label_name = LABEL_NAMES.get(smooth_pred, "Unknown")
            color = LABEL_COLORS.get(smooth_pred, (255, 255, 255))

            # 顯示主要結果
            cv2.putText(bgr, f"Gesture: {label_name}", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3, cv2.LINE_AA)

            # 顯示信心度條
            bar_x, bar_y, bar_w, bar_h = 10, 65, 300, 18
            cv2.rectangle(bgr, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (60, 60, 60), -1)
            cv2.rectangle(bgr, (bar_x, bar_y), (bar_x + int(bar_w * confidence), bar_y + bar_h), color, -1)
            cv2.putText(bgr, f"Smoothed confidence: {confidence*100:.0f}%", (bar_x, bar_y + bar_h + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA)

            # 右上顯示原始每幀預測（debug 用）
            raw_name = LABEL_NAMES.get(raw_pred, "?")
            cv2.putText(bgr, f"Raw: {raw_name}", (bgr.shape[1] - 200, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1, cv2.LINE_AA)
        else:
            prediction_buffer.clear()
            cv2.putText(bgr, "No Hand Detected", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        cv2.imshow("Real-time Model Test (Press Esc to quit)", bgr)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            running = False

    camera.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_realtime()
