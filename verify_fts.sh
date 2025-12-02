#!/bin/bash

# 0. Register Admin (ignore error if exists)
echo "Registering admin..."
curl -s -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"email": "admin_fts@example.com", "password": "adminpass123", "name": "FTS Admin", "role_id": 2}'

# 1. Login to get token
echo "Logging in..."
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "admin_fts@example.com", "password": "adminpass123"}' | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Create a book for FTS testing
echo "Creating test book..."
curl -s -X POST "http://localhost:8000/books" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "title": "Advanced PostgreSQL Search",
           "description": "Learn about GIN indexes and tsvector for full-text search.",
           "isbn": "ISBN-FTS-DEMO-001",
           "author": "Db Admin",
           "genre": "Database",
           "published_date": "2023-01-01"
         }' | jq '.'

# 3. Perform FTS Search (Simple)
echo "\n\n--- Simple Search 'gin' ---"
curl -s "http://localhost:8000/books?q=gin" | jq '.'

# 4. Perform FTS Search (Complex OR)
echo "\n\n--- Complex Search 'postgres OR mysql' ---"
curl -s "http://localhost:8000/books?q=postgres%20OR%20mysql" | jq '.'

# 5. Perform FTS Search (Negation)
echo "\n\n--- Negation Search 'postgres -indexes' ---"
curl -s "http://localhost:8000/books?q=postgres%20-indexes" | jq '.'

# 6. Perform FTS Search (Stemming)
# Description has "indexes". Query "indexing" should match with FTS, but fail with ILIKE.
echo "\n\n--- Stemming Search 'indexing' ---"
curl -s "http://localhost:8000/books?q=indexing" | jq '.'
