# Docker Setup Guide

## Prerequisites

- Docker installed on your system
- Docker Compose installed

## Quick Start

1. **Navigate to the SKYNET directory:**
   ```bash
   cd SKYNET
   ```

2. **Run the application:**
   ```bash
   docker-compose up --build
   ```

   This will:
   - Build all three services (postgres, backend, frontend)
   - Start them in the correct order with proper health checks
   - Wait for each service to be ready before starting dependent services

3. **Access the application:**
   - Frontend: http://localhost:5000
   - Backend API: http://localhost:8000
   - Backend Health Check: http://localhost:8000/health
   - Backend Docs: http://localhost:8000/docs

## What's Fixed

The Docker configuration now includes:

1. **Backend Health Check** - The backend service has a health check that verifies the API is responding
2. **Proper Service Dependencies** - The frontend waits for the backend to be healthy before starting
3. **Optimized Builds** - `.dockerignore` files exclude unnecessary files from Docker builds
4. **Environment Variables** - All required environment variables are properly configured

## Service Architecture

```
┌─────────────────┐
│   PostgreSQL    │
│   (port 5432)   │
└────────┬────────┘
         │
         │ (waits for DB to be healthy)
         ▼
┌─────────────────┐
│  Backend (API)  │
│   (port 8000)   │
└────────┬────────┘
         │
         │ (waits for backend to be healthy)
         ▼
┌─────────────────┐
│  Frontend (UI)  │
│   (port 5000)   │
└─────────────────┘
```

## Environment Variables

The default configuration uses these values (defined in docker-compose.yml):

- **Database**: `postgresql://user:password@postgres:5432/llm_playground`
- **JWT Secret**: Pre-configured for development
- **Backend URL**: `http://backend:8000` (internal Docker networking)

For production or custom configuration, create a `.env` file in the SKYNET directory based on `.env.example`.

## Optional: LLM Provider API Keys

If you want to use OpenAI, Anthropic, or Gemini models, add these environment variables to the `backend` service in `docker-compose.yml`:

```yaml
environment:
  OPENAI_API_KEY: your-key-here
  ANTHROPIC_API_KEY: your-key-here
  GEMINI_API_KEY: your-key-here
```

## Stopping the Application

```bash
docker-compose down
```

To also remove volumes (database data):
```bash
docker-compose down -v
```

## Troubleshooting

### Frontend can't connect to backend
- Verify all services are running: `docker-compose ps`
- Check backend health: `curl http://localhost:8000/health`
- Check logs: `docker-compose logs backend`

### Database connection errors
- Ensure postgres service is healthy: `docker-compose ps`
- Check logs: `docker-compose logs postgres`

### Port already in use
If ports 5000, 8000, or 5432 are already in use, edit `docker-compose.yml` and change the port mappings:
```yaml
ports:
  - "NEW_PORT:5000"  # Change NEW_PORT to an available port
```

## Development

To rebuild after code changes:
```bash
docker-compose up --build
```

To restart a specific service:
```bash
docker-compose restart backend
```

To view logs for a specific service:
```bash
docker-compose logs -f backend
```
