# 📚 API Endpoints with RBAC

Based on `book_management_rbac.csv`

## 🔐 Authentication (Public - No RBAC)
| Endpoint | Method | Member | Librarian | Admin |
|:---------|:-------|:------:|:---------:|:-----:|
| `/auth/register` | POST | ✔️ | ✔️ | ✔️ |
| `/auth/login` | POST | ✔️ | ✔️ | ✔️ |
| `/auth/refresh` | POST | ✔️ | ✔️ | ✔️ |

## 👤 Users
| Endpoint | Method | Member | Librarian | Admin | Notes |
|:---------|:-------|:------:|:---------:|:-----:|:------|
| `/users` | GET | ❌ | ✔️ | ✔️ | List all users |
| `/users` | POST | ❌ | ✔️ | ✔️ | Create new user |
| `/users/{user_id}` | GET | Self-Only | ✔️ | ✔️ | Member sees self only |
| `/users/{user_id}` | PUT | Self-Only | ✔️ | ✔️ | Member updates self |
| `/users/{user_id}` | DELETE | ❌ | ❌ | ✔️ | Admin only |

## 📖 Books
| Endpoint | Method | Member | Librarian | Admin | Notes |
|:---------|:-------|:------:|:---------:|:-----:|:------|
| `/books` | GET | ✔️ | ✔️ | ✔️ | List all books |
| `/books` | POST | ❌ | ✔️ | ✔️ | Create new book |
| `/books/{book_id}` | GET | ✔️ | ✔️ | ✔️ | Get book details |
| `/books/{book_id}` | PUT | ❌ | ✔️ | ✔️ | Update book |
| `/books/{book_id}` | DELETE | ❌ | ❌ | ✔️ | **Admin only** |

## 📚 Borrowings
| Endpoint | Method | Member | Librarian | Admin | Notes |
|:---------|:-------|:------:|:---------:|:-----:|:------|
| `/borrowings` | POST | ✔️ | ❌ | ❌ | **Only Members** can borrow |
| `/borrowings` | GET | Self-Only | ✔️ | ✔️ | Members see own; staff see all |
| `/borrowings/{borrowing_id}/return` | PATCH | ❌ | ✔️ | ✔️ | **Librarian/Admin only** |
| `/borrowings/{borrowing_id}` | GET | Self-Only | ✔️ | ✔️ | Members see own only |

## ⭐ Reviews
| Endpoint | Method | Member | Librarian | Admin | Notes |
|:---------|:-------|:------:|:---------:|:-----:|:------|
| `/books/{book_id}/reviews` | POST | ✔️ | ❌ | ❌ | **Only Members** create reviews |
| `/books/{book_id}/reviews` | GET | ✔️ | ✔️ | ✔️ | All can view |
| `/books/{book_id}/rating` | GET | ✔️ | ✔️ | ✔️ | Get average rating |
| `/users/{user_id}/reviews` | GET | ✔️ | ✔️ | ✔️ | Get user's reviews |
| `/reviews/{review_id}` | DELETE | Self-Only | ❌ | ✔️ | Member deletes own; Admin any |

## 🤖 AI Features
| Endpoint | Method | Member | Librarian | Admin |
|:---------|:-------|:------:|:---------:|:-----:|
| `/ai/books/recommend` | GET | ✔️ | ✔️ | ✔️ |
| `/ai/books/search_nl` | POST | ✔️ | ✔️ | ✔️ |

## 🏥 System
| Endpoint | Method | Member | Librarian | Admin |
|:---------|:-------|:------:|:---------:|:-----:|
| `/` | GET | ✔️ | ✔️ | ✔️ |
| `/health` | GET | ✔️ | ✔️ | ✔️ |

---

### 🔑 Role IDs
*   **Member**: `role_id = 1`
*   **Admin**: `role_id = 2`
*   **Librarian**: `role_id = 3`

### 📝 Key Rules
1.  **Delete Book**: Admin only (Librarian cannot delete)
2.  **Borrow Book**: Only Members can borrow (not Librarian/Admin)
3.  **Return Book**: Only Librarian/Admin can process returns
4.  **Create Review**: Only Members can create reviews
5.  **Create User**: Both Librarian and Admin can create users
