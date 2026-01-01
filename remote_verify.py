
import requests
import json
import base64
import os
import uuid
import time
from PIL import Image
import io

# 核心：直接测试公网服务器！
BASE_URL = "https://nbfive.com"

# 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def print_pass(msg):
    print(f"{GREEN}[PASS] {msg}{RESET}")

def print_fail(msg):
    print(f"{RED}[FAIL] {msg}{RESET}")

# 1. 准备测试数据
def create_test_image():
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return base64.b64encode(img_byte_arr).decode('utf-8')

TEST_IMAGE_B64 = create_test_image()

def run_regression_test():
    print(f"🚀 Starting Remote Regression Test against: {BASE_URL}")
    print("This mimics a REAL user accessing the website.\n")
    
    session = requests.Session()
    
    # 2. 检测服务器是否存活
    try:
        resp = session.get(f"{BASE_URL}/")
        if resp.status_code == 200:
            print_pass("Server is reachable (HTTP 200)")
        else:
            print_fail(f"Server returned {resp.status_code}")
            return
    except Exception as e:
        print_fail(f"Could not connect to server: {e}")
        return

    # 3. 注册新用户 (保证是最新的逻辑)
    unique_id = uuid.uuid4().hex[:6]
    email = f"qa_robot_{unique_id}@test.com"
    password = "qa_password_123"
    
    print(f"\n--- Testing Auth Flow (User: {email}) ---")
    try:
        reg_resp = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": password,
            "name": "QA Robot"
        })
        
        token = ""
        if reg_resp.status_code in [200, 201]:
            data = reg_resp.json()
            token = data.get('token')
            print_pass("Registration successful")
        else:
            print_fail(f"Registration failed: {reg_resp.text}")
            return
            
    except Exception as e:
        print_fail(f"Auth Exception: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    # 4. 测试关键工具 (Regression Check)
    # 尽可能覆盖 sk_app.py 中定义的所有功能
    tools_to_test = [
        ("Background Remover", "/api/tools/remove-background", {"image": f"data:image/png;base64,{TEST_IMAGE_B64}"}),
        ("Keyword Analyzer", "/api/tools/keyword-analyzer", {"product_description": "wireless earbuds", "platform": "amazon", "action": "extract"}),
        ("Currency Converter", "/api/tools/currency-converter", {"amount": 100, "from_currency": "USD", "to_currency": "CNY"}),
        ("Unit Converter", "/api/tools/unit-converter", {"value": 100, "from_unit": "kg", "to_unit": "lb", "category": "weight"}),
        ("Shipping Calculator", "/api/tools/shipping-calculator", {"weight": 2.5, "length": 10, "width": 10, "height": 10, "dim_unit": "cm", "weight_unit": "kg"}),
        ("Add Watermark", "/api/tools/add-watermark-v2", {
            "image": f"data:image/png;base64,{TEST_IMAGE_B64}", 
            "watermark_text": "NBFive QA", 
            "watermark_position": "bottom-right",
            "opacity": 0.5
        }),
        ("Image Compressor", "/api/tools/image-compressor", {"image": f"data:image/png;base64,{TEST_IMAGE_B64}", "quality": 80}),
        ("Image Rotate/Flip", "/api/tools/rotate-flip", {"image": f"data:image/png;base64,{TEST_IMAGE_B64}", "operation": "rotate_90_cw"}),
        ("Listing Generator", "/api/tools/generate-listing", {"product_info": "Magic Brush", "platform": "amazon"}),
        ("Email Sharing", "/api/tools/send-email", {"to": "test@test.com", "subject": "Test Result", "body": "Test successful"})
    ]
    
    for name, endpoint, payload in tools_to_test:
        print(f"\n--- Testing {name} ---")
        try:
            start_time = time.time()
            resp = session.post(f"{BASE_URL}{endpoint}", json=payload, headers=headers)
            duration = time.time() - start_time
            
            if resp.status_code == 200:
                print_pass(f"{name} worked in {duration:.2f}s")
            else:
                print_fail(f"{name} failed ({resp.status_code}): {resp.text[:100]}")
        except Exception as e:
            print_fail(f"{name} Exception: {e}")

    print("\n------------------------------------------------")
    print("🎉 Regression Test Complete.")
    print("If you see any RED lines, DO NOT DEPLOY.")

if __name__ == "__main__":
    run_regression_test()
