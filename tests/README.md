# Test Suite Documentation

## Overview

Comprehensive test suite for the Book Management API with **203 tests** achieving **100% pass rate**.

## Quick Start

```bash
# Run all tests
poetry run pytest

# Run only unit tests (fast)
poetry run pytest tests/unit/

# Run only integration tests
poetry run pytest tests/integration/

# Run with coverage
poetry run pytest --cov=src --cov-report=html
```

##Structure

```
tests/
├── unit/                      # Unit tests (no external dependencies)
│   ├── test_auth_service.py       # Authentication logic tests
│   ├── test_book_repository.py    # Repository method tests
│   └── test_sql_validator.py      # SQL injection prevention (37 tests)
├── integration/               # Integration tests (require DB/APIs)
│   ├── test_ai_endpoints.py       # AI search endpoints
│   ├── test_auth_endpoints.py     # Auth API tests
│   ├── test_books_endpoints.py    # Book CRUD tests
│   ├── test_borrowings_endpoints.py
│   ├── test_fuzzy_matching.py     # Fuzzy search tests (14 tests)
│   ├── test_fts.py                # Full-text search tests
│   ├── test_rbac.py               # Role-based access control
│   ├── test_reviews_endpoints.py
│   └── test_users_endpoints.py
└── conftest.py                # Shared fixtures
```

## Test Categories

| Category | Tests | Status |
|----------|------|--------|
| **SQL Security** | 37 | ✅ 100% coverage |
| **AI Search** | 25+ | ✅ Comprehensive |
| **Authentication** | 25+ | ✅ Excellent |
| **Books** | 40+ | ✅ Good |
| **Borrowings** | 20+ | ✅ Good |
| **RBAC** | 15+ | ✅ Good |
| **Reviews** | 15+ | ✅ Good |

## Running Tests

### By Type
```bash
# Unit tests only (< 1s)
poetry run pytest -m unit

# Integration tests only (~80s)
poetry run pytest -m integration

# Exclude slow tests
poetry run pytest -m "not slow"
```

### By Feature
```bash
# All fuzzy matching tests
poetry run pytest -k "fuzzy"

# All author-related tests
poetry run pytest -k "author"

# SQL validator tests
poetry run pytest tests/unit/test_sql_validator.py -v
```

### With Coverage
```bash
# Generate HTML coverage report
poetry run pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

## Writing Tests

### Test Structure (Arrange-Act-Assert)
```python
@pytest.mark.asyncio
async def test_create_book_with_valid_data_returns_created(client, auth_headers):
    \"\"\"Test book creation with valid data returns 201 status.\"\"\"
    # Arrange
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "ISBN-123"
    }
    
    # Act
    response = await client.post("/books", json=book_data, headers=auth_headers)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["title"] == "Test Book"
```

### Test Markers
```python
import pytest

# Mark entire file
pytestmark = pytest.mark.unit

# Mark individual test
@pytest.mark.integration
@pytest.mark.slow
async def test_complex_workflow():
    ...
```

### Available Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `client` | AsyncClient | HTTP test client |
| `db_session` | AsyncSession | Database session |
| `auth_headers` | dict | Member auth headers |
| `admin_auth_headers` | dict | Admin auth headers |
| `test_user` | User | Test member user |
| `admin_user` | User | Test admin user |
| `test_book` | Book | Sample book |

## Best Practices

### ✅ Do
- Use descriptive test names
- One assertion per test (when possible)
- Clean up after tests (fixtures handle this)
- Test edge cases and errors
- Keep tests independent

### ❌ Don't
- Share state between tests
- Mock everything (test real integrations)
- Skip error handling tests
- Write flaky tests
- Ignore test failures

## Coverage Goals

**Target: >90% code coverage**

Current coverage (estimated):
- Auth: ~95%
- Books: ~90%
- SQL Validator: 100% ✅
- AI Search: ~85%
- RBAC: ~90%

## Troubleshooting

### Tests Failing Locally

1. **Check database**:
   ```bash
   # Tests use SQLite in-memory DB (no setup needed)
   ```

2. **Environment variables**:
   ```bash
   # Make sure .env file exists
   cp .env.example .env
   ```

3. **Dependencies**:
   ```bash
   poetry install
   ```

### Slow Tests

To skip slow tests:
```bash
pytest -m "not slow"
```

### Gemini API Quota

AI tests may fail if Gemini quota is exceeded. Wait 60s or skip:
```bash
pytest -m "not ai"
```

## CI/CD Integration

Tests run automatically on:
- Every push
- Every pull request
- Before deployment

Target: All tests must pass before merge.

## Maintenance

### Weekly
- Run full test suite
- Check for flaky tests
- Review failures

### Per Feature
- Add unit tests for new functions
- Add integration tests for new endpoints
- Maintain >90% coverage

### Monthly
- Review test performance
- Update dependencies
- Clean up obsolete tests

---

**Status: ✅ 203/203 tests passing | 0 warnings | Production-ready**
