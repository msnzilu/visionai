"""
Simple test to check Google OAuth configuration and endpoint availability
"""

import urllib.request
import urllib.error
import json

def test_google_login():
    """Test the Google login endpoint"""
    print("Testing Google OAuth Login Endpoint...")
    print("=" * 60)
    
    url = "http://localhost:8000/api/v1/auth/google/login"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            response_body = response.read().decode('utf-8')
            
            print(f"Status Code: {status_code}")
            print(f"Response:\n{response_body}\n")
            
            if status_code == 200:
                data = json.loads(response_body)
                if data.get("success"):
                    print("✓ SUCCESS: Google login endpoint is working!")
                    print(f"✓ Auth URL: {data.get('auth_url')[:100]}...")
                    print(f"✓ State: {data.get('state')}")
                else:
                    print("✗ FAILED: Response success is False")
                    print(f"Message: {data.get('message', 'No message')}")
            else:
                print(f"✗ FAILED: Unexpected status code")
                
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP ERROR: {e.code}")
        error_body = e.read().decode('utf-8')
        print(f"Error Response:\n{error_body}")
        
        try:
            error_data = json.loads(error_body)
            print(f"\nError Details:")
            print(json.dumps(error_data, indent=2))
        except:
            pass
            
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_google_login()
