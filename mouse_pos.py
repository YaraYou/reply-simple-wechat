import pyautogui
import time

print("鼠标位置实时显示（按 Ctrl+C 退出）")
try:
    while True:
        x, y = pyautogui.position()
        print(f"({x}, {y})", end='\r')
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n已退出")