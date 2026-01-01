
import requests
import json
import time
import os
import uuid


BASE_URL = "http://127.0.0.1:5000"
ORDERS_FILE = os.path.join("data", "orders.json")

def print_step(step):
    print(f"\n{'='*50}", flush=True)
    print(f"STEP: {step}", flush=True)
    print(f"{'='*50}", flush=True)


def verify_flow():
    # 1. 注册用户
    print_step("1. Registering User")
    email = f"test_auto_{uuid.uuid4().hex[:8]}@example.com"
    password = "password123"
    name = "Test User"
    
    register_data = {
        "email": email,
        "password": password,
        "name": name
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        if response.status_code not in [200, 201]:
            print(f"❌ Registration failed: {response.text}")
            return False
        
        user_data = response.json()
        token = user_data.get('token')
        
        # 处理不同的返回结构 (sk_app.py 中返回结构有些差异)
        if 'user' in user_data:
             user_id = user_data['user']['id']
        else:
             user_id = user_data.get('user_id')
             
        print(f"✅ Registered successfully. User ID: {user_id}, Token: {token}")
    except Exception as e:
        print(f"❌ Registration exception: {e}")
        return False

    # 2. 创建订单
    print_step("2. Creating Order")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    order_data = {
        "plan": "buyout",
        "billing_period": "yearly", # Buyout usually doesn't need period but API expects it
        "payment_method": "alipay_qrcode"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/payment/create-order", json=order_data, headers=headers)
        if response.status_code != 200:
            print(f"❌ Create order failed: {response.text}")
            return False
        
        order_resp = response.json()
        order_no = order_resp['order']['order_no']
        print(f"✅ Order created successfully. Order No: {order_no}")
    except Exception as e:
        print(f"❌ Create order exception: {e}")
        return False

    # 3. 标记为已支付
    print_step("3. Marking as Paid")
    mark_paid_data = {
        "order_no": order_no
    }
    
    try:
        # Note: mark-paid doesn't strictly need auth in current implementation logic usually, 
        # but let's see. logic in sk_app.py:5958 doesn't check auth, just order_no.
        # But wait, logic: 
        # 5961: data = request.get_json()
        # 5968: if order_no not in payment_orders: ...
        # It updates `order['status'] = 'waiting_confirmation'` -> saves to data_manager.
        
        response = requests.post(f"{BASE_URL}/api/payment/mark-paid", json=mark_paid_data, headers=headers)
        if response.status_code != 200:
            print(f"❌ Mark paid failed: {response.text}")
            return False
            
        result = response.json()
        print(f"✅ Mark paid result: {result.get('message')}")
    except Exception as e:
        print(f"❌ Mark paid exception: {e}")
        return False

    # 4. 验证持久化文件
    print_step("4. Verifying Persistence (orders.json)")
    
    # 给一点时间写入文件
    time.sleep(1)
    
    if not os.path.exists(ORDERS_FILE):
        print(f"❌ orders.json does not exist!")
        return False
        
    try:
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            orders_db = json.load(f)
            
        if order_no not in orders_db:
            print(f"❌ Order {order_no} not found in orders.json")
            return False
            
        saved_order = orders_db[order_no]
        saved_status = saved_order.get('status')
        print(f"💾 Saved Order Status: {saved_status}")
        
        if saved_status == 'waiting_confirmation':
            print("✅ SUCCESS: Order status correctly saved as 'waiting_confirmation' in persistent storage.")
            return True
        else:
            print(f"❌ FAILURE: Order status is '{saved_status}', expected 'waiting_confirmation'")
            return False
            
    except Exception as e:
        print(f"❌ Verification exception: {e}")
        return False

if __name__ == "__main__":
    if verify_flow():
        print("\n🎉 SELF-VERIFICATION PASSED: The cycle is closed and persistent.")
    else:
        print("\n💥 SELF-VERIFICATION FAILED")
