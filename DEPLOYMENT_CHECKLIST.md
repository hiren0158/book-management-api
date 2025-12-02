# ✅ Render Deployment Checklist

Use this checklist to ensure successful deployment to Render.

## Pre-Deployment

- [ ] Code ready in GitHub repository
- [ ] All tests passing (200/200)
- [ ] `.gitignore` includes `.env` (never commit secrets!)
- [ ] `render.yaml` file exists
- [ ] `DEPLOYMENT.md` reviewed

## Render Setup

### 1. Create PostgreSQL Database

- [ ] Go to Render Dashboard
- [ ] Click "+ New" → "PostgreSQL"
- [ ] Name: `book-management-db`
- [ ] Region: Oregon (or your preferred)
- [ ] Plan: Free
- [ ] Click "Create Database"
- [ ] **Save Internal Database URL**

### 2. Install PostgreSQL Extensions

```bash
# Connect via PSQL (get command from Render dashboard)
psql -h <hostname> -U book_admin book_management

# Run these commands:
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
\q
```

- [ ] pg_trgm extension installed
- [ ] btree_gin extension installed

### 3. Create Web Service

- [ ] Click "+ New" → "Web Service"
- [ ] Connect GitHub repository
- [ ] Select repository
- [ ] Name: `book-management-api`
- [ ] Region: Oregon (same as database)
- [ ] Branch: `main`
- [ ] Runtime: Python 3
- [ ] Plan: Free

### 4. Configure Build & Start

**Build Command**:
```bash
pip install --upgrade pip && pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi
```

- [ ] Build command set

**Start Command**:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

- [ ] Start command set

### 5. Set Environment Variables

- [ ] `DATABASE_URL` → Linked to database (auto-set)
- [ ] `JWT_SECRET_KEY` → Generated (use "Generate" button)
- [ ] `JWT_ALGORITHM` → `HS256`
- [ ] `GEMINI_API_KEY` → Your API key from Google AI Studio
- [ ] `PYTHON_VERSION` → `3.13`
- [ ] `ALLOWED_ORIGINS` → Your frontend URL (e.g., `https://yourfrontend.com`)

### 6. Deploy

- [ ] Click "Create Web Service"
- [ ] Wait for build to complete (~5 minutes)
- [ ] Check build logs for errors

## Post-Deployment

### 7. Run Migrations

```bash
# In Render Shell
alembic upgrade head
```

- [ ] Migrations completed successfully

### 8. Initialize Database

```bash
# In Render Shell
python scripts/init_database.py
```

- [ ] Extensions verified
- [ ] Roles created (Member, Admin, Librarian)
- [ ] Database verified

## Verification

### 9. Test Endpoints

**Health Check**:
```bash
curl https://your-app.onrender.com/health
```

- [ ] Health check returns 200
- [ ] Database status: "connected"
- [ ] Gemini API: "configured"

**API Documentation**:
```
https://your-app.onrender.com/docs
```

- [ ] Swagger UI loads
- [ ] All endpoints visible

**Root Endpoint**:
```bash
curl https://your-app.onrender.com/
```

- [ ] Returns welcome message

### 10. Test Authentication

```bash
# Register user
curl -X POST "https://your-app.onrender.com/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test","password":"test123","role_id":1}'

# Login
curl -X POST "https://your-app.onrender.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

- [ ] Registration works
- [ ] Login returns token

### 11. Test Database

```bash
curl "https://your-app.onrender.com/books"
```

- [ ] Books endpoint returns (empty array is OK)

### 12. Test AI Features (Optional)

```bash
curl -X POST "https://your-app.onrender.com/ai/books/search_nl" \
  -H "Content-Type: application/json" \
  -d '{"query":"science fiction"}'
```

- [ ] AI search works (if GEMINI_API_KEY set)

## Monitoring

### 13. Set Up Monitoring

- [ ] Check logs in Render dashboard
- [ ] Set up email notifications
- [ ] Monitor for errors

### 14. Performance Check

- [ ] Application responds < 2s
- [ ] No crashed instances
- [ ] Database connections working

## Optional: Production Upgrades

- [ ] Upgrade to Starter plan ($7/month) for better performance
- [ ] Add custom domain
- [ ] Set up database backups
- [ ] Configure auto-scaling

## Troubleshooting

If something fails, check:

1. **Build Logs**: Render Dashboard → Events
2. **Runtime Logs**: Render Dashboard → Logs
3. **Environment Variables**: Dashboard → Environment
4. **Database Status**: Dashboard → Database
5. **See DEPLOYMENT.md** for detailed troubleshooting

## Success Criteria

✅ All checklist items completed  
✅ Health check returning "healthy"  
✅ API documentation accessible  
✅ Authentication working  
✅ Database queries working  
✅ No errors in logs  

---

**Deployment Time**: ~15-20 minutes  
**Status**: Ready for production  

🎉 **Your API is live!**

Save your URLs:
- **API**: `https://your-app.onrender.com`
- **Docs**: `https://your-app.onrender.com/docs`
- **Health**: `https://your-app.onrender.com/health`
