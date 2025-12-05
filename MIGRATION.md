# RAG Microservice Migration Guide

This document outlines the migration from embedded RAG to microservice architecture.

## Architecture Changes

### Before (Embedded RAG)
```
┌─────────────────────────────────────────┐
│     Main Application (Render)          │
│  ┌─────────────────────────────────┐  │
│  │  FastAPI Routes                  │  │
│  ├─────────────────────────────────┤  │
│  │  PDF Service                     │  │
│  │  Embedding Service (Heavy)       │  │
│  │  Vector Store (ChromaDB)         │  │
│  │  Gemini AI                       │  │
│  └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### After (Microservice)
```
┌──────────────────────────────┐        ┌──────────────────────────────┐
│  Main App (Render)          │        │  RAG Service (HF Spaces)     │
│  ┌────────────────────────┐  │        │  ┌────────────────────────┐  │
│  │  RAG Routes            │──┼────────┼──│  Upload Endpoint       │  │
│  │  (Proxy + Auth)        │  │  HTTP  │  │  Ask Endpoint          │  │
│  ├────────────────────────┤  │        │  │  Delete Endpoint       │  │
│  │  RAG Client (httpx)    │  │        │  ├────────────────────────┤  │
│  │  Database (Postgres)   │  │        │  │  PDF Service           │  │
│  └────────────────────────┘  │        │  │  Embedding Service     │  │
└──────────────────────────────┘        │  │  Vector Store          │  │
                                        │  │  Gemini AI             │  │
                                        │  └────────────────────────┘  │
                                        └──────────────────────────────┘
```

## What Changed

### Files Modified in Main App

1. **`src/api/endpoints/rag.py`** - Refactored to proxy requests
   - Removed direct PDF processing
   - Removed direct embedding generation
   - Removed direct vector store operations
   - Added RAG client calls
   - Kept authentication and database operations

2. **`src/service/rag_client.py`** - NEW HTTP client
   - Handles communication with RAG microservice
   - Manages API key authentication
   - Handles errors and timeouts

3. **`pyproject.toml`** - Updated dependencies
   - **Removed**: chromadb, sentence-transformers, PyMuPDF, wordninja
   - **Added**: httpx
   - **Benefit**: Reduced image size, faster deployments

4. **`.env.example`** - Added configuration
   - `RAG_SERVICE_URL`: URL of HF Spaces deployment
   - `RAG_API_KEY`: API key for authentication

### New RAG Microservice Files

All files in `/rag-microservice/` directory:
- `main.py` - FastAPI application
- `Dockerfile` - Container configuration
- `requirements.txt` - Python dependencies
- `README.md` - Service documentation
- `DEPLOYMENT.md` - Deployment guide
- `service/` - Copied from main app
- `utils/` - Copied from main app
- `schema/` - Updated schemas

## Migration Steps

### 1. Before Migration

**Backup Data** (if you have existing RAG documents):
```bash
# Copy chroma_db folder
cp -r chroma_db chroma_db_backup
```

### 2. Deploy RAG Microservice

Follow `DEPLOYMENT.md` to:
1. Create HF Space
2. Configure secrets
3. Push code
4. Verify deployment

### 3. Update Main Application

```bash
# Update dependencies
cd /Users/admin/Documents/book-management-main
poetry lock
poetry install

# Update environment variables
# Add to your .env file:
RAG_SERVICE_URL=https://your-space.hf.space
RAG_API_KEY=your-api-key
```

### 4. Test Integration

```bash
# Start main app locally
poetry run uvicorn main:app --reload

# In another terminal, test RAG endpoints
curl http://localhost:8000/docs
```

### 5. Deploy to Render

```bash
# Commit changes
git add .
git commit -m "Migrate to RAG microservice architecture"
git push origin main

# Update Render environment variables via dashboard
# Then redeploy
```

6. **Verify Production**

Test RAG endpoints on your Render deployment to ensure they work with HF Spaces.

## Data Migration (Optional)

If you have existing RAG documents and want to preserve them:

### Option 1: Re-upload Documents

Simplest approach - just re-upload all PDFs through the new system.

### Option 2: Migrate ChromaDB Data

More complex but preserves vector embeddings:

1. Copy `chroma_db` folder to HF Spaces persistent storage
2. Requires manual setup and Space restart

**Recommendation**: Use Option 1 (re-upload) for simplicity.

## Rollback Plan

If you need to rollback to embedded RAG:

1. **Restore Dependencies**:
   ```bash
   # In pyproject.toml, restore:
   chromadb (>=0.5.3,<0.6.0)
   sentence-transformers (>=2.7.0,<3.0.0)
   PyMuPDF (>=1.24.0,<2.0.0)
   wordninja (>=2.0.0,<3.0.0)
   
   poetry lock
   poetry install
   ```

2. **Revert Code Changes**:
   ```bash
   git revert <commit-hash-of-migration>
   git push origin main
   ```

3. **Remove Environment Variables**:
   - Remove `RAG_SERVICE_URL` and `RAG_API_KEY` from Render

4. **Restore Database** (if needed):
   ```bash
   cp -r chroma_db_backup chroma_db
   ```

## Benefits of New Architecture

### Resource Optimization
- **Main App**: Reduced memory usage (~50% less)
- **Main App**: Faster startup time
- **Main App**: Smaller Docker image

### Scaling
- RAG service can scale independently
- Can upgrade HF Space hardware without affecting main app
- Better resource utilization

### Development
- Easier to test RAG features in isolation
- Can update RAG service without redeploying main app
- Clearer separation of concerns

### Cost (Free Tier)
- **Before**: Render free tier struggled with embedding models
- **After**: Main app uses less resources, RAG on HF Spaces handles heavy ML

## Limitations & Considerations

### Network Latency
- RAG operations now require HTTP round-trip to HF Spaces
- Typically adds 200-500ms per request
- Mitigated by efficient caching and async operations

### Dependency
- Main app now depends on HF Spaces availability
- **Mitigation**: Error handling, graceful degradation
- Consider health checks and monitoring

### API Key Management
- Must keep API keys in sync between services
- **Best Practice**: Use secret management tools
- Rotate keys periodically

## Monitoring

### Metrics to Track

**Main App**:
- RAG client request counts
- RAG client error rates
- RAG client latency

**HF Spaces**:
- Request volume
- Response times
- Error rates
- Resource usage (CPU, memory)

### Logging

Both services log RAG operations:
- Look for `[RAG Upload]`, `[RAG Ask]`, `[RAG Delete]` in logs
- Check for `[RAG Client]` in main app logs

## FAQ

### Q: Can I run both services locally for development?

Yes! Start RAG microservice on port 7860 and main app on port 8000:
```bash
# Terminal 1: RAG service
cd rag-microservice
pip install -r requirements.txt
uvicorn main:app --reload --port 7860

# Terminal 2: Main app
cd /Users/admin/Documents/book-management-main
export RAG_SERVICE_URL=http://localhost:7860
export RAG_API_KEY=test-key
poetry run uvicorn main:app --reload
```

### Q: What happens if HF Spaces is down?

The main app will return HTTP errors for RAG operations. Other features (books, users, borrowings) continue to work normally.

### Q: Can I use a different hosting provider instead of HF Spaces?

Yes! The RAG microservice is a standard Docker container. You can deploy it to:
- AWS (EC2, ECS, Lambda)
- GCP (Cloud Run, Compute Engine)
- Azure (Container Instances, App Service)
- Any Docker-compatible host

Just update `RAG_SERVICE_URL` to point to your deployment.

### Q: How do I upgrade the embedding model?

Modify `rag-microservice/service/embedding_service.py` to use a different sentence-transformers model, then redeploy to HF Spaces.

## Support

For issues or questions:
1. Check HF Spaces logs
2. Check main app logs
3. Verify environment variables
4. Test `/health` endpoint
5. Review this migration guide
