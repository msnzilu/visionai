"""
Test script to debug Google OAuth authentication flow
Run with: python test_google_oauth.py
"""

import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://localhost:8000"

def test_google_login_endpoint():
    """Test the Google login endpoint"""
    print("=" * 60)
    print("TEST 1: Google Login Endpoint")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/v1/auth/google/login"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            response_body = response.read().decode('utf-8')
            
            print(f"✓ Status Code: {status_code}")
            
            if status_code == 200:
                data = json.loads(response_body)
                print(f"✓ Response: {json.dumps(data, indent=2)}")
                
                if data.get("success"):
                    print(f"✓ Auth URL generated: {data.get('auth_url')[:100]}...")
                    print(f"✓ State token: {data.get('state')}")
                    return True, data
                else:
                    print(f"✗ Success is False")
                    return False, data
            else:
                print(f"✗ Unexpected status code: {status_code}")
                return False, None
                
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP Error: {e.code}")
        error_body = e.read().decode('utf-8')
        print(f"✗ Error Response: {error_body}")
        try:
            error_data = json.loads(error_body)
            print(f"✗ Error Details: {json.dumps(error_data, indent=2)}")
        except:
            pass
        return False, None
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None


def test_config_values():
    """Test if configuration values are properly set"""
    print("\n" + "=" * 60)
    print("TEST 2: Configuration Check")
    print("=" * 60)
    
    try:
        # Try to import and check config
        sys.path.insert(0, 'backend')
        from app.config import settings
        
        print(f"✓ Config loaded successfully")
        
        # Check Google OAuth settings
        google_client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
        google_client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
        google_redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', None)
        
        print(f"\nGoogle OAuth Configuration:")
        print(f"  GOOGLE_CLIENT_ID: {'SET' if google_client_id else 'NOT SET'}")
        if google_client_id:
            print(f"    Value: {google_client_id[:20]}...")
        
        print(f"  GOOGLE_CLIENT_SECRET: {'SET' if google_client_secret else 'NOT SET'}")
        if google_client_secret:
            print(f"    Value: {google_client_secret[:10]}...")
        
        print(f"  GOOGLE_REDIRECT_URI: {google_redirect_uri}")
        
        if not google_client_id or not google_client_secret or not google_redirect_uri:
            print(f"\n✗ Missing required Google OAuth configuration!")
            return False
        
        print(f"\n✓ All Google OAuth config values are set")
        return True
        
    except Exception as e:
        print(f"✗ Error checking config: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_oauth_service():
    """Test OAuth service directly"""
    print("\n" + "=" * 60)
    print("TEST 3: OAuth Service Direct Test")
    print("=" * 60)
    
    try:
        sys.path.insert(0, 'backend')
        from app.services.oauth_service import OAuthService
        
        print(f"✓ OAuthService imported successfully")
        
        # Test state token generation
        state = OAuthService.generate_state_token()
        print(f"✓ State token generated: {state[:20]}...")
        
        # Test state token verification
        is_valid = OAuthService.verify_state_token(state)
        print(f"✓ State token verified: {is_valid}")
        
        # Test Google auth URL generation
        try:
            auth_url, state = OAuthService.get_google_auth_url()
            print(f"✓ Google auth URL generated: {auth_url[:100]}...")
            print(f"✓ State: {state[:20]}...")
            
            # Check if URL contains required parameters
            required_params = ['client_id', 'redirect_uri', 'response_type', 'scope', 'state']
            for param in required_params:
                if param in auth_url:
                    print(f"  ✓ URL contains '{param}'")
                else:
                    print(f"  ✗ URL missing '{param}'")
            
            return True
        except Exception as e:
            print(f"✗ Error generating Google auth URL: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"✗ Error testing OAuth service: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_available_endpoints():
    """Check what endpoints are available"""
    print("\n" + "=" * 60)
    print("TEST 4: Available Endpoints")
    print("=" * 60)
    
    url = f"{BASE_URL}/openapi.json"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            print("Auth-related endpoints:")
            for path, methods in data['paths'].items():
                if 'auth' in path.lower() or 'google' in path.lower():
                    print(f"  {path}: {list(methods.keys())}")
            
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("GOOGLE OAUTH AUTHENTICATION DEBUG")
    print("=" * 60)
    
    results = []
    
    # Test 1: Check available endpoints
    results.append(("Available Endpoints", test_available_endpoints()))
    
    # Test 2: Check configuration
    results.append(("Configuration Check", test_config_values()))
    
    # Test 3: Test OAuth service directly
    results.append(("OAuth Service Test", test_oauth_service()))
    
    # Test 4: Test Google login endpoint
    results.append(("Google Login Endpoint", test_google_login_endpoint()[0]))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n✓ All tests passed! Google OAuth should be working.")
    else:
        print("\n✗ Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()
