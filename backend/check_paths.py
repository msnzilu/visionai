import urllib.request
import json

def check_openapi():
    url = "http://localhost:8000/openapi.json"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            print("Available Paths:")
            for path in data['paths']:
                print(f"{path} : {list(data['paths'][path].keys())}")
    except Exception as e:
        print(f"Error fetching openapi.json: {e}")

if __name__ == "__main__":
    check_openapi()
