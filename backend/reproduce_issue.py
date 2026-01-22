import os
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_merge():
    print("Starting merge test...")
    file_path = "test.pdf"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        # Create a dummy pdf if needed, but we saw it in ls
        return

    files = [
        (
            "files",
            (os.path.basename(file_path), open(file_path, "rb"), "application/pdf"),
        ),
        (
            "files",
            (os.path.basename(file_path), open(file_path, "rb"), "application/pdf"),
        ),
    ]

    try:
        print("Sending request...")
        response = client.post("/merge/", files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        for _, file_tuple in files:
            file_tuple[1].close()


if __name__ == "__main__":
    test_merge()
