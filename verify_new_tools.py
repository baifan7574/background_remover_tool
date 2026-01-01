import requests
import json

BASE_URL = 'http://127.0.0.1:5000'

def test_unit_converter():
    print("\nTesting Unit Converter...")
    url = f"{BASE_URL}/api/tools/unit-converter"
    
    # Mock login or bypass auth? 
    # The API requires a token. I need to simulate a login first.
    # Or I can temporarily disable auth for testing? 
    # Better to register/login a test user.
    
    # Let's try to register a test user first
    register_url = f"{BASE_URL}/api/auth/register"
    user_data = {
        "email": "test_verify@example.com",
        "password": "password123",
        "name": "Test User"
    }
    
    session = requests.Session()
    
    # Try login first in case user exists
    login_url = f"{BASE_URL}/api/auth/login"
    login_data = {"email": "test_verify@example.com", "password": "password123"}
    
    print("Logging in...")
    try:
        resp = session.post(login_url, json=login_data)
        if resp.status_code != 200:
            print("Login failed, trying to register...")
            resp = session.post(register_url, json=user_data)
            if resp.status_code == 200:
                 print("Registered successfully.")
                 # Login again to get token if needed, or use response
                 resp = session.post(login_url, json=login_data)
            else:
                 print(f"Registration failed: {resp.text}")
                 return

        token = resp.json().get('token')
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test Length
        payload = {
            "category": "length",
            "value": 1,
            "from_unit": "m",
            "to_unit": "cm"
        }
        r = requests.post(url, json=payload, headers=headers)
        print(f"1 m to cm: {r.json()}")
        assert r.json()['result'] == 100.0
        
        # Test Weight
        payload = {
            "category": "weight",
            "value": 1,
            "from_unit": "kg",
            "to_unit": "g"
        }
        r = requests.post(url, json=payload, headers=headers)
        print(f"1 kg to g: {r.json()}")
        assert r.json()['result'] == 1000.0

        print("Unit Converter Verification Passed!")
        return headers
        
    except Exception as e:
        print(f"Unit Converter Test Failed: {e}")
        return None

def test_shipping_calculator(headers):
    if not headers:
        print("Skipping Shipping Calculator test due to auth failure.")
        return

    print("\nTesting Shipping Calculator...")
    url = f"{BASE_URL}/api/tools/shipping-calculator"
    
    payload = {
        "length": 50,
        "width": 50,
        "height": 50,
        "weight": 10,
        "dim_unit": "cm",
        "weight_unit": "kg"
    }
    
    try:
        r = requests.post(url, json=payload, headers=headers)
        print(f"Shipping Calc Response: {r.json()}")
        data = r.json()
        
        # Volumetric weight: 50*50*50 / 5000 = 25
        assert data['volumetric_weight'] == 25.0
        # Billable weight: max(10, 25) = 25
        assert data['billable_weight'] == 25.0
        
        print("Shipping Calculator Verification Passed!")
        
    except Exception as e:
        print(f"Shipping Calculator Test Failed: {e}")

if __name__ == "__main__":
    try:
        requests.get(BASE_URL)
        headers = test_unit_converter()
        test_shipping_calculator(headers)
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start sk_app.py first.")
