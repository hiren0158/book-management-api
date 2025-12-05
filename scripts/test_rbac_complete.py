import requests
import json
import sys

BASE_URL = "http://localhost:8089"
ADMIN_EMAIL = "admin_rbac_test@example.com"
LIBRARIAN_EMAIL = "librarian_rbac_test@example.com"
MEMBER_EMAIL = "member_rbac_test@example.com"
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
    # Register and login all roles
    print_step("1. Setting up users (Admin, Librarian, Member)")

    # Admin
    requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": ADMIN_EMAIL,
            "name": "Admin Test",
            "password": PASSWORD,
            "role_id": 2,
        },
    )
    admin_token = requests.post(
        f"{BASE_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": PASSWORD}
    ).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Librarian
    requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": LIBRARIAN_EMAIL,
            "name": "Librarian Test",
            "password": PASSWORD,
            "role_id": 3,
        },
    )
    librarian_token = requests.post(
        f"{BASE_URL}/auth/login", json={"email": LIBRARIAN_EMAIL, "password": PASSWORD}
    ).json()["access_token"]
    librarian_headers = {"Authorization": f"Bearer {librarian_token}"}

    # Member
    requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": MEMBER_EMAIL,
            "name": "Member Test",
            "password": PASSWORD,
            "role_id": 1,
        },
    )
    member_token = requests.post(
        f"{BASE_URL}/auth/login", json={"email": MEMBER_EMAIL, "password": PASSWORD}
    ).json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}

    print("✅ All users created and logged in")

    # Test Book Operations
    print_step("2. Testing Book Operations")

    import time

    book_payload = {
        "title": "RBAC Test Book",
        "description": "Testing RBAC",
        "isbn": f"RBAC-{int(time.time())}",
        "author": "Test Author",
        "genre": "Testing",
        "published_date": "2024-01-01",
    }

    # Librarian can create book
    response = requests.post(
        f"{BASE_URL}/books", json=book_payload, headers=librarian_headers
    )
    book = check_response(response, 201)
    book_id = book["id"]
    print(f"✅ Librarian created book ID: {book_id}")

    # Member CANNOT delete book
    print_step("3. Testing DELETE Book (Admin only)")
    response = requests.delete(f"{BASE_URL}/books/{book_id}", headers=member_headers)
    if response.status_code == 403:
        print("✅ Member blocked from deleting book")
    else:
        print(f"❌ Expected 403, got {response.status_code}")
        sys.exit(1)

    # Librarian CANNOT delete book (Admin only)
    response = requests.delete(f"{BASE_URL}/books/{book_id}", headers=librarian_headers)
    if response.status_code == 403:
        print("✅ Librarian blocked from deleting book")
    else:
        print(f"❌ Expected 403, got {response.status_code}")
        sys.exit(1)

    # Test Borrowing Operations
    print_step("4. Testing Borrowing (Member only)")

    # Member can borrow
    response = requests.post(
        f"{BASE_URL}/borrowings", json={"book_id": book_id}, headers=member_headers
    )
    borrowing = check_response(response, 201)
    borrowing_id = borrowing["id"]
    print(f"✅ Member borrowed book, borrowing ID: {borrowing_id}")

    # Librarian CANNOT borrow
    response = requests.post(
        f"{BASE_URL}/borrowings", json={"book_id": book_id}, headers=librarian_headers
    )
    if response.status_code == 403:
        print("✅ Librarian blocked from borrowing")
    else:
        print(f"❌ Expected 403, got {response.status_code}")
        sys.exit(1)

    # Test Return Operations
    print_step("5. Testing Return Book (Librarian/Admin only)")

    # Member CANNOT return
    response = requests.patch(
        f"{BASE_URL}/borrowings/{borrowing_id}/return", headers=member_headers
    )
    if response.status_code == 403:
        print("✅ Member blocked from returning book")
    else:
        print(f"❌ Expected 403, got {response.status_code}")
        sys.exit(1)

    # Librarian CAN return
    response = requests.patch(
        f"{BASE_URL}/borrowings/{borrowing_id}/return", headers=librarian_headers
    )
    check_response(response, 200)
    print("✅ Librarian successfully returned book")

    # Test Review Operations
    print_step("6. Testing Reviews (Member only)")

    # Need to borrow again for review
    response = requests.post(
        f"{BASE_URL}/borrowings", json={"book_id": book_id}, headers=member_headers
    )
    check_response(response, 201)

    # Member can review (after borrowing)
    response = requests.post(
        f"{BASE_URL}/books/{book_id}/reviews",
        json={"rating": 5, "text": "Great!"},
        headers=member_headers,
    )
    check_response(response, 201)
    print("✅ Member created review")

    # Librarian CANNOT create review
    response = requests.post(
        f"{BASE_URL}/books/{book_id}/reviews",
        json={"rating": 4, "text": "Good"},
        headers=librarian_headers,
    )
    if response.status_code == 403:
        print("✅ Librarian blocked from creating review")
    else:
        print(f"❌ Expected 403, got {response.status_code}")
        sys.exit(1)

    # Test User Operations
    print_step("7. Testing User Creation")

    # Librarian can create user
    response = requests.post(
        f"{BASE_URL}/users",
        json={
            "email": "created_by_lib@test.com",
            "name": "Created by Lib",
            "password": PASSWORD,
            "role_id": 1,
        },
        headers=librarian_headers,
    )
    check_response(response, 201)
    print("✅ Librarian created user")

    # Test Delete Book (Admin only)
    print_step("8. Testing Admin-only Book Deletion")
    response = requests.delete(f"{BASE_URL}/books/{book_id}", headers=admin_headers)
    check_response(response, 204)
    print("✅ Admin deleted book")

    print("\n" + "=" * 50)
    print("✅ ALL RBAC TESTS PASSED!")
    print("=" * 50)
    return True


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
