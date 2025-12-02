import urllib.request
import urllib.error
import json

def test_login():
    url = "http://localhost:8000/api/v1/auth/login/"
    payload = {
        "email": "test@example.com",
        "password": "password123"
    }
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            response_body = response.read().decode('utf-8')
            print(f"Status Code: {status_code}")
            print(f"Response: {response_body}")
            
            if status_code == 200:
                resp_json = json.loads(response_body)
                if resp_json.get("success"):
                    print("Login SUCCESS!")
                    token = resp_json["data"]["access_token"]
                    print(f"Token: {token[:20]}...")
                    
                    # Test protected endpoint
                    test_protected(token)
                else:
                    print("Login FAILED (logic):", resp_json.get("message"))
            else:
                print("Login FAILED (http)")
                
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(f"Response: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Error: {e}")

def test_protected(token):
    url = "http://localhost:8000/api/v1/users/me"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    
    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            response_body = response.read().decode('utf-8')
            print(f"\nProtected Endpoint Status: {status_code}")
            print(f"Protected Endpoint Response: {response_body}")
            
            if status_code == 200:
                print("Protected Endpoint SUCCESS!")
            else:
                print("Protected Endpoint FAILED")
                
    except urllib.error.HTTPError as e:
        print(f"\nProtected Endpoint HTTP Error: {e.code}")
        print(f"Response: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
