"""
Simulate frontend API call for featured post
"""
import requests
import json

API_URL = "http://localhost:8000/api/v1/blog/posts?size=1&page=1&status=published"

try:
    print(f"Fetching from: {API_URL}")
    response = requests.get(API_URL)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total Posts: {data.get('total')}")
        posts = data.get('posts', [])
        print(f"Returned Posts Count: {len(posts)}")
        
        if posts:
            print("\nFeatured Post Details:")
            print(json.dumps(posts[0], indent=2))
        else:
            print("\n❌ No posts returned!")
    else:
        print(f"\n❌ Error: {response.text}")
        
except Exception as e:
    print(f"\n❌ Exception: {e}")
