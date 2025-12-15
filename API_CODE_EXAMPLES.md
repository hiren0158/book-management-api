# API Code Examples

Complete code examples for integrating with the Book Management API.

---

## Table of Contents

1. [React/TypeScript](#reacttypescript)
2. [Vanilla JavaScript](#vanilla-javascript)
3. [Vue.js](#vuejs)

---

## React/TypeScript

### API Client

```typescript
// api/client.ts
import axios from 'axios';

const API_BASE_URL = 'https://book-management-api-latest.onrender.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' }
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken
        });
        
        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
```

### Login Component

```typescript
// components/LoginForm.tsx
import React, { useState } from 'react';
import api from './api/client';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const response = await api.post('/auth/login', { email, password });
      const { access_token, refresh_token } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      window.location.href = '/dashboard';
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <form onSubmit={handleLogin}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
```

### Book List with Pagination

```typescript
// components/BookList.tsx
import React, { useState, useEffect } from 'react';
import api from './api/client';

interface Book {
  id: number;
  title: string;
  author: string;
  genre: string;
  isbn: string;
  description: string;
  published_date: string;
  created_at: string;
}

export function BookList() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(false);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  
  const loadBooks = async (nextCursor: string | null = null) => {
    try {
      setLoading(true);
      const url = nextCursor 
        ? `/books?limit=20&cursor=${nextCursor}`
        : '/books?limit=20';
        
      const response = await api.get(url);
      
      setBooks(prev => 
        nextCursor ? [...prev, ...response.data.data] : response.data.data
      );
      setCursor(response.data.next_cursor);
      setHasMore(response.data.has_next_page);
    } catch (err) {
      console.error('Failed to load books:', err);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    loadBooks();
  }, []);
  
  return (
    <div>
      <h1>Books</h1>
      <div className="book-grid">
        {books.map(book => (
          <div key={book.id} className="book-card">
            <h3>{book.title}</h3>
            <p>by {book.author}</p>
            <p>{book.genre} | {book.published_date}</p>
            <p>{book.description}</p>
          </div>
        ))}
      </div>
      
      {loading && <p>Loading...</p>}
      
      {hasMore && !loading && (
        <button onClick={() => loadBooks(cursor)}>
          Load More
        </button>
      )}
    </div>
  );
}
```

### Search with Debouncing

```typescript
// components/BookSearch.tsx
import React, { useState, useEffect } from 'react';
import api from './api/client';

export function BookSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    
    const timeoutId = setTimeout(async () => {
      setLoading(true);
      try {
        const response = await api.get(`/books?search=${encodeURIComponent(query)}`);
        setResults(response.data.data);
      } catch (err) {
        console.error('Search failed:', err);
      } finally {
        setLoading(false);
      }
    }, 500); // Wait 500ms after typing stops
    
    return () => clearTimeout(timeoutId);
  }, [query]);
  
  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search books..."
      />
      
      {loading && <p>Searching...</p>}
      
      <div>
        {results.map((book: any) => (
          <div key={book.id}>{book.title} - {book.author}</div>
        ))}
      </div>
    </div>
  );
}
```

### Borrow Book

```typescript
// components/BorrowButton.tsx
import React, { useState } from 'react';
import api from './api/client';

export function BorrowButton({ bookId }: { bookId: number }) {
  const [borrowing, setBorrowing] = useState(false);
  
  const handleBorrow = async () => {
    setBorrowing(true);
    try {
      await api.post('/borrowings', { book_id: bookId });
      alert('Book borrowed successfully! Due in 14 days.');
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to borrow book';
      alert(message);
    } finally {
      setBorrowing(false);
    }
  };
  
  return (
    <button onClick={handleBorrow} disabled={borrowing}>
      {borrowing ? 'Borrowing...' : 'Borrow Book'}
    </button>
  );
}
```

### PDF Upload with Progress

```typescript
// components/PDFUpload.tsx
import React, { useState } from 'react';
import api from './api/client';

export function PDFUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  
  const handleUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await api.post('/rag/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total!
          );
          setProgress(percentCompleted);
        }
      });
      
      alert(`PDF uploaded! Document ID: ${response.data.document_id}`);
      setFile(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };
  
  return (
    <div>
      <input
        type="file"
        accept=".pdf"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button onClick={handleUpload} disabled={!file || uploading}>
        {uploading ? `Uploading... ${progress}%` : 'Upload PDF'}
      </button>
      {uploading && (
        <div className="progress-bar">
          <div style={{ width: `${progress}%` }} />
        </div>
      )}
    </div>
  );
}
```

### RAG Question

```typescript
// components/RAGQuestion.tsx
import React, { useState } from 'react';
import api from './api/client';

export function RAGQuestion() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [context, setContext] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAnswer('');
    
    try {
      const response = await api.post('/rag/ask', {
        question,
        top_k: 5,
        doc_id: 0 // Search all documents
      });
      
      setAnswer(response.data.answer);
      setContext(response.data.context);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to get answer');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <form onSubmit={handleAsk}>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your documents..."
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Processing...' : 'Ask'}
        </button>
      </form>
      
      {answer && (
        <div className="answer">
          <h3>Answer:</h3>
          <p>{answer}</p>
          
          <h4>Sources:</h4>
          {context.map((ctx: any, idx) => (
            <div key={idx} className="context">
              <small>Document {ctx.document_id} (score: {ctx.score})</small>
              <p>{ctx.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Vanilla JavaScript

### Complete API Client

```javascript
// api/client.js
class BookManagementAPI {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }
  
  async request(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
        ...(token && { 'Authorization': `Bearer ${token}` })
      }
    };
    
    const response = await fetch(`${this.baseURL}${endpoint}`, config);
    
    // Handle 401 - try refresh
    if (response.status === 401 && !options._retry) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        return this.request(endpoint, { ...options, _retry: true });
      }
      window.location.href = '/login';
      throw new Error('Session expired');
    }
    
    // Handle 204 No Content
    if (response.status === 204) return null;
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Request failed');
    }
    
    return data;
  }
  
  // Auth
  async login(email, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  }
  
  async register(email, name, password, roleId = 1) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, name, password, role_id: roleId })
    });
  }
  
  async refreshToken() {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      const data = await this.request('/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshToken })
      });
      
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }
  
  // Books
  async getBooks(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/books${queryString ? '?' + queryString : ''}`);
  }
  
  async getBook(id) {
    return this.request(`/books/${id}`);
  }
  
  async createBook(bookData) {
    return this.request('/books', {
      method: 'POST',
      body: JSON.stringify(bookData)
    });
  }
  
  async updateBook(id, bookData) {
    return this.request(`/books/${id}`, {
      method: 'PUT',
      body: JSON.stringify(bookData)
    });
  }
  
  async deleteBook(id) {
    return this.request(`/books/${id}`, { method: 'DELETE' });
  }
  
  // Borrowings
  async borrowBook(bookId) {
    return this.request('/borrowings', {
      method: 'POST',
      body: JSON.stringify({ book_id: bookId })
    });
  }
  
  async returnBook(borrowingId) {
    return this.request(`/borrowings/${borrowingId}/return`, {
      method: 'PATCH'
    });
  }
  
  async getBorrowings(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/borrowings${queryString ? '?' + queryString : ''}`);
  }
  
  // Reviews
  async createReview(bookId, rating, text) {
    return this.request(`/books/${bookId}/reviews`, {
      method: 'POST',
      body: JSON.stringify({ rating, text })
    });
  }
  
  async getBookReviews(bookId, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/books/${bookId}/reviews${queryString ? '?' + queryString : ''}`);
  }
  
  async getBookRating(bookId) {
    return this.request(`/books/${bookId}/reviews/rating`);
  }
  
  // AI
  async getRecommendations(limit = 5, genre = null) {
    const params = { limit, ...(genre && { genre }) };
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/ai/books/recommend?${queryString}`);
  }
  
  async naturalLanguageSearch(query, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/ai/books/search_nl${queryString ? '?' + queryString : ''}`, {
      method: 'POST',
      body: JSON.stringify({ query })
    });
  }
  
  // RAG
  async uploadPDF(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${this.baseURL}/rag/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }
    
    return response.json();
  }
  
  async askQuestion(question, topK = 5, docId = 0) {
    return this.request('/rag/ask', {
      method: 'POST',
      body: JSON.stringify({
        question,
        top_k: topK,
        doc_id: docId
      })
    });
  }
  
  async deleteDocument(documentId) {
    return this.request(`/rag/documents/${documentId}`, {
      method: 'DELETE'
    });
  }
}

// Usage
const api = new BookManagementAPI('https://book-management-api-latest.onrender.com');

// Example: Login
async function login() {
  try {
    await api.login('user@example.com', 'SecurePass123!');
    console.log('Logged in!');
  } catch (error) {
    console.error('Login failed:', error.message);
  }
}

// Example: Search books
async function searchBooks() {
  try {
    const response = await api.getBooks({
      search: 'harry potter',
      limit: 10
    });
    console.log('Books:', response.data);
  } catch (error) {
    console.error('Search failed:', error.message);
  }
}

// Example: Borrow book
async function borrowBook(bookId) {
  try {
    const borrowing = await api.borrowBook(bookId);
    console.log('Borrowed!', borrowing);
  } catch (error) {
    console.error('Borrow failed:', error.message);
  }
}
```

---

## Vue.js

### API Service

```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://book-management-api-latest.onrender.com',
  headers: { 'Content-Type': 'application/json' }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(
          'https://book-management-api-latest.onrender.com/auth/refresh',
          { refresh_token: refreshToken }
        );
        
        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        
        error.config.headers.Authorization = `Bearer ${access_token}`;
        return api(error.config);
      } catch {
        localStorage.clear();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Login Component

```vue
<!-- components/LoginForm.vue -->
<template>
  <form @submit.prevent="handleLogin">
    <input
      v-model="email"
      type="email"
      placeholder="Email"
      required
    />
    <input
      v-model="password"
      type="password"
      placeholder="Password"
      required
    />
    <button type="submit" :disabled="loading">
      {{ loading ? 'Logging in...' : 'Login' }}
    </button>
    <p v-if="error" class="error">{{ error }}</p>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import api from '@/services/api';
import { useRouter } from 'vue-router';

const router = useRouter();
const email = ref('');
const password = ref('');
const error = ref('');
const loading = ref(false);

const handleLogin = async () => {
  error.value = '';
  loading.value = true;
  
  try {
    const response = await api.post('/auth/login', {
      email: email.value,
      password: password.value
    });
    
    const { access_token, refresh_token } = response.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    
    router.push('/dashboard');
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Login failed';
  } finally {
    loading.value = false;
  }
};
</script>
```

### Book List

```vue
<!-- components/BookList.vue -->
<template>
  <div>
    <h1>Books</h1>
    <div class="book-grid">
      <div v-for="book in books" :key="book.id" class="book-card">
        <h3>{{ book.title }}</h3>
        <p>by {{ book.author }}</p>
        <p>{{ book.genre }} | {{ book.published_date }}</p>
      </div>
    </div>
    
    <p v-if="loading">Loading...</p>
    
    <button
      v-if="hasMore && !loading"
      @click="loadMore"
    >
      Load More
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import api from '@/services/api';

interface Book {
  id: number;
  title: string;
  author: string;
  genre: string;
  published_date: string;
}

const books = ref<Book[]>([]);
const loading = ref(false);
const cursor = ref<string | null>(null);
const hasMore = ref(false);

const loadBooks = async (nextCursor: string | null = null) => {
  try {
    loading.value = true;
    const url = nextCursor 
      ? `/books?limit=20&cursor=${nextCursor}`
      : '/books?limit=20';
      
    const response = await api.get(url);
    
    if (nextCursor) {
      books.value = [...books.value, ...response.data.data];
    } else {
      books.value = response.data.data;
    }
    
    cursor.value = response.data.next_cursor;
    hasMore.value = response.data.has_next_page;
  } catch (err) {
    console.error('Failed to load books:', err);
  } finally {
    loading.value = false;
  }
};

const loadMore = () => loadBooks(cursor.value);

onMounted(() => loadBooks());
</script>
```

---

**Note:** All examples use the production API URL. For local development, change to `http://localhost:8000`.
