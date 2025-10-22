# SKYNET Troubleshooting Guide

## Issue: "No models available" after configuring API key

### What was fixed:

1. **Auto-registration of models**: When you add an API key, the backend now automatically creates model entries in the database for all available models from that provider.

2. **Frontend model refresh**: The frontend now properly refreshes the models list after adding an API key.

3. **Database connection**: Fixed SSL mode configuration for local PostgreSQL Docker container.

### Steps to fix and test:

#### 1. Rebuild and restart Docker containers

```bash
cd SKYNET
docker compose down
docker compose build --no-cache
docker compose up
```

Wait for all containers to be healthy. You should see:
- `postgres_db` - Database ready to accept connections
- `llm_backend` - Backend API running on port 8000
- `llm_frontend` - Frontend running on port 5000

#### 2. Test the backend API (Optional)

In a new terminal:

```bash
cd SKYNET
python test_api.py
```

This will verify:
- Backend health check
- Available models endpoint
- API key creation
- Model listing

#### 3. Access the playground

Open your browser and go to: `http://localhost:5000/playground`

#### 4. Configure an API key

1. In the left sidebar, you'll see "Configure API Providers" section
2. Find your provider (e.g., OpenAI, Anthropic, or Gemini)
3. Click "Add Key" button
4. Enter your API key when prompted
5. Click OK

#### 5. Verify models appear

After adding the API key:
- The button should change from "Add Key" to "Update Key"
- You should see "✓ API Key Configured" below the provider
- **Models should now appear in the "Models" section above**
- For example, if you added OpenAI key, you should see:
  - GPT-4 Turbo
  - GPT-4
  - GPT-3.5 Turbo

#### 6. Start chatting

1. Click on any model in the list to select it
2. Type your message in the input box at the bottom
3. Click "Send" or press Enter
4. The model will respond using your API key

### Debugging tips:

#### Check browser console

Open Developer Tools (F12) and check the Console tab for:
- "Fetched models:" - Should show an array of models
- "Fetched API keys:" - Should show your configured API keys
- Any error messages

#### Check backend logs

```bash
docker compose logs backend --tail 100
```

Look for:
- Database connection errors
- API key encryption errors
- Model registration messages

#### Check database directly

```bash
docker compose exec postgres psql -U user -d llm_playground

# In psql:
\dt                          # List all tables
SELECT * FROM api_keys;      # Check API keys
SELECT * FROM models;        # Check registered models
\q                          # Exit
```

#### Test backend API manually

```bash
# Check available models
curl http://localhost:8000/llm/available-models

# Check registered models
curl http://localhost:8000/models

# Check API keys
curl http://localhost:8000/llm/api-keys

# Add API key
curl -X POST http://localhost:8000/llm/api-keys \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "api_key": "sk-your-key-here"}'
```

### Common issues:

#### Issue: Frontend can't connect to backend

**Symptom**: Console shows "Failed to fetch" errors

**Solution**:
- Verify backend is running: `docker compose ps`
- Check backend logs: `docker compose logs backend`
- Make sure port 8000 is not blocked by firewall

#### Issue: Database connection errors

**Symptom**: Backend logs show "connection refused" or SSL errors

**Solution**:
- Check postgres container is running: `docker compose ps`
- Verify SSL_MODE is set to "disable" in docker-compose.yml
- Restart containers: `docker compose restart`

#### Issue: Models registered but not showing

**Symptom**: Database shows models but frontend doesn't display them

**Solution**:
1. Clear browser cache and reload
2. Check browser console for JavaScript errors
3. Verify API proxy is working: `curl http://localhost:5000/api/models`

#### Issue: API key encryption errors

**Symptom**: Backend logs show "ENCRYPTION_KEY must be set"

**Solution**:
- Verify ENCRYPTION_KEY is set in docker-compose.yml backend environment
- Should be: `ENCRYPTION_KEY: vafb1MNFUoJDJ90DRXnzZ0V4H1Ty1VZa0l5HQE7yxY8=`

### Architecture overview:

```
Frontend (Next.js on port 5000)
    ↓ /api/* requests proxied to backend
Backend (FastAPI on port 8000)
    ↓ Connects to
Database (PostgreSQL on port 5432)

Flow when adding API key:
1. User enters API key in frontend
2. Frontend POST to /api/llm/api-keys
3. Backend encrypts and stores API key
4. Backend auto-registers models from provider
5. Frontend refreshes models list
6. Models appear in UI
```

### Files modified:

1. `backend/database.py` - Made SSL mode configurable
2. `backend/api_routes_no_auth.py` - Added auto-registration of models
3. `frontend/app/playground/page.tsx` - Added model refresh after API key config
4. `docker-compose.yml` - Added SSL_MODE=disable for backend

### Need more help?

Check the logs for specific error messages:
```bash
# All logs
docker compose logs -f

# Just backend
docker compose logs -f backend

# Just frontend
docker compose logs -f frontend

# Just database
docker compose logs -f postgres
```
