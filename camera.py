from picamera2 import Picamera2
import time
from PIL import Image  # Add this import
from gtts import gTTS
import os
import base64
import json
import asyncio
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI
from openai import AsyncAzureOpenAI, AsyncOpenAI
# 初始化相機

load_dotenv(override=True)
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
RESOURCE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

azure_client = AzureOpenAI(
    api_key=API_KEY,
    api_version="2024-09-01-preview",
    azure_endpoint=RESOURCE_ENDPOINT
)
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

async_azure_client = AsyncAzureOpenAI(
    api_key=API_KEY,
    api_version="2024-09-01-preview",
    azure_endpoint=RESOURCE_ENDPOINT
)
async_openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Synchronous request functions (unchanged for reference)
def gpt4o_request(messages):
    """Send a request to the GPT-4o model and return the response content."""
    try:
        response = azure_client.chat.completions.create(
            model="gpt4o",
            messages=messages
        )
        return response.choices[0].message.content
    except:
        return "error"

def o1_request(messages):
    """Send a request to the O1 model and return the response content."""
    try:
        response = openai_client.chat.completions.create(
            model="o1",
            messages=messages
        )
        return response.choices[0].message.content
    except:
        return "error"

def json_request(messages):
    """Send a request and return the response content in JSON format."""
    response = azure_client.chat.completions.create(
        model="gpt4o",
        messages=messages,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# Asynchronous request functions
async def async_gpt4o_request(messages):
    """Send an asynchronous request to the GPT-4o model and return the response content."""
    try:
        response = await async_azure_client.chat.completions.create(
            model="gpt4o",
            messages=messages
        )
        return response.choices[0].message.content
    except:
        return "error"

async def async_o1_request(messages):
    """Send an asynchronous request to the O1 model and return the response content."""
    try:
        response = await async_openai_client.chat.completions.create(
            model="o1",
            messages=messages
        )
        return response.choices[0].message.content
    except:
        return "error"

async def async_json_request(messages):
    """Send an asynchronous request and return the response content in JSON format."""
    try:
        response = await async_azure_client.chat.completions.create(
            model="gpt4o",
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except:
        return {"error": "An error occurred"}

class ExamProcessor:
    def __init__(self):
        """Initialize ExamProcessor with default prompt and state."""
        self.class_prompt = "這是單選題 只有一個正確答案 只要回答我答案選項12345就好 不用答案内容"
        self.mixd = False
        self.bad_set = None
        self.bad_img = None
        self.bad_changed_class = None

    async def img_number(self, img):
        """Extract question numbers and sets from an image asynchronously."""
        prompt = """
        1.請忽略題目内容 列出本圖片中有題號且出現的獨立題目的題號，或是題組中在本圖片中出現的題目，但不包含題組中未在圖片中出現的題目。最後輸出一個題號list:"number":[int]
        2.假如看到紙上有寫 "xx-xx題為題組"（xx是一個整數 可能是個位數或十位數）列出題組的題號(xx-xx中的所有數字) 給我一個"set"list 告訴我幾到幾題為題組 假如沒有題組就給我一個空list
        3.注意1.和2.是互相獨立的任務
        4.有可能set不完全在number中 但set中至少有一題在number中
        Use JSON with keys: "set":[int],"number":[int]
        Example of a valid JSON response:
        {
            "set":[2,3],
            "number":[1,2,3,4]
        }
        """
        msgs = [
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}", "detail": "high"}}]},
            {"role": "user", "content": prompt}
        ]
        return await async_json_request(msgs)

    async def img_change(self, img):
        """Detect question type changes and starting number asynchronously."""
        prompt = """
        假如有粗體字寫題型和配分 比如："一、單選題（占xx分）" , "二、多選題（占xx分）" , "第貳部分、混合題或非選擇題（占xx分）"
        請在json response中寫新題型和新題型的第一題的題號入比如:{"class":"單選題","n":4} 題型可能是"單選題" "多選題" "選填題" "混合題"(混合題或非選擇題) 之一
        若沒有有粗體字寫題型和配分 則 {"class":"無","n":0}

        Use JSON with keys: "class":str,"n":int
        Example of a valid JSON response:
        {
            "class": "",(value = "單選題" or "多選題" or "填充題" or "混合題" or "無")
            "n": 4
        }
        """
        msgs = [
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}", "detail": "high"}}]},
            {"role": "user", "content": prompt}
        ]
        return await async_json_request(msgs)

    async def img_ans(self, imgs, prompt):
        """Generate answers for questions or sets using one or more images asynchronously."""
        # Placeholder implementation; replace with actual AI model call
        print(prompt)
        return "skip"
        # Uncomment and adjust for actual implementation:
        # msgs = [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}", "detail": "high"}} for img in imgs]},
        #         {"role": "user", "content": prompt}]
        # return await async_gpt4o_request(msgs)

    def class_match(self, class_type):
        """Map question type to the corresponding prompt."""
        match class_type:
            case "單選題":
                return "這是單選題 只有一個正確答案 只要回答我答案選項12345就好 不用答案内容"
            case "多選題":
                return "這是多選題 可能有多個正確答案 只要回答我答案選項12345就好 不用答案内容 請用list回答"
            case "選填題":
                return "這是選填題 只要回答我答案就好 請用latex回答"
            case "混合題":
                self.mixd = True
                return ("這是混合題 可能是 單選題（只要回答我答案就好） "
                        "多選題（用list回答 只要回答我答案就好） "
                        "填充題（用latex回答 只要回答我答案就好） "
                        "非選擇題（用latex回答 給我最簡計算過程）")
        return self.class_prompt  # Default fallback

    async def process_block(self, imgs, block, changed_class):
        start_n = block[0]
        # Update prompt if there’s a type change and not in mixed mode
        if start_n == changed_class["n"] and not self.mixd and changed_class["class"] != "無":
            self.class_prompt = self.class_match(changed_class["class"])

        if len(block) == 1:
            prompt = f"請回答第{block[0]}題 並忽略其他所有題目，{self.class_prompt}"
        else:
            prompt = f"請回答第{block}題 並忽略其他所有題目，{self.class_prompt}"
        
        answer = await self.img_ans(imgs, prompt)
        return f"第{block}題{answer}"

    async def process_bad_set(self, img1, img2, set_list, changed_class):
        for n in set_list:
            if n == changed_class["n"] and changed_class["class"] != "無":
                self.class_prompt = self.class_match(changed_class["class"])
        
        prompt = f"請回答第{set_list}題 並忽略其他所有題目，{self.class_prompt}"
        answer = await self.img_ans([img1, img2], prompt)
        return f"第{set_list}題{answer}"

    async def main(self, path):
        with open(path, "rb") as image_file:
            img = base64.b64encode(image_file.read()).decode('utf-8')

        # Run img_number and img_change concurrently
        reply_number, reply_change = await asyncio.gather(
            self.img_number(img),
            self.img_change(img)
        )

        # Voice prompt for detected questions and sets
        if reply_number.get("error"):
            speak_text("獲取題目數量失敗")
        else:
            number = reply_number.get("number", [])
            set_list = reply_number.get("set", [])

            message = f"拍到 {number} 題"
            if set_list:
                message += f"，題組為第 {', '.join(map(str, set_list))} 題"
            else:
                message += "，沒有題組"
            speak_text(message)
            # Ensure number and set_list are available for subsequent logic even if initially empty
            number = reply_number.get("number", [])
            set_list = reply_number.get("set", [])


        # Voice prompt for question type change
        if reply_change.get("error"):
            speak_text("獲取題型變換失敗")
        elif reply_change.get("class") and reply_change["class"] != "無":
            class_type = reply_change["class"]
            start_num = reply_change["n"]
            
            speak_text(f"題型變換為 {class_type}，從第 {start_num} 題開始")

        # Ensure number and set_list are from the successful reply_number if no error
        if not reply_number.get("error"):
            number = reply_number.get("number", [])
            set_list = reply_number.get("set", [])
        else: # Fallback to empty lists if there was an error
            number = []
            set_list = []


        # 如果前一張圖片有跨頁的題組，先處理並 yield 結果
        if self.bad_set is not None:
            result = await self.process_bad_set(self.bad_img, img, self.bad_set, self.bad_changed_class)
            yield result
            # Exclude bad set questions from current processing
            number = [n for n in number if n not in self.bad_set]
            self.bad_set = None
            self.bad_img = None
            self.bad_changed_class = None

        # Determine blocks to process in the current image
        if set_list and not set(set_list).issubset(set(number)):
            # Set spans to the next image (bad set)
            self.bad_set = set_list
            self.bad_img = img
            self.bad_changed_class = reply_change
            blocks = [[n] for n in number if n not in set_list]
        else:
            # Normal case: set is fully contained or no set
            if set_list:
                blocks = [[n] for n in number if n not in set_list] + [set_list]
            else:
                blocks = [[n] for n in number]

        # Process all blocks concurrently and yield each result as完成
        tasks = [self.process_block([img], block, reply_change) for block in blocks]
        for coro in asyncio.as_completed(tasks):
            result = await coro
            yield result


# Initialize ExamProcessor
processor = ExamProcessor()
# Function to use Google Text-to-Speech
def speak_text(text, lang='zh-TW', slow=False):
    try:
        tts = gTTS(text=text, lang=lang, slow=slow)
        temp_filename = "temp_speech.mp3"
        tts.save(temp_filename)
        os.system(f"mpg321 {temp_filename}")
        # Clean up the temporary file
        try:
            os.remove(temp_filename)
        except:
            pass
        return True
    except Exception as e:
        print(f"TTS Error: {e}")
        return False

camera = Picamera2()
camera_config = camera.create_still_configuration()
camera.configure(camera_config)
camera.set_controls({"AfMode": 2,"AeEnable": True, "AwbEnable": True})

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
    speak_text("拍照成功") # Voice prompt for successful photo capture

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
            speak_text(result) # This already handles speaking the answer


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