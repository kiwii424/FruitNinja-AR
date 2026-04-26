 import cv2
import csv
import os
import pygame
from game.gestures import HandTracker
from game.camera import CameraFeed

# 定義我們要收集的手勢標籤
# 0: SWORD, 1: FIST, 2: STOP, 3: SPEED_UP, 4: SKILL
LABELS = {
    pygame.K_0: 0, pygame.K_1: 1, pygame.K_2: 2, 
    pygame.K_3: 3, pygame.K_4: 4
}

def collect():
    pygame.init()
    tracker = HandTracker()
    camera = CameraFeed(640, 480)
    
    # 建立 CSV 檔案
    csv_path = "data/gesture_data.csv"
    os.makedirs("data", exist_ok=True)
    
    print("開始採集！請對著鏡頭比手勢，並按住鍵盤數字鍵錄製：")
    print("0: 切 (Sword), 1: 抓 (Fist), 2: 停 (Stop), 3: 加速, 4: 技能")

    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        running = True
        while running:
            rgb = camera.read_rgb()
            if rgb is None: continue
            
            gesture = tracker.update(rgb)
            
            # 取得 MediaPipe 的原始 Landmarks (這部分需要修改 gestures.py 暴露出來)
            # 這裡假設我們暫時直接調用 tracker 的內部結果
            if gesture.tracking_points:
                keys = pygame.key.get_pressed()
                for key, label in LABELS.items():
                    if keys[key]:
                        # 儲存標籤 + 21 個點的 (x, y) 座標
                        # 建議存相對座標：所有點減去手腕(第0點)
                        wrist = gesture.tracking_points[0]
                        row = [label]
                        for pt in gesture.tracking_points:
                            row.extend([pt[0] - wrist[0], pt[1] - wrist[1]])
                        writer.writerow(row)
                        print(f"已記錄標籤 {label}", end="\r")

            # 顯示畫面方便預覽
            cv2.imshow("Data Collection (Press Esc to quit)", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
            if cv2.waitKey(1) & 0xFF == 27: running = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False

    camera.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    collect()