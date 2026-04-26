import cv2
import csv
import os
from game.gestures import HandTracker
from game.camera import CameraFeed

def collect():
    tracker = HandTracker()
    camera = CameraFeed(640, 480)
    
    # 建立 CSV 檔案
    csv_path = "data/gesture_data.csv"
    os.makedirs("data", exist_ok=True)
    
    print("開始採集！請對著鏡頭比手勢，確認畫面為選取狀態後按鍵盤數字鍵錄製：")
    print("0: 切 (Sword), 1: 抓 (Fist), 2: 停 (Stop), 3: 加速, 4: 技能")

    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        running = True
        while running:
            rgb = camera.read_rgb()
            if rgb is None: continue
            
            gesture = tracker.process(rgb, (640, 480))
            
            # 顯示畫面方便預覽
            cv2.imshow("Data Collection (Press Esc to quit)", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
            key = cv2.waitKey(1) & 0xFF
            if key == 27: 
                running = False
            
            if gesture.tracking_points:
                label = None
                if key == ord('0'): label = 0
                elif key == ord('1'): label = 1
                elif key == ord('2'): label = 2
                elif key == ord('3'): label = 3
                elif key == ord('4'): label = 4
                
                if label is not None:
                    # 儲存標籤 + 21 個點的 (x, y) 座標
                    # 建議存相對座標：所有點減去手腕(第0點)
                    wrist = gesture.tracking_points[0]
                    features = []
                    for pt in gesture.tracking_points:
                        features.extend([pt[0] - wrist[0], pt[1] - wrist[1]])
                    
                    # 正規化 (Normalization) - 消除手部距離鏡頭遠近的影響
                    max_val = max(abs(f) for f in features) if features else 1.0
                    if max_val == 0: max_val = 1.0
                    features = [f / max_val for f in features]
                    
                    row = [label] + features
                    writer.writerow(row)
                    print(f"已記錄標籤 {label}        ", end="\r")

    camera.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    collect()