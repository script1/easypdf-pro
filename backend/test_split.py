import os
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_split():
    print("Starting split test...")
    file_path = "test.pdf"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    with open(file_path, "rb") as f:
        print("Sending request to /split/...")
        response = client.post(
            "/split/", files={"file": ("test.pdf", f, "application/pdf")}
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            zip_url = response.json().get("download_url")
            print(f"Success! Download URL: {zip_url}")
        else:
            print("Failed.")


if __name__ == "__main__":
    test_split()
