"""
Check if auth router is loaded and what routes are available
"""
import urllib.request
import json

def check_routes():
    url = "http://localhost:8000/openapi.json"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            print("All available routes:")
            print("=" * 60)
            for path in sorted(data['paths'].keys()):
                methods = list(data['paths'][path].keys())
                print(f"{path}: {methods}")
            
            print("\n" + "=" * 60)
            print("Auth-related routes:")
            print("=" * 60)
            auth_routes = [p for p in data['paths'].keys() if 'auth' in p.lower()]
            if auth_routes:
                for route in auth_routes:
                    methods = list(data['paths'][route].keys())
                    print(f"{route}: {methods}")
            else:
                print("No auth routes found!")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_routes()
