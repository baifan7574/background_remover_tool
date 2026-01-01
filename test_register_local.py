import requests
import json

def test_registration():
    url = "http://localhost:5000/api/auth/register"
    payload = {
        "name": "AutoTestUser",
        "email": "autotest@example.com",
        "password": "password123",
        "invite_code": "" 
    }
    
    print(f"Testing registration against {url}...")
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ Backend Registration TEST SUCCESS")
        else:
            print("❌ Backend Registration TEST FAILED")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_registration()
