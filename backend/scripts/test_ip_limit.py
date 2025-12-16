
import requests
import random
import string
import time

BASE_URL = "http://localhost:8000/api/v1"

def generate_random_email():
    return f"test_limit_{''.join(random.choices(string.ascii_lowercase, k=8))}@example.com"

def register_user(email):
    payload = {
        "email": email,
        "password": "Password123!",
        "first_name": "Test",
        "last_name": "User",
        "terms_accepted": True
    }
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        return response.status_code, response.json()
    except Exception as e:
        print(f"Request failed: {e}")
        return 0, {}

def main():
    print(f"Testing IP Registration Limit against {BASE_URL}...")
    
    # 1. Register 1st account
    email1 = generate_random_email()
    print(f"\nAttempt 1: Registering {email1}...")
    status1, data1 = register_user(email1)
    print(f"Status: {status1}, Response: {data1}")
    
    if status1 != 200:
        print("Initial registration failed. Is the server running?")
        return

    # 2. Register 2nd account
    email2 = generate_random_email()
    print(f"\nAttempt 2: Registering {email2}...")
    status2, data2 = register_user(email2)
    print(f"Status: {status2}, Response: {data2}")

    # 3. Register 3rd account
    email3 = generate_random_email()
    print(f"\nAttempt 3: Registering {email3}...")
    status3, data3 = register_user(email3)
    print(f"Status: {status3}, Response: {data3}")

    # 4. Attempt 4th account (Should Fail)
    email4 = generate_random_email()
    print(f"\nAttempt 4: Registering {email4} (Expected Failure)...")
    status4, data4 = register_user(email4)
    print(f"Status: {status4}, Response: {data4}")

    if status4 == 400 or data4.get("success") is False:
        print("\nSUCCESS: 4th registration attempt was blocked as expected.")
    else:
        print("\nFAILURE: 4th registration attempt succeeded (Limit not enforced).")

if __name__ == "__main__":
    main()
