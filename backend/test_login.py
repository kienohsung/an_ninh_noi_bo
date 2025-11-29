import requests
import sys

URL = "http://127.0.0.1:8001/token"
USERNAME = "admin"
PASSWORD = "admin123"

def test_login():
    try:
        response = requests.post(
            URL,
            data={"username": USERNAME, "password": PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
