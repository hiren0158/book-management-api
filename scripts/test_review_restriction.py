#!/usr/bin/env python3
"""
Test Review Restriction: Users can only review books they have borrowed
"""
import requests
import json

BASE_URL = "http://localhost:8089"

def test_review_restriction():
    print("=" * 60)
    print("Testing Review Restriction")
    print("=" * 60)
    
    # 1. Register and login as Member
    print("\n1. Creating Member user...")
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": "member_review_test@example.com",
        "name": "Review Test Member",
        "password": "testpass123",
        "role_id": 1
    })
    
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "member_review_test@example.com",
        "password": "testpass123"
    })
    member_token = response.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}
    print("✅ Member logged in")
    
    # 2. Create Admin and Book
    print("\n2. Creating Admin and Book...")
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": "admin_review_test@example.com",
        "name": "Review Test Admin",
        "password": "testpass123",
        "role_id": 2
    })
    
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin_review_test@example.com",
        "password": "testpass123"
    })
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create a book
    import time
    response = requests.post(f"{BASE_URL}/books", json={
        "title": "Review Test Book",
        "description": "A book for testing reviews",
        "isbn": f"TEST-{int(time.time())}",
        "author": "Test Author",
        "genre": "Testing",
        "published_date": "2024-01-01"
    }, headers=admin_headers)
    book_id = response.json()["id"]
    print(f"✅ Created book with ID: {book_id}")
    
    # 3. Try to review WITHOUT borrowing (should FAIL)
    print("\n3. Trying to review without borrowing...")
    response = requests.post(f"{BASE_URL}/books/{book_id}/reviews", json={
        "rating": 5,
        "text": "Great book!"
    }, headers=member_headers)
    
    if response.status_code == 400 and "can only review books you have borrowed" in response.text.lower():
        print("✅ PASS: Member cannot review book they haven't borrowed")
        print(f"   Error: {response.json()['detail']}")
    else:
        print(f"❌ FAIL: Expected 400 error, got {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # 4. Borrow the book
    print("\n4. Borrowing the book...")
    response = requests.post(f"{BASE_URL}/borrowings", json={
        "book_id": book_id
    }, headers=member_headers)
    
    if response.status_code == 201:
        print("✅ Book borrowed successfully")
    else:
        print(f"❌ Failed to borrow: {response.status_code} - {response.text}")
        return False
    
    # 5. Now try to review AFTER borrowing (should SUCCEED)
    print("\n5. Trying to review after borrowing...")
    response = requests.post(f"{BASE_URL}/books/{book_id}/reviews", json={
        "rating": 5,
        "text": "Great book! I borrowed it first."
    }, headers=member_headers)
    
    if response.status_code == 201:
        print("✅ PASS: Member can review book after borrowing")
        review = response.json()
        print(f"   Review ID: {review['id']}")
        print(f"   Rating: {review['rating']}")
    else:
        print(f"❌ FAIL: Expected 201, got {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # 6. Try to review again (should FAIL - already reviewed)
    print("\n6. Trying to review the same book again...")
    response = requests.post(f"{BASE_URL}/books/{book_id}/reviews", json={
        "rating": 4,
        "text": "Changed my mind"
    }, headers=member_headers)
    
    if response.status_code == 400 and "already reviewed" in response.text.lower():
        print("✅ PASS: Cannot review the same book twice")
        print(f"   Error: {response.json()['detail']}")
    else:
        print(f"❌ FAIL: Expected 400 error, got {response.status_code}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL REVIEW RESTRICTION TESTS PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_review_restriction()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
