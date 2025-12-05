import requests
import json
import sys

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin_test_auto@example.com"
USER_EMAIL = "user_test_auto@example.com"
PASSWORD = "testpass123"


def print_step(step):
    print(f"\n{'='*50}\n{step}\n{'='*50}")


def check_response(response, expected_status=200):
    if response.status_code != expected_status:
        print(f"FAILED: Expected {expected_status}, got {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)
    print("SUCCESS")
    return response.json()


def main():
    # 1. Register Admin
    print_step("1. Registering Admin User")
    payload = {
        "email": ADMIN_EMAIL,
        "name": "Admin Tester",
        "password": PASSWORD,
        "role_id": 2,  # Admin
    }
    # Ignore error if already exists
    requests.post(f"{BASE_URL}/auth/register", json=payload)

    # 2. Login Admin
    print_step("2. Logging in Admin")
    response = requests.post(
        f"{BASE_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": PASSWORD}
    )
    admin_token = check_response(response)["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3. Register Regular User
    print_step("3. Registering Regular User")
    payload = {
        "email": USER_EMAIL,
        "name": "Regular Tester",
        "password": PASSWORD,
        "role_id": 1,  # Member
    }
    requests.post(f"{BASE_URL}/auth/register", json=payload)

    # 4. Login Regular User
    print_step("4. Logging in Regular User")
    response = requests.post(
        f"{BASE_URL}/auth/login", json={"email": USER_EMAIL, "password": PASSWORD}
    )
    user_token = check_response(response)["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 5. Admin: Create Book
    print_step("5. Admin: Creating a Book")
    book_payload = {
        "title": "Automated Testing Guide",
        "description": "A book about testing",
        "isbn": f"978-0-0000-0000-{json.dumps(datetime.now().timestamp())[-1]}",  # Randomish ISBN
        "author": "Test Bot",
        "genre": "Technology",
        "published_date": "2024-01-01",
    }
    # Use a unique ISBN to avoid conflicts
    import time

    book_payload["isbn"] = f"978-TEST-{int(time.time())}"

    response = requests.post(
        f"{BASE_URL}/books", json=book_payload, headers=admin_headers
    )
    book = check_response(response, 201)
    book_id = book["id"]
    print(f"Created Book ID: {book_id}")

    # 6. User: List Books
    print_step("6. User: Listing Books")
    response = requests.get(f"{BASE_URL}/books", headers=user_headers)
    books = check_response(response)
    print(f"Found {len(books)} books")

    # 7. User: Borrow Book
    print_step("7. User: Borrowing Book")
    response = requests.post(
        f"{BASE_URL}/borrowings", json={"book_id": book_id}, headers=user_headers
    )
    borrowing = check_response(response, 201)
    borrowing_id = borrowing["id"]
    print(f"Borrowing ID: {borrowing_id}")

    # 8. User: Create Review
    print_step("8. User: Creating Review")
    review_payload = {"rating": 5, "text": "Great test book!"}
    response = requests.post(
        f"{BASE_URL}/books/{book_id}/reviews", json=review_payload, headers=user_headers
    )
    check_response(response, 201)

    # 9. User: Return Book
    print_step("9. User: Returning Book")
    response = requests.patch(
        f"{BASE_URL}/borrowings/{borrowing_id}/return", headers=user_headers
    )
    check_response(response)

    # 10. Verify RBAC (User tries to create book)
    print_step("10. RBAC Test: User trying to create book (Should Fail)")
    response = requests.post(
        f"{BASE_URL}/books", json=book_payload, headers=user_headers
    )
    if response.status_code == 403:
        print("SUCCESS: Access Denied as expected")
    else:
        print(f"FAILED: Expected 403, got {response.status_code}")
        sys.exit(1)

    print("\n✅ ALL TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    from datetime import datetime

    main()
