# 📘 Frontend Developer Guide - Book Management API

**Complete API Documentation & Integration Guide**

Version: 1.0  
Base URL (Production): `https://book-management-api-latest.onrender.com`  
Base URL (Local): `http://localhost:8000`

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication System](#authentication-system)
3. [API Endpoints](#api-endpoints)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Code Examples](#code-examples)

---

## Overview

### System Architecture

```
┌─────────────────┐
│   Frontend App  │
└────────┬────────┘
         │ HTTPS/REST
         ▼
┌──────────────────────────────┐
│  Book Management API         │
│  (FastAPI + PostgreSQL)      │
└────────┬──────────┬──────────┘
         │          │
         ▼          ▼
    ┌────┐      ┌──────────┐
    │ DB │      │ Gemini AI│
    └────┘      └──────────┘
```

### Key Features

- ✅ User Authentication (JWT)
- ✅ Role-Based Access Control (Member, Librarian, Admin)
- ✅ Book CRUD Operations
- ✅ Advanced Search & Filtering
- ✅ Borrowing System
- ✅ Review & Rating System
- ✅ AI-Powered Recommendations
- ✅ Natural Language Search
- ✅ RAG (PDF Q&A)

### User Roles

| Role | ID | Capabilities |
|------|-----|-------------|
| **Member** | 1 | Browse, borrow books, write reviews, use AI features |
| **Admin** | 2 | Full access, delete books/users |
| **Librarian** | 3 | Manage books, process returns, manage users |

---

## Authentication System

### Flow Diagram

```
Register → Login → Get Tokens → Use Access Token → Refresh when expired
```

### Token Management

**Access Token:**
- Expires: 30 minutes
- Usage: All authenticated requests
- Header: `Authorization: Bearer <access_token>`

**Refresh Token:**
- Expires: 7 days
- Usage: Get new access tokens
- Endpoint: `POST /auth/refresh`

### Storage

```javascript
// Save tokens
localStorage.setItem('access_token', token.access_token);
localStorage.setItem('refresh_token', token.refresh_token);

// Auto-refresh
async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  const response = await fetch('/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  const newTokens = await response.json();
  localStorage.setItem('access_token', newTokens.access_token);
  localStorage.setItem('refresh_token', newTokens.refresh_token);
}
```

---

## API Endpoints

### 1. Authentication

#### POST /auth/register

**Request:**
```json
{
  "email": "john@example.com",
  "name": "John Doe",
  "password": "SecurePass123!",
  "role_id": 1
}
```

**Password Requirements:**
- 8-72 characters
- ≥1 uppercase, ≥1 lowercase, ≥1 digit, ≥1 special char

**Response: 201**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 42,
    "email": "john@example.com",
    "name": "John Doe",
    "role_id": 1
  }
}
```

---

#### POST /auth/login

**Request:**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response: 200**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

---

#### POST /auth/refresh

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response: 200**
```json
{
  "access_token": "new_token",
  "refresh_token": "new_refresh",
  "token_type": "bearer"
}
```

---

### 2. Books

#### GET /books

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `search` | string | Full-text search |
| `author` | string | Author name (fuzzy) |
| `genre` | string | Genre filter |
| `published_year` | int | Year filter |
| `limit` | int | Per page (1-100) |
| `cursor` | string | Pagination cursor |
| `sort_order` | string | asc/desc |

**Examples:**
```bash
GET /books
GET /books?search=harry%20potter
GET /books?author=Rowling&genre=Fantasy
GET /books?limit=20&cursor=base64...
```

**Response: 200**
```json
{
  "data": [
    {
      "id": 1,
      "title": "Harry Potter",
      "author": "J.K. Rowling",
      "genre": "Fantasy",
      "isbn": "978-...",
      "description": "...",
      "published_date": "1997-06-26",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "next_cursor": "eyJpZCI6Mn0=",
  "has_next_page": true
}
```

---

#### GET /books/{book_id}

**Response: 200**
```json
{
  "id": 1,
  "title": "Harry Potter",
  "author": "J.K. Rowling",
  "genre": "Fantasy",
  "isbn": "978-...",
  "description": "...",
  "published_date": "1997-06-26",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

#### POST /books
*Requires: Admin or Librarian*

**Request:**
```json
{
  "title": "The Great Gatsby",
  "description": "Classic novel...",
  "isbn": "978-0-7432-7356-5",
  "author": "F. Scott Fitzgerald",
  "genre": "Fiction",
  "published_date": "1925-04-10"
}
```

**Response: 201**
```json
{
  "id": 42,
  "title": "The Great Gatsby",
  ...
}
```

---

#### PUT /books/{book_id}
*Requires: Admin or Librarian*

**Request:** (all fields optional)
```json
{
  "title": "Updated Title",
  "description": "Updated desc"
}
```

---

#### DELETE /books/{book_id}
*Requires: Admin*

**Response: 204 No Content**

---

### 3. Borrowings

#### POST /borrowings
*Requires: Member*

**Request:**
```json
{
  "book_id": 5
}
```

**Response: 201**
```json
{
  "id": 100,
  "user_id": 1,
  "book_id": 5,
  "borrowed_at": "2024-12-08T10:00:00Z",
  "due_date": "2024-12-22T10:00:00Z",
  "returned_at": null
}
```

**Rules:**
- Max 5 concurrent borrowings
- 14-day due date
- Cannot borrow already-borrowed books

---

#### PATCH /borrowings/{id}/return
*Requires: Admin or Librarian*

**Response: 200**
```json
{
  "id": 100,
  "returned_at": "2024-12-10T14:30:00Z",
  ...
}
```

---

#### GET /borrowings

**Query Parameters:**
- `user_id` (int) - Filter by user
- `book_id` (int) - Filter by book
- `active_only` (bool) - Active only
- `limit`, `cursor` - Pagination

**Response: 200**
```json
[
  {
    "id": 100,
    "user_id": 1,
    "book_id": 5,
    "borrowed_at": "...",
    "due_date": "...",
    "returned_at": null
  }
]
```

---

### 4. Reviews

#### POST /books/{book_id}/reviews
*Requires: Member*

**Request:**
```json
{
  "rating": 5,
  "text": "Excellent book!"
}
```

**Response: 201**
```json
{
  "id": 50,
  "user_id": 1,
  "book_id": 5,
  "rating": 5,
  "text": "Excellent book!",
  "created_at": "2024-12-08T10:00:00Z"
}
```

**Rules:**
- Rating: 1-5
- One review per user per book
- Must have borrowed the book

---

#### GET /books/{book_id}/reviews

**Response: 200**
```json
[
  {
    "id": 50,
    "user_id": 1,
    "book_id": 5,
    "rating": 5,
    "text": "Excellent!",
    "created_at": "..."
  }
]
```

---

#### GET /books/{book_id}/reviews/rating

**Response: 200**
```json
{
  "book_id": 5,
  "average_rating": 4.5,
  "rating": 4.5
}
```

---

### 5. AI Features

#### GET /ai/books/recommend
*Requires: Authentication*

**Query Parameters:**
- `limit` (1-20, default: 5)
- `genre` (optional)

**Response: 200**
```json
{
  "user_id": 1,
  "genre_filter": "Sci-Fi",
  "recommendations": [
    {
      "id": 42,
      "title": "Dune",
      "author": "Frank Herbert",
      "genre": "Sci-Fi",
      "reason": "Based on your reading history..."
    }
  ],
  "count": 1
}
```

---

#### POST /ai/books/search_nl

**Request:**
```json
{
  "query": "science fiction from 2020 about space"
}
```

**Response: 200**
```json
{
  "query": "science fiction from 2020 about space",
  "method": "sql_where_clause",
  "books": [...],
  "count": 5,
  "fallback_used": false
}
```

**Example Queries:**
- "books by J.K. Rowling"
- "mystery novels from 2020"
- "fantasy about dragons"

---

### 6. RAG (PDF Q&A)

#### POST /rag/upload
*Requires: Authentication*

**Request:** multipart/form-data
```javascript
const formData = new FormData();
formData.append('file', pdfFile);
```

**Response: 200**
```json
{
  "document_id": 42,
  "filename": "ml_guide.pdf",
  "chunk_count": 145,
  "message": "PDF uploaded successfully"
}
```

---

#### POST /rag/ask
*Requires: Authentication*

**Request:**
```json
{
  "question": "What is machine learning?",
  "top_k": 5,
  "doc_id": 0
}
```

`doc_id = 0` searches all your documents  
`doc_id = 42` searches specific document

**Response: 200**
```json
{
  "answer": "Machine learning is...",
  "context": [
    {
      "text": "ML is a subset of AI...",
      "score": 0.89,
      "document_id": 42
    }
  ],
  "sources": [42]
}
```

---

#### DELETE /rag/documents/{document_id}
*Requires: Authentication*

**Response: 204 No Content**

---

## Data Models

### User
```typescript
interface User {
  id: number;
  email: string;
  name: string;
  role_id: number;
  is_active: boolean;
  created_at: string;
  role?: {
    id: number;
    name: "Member" | "Admin" | "Librarian";
  };
}
```

### Book
```typescript
interface Book {
  id: number;
  title: string;
  description: string;
  isbn: string;
  author: string;
  genre: string;
  published_date: string; // YYYY-MM-DD
  created_at: string;
}
```

### Borrowing
```typescript
interface Borrowing {
  id: number;
  user_id: number;
  book_id: number;
  borrowed_at: string;
  due_date: string;
  returned_at: string | null;
}
```

### Review
```typescript
interface Review {
  id: number;
  user_id: number;
  book_id: number;
  rating: number; // 1-5
  text: string;
  created_at: string;
}
```

---

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error message"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Server Error |

### Error Handling Pattern
```javascript
async function apiRequest(url, options) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 401:
          await refreshAccessToken();
          return apiRequest(url, options);
        case 403:
          alert('Permission denied');
          break;
        case 404:
          alert('Not found');
          break;
        default:
          alert(error.detail);
      }
      throw new Error(error.detail);
    }
    
    if (response.status === 204) return null;
    return await response.json();
  } catch (error) {
    console.error('API error:', error);
    throw error;
  }
}
```

---

## Code Examples

See [API_CODE_EXAMPLES.md](./API_CODE_EXAMPLES.md) for complete implementations in:
- React/TypeScript
- Vanilla JavaScript
- Vue.js
- Angular

### Quick Start

```javascript
// Initialize
const API_URL = 'https://book-management-api-latest.onrender.com';

// Login
const response = await fetch(`${API_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePass123!'
  })
});
const tokens = await response.json();
localStorage.setItem('access_token', tokens.access_token);

// Get books
const booksResponse = await fetch(`${API_URL}/books`, {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
});
const books = await booksResponse.json();
```

---

## Best Practices

1. **Token Management**: Auto-refresh on 401
2. **Pagination**: Use cursor-based pagination
3. **Search**: Debounce search inputs (500ms)
4. **File Upload**: Show progress for PDFs
5. **Error Handling**: Show user-friendly messages
6. **Role-Based UI**: Hide features based on user role

---

## Additional Resources

- **Swagger UI**: `https://your-api.com/docs`
- **ReDoc**: `https://your-api.com/redoc`
- **GitHub**: Repository link

---

**Document Version:** 1.0  
**Last Updated:** December 8, 2024  
**API Version:** 1.0
