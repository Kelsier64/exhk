from picamera2 import Picamera2
import time
from img_processor import ExamProcessor
from PIL import Image  # Add this import

# 初始化相機
camera = Picamera2()
camera_config = camera.create_still_configuration()
camera.configure(camera_config)
camera.set_controls({"AfMode": 2,"AeEnable": True, "AwbEnable": True})

# Initialize ExamProcessor
processor = ExamProcessor()

# 修改 take_photo 函數，加入 img_processor 的處理邏輯
def take_photo():
    # 啟動相機
    camera.start()
    time.sleep(1)  # 給相機一點時間穩定

    # 拍攝照片並儲存
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.jpg"
    camera.capture_file(filename)
    print(f"照片已儲存: {filename}")

    # Rotate the image
    try:
        img = Image.open(filename)
        rotated_img = img.rotate(90, expand=True)
        rotated_img.save(filename)
        print(f"照片已向右旋轉90度: {filename}")
    except Exception as e:
        print(f"旋轉照片時發生錯誤: {e}")

    # 使用 ExamProcessor 處理拍攝的照片
    print("正在處理圖片...")
    async def process_image():
        async for result in processor.main(filename):
            print(result)

    import asyncio
    asyncio.run(process_image())

    # 停止相機
    camera.stop()

def main():
    print("相機程式已啟動")
    print("輸入 '1' 拍照，輸入 'q' 退出")

    while True:
        user_input = input("請輸入指令: ")

        if user_input == "1":
            take_photo()
        elif user_input == "q":
            print("程式結束")
            break
        else:
            print("無效指令，請輸入 '1' 拍照或 'q' 退出")

if __name__ == "__main__":
    main()