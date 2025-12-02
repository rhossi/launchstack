# Stack & Agent Management Web Application

Full-stack web application for managing stacks and agents with Kubernetes integration. Each stack maps to a Kubernetes namespace and contains multiple agents deployed as Kubernetes deployments.

## Architecture

- **Stack** = Kubernetes namespace (e.g., `stack-123`)
- **Agent** = Kubernetes deployment within a stack's namespace
- **One stack** → **Many agents**
- **One agent** → **One stack**

When you create a stack, the system:
1. Creates a Kubernetes namespace
2. Creates a disk directory structure
3. Stores stack metadata in PostgreSQL

When you create an agent, the system:
1. Accepts a ZIP file upload containing agent code
2. Extracts the code to disk
3. Creates Kubernetes Deployment, Service, and Ingress
4. Mounts the code directory as a hostPath volume

## Tech Stack

- **Frontend**: Next.js 14+ (App Router), React Server Components, Shadcn UI, Tailwind CSS, TypeScript
- **Backend**: FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, PostgreSQL
- **Kubernetes**: Kubernetes Python SDK (`kubernetes` library) for namespace and deployment management
- **Authentication**: JWT tokens (access + refresh)
- **Development**: Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)
- UV (Python package manager)
- Kubernetes cluster access (for production deployment)
- Kubernetes Python SDK automatically handles cluster access via:
  - In-cluster config (when running inside K8s pods)
  - Kubeconfig file (for local development - optional, auto-detected)

### Setup

1. **Clone the repository**

2. **Start services with Docker Compose**

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database on port 5432
- FastAPI backend on port 8000
- Next.js frontend on port 3001 (mapped from container port 3000)

**Note**: The backend uses volume mounts and `--reload`, so code changes are picked up automatically. However, environment variable changes in `docker-compose.yml` require a container restart: `docker-compose restart backend`

3. **Configure environment variables**

```bash
cd backend
cp .env.example .env
# Edit .env with your database credentials if needed
```

4. **Run database migrations**

```bash
cd backend
alembic upgrade head
```

Or if using Docker:

```bash
docker-compose exec backend alembic upgrade head
```

**Note on Docker vs Local Development:**
- **Docker**: Environment variables in `docker-compose.yml` override `config.py` defaults. Changes to env vars require: `docker-compose restart backend`
- **Local**: Uses `.env` file and `config.py` defaults. Code changes auto-reload with `--reload` flag.
- **Rebuild needed**: Only if you change `pyproject.toml` dependencies or Dockerfile: `docker-compose build backend`

4. **Verify backend is running**

Test the backend health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response: `{"status":"healthy"}`

If this fails, check backend logs:
```bash
docker-compose logs backend
```

5. **Access the application**

- Frontend: http://localhost:3001
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

**Troubleshooting "Cannot connect to backend API":**

1. **Verify backend is running:**
   ```bash
   docker-compose ps
   # Should show backend as "Up"
   ```

2. **Check backend logs for errors:**
   ```bash
   docker-compose logs backend
   ```

3. **Test backend directly:**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/
   ```

4. **If frontend runs locally (not Docker):**
   - Ensure `frontend/.env.local` exists with `NEXT_PUBLIC_API_URL=http://localhost:8000`
   - Restart Next.js dev server after creating/editing `.env.local`

5. **If frontend runs in Docker:**
   - **Important**: `NEXT_PUBLIC_*` env vars are embedded at build time in Next.js
   - If you changed `NEXT_PUBLIC_API_URL` in `docker-compose.yml`, you must rebuild:
     ```bash
     docker-compose build frontend
     docker-compose up -d frontend
     ```
   - Or restart with rebuild: `docker-compose up -d --build frontend`

## Development

### Backend

```bash
cd backend

# Install dependencies with UV
uv pip install -e .

# Run migrations
alembic upgrade head

# Run development server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## Environment Variables

### Backend

Create `backend/.env`:

```
DATABASE_URL=postgresql+asyncpg://stackagent:dev_password@localhost:5432/stack_agent_db
SECRET_KEY=your-secret-key-here-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
ENVIRONMENT=development
```

#### SECRET_KEY Explained

The `SECRET_KEY` is used to sign and verify JWT (JSON Web Token) tokens for user authentication. It must be:
- **At least 32 characters long** (required for security)
- **Random and unpredictable** (never use predictable values like "password123")
- **Kept secret** (never commit to version control, use different keys for dev/prod)

**How to generate a secure SECRET_KEY:**

**Option 1: Using Python (recommended)**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Option 2: Using OpenSSL**
```bash
openssl rand -hex 32
```

**Option 3: Using Python's secrets module**
```python
import secrets
print(secrets.token_urlsafe(32))
```

**Example output:**
```
SECRET_KEY=K8jX2mP9qL5nR7sT3vW6yZ1aB4cD8eF0gH2iJ5kM9oP3qR6sT9uV2wX5yZ8a
```

**⚠️ Security Warning:**
- Use a **different SECRET_KEY** for production than development
- If you change the SECRET_KEY, all existing JWT tokens will become invalid (users will need to log in again)
- Store production SECRET_KEY securely (environment variables, secret management service)
- Never expose the SECRET_KEY in logs, error messages, or client-side code

# Kubernetes configuration (optional)
K8S_CONFIG_PATH=/path/to/kubeconfig  # Path to kubeconfig file (default: auto-detect)
KUBECONFIG=/path/to/kubeconfig      # Alternative env var name

# Agent platform file system configuration
AGENT_PLATFORM_BASE_PATH=/var/agent-platform  # Base path for agent code storage

# Ingress configuration
INGRESS_HOST=agents.yourdomain.com  # Hostname for ingress rules
```

### Frontend

Create `frontend/.env.local` (copy from `.env.local.example`):

```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local if your backend runs on a different URL
```

Or create it manually:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Note**: If running via Docker Compose, the API URL is automatically set. This file is only needed for local development outside Docker.

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Project Structure

```
stack-agent-manager/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── routers/  # API routes
│   │   ├── services/ # Business logic
│   │   └── utils/    # Utilities
│   │       ├── k8s.py          # Kubernetes client utilities
│   │       ├── k8s_deploy.py   # K8s deployment manifests
│   │       └── filesystem.py   # Disk layout operations
│   └── alembic/      # Database migrations
├── frontend/         # Next.js frontend
│   ├── app/          # App Router pages
│   ├── components/   # React components
│   ├── lib/          # Utilities and API client
│   └── types/        # TypeScript types
└── docker-compose.yml
```

## Disk Layout

Agent code is stored on disk following this structure:

```
/var/agent-platform/
  stacks/
    <stack-id>/
      agents/
        <agent-id>/
          agent.zip          # Uploaded zip file
          extracted/         # Extracted agent code
            graph.py
            config.yaml
            ...
```

This directory structure is mounted into Kubernetes pods via `hostPath` volumes.

## Features

- **User Authentication**: Register, login, logout with JWT tokens
- **Stack Management**: 
  - Create stacks (automatically creates K8s namespace)
  - List, view, update, delete stacks
  - Each stack maps to a Kubernetes namespace
- **Agent Management**:
  - Create agents with ZIP file upload
  - Automatic code extraction and deployment
  - Kubernetes Deployment, Service, and Ingress creation
  - Agent status tracking (pending, deploying, running, failed)
  - API and UI URLs for each agent
- **Authorization**: Users can only modify their own resources
- **Responsive Design**: Modern UI with Shadcn components
- **Kubernetes Integration**: Full lifecycle management of K8s resources

## API Endpoints

### Stacks

- `POST /api/stacks` - Create a new stack (creates K8s namespace)
- `GET /api/stacks` - List stacks with pagination
- `GET /api/stacks/{stack_id}` - Get stack details with agents
- `PUT /api/stacks/{stack_id}` - Update stack
- `DELETE /api/stacks/{stack_id}` - Delete stack (deletes K8s namespace and all agents)

### Agents

- `POST /api/stacks/{stack_id}/agents` - Create agent (multipart form with ZIP file)
- `GET /api/stacks/{stack_id}/agents` - List agents in a stack
- `GET /api/agents/{agent_id}` - Get agent details
- `PUT /api/agents/{agent_id}` - Update agent
- `DELETE /api/agents/{agent_id}` - Delete agent (removes K8s resources)

See http://localhost:8000/docs for interactive API documentation.

## Kubernetes Deployment

### Prerequisites

- Access to a Kubernetes cluster
- Kubernetes Python SDK will automatically authenticate using:
  - In-cluster config (when running inside K8s pods)
  - Kubeconfig file (for local development - auto-detected from `~/.kube/config` or `KUBECONFIG` env var)
- Ingress controller installed (for agent URLs)

**Note**: `kubectl` is not required for the application to work. It's only useful for manual cluster operations and testing. The Python SDK handles all K8s API interactions.

### Configuration

The Kubernetes Python SDK automatically detects cluster configuration:
1. **In-cluster config** (when running inside K8s pods) - automatically detected
2. **Kubeconfig file** (for local development) - auto-detected from:
   - `~/.kube/config` (default location)
   - `KUBECONFIG` environment variable
   - `K8S_CONFIG_PATH` environment variable (custom path)

**Note**: `kubectl` is not required for the application to work. It's only useful for manual cluster operations and testing. The Python SDK handles all K8s API interactions.

### Agent Deployment Details

When an agent is created:
1. ZIP file is uploaded and saved to disk
2. Code is extracted to `extracted/` directory
3. Kubernetes Deployment is created with:
   - Image: `iad.ocir.io/tenant/aegra-runtime:latest` (configurable)
   - Volume mount: Agent code directory → `/app/graphs`
   - Port: 8000
4. Kubernetes Service exposes the deployment
5. Kubernetes Ingress creates public URL: `https://{INGRESS_HOST}/stacks/{stack_id}/agents/{agent_id}/`

### Production Considerations

- Ensure `/var/agent-platform` is accessible from Kubernetes nodes
- Configure persistent storage if needed
- Set up ingress controller with proper TLS certificates
- Configure image pull secrets for private registries
- Monitor disk space for agent code storage

## License

MIT

