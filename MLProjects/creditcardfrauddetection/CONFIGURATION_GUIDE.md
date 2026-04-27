# Configuration Guide: Local vs Docker Deployment

## Overview
This guide explains the configuration differences between local and Docker deployments of the Credit Card Fraud Detection System.

---

## 🏠 LOCAL DEPLOYMENT

### Environment File: `.env.local`

**Key Configuration Points:**

1. **API Server Settings**
   ```env
   APP_ENV=development
   DEBUG=True
   HOST=0.0.0.0
   PORT=8000
   ```
   - Runs in development mode with debug enabled
   - Listens on all interfaces (0.0.0.0) but binds to port 8000

2. **UI API Connection** ✨ **CRITICAL**
   ```env
   API_URL=http://localhost:8000
   API_BASE_URL=http://localhost:8000
   ```
   - UI connects to API via **localhost** (127.0.0.1)
   - Both services run on the same machine

3. **Authentication**
   ```env
   AUTH_REQUIRED=False
   API_KEY=development_api_key_for_testing
   ```
   - Relaxed authentication for local testing

4. **LLM Services**
   ```env
   USE_LOCAL_LLM=True
   FORCE_LOCAL_LLM=False
   LOCAL_LLM_API_URL=http://localhost:11434/api
   ```
   - Can connect to locally running Ollama on port 11434
   - Falls back to enhanced mock if unavailable

5. **File Paths**
   - All paths are relative to project root
   - Data: `./data/`
   - Logs: `./logs/`
   - Models: `./models/`
   - ChromaDB: `./data/chroma_db/`

### Launch Commands
```powershell
# Option 1: Using launch script
.\launch_local.ps1

# Option 2: Manual launch
# Terminal 1 - API Server
cd D:\Study\AILearning\MLProjects\creditcardfrauddetection
& "D:\Study\AILearning\shared_Environment\Scripts\python.exe" run_server.py

# Terminal 2 - UI Dashboard
cd D:\Study\AILearning\MLProjects\creditcardfrauddetection\ui
& "D:\Study\AILearning\shared_Environment\Scripts\streamlit.exe" run app.py --server.port 8501
```

### Access URLs
- **Dashboard**: http://localhost:8501
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🐳 DOCKER DEPLOYMENT

### Environment File: `.env.docker`

**Key Configuration Points:**

1. **API Server Settings**
   ```env
   APP_ENV=production
   DEBUG=False
   HOST=0.0.0.0
   PORT=8000
   ```
   - Runs in production mode (debug disabled)
   - Stricter error handling

2. **UI API Connection** ✨ **CRITICAL**
   ```env
   API_URL=http://fraud-detection-api:8000
   API_BASE_URL=http://fraud-detection-api:8000
   ```
   - UI connects to API via **Docker service name** (`fraud-detection-api`)
   - Docker's internal DNS resolves service names to container IPs
   - Services communicate within Docker network

3. **Authentication**
   ```env
   AUTH_REQUIRED=False
   API_KEY=development_api_key_for_testing
   SECRET_KEY=production_secret_key_change_in_prod
   ```
   - **IMPORTANT**: Change `SECRET_KEY` in production!

4. **LLM Services**
   ```env
   USE_LOCAL_LLM=True
   LOCAL_LLM_API_URL=http://ollama:11434/api
   ```
   - Connects to Ollama container via service name `ollama`

5. **File Paths**
   - Paths mapped via Docker volumes
   - Data: `/app/data/` → `./data/`
   - Logs: `/app/logs/` → `./logs/`
   - Models: `/app/models/` → `./models/`
   - ChromaDB: `/app/data/chroma_db/` → `./data/chroma_db/`

### Launch Commands
```powershell
# Option 1: Using launch script
.\launch_docker.ps1

# Option 2: Manual docker-compose
docker-compose -f docker-compose.yml --env-file .env.docker up -d
```

### Access URLs
- **Dashboard**: http://localhost:8501
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

*Note: Same external URLs as local, but internal communication uses service names*

---

## 📊 Configuration Comparison Matrix

| Setting | Local | Docker | Purpose |
|---------|-------|--------|---------|
| **API_URL** | `http://localhost:8000` | `http://fraud-detection-api:8000` | UI → API connection |
| **APP_ENV** | `development` | `production` | Environment mode |
| **DEBUG** | `True` | `False` | Debug mode |
| **LOCAL_LLM_API_URL** | `http://localhost:11434/api` | `http://ollama:11434/api` | Ollama connection |
| **File Paths** | Relative (`./data/`) | Absolute (`/app/data/`) | Data location |
| **SECRET_KEY** | `development_secret...` | `production_secret...` | Security key |
| **Network** | Host network | Docker bridge network | Network isolation |

---

## 🔧 Troubleshooting

### Local Deployment Issues

**Issue**: UI shows "Connection failed" with `http://fraud-detection-api:8000`
```
✗ Solution: Ensure .env.local is loaded (not .env.docker)
✓ Verify: Check UI sidebar shows http://localhost:8000
```

**Issue**: API not accessible on localhost:8000
```
✗ Check: Is API server running? Look for "Uvicorn running on..." message
✓ Test: curl http://localhost:8000/health
```

**Issue**: Pydantic ValidationError with extra fields
```
✗ Solution: Remove unsupported fields from .env.local
✓ Fields to remove: DEPLOYMENT_MODE, DATA_DIR, LOGS_DIR, MODELS_DIR
```

### Docker Deployment Issues

**Issue**: UI can't connect to API
```
✗ Check: Services on same Docker network?
✓ Verify: docker network inspect creditcardfrauddetection_default
```

**Issue**: Services start but can't communicate
```
✗ Check: Is API_URL set to service name (fraud-detection-api)?
✓ Verify: docker-compose logs to see connection attempts
```

**Issue**: Volumes not persisting data
```
✗ Check: Volume mappings in docker-compose.yml
✓ Verify: docker volume ls and inspect volume paths
```

---

## 🎯 Best Practices

### For Local Development
1. ✅ Always use `.env.local` file
2. ✅ Set `DEBUG=True` to see detailed errors
3. ✅ Use `http://localhost:8000` for API URL
4. ✅ Run services in separate terminal windows for easy debugging
5. ✅ Check logs in `./logs/` directory

### For Docker Deployment
1. ✅ Always use `.env.docker` file
2. ✅ Set `DEBUG=False` in production
3. ✅ Use Docker service names for internal communication
4. ✅ Change `SECRET_KEY` before deploying to production
5. ✅ Use `docker-compose logs -f` to monitor all services
6. ✅ Persist data with named volumes

### Configuration Management
1. ✅ Never commit `.env` files with real credentials to git
2. ✅ Use `.env.example` as template
3. ✅ Document all environment variables
4. ✅ Validate configuration on startup
5. ✅ Use different API keys for dev/prod

---

## 📝 Environment Variable Reference

### API Settings
- `APP_ENV`: Environment mode (development/production)
- `DEBUG`: Enable debug mode (True/False)
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `SECRET_KEY`: Security key for sessions/tokens
- `HOST`: Server bind address (0.0.0.0)
- `PORT`: Server port (8000)
- `WORKERS`: Number of worker processes (4)

### UI Settings
- `API_URL`: Primary API endpoint URL
- `API_BASE_URL`: Alternative API URL (fallback)

### Authentication
- `AUTH_REQUIRED`: Enable API authentication (True/False)
- `API_KEY`: API key for authentication

### OpenAI
- `OPENAI_API_KEY`: OpenAI API key
- `LLM_MODEL`: Model name (gpt-3.5-turbo)
- `EMBEDDING_MODEL`: Embedding model (sentence-transformers/all-MiniLM-L6-v2)

### Vector Database
- `USE_PINECONE`: Use Pinecone instead of ChromaDB (True/False)
- `VECTOR_DIMENSION`: Embedding dimension (384)
- `EMBEDDING_BATCH_SIZE`: Batch size for embeddings (32)

### Fraud Detection
- `CONFIDENCE_THRESHOLD`: Minimum confidence for fraud detection (0.85)
- `DEFAULT_SIMILARITY_THRESHOLD`: Pattern matching threshold (0.75)
- `TRANSACTION_HISTORY_WINDOW`: Days to analyze history (30)

### LLM Fallback
- `USE_LOCAL_LLM`: Enable local LLM (True/False)
- `FORCE_LOCAL_LLM`: Force local LLM only (True/False)
- `LOCAL_LLM_MODEL`: Model name (llama3)
- `LOCAL_LLM_API_URL`: Ollama API URL

---

## 🚀 Quick Start Checklists

### Local Deployment Checklist
- [ ] Copy `.env.local` to `.env` (or ensure .env.local is loaded)
- [ ] Verify `API_URL=http://localhost:8000` in config
- [ ] Activate Python environment
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Start API server (`python run_server.py`)
- [ ] Start UI dashboard (`streamlit run ui/app.py`)
- [ ] Verify both services accessible
- [ ] Test fraud detection with sample transaction

### Docker Deployment Checklist
- [ ] Verify `.env.docker` exists with correct settings
- [ ] Ensure `API_URL=http://fraud-detection-api:8000`
- [ ] Build Docker images (`docker-compose build`)
- [ ] Start services (`docker-compose up -d`)
- [ ] Check container status (`docker-compose ps`)
- [ ] Verify logs (`docker-compose logs -f`)
- [ ] Test API health (`curl http://localhost:8000/health`)
- [ ] Access UI dashboard (`http://localhost:8501`)

---

## 📞 Support

For configuration issues:
1. Check this guide first
2. Review logs (local: `./logs/`, Docker: `docker-compose logs`)
3. Verify environment variables are loaded correctly
4. Test API connectivity separately from UI
5. Consult README.md for additional deployment details

---

**Last Updated**: February 18, 2026
**Version**: 2.0
