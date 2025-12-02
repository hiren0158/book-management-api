# Manual Testing Guide

## Prerequisites
Before testing, ensure you have:
1. PostgreSQL running
2. Environment variables configured in `.env`
3. Database created
4. Migrations applied

## Setup Steps

### 1. Create PostgreSQL Database
```bash
createdb book_management_db
```

### 2. Copy and configure .env
```bash
cp .env.example .env
```

Edit `.env`:
```env
DATABASE_URL="postgresql://postgres:YourPassword@localhost/book_management_db"
JWT_SECRET_KEY="your-super-secret-key-change-this"
JWT_REFRESH_SECRET_KEY="your-refresh-secret-key-change-this"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
OPENAI_API_KEY="sk-your-openai-key"
```

### 3. Run Migrations
```bash
poetry run alembic upgrade head
```

### 4. Create Initial Roles
Connect to PostgreSQL:
```bash
psql book_management_db
```

Run SQL:
```sql
INSERT INTO roles (id, name) VALUES (1, 'Member');
INSERT INTO roles (id, name) VALUES (2, 'Admin');
INSERT INTO roles (id, name) VALUES (3, 'Librarian');
```

### 5. Start the Server
```bash
poetry run uvicorn main:app --reload
```

Server will run at: http://localhost:8000

## Testing Endpoints

### Step 1: Register a User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "testpass123",
    "role_id": 1
  }'
```

### Step 2: Register an Admin User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "name": "Admin User",
    "password": "adminpass123",
    "role_id": 2
  }'
```

### Step 3: Login as Regular User

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

**Save the access_token from response!**

### Step 4: Login as Admin

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "adminpass123"
  }'
```

**Save the admin access_token!**

### Step 5: Create Books (as Admin)

```bash
# Replace YOUR_ADMIN_TOKEN with actual token
curl -X POST http://localhost:8000/books \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Great Gatsby",
    "description": "A classic American novel",
    "isbn": "978-0-7432-7356-5",
    "author": "F. Scott Fitzgerald",
    "genre": "Fiction",
    "published_date": "1925-04-10"
  }'

curl -X POST http://localhost:8000/books \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "1984",
    "description": "Dystopian social science fiction",
    "isbn": "978-0-452-28423-4",
    "author": "George Orwell",
    "genre": "Fiction",
    "published_date": "1949-06-08"
  }'

curl -X POST http://localhost:8000/books \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "To Kill a Mockingbird",
    "description": "A novel about racial injustice",
    "isbn": "978-0-06-112008-4",
    "author": "Harper Lee",
    "genre": "Fiction",
    "published_date": "1960-07-11"
  }'
```

### Step 6: List All Books (Public)

```bash
curl http://localhost:8000/books
```

### Step 7: Search Books

```bash
# By author
curl "http://localhost:8000/books?author=George%20Orwell"

# By genre
curl "http://localhost:8000/books?genre=Fiction"

# Search query
curl "http://localhost:8000/books?q=gatsby"

# With pagination
curl "http://localhost:8000/books?limit=2"
```

### Step 8: Borrow a Book (as Regular User)

```bash
# Replace YOUR_USER_TOKEN and book_id
curl -X POST http://localhost:8000/borrowings \
  -H "Authorization: Bearer YOUR_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": 1
  }'
```

### Step 9: List My Borrowings

```bash
curl http://localhost:8000/borrowings \
  -H "Authorization: Bearer YOUR_USER_TOKEN"
```

### Step 10: Create a Review

```bash
curl -X POST http://localhost:8000/books/1/reviews \
  -H "Authorization: Bearer YOUR_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 5,
    "text": "Excellent book! Highly recommended."
  }'
```

### Step 11: Get Book Reviews

```bash
curl http://localhost:8000/books/1/reviews
```

### Step 12: Get Average Rating

```bash
curl http://localhost:8000/books/1/reviews/rating
```

### Step 13: Return a Book

```bash
# Replace borrowing_id with actual ID from step 8
curl -X PATCH http://localhost:8000/borrowings/1/return \
  -H "Authorization: Bearer YOUR_USER_TOKEN"
```

### Step 14: AI Recommendations (Optional - requires OpenAI key)

```bash
curl http://localhost:8000/ai/books/recommend?limit=3 \
  -H "Authorization: Bearer YOUR_USER_TOKEN"
```

### Step 15: Natural Language Search (Optional)

```bash
curl -X POST http://localhost:8000/ai/books/search_nl \
  -H "Content-Type: application/json" \
  -d '{
    "query": "fiction books by classic authors"
  }'
```

## Test RBAC

### Try to create book as regular user (should fail)

```bash
curl -X POST http://localhost:8000/books \
  -H "Authorization: Bearer YOUR_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Should Fail",
    "description": "This should fail",
    "isbn": "978-1-234567-89-0",
    "author": "Test",
    "genre": "Test",
    "published_date": "2024-01-01"
  }'
```

Expected: 403 Forbidden

### Try to delete user as regular user (should fail)

```bash
curl -X DELETE http://localhost:8000/users/2 \
  -H "Authorization: Bearer YOUR_USER_TOKEN"
```

Expected: 403 Forbidden

## Access API Documentation

Visit in browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Troubleshooting

### Database Connection Error
- Check PostgreSQL is running: `pg_isctl status`
- Verify DATABASE_URL in .env
- Check database exists: `psql -l | grep book_management_db`

### Migration Errors
- Check alembic/env.py imports all models
- Run: `poetry run alembic revision --autogenerate -m "init"`
- Apply: `poetry run alembic upgrade head`

### Import Errors
- Ensure all dependencies installed: `poetry install`
- Check Python path includes project root

### 401 Unauthorized
- Token expired, login again
- Check Authorization header format: `Bearer <token>`

### 500 Internal Server Error
- Check server logs
- Verify all environment variables set
- Ensure database migrations applied
