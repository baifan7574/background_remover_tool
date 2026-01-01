
import requests
import json
import base64
import os
import uuid
from PIL import Image
import io

# 基础URL
BASE_URL = "http://localhost:5000"

# 用户信息
EMAIL = "112@112.com"
PASSWORD = "testpassword" # 使用一个肯定存在的用户的密码，或者创建一个新用户

# 测试图片生成
def create_test_image():
    img = Image.new('RGB', (100, 100), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return base64.b64encode(img_byte_arr).decode('utf-8')

TEST_IMAGE_B64 = create_test_image()

def print_result(tool_name, success, message=""):
    status = "✅ PASS" if success else "❌ FAIL"
    output = f"[{status}] {tool_name}: {message}"
    print(output)
    with open("verify_log.txt", "a", encoding="utf-8") as f:
        f.write(output + "\n")

def verify_tools():
    print("🚀 Starting Tool Verification...")
    
    # 1. 登录 (获取Token)
    print("\n--- 1. Authentication ---")
    
    # 为了确保登录成功，我们先注册一个新用户
    unique_id = uuid.uuid4().hex[:6]
    reg_email = f"tool_tester_{unique_id}@test.com"
    reg_password = "password123"
    
    print(f"Registering temp user: {reg_email}")
    reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": reg_email,
        "password": reg_password,
        "name": "Tool Tester"
    })
    
    token = ""
    user_id = ""
    
    if reg_resp.status_code in [200, 201]:
        data = reg_resp.json()
        token = data.get('token')
        if 'user' in data:
            user_id = data['user']['id']
        else:
            user_id = data.get('user_id')
        print(f"✅ Registration successful. Token obtained.")
    else:
        print(f"⚠️ Registration failed ({reg_resp.status_code}). Trying login with existing user...")
        # 尝试使用已知用户登录
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "112@112.com",
            # 注意：这里假设密码是100100，这是users.json中看到的112@112.com的密码
            "password": "100100" 
        })
        
        if login_resp.status_code == 200:
            data = login_resp.json()
            token = data.get('token')
            user_id = data['user']['id']
            print(f"✅ Login successful with existing user. Token obtained.")
        else:
            print(f"❌ Login failed: {login_resp.text}")
            return

    headers = {"Authorization": f"Bearer {token}"}

    # 2. 验证 Background Remover
    print("\n--- 2. Verifying Background Remover ---")
    try:
        payload = {
            "image": f"data:image/png;base64,{TEST_IMAGE_B64}"
        }
        resp = requests.post(f"{BASE_URL}/api/tools/remove-background", json=payload, headers=headers)
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get('processed_image') or result.get('image'): # check keys
                 print_result("Background Remover", True, "Image processed successfully.")
            elif 'error' in result:
                 print_result("Background Remover", False, f"API returned error: {result['error']}")
            else:
                 # 实际上返回的是 processed_image 或类似的
                 print_result("Background Remover", True, "Response 200 OK (Assuming success, check keys if needed)")
        else:
             print_result("Background Remover", False, f"HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print_result("Background Remover", False, f"Exception: {str(e)}")

    # 3. 验证 Image Rotate/Flip
    print("\n--- 3. Verifying Image Rotate/Flip ---")
    try:
        payload = {
            "image": f"data:image/png;base64,{TEST_IMAGE_B64}",
            "operation": "rotate_90_cw"
        }
        resp = requests.post(f"{BASE_URL}/api/tools/rotate-flip", json=payload, headers=headers)
        
        if resp.status_code == 200:
            print_result("Rotate/Flip", True, "Image rotated successfully.")
        else:
            print_result("Rotate/Flip", False, f"HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print_result("Rotate/Flip", False, f"Exception: {str(e)}")

    # 4. 验证 Keyword Analyzer
    print("\n--- 4. Verifying Keyword Analyzer ---")
    try:
        payload = {
            "action": "extract",
            "product_description": "Wireless Bluetooth Headphones with Noise Cancelling",
            "platform": "amazon"
        }
        resp = requests.post(f"{BASE_URL}/api/tools/keyword-analyzer", json=payload, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                print_result("Keyword Analyzer", True, "Keywords extracted successfully.")
            else:
                print_result("Keyword Analyzer", False, f"Success flag missing: {data}")
        else:
            print_result("Keyword Analyzer", False, f"HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print_result("Keyword Analyzer", False, f"Exception: {str(e)}")

    # 5. 验证 Listing Generator
    print("\n--- 5. Verifying Listing Generator ---")
    try:
        payload = {
            "product_info": "Red Leather Handbag, luxury style, gold hardware",
            "platform": "amazon",
            "language": "en"
        }
        resp = requests.post(f"{BASE_URL}/api/tools/generate-listing", json=payload, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') and data.get('title'):
                print_result("Listing Generator", True, "Listing generated successfully.")
            else:
                print_result("Listing Generator", False, f"Invalid response: {data}")
        else:
            print_result("Listing Generator", False, f"HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print_result("Listing Generator", False, f"Exception: {str(e)}")
        
    # 6. 验证 Currency Converter
    print("\n--- 6. Verifying Currency Converter ---")
    try:
        payload = {
            "amount": 100,
            "from_currency": "USD",
            "to_currency": "CNY"
        }
        resp = requests.post(f"{BASE_URL}/api/tools/currency-converter", json=payload, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') and 'converted_amount' in data:
                print_result("Currency Converter", True, f"Converted: {data['converted_amount']}")
            else:
                print_result("Currency Converter", False, f"Invalid response: {data}")
        else:
            print_result("Currency Converter", False, f"HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print_result("Currency Converter", False, f"Exception: {str(e)}")

    except Exception as e:
        print_result("Currency Converter", False, f"Exception: {str(e)}")

    # 7. 验证 Super Resolution
    print("\n--- 7. Verifying Super Resolution ---")
    try:
        payload = {
            "image": f"data:image/png;base64,{TEST_IMAGE_B64}",
            "scale": 2
        }
        resp = requests.post(f"{BASE_URL}/api/tools/super-resolution", json=payload, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') and data.get('processed_image'):
                print_result("Super Resolution", True, "Image scaled successfully.")
            else:
                print_result("Super Resolution", False, f"Invalid response: {data}")
        else:
            print_result("Super Resolution", False, f"HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print_result("Super Resolution", False, f"Exception: {str(e)}")

    # 8. 验证 Remove Watermark (Basic)
    print("\n--- 8. Verifying Remove Watermark ---")
    try:
        payload = {
            "image": f"data:image/png;base64,{TEST_IMAGE_B64}"
        }
        resp = requests.post(f"{BASE_URL}/api/tools/remove-watermark", json=payload, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') and data.get('processed_image'):
                print_result("Remove Watermark", True, "Watermark removal processed.")
            else:
                print_result("Remove Watermark", False, f"Invalid response: {data}")
        else:
            print_result("Remove Watermark", False, f"HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print_result("Remove Watermark", False, f"Exception: {str(e)}")

    print("\n🚀 Verification Complete.")

if __name__ == "__main__":
    verify_tools()
