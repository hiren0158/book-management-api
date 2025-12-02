# Book Management API

A modern, production-ready FastAPI application for managing a book library system with user authentication, role-based access control, and AI-powered features.

## 🚀 Features

### Core Functionality
- **User Management**: Registration, authentication, and profile management
- **Book Management**: Full CRUD operations for books with metadata
- **Borrowing System**: Track book borrowings with due dates and return status
- **Review System**: Users can rate and review books

### Authentication & Security
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Role-Based Access Control (RBAC)**: Three roles - Admin, Librarian, Member
- **Password Hashing**: Bcrypt for secure password storage

### Advanced Features
- **Cursor-Based Pagination**: Efficient pagination for large datasets
- **Advanced Search**: Full-text search across titles, authors, and descriptions
- **Multi-Field Filtering**: Filter by author, genre, publication year
- **AI-Powered Recommendations**: Personalized book recommendations using OpenAI
- **Natural Language Search**: Convert natural language queries to structured filters

### Technical Features
- **Async/Await**: Fully asynchronous for high performance
- **PostgreSQL**: Robust relational database with SQLModel ORM
- **Alembic Migrations**: Database version control
- **Docker Support**: Containerized deployment with Docker Compose
- **Comprehensive Testing**: Unit and integration tests with pytest
- **CI/CD Ready**: GitHub Actions workflows included

## 📋 Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with async support (asyncpg)
- **ORM**: SQLModel + SQLAlchemy
- **Authentication**: JWT (python-jose) + Passlib (bcrypt)
- **Migrations**: Alembic
- **AI**: OpenAI GPT-3.5
- **Testing**: Pytest + httpx
- **Containerization**: Docker + Docker Compose

## 📦 Project Structure

```
book-management-api/
├── src/
│   ├── api/
│   │   ├── endpoints/      # API route handlers
│   │   └── dependencies.py # Auth dependencies
│   ├── core/              # Database config
│   ├── model/             # SQLModel database models
│   ├── schema/            # Pydantic schemas
│   ├── repository/        # Data access layer
│   ├── service/           # Business logic
│   ├── tools/             # AI tools
│   └── utils/             # Helper utilities
├── tests/
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── alembic/               # Database migrations
├── scripts/               # Utility scripts
├── main.py                # Application entry point
├── docker-compose.yml     # Docker orchestration
└── .env.example           # Environment variables template
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (or use Docker)
- Poetry (Python package manager)
- OpenAI API key (for AI features)

### Local Development Setup

#### 1. Clone the repository
```bash
git clone <repository-url>
cd book-management-api
```

#### 2. Install dependencies
```bash
poetry install
```

#### 3. Configure environment variables
```bash
cp .env.example .env
```

Edit `.env` and set your values:
```env
DATABASE_URL="postgresql://postgres:password@localhost/book_management_db"
JWT_SECRET_KEY="your-secret-key-here"
JWT_REFRESH_SECRET_KEY="your-refresh-secret-key-here"
OPENAI_API_KEY="your-openai-api-key"
```

#### 4. Create database
```bash
createdb book_management_db
```

#### 5. Run migrations
```bash
poetry run alembic upgrade head
```

#### 6. Start the server
```bash
poetry run uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker Setup

#### 1. Configure environment
```bash
cp .env.example .env
# Edit .env with your values
```

#### 2. Start services
```bash
# Start API + PostgreSQL
docker-compose up -d

# With pgAdmin (optional)
docker-compose --profile tools up -d
```

#### 3. Run migrations
```bash
docker-compose exec api poetry run alembic upgrade head
```

The API will be available at `http://localhost:8000`  
pgAdmin (if started) at `http://localhost:5050`

## 🗃️ Database Migrations

### Create a new migration
```bash
poetry run alembic revision --autogenerate -m "description"
```

### Apply migrations
```bash
poetry run alembic upgrade head
```

### Rollback migration
```bash
poetry run alembic downgrade -1
```

### View migration history
```bash
poetry run alembic history
```

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Example API Requests

### Authentication

#### Register
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "password": "securepass123",
    "role_id": 1
  }'
```

#### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### Refresh Token
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your-refresh-token"
  }'
```

### Books

#### List books with filters
```bash
# All books
curl http://localhost:8000/books

# Filter by author
curl http://localhost:8000/books?author=J.K.%20Rowling

# Filter by genre
curl http://localhost:8000/books?genre=Fiction

# Search query
curl http://localhost:8000/books?q=harry%20potter

# Pagination
curl http://localhost:8000/books?limit=10&cursor=base64encodedcursor
```

#### Get book by ID
```bash
curl http://localhost:8000/books/1
```

#### Create book (Admin/Librarian only)
```bash
curl -X POST http://localhost:8000/books \
  -H "Authorization: Bearer your-access-token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Great Gatsby",
    "description": "A novel by F. Scott Fitzgerald",
    "isbn": "978-0-7432-7356-5",
    "author": "F. Scott Fitzgerald",
    "genre": "Fiction",
    "published_date": "1925-04-10"
  }'
```

### Borrowings

#### Borrow a book
```bash
curl -X POST http://localhost:8000/borrowings \
  -H "Authorization: Bearer your-access-token" \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": 1
  }'
```

#### Return a book
```bash
curl -X PATCH http://localhost:8000/borrowings/1/return \
  -H "Authorization: Bearer your-access-token"
```

#### List my borrowings
```bash
curl http://localhost:8000/borrowings \
  -H "Authorization: Bearer your-access-token"
```

### Reviews

#### Create a review
```bash
curl -X POST http://localhost:8000/books/1/reviews \
  -H "Authorization: Bearer your-access-token" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 5,
    "text": "Excellent book! Highly recommended."
  }'
```

#### Get book reviews
```bash
curl http://localhost:8000/books/1/reviews
```

#### Get book average rating
```bash
curl http://localhost:8000/books/1/reviews/rating
```

### AI Features

#### Get personalized recommendations
```bash
curl http://localhost:8000/ai/books/recommend?limit=5 \
  -H "Authorization: Bearer your-access-token"

# With genre filter
curl http://localhost:8000/ai/books/recommend?genre=Fiction&limit=5 \
  -H "Authorization: Bearer your-access-token"
```

#### Natural language search
```bash
curl -X POST http://localhost:8000/ai/books/search_nl \
  -H "Content-Type: application/json" \
  -d '{
    "query": "science fiction books from 2020 about space exploration"
  }'
```

Response:
```json
{
  "query": "science fiction books from 2020 about space exploration",
  "extracted_filters": {
    "author": null,
    "genre": "Sci-Fi",
    "published_year": 2020,
    "search_query": "space exploration"
  },
  "books": [...],
  "count": 5
}
```

## 🤖 AI Tools

### Book Recommendations
The recommendation system uses OpenAI to analyze:
- User's borrowing history
- User's review patterns and ratings
- Book preferences (genres, authors)
- Optional genre filter

**Features:**
- Personalized based on reading history
- Considers both borrowed and reviewed books
- Returns only available books from your catalog
- Configurable limit (1-20 books)

### Natural Language Search
Convert natural language queries to structured database filters.

**Examples:**
- "books by J.K. Rowling" → `{author: "J.K. Rowling"}`
- "mystery novels from 2020" → `{genre: "Mystery", published_year: 2020}`
- "science fiction about AI" → `{genre: "Sci-Fi", search_query: "AI"}`

**Note:** AI features require a valid OpenAI API key in your `.env` file.

## 👥 Role-Based Access Control

| Action | Member | Librarian | Admin |
|--------|:------:|:---------:|:-----:|
| View books | ✅ | ✅ | ✅ |
| Borrow books | ✅ | ❌ | ❌ |
| Return books | ❌ | ✅ | ✅ |
| Create reviews | ✅ | ❌ | ❌ |
| Create/Edit books | ❌ | ✅ | ✅ |
| Delete books | ❌ | ❌ | ✅ |
| Manage users | ❌ | ✅ | ✅ |
| Delete users | ❌ | ❌ | ✅ |

### Borrowing Rules
- Members can borrow up to **5 books** simultaneously
- Default borrowing period: **14 days**
- Cannot borrow a book that is currently borrowed
- Can view own borrowing history

## 🧪 Testing

### Run all tests
```bash
poetry run pytest
```

### Run unit tests
```bash
poetry run pytest tests/unit/ -v
```

### Run integration tests
```bash
poetry run pytest tests/integration/ -v
```

### With coverage
```bash
poetry run pytest --cov=src --cov-report=html
```

View coverage report: `htmlcov/index.html`

## 🚀 Deployment

### Using Docker
```bash
docker build -t book-management-api .
docker run -p 8000:8000 --env-file .env book-management-api
```

### Environment Variables
Required environment variables for production:
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret key for access tokens
- `JWT_REFRESH_SECRET_KEY` - Secret key for refresh tokens
- `OPENAI_API_KEY` - OpenAI API key for AI features
- `ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration (default: 30)
- `REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token expiration (default: 7)

## 📄 License

MIT

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on GitHub.
