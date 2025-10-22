# SKYNET LLM IDE Platform - Docker Setup

## Quick Start with Docker

### Prerequisites
- Docker Desktop installed and running
- Docker Compose installed (included with Docker Desktop)

### Running the Application

1. **Clone or navigate to the SKYNET directory**:
   ```bash
   cd SKYNET
   ```

2. **Start all services**:
   ```bash
   docker-compose up --build
   ```

   This will:
   - Build the frontend and backend containers
   - Start PostgreSQL database
   - Initialize all services
   - Make the application available at http://localhost:5000

3. **Stop the services**:
   ```bash
   docker-compose down
   ```

   To remove volumes (database data) as well:
   ```bash
   docker-compose down -v
   ```

### Services

The Docker Compose setup includes:

- **Frontend** (port 5000): Next.js application
- **Backend** (port 8000): FastAPI Python server
- **PostgreSQL** (port 5432): Database for storing models and sessions

### Environment Variables

The default configuration includes:
- `JWT_SECRET_KEY`: Pre-generated Fernet key for JWT signing
- `ENCRYPTION_KEY`: Pre-generated Fernet key for API key encryption
- Database credentials are set in docker-compose.yml

**For production**, you should change these keys in `docker-compose.yml`:
```yaml
environment:
  JWT_SECRET_KEY: your-production-jwt-key
  ENCRYPTION_KEY: your-production-encryption-key
```

### Generating New Keys

To generate new Fernet keys for production:
```bash
python3 << 'EOF'
from cryptography.fernet import Fernet
print(f"JWT_SECRET_KEY={Fernet.generate_key().decode()}")
print(f"ENCRYPTION_KEY={Fernet.generate_key().decode()}")
EOF
```

### Development vs Production

**Current setup is for development**. For production:

1. Edit `frontend/Dockerfile` and uncomment the production build lines:
   ```dockerfile
   RUN npm run build
   CMD ["npm", "start"]
   ```

2. Comment out the development line:
   ```dockerfile
   # CMD ["npm", "run", "dev"]
   ```

3. Update keys in docker-compose.yml with secure production keys

### Troubleshooting

**Database connection issues**:
- Wait for PostgreSQL to be ready (healthcheck runs automatically)
- Check logs: `docker-compose logs postgres`

**Frontend can't connect to backend**:
- Ensure BACKEND_URL is set to `http://backend:8000` in docker-compose.yml
- Check network connectivity: `docker-compose logs frontend`

**Build errors**:
- Clear Docker cache: `docker-compose build --no-cache`
- Remove old containers: `docker-compose down && docker system prune`

### Accessing Services

- **Frontend UI**: http://localhost:5000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432 (user: user, password: password, db: llm_playground)

### Notes

- The application runs with no authentication required by default
- All features are accessible immediately
- Data persists in Docker volumes between restarts
- For Replit deployment, use the Replit workflows instead of Docker
