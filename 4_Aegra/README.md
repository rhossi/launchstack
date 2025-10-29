# Aegra - Self-Hosted LangGraph Platform Alternative

Aegra is an open-source, self-hosted alternative to LangGraph Platform. Run agent workflows on your infrastructure with zero vendor lock-in while maintaining full API compatibility with the LangGraph Client SDK.

---

## QUICKSTART

Get Aegra running quickly for local development or production deployment.

### Prerequisites

Before starting, ensure you have:

**For Local Development:**

- `git` CLI installed
- `podman` and `podman-compose` installed
- Python 3.11+ (for running migrations)

**For Production Deployment:**

- A running Kubernetes cluster
- `kubectl` configured to access your cluster
- `git` CLI installed

### Step 1: Clone the Aegra Repository

```bash
# Clone the repository
git clone https://github.com/rhossi/aegra.git
cd aegra
```

### Step 2: Review Project Structure

The repository contains:

- **`graphs/`**: Agent definitions (ReAct agent examples)
- **`src/agent_server/`**: FastAPI application and business logic
- **`deployments/`**: Kubernetes manifests and Podman Compose files
- **`scripts/`**: Database migration and utility scripts
- **`aegra.json`**: Graph configuration file

---

### Local Development/Testing

Quick setup for testing and development using Podman Compose.

#### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Key variables to set in `.env`:

```bash
# LLM Providers (at least one required)
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=...
# TOGETHER_API_KEY=...

# Database (default for local dev)
DATABASE_URL=postgresql+asyncpg://aegra:aegra@postgres:5432/aegra

# Authentication (for dev, use noop)
AUTH_TYPE=noop

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Optional: Langfuse integration
# LANGFUSE_PUBLIC_KEY=pk-...
# LANGFUSE_SECRET_KEY=sk-...
# LANGFUSE_HOST=https://your-langfuse-instance.com
```

#### Step 4: Start Services

```bash
# Start all services (PostgreSQL + Aegra)
podman-compose up -d

# Check logs
podman-compose logs -f aegra
```

#### Step 5: Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs
```

Access Aegra at **<http://localhost:8000>**

#### Step 6: Test with LangGraph Client SDK

```python
import asyncio
from langgraph_sdk import get_client

async def main():
    # Connect to your local Aegra instance
    client = get_client(url="http://localhost:8000")
    
    # Create assistant
    assistant = await client.assistants.create(
        graph_id="agent",
        config={},
    )
    
    # Create thread
    thread = await client.threads.create()
    
    # Stream responses
    stream = client.runs.stream(
        thread_id=thread["thread_id"],
        assistant_id=assistant["assistant_id"],
        input={
            "messages": [
                {"type": "human", "content": [{"type": "text", "text": "Hello!"}]}
            ]
        },
        stream_mode=["values", "messages-tuple"],
    )
    
    async for chunk in stream:
        print(f"Received: {chunk.data}")

asyncio.run(main())
```

#### Stop Services

```bash
# Stop all services
podman-compose down

# Stop and remove volumes (clean slate)
podman-compose down -v
```

---

### Production Deployment

Deploy Aegra to your Kubernetes cluster using the included deployment manifests and scripts.

#### Step 3: Navigate to Kubernetes Deployment Directory

```bash
cd deployments/k8s
```

The `deployments/k8s/` directory contains:

- **01-namespace.yaml**: Namespace definition
- **02-configmap.yaml**: Application configuration
- **02-configmap-files.yaml**: Configuration files (aegra.json, auth.py, alembic)
- **03-secrets.example.yaml**: Template for secrets
- **04-pvc.yaml**: Persistent volume claims
- **05-postgres.yaml**: PostgreSQL deployment
- **06-aegra-app.yaml**: Aegra application deployment
- **07-services.yaml**: Kubernetes services (ClusterIP and LoadBalancer)
- **build-and-push.sh**: Script to build and push Docker image to OCI Registry
- **deploy.sh**: Automated deployment script
- **oci-setup.sh**: Helper script for OCI Container Registry authentication

#### Step 4: Configure Secrets

```bash
# Copy the secrets template
cp 03-secrets.example.yaml 03-secrets.yaml

# Generate a secure PostgreSQL password
echo -n "your-secure-password" | base64

# Edit 03-secrets.yaml with your actual values
nano 03-secrets.yaml
```

Update the following in `03-secrets.yaml`:

```yaml
data:
  # PostgreSQL password (base64 encoded)
  POSTGRES_PASSWORD: "your-base64-encoded-password"  # REQUIRED
  
  # Optional: API keys for LLM providers
  OPENAI_API_KEY: "your-openai-key-base64"  # Optional
  ANTHROPIC_API_KEY: "your-anthropic-key-base64"  # Optional
  
  # Optional: Langfuse integration
  LANGFUSE_PUBLIC_KEY: "your-public-key-base64"  # Optional
  LANGFUSE_SECRET_KEY: "your-secret-key-base64"  # Optional
```

> **Note**: All values must be base64 encoded. Use: `echo -n "your-value" | base64`

#### Step 5: Set Up OCI Container Registry

Aegra needs to be built and pushed to a container registry. The repository includes scripts optimized for OCI Container Registry.

##### Option A: Automated Setup (Recommended)

```bash
# Run the OCI setup helper script
./oci-setup.sh
```

This script will guide you through:

1. Setting your OCI namespace
2. Configuring authentication
3. Logging into the registry

##### Option B: Manual Setup

```bash
# Set your OCI namespace (find in OCI Console → Administration → Tenancy Details)
export OCI_NAMESPACE=your-namespace
export OCI_REGION=us-chicago-1  # or your region

# Login to OCI Container Registry
# For federated users (Oracle Identity Cloud Service):
podman login us-chicago-1.ocir.io \
  -u "your-namespace/oracleidentitycloudservice/your-email@domain.com" \
  -p "your-auth-token"

# For non-federated users:
podman login us-chicago-1.ocir.io \
  -u "your-namespace/your-username" \
  -p "your-auth-token"
```

> **Getting your Auth Token**: OCI Console → Profile → My profile → Auth Tokens → Generate Token

#### Step 6: Build and Push Docker Image

```bash
# Build and push the image to OCI Container Registry
./build-and-push.sh --push
```

This script will:

- Build the Docker image for linux/amd64 architecture
- Tag it with your OCI registry URL
- Push it to OCI Container Registry
- Use Podman by default (falls back to Docker if needed)

#### Step 7: Update Image Reference

Edit `06-aegra-app.yaml` and update the image reference:

```bash
# Find the line with the image reference
nano 06-aegra-app.yaml

# Change from:
# image: aegra:latest

# To:
# image: us-chicago-1.ocir.io/your-namespace/aegra:latest
```

#### Step 8: Deploy to Kubernetes

##### Option A: Automated Deployment (Recommended)

```bash
# Deploy all components
./deploy.sh

# Or deploy with Redis (optional, for caching)
./deploy.sh --with-redis
```

The `deploy.sh` script will:

- Create the namespace
- Apply all configurations in the correct order
- Deploy PostgreSQL
- Deploy Aegra application
- Create services (ClusterIP and LoadBalancer)
- Show deployment status and access information

##### Option B: Manual Deployment

```bash
# Apply manifests in order
kubectl apply -f 01-namespace.yaml
kubectl apply -f 02-configmap.yaml
kubectl apply -f 02-configmap-files.yaml
kubectl apply -f 03-secrets.yaml
kubectl apply -f 04-pvc.yaml
kubectl apply -f 05-postgres.yaml
kubectl apply -f 06-aegra-app.yaml
kubectl apply -f 07-services.yaml
```

#### Step 9: Verify Deployment

```bash
# Check pod status
kubectl get pods -n aegra

# Expected output:
# NAME                        READY   STATUS    RESTARTS   AGE
# aegra-app-xxxxxxxxx-xxxxx   1/1     Running   0          2m
# postgres-xxxxxxxxx-xxxxx    1/1     Running   0          2m

# Check logs
kubectl logs -n aegra -l app.kubernetes.io/name=aegra

# Check services
kubectl get services -n aegra
```

#### Step 10: Access Aegra

##### Option A: Port Forward (Testing)

```bash
kubectl port-forward -n aegra svc/aegra-service 8000:80
```

Access at **<http://localhost:8000>**

##### Option B: LoadBalancer (Production)

```bash
# Get external IP
kubectl get svc aegra-loadbalancer -n aegra

# Wait for EXTERNAL-IP to be assigned
# Access at http://EXTERNAL-IP
```

##### Option C: Configure Ingress (Recommended for Production)

See the [Ingress and TLS](#ingress-and-tls) section in the CUSTOMIZATION guide below.

#### Step 11: Test with LangGraph Client SDK

```python
import asyncio
from langgraph_sdk import get_client

async def main():
    # Connect to your Aegra instance
    # Use localhost:8000 for port-forward or your external IP/domain
    client = get_client(url="http://localhost:8000")
    
    # Create assistant
    assistant = await client.assistants.create(
        graph_id="agent",
        config={},
    )
    
    # Create thread
    thread = await client.threads.create()
    
    # Stream responses
    stream = client.runs.stream(
        thread_id=thread["thread_id"],
        assistant_id=assistant["assistant_id"],
        input={
            "messages": [
                {"type": "human", "content": [{"type": "text", "text": "Hello!"}]}
            ]
        },
        stream_mode=["values", "messages-tuple"],
    )
    
    async for chunk in stream:
        print(f"Received: {chunk.data}")

asyncio.run(main())
```

> **📚 Detailed Documentation**: The `deployments/k8s/README.md` file contains comprehensive documentation including:
>
> - Troubleshooting common issues
> - Scaling instructions
> - Manual container build commands
> - Production considerations
> - Security best practices
> - Backup procedures

---

### What's Included

Both deployments create:

- **Aegra API Server**: FastAPI application serving Agent Protocol endpoints
- **PostgreSQL Database**: Persistent storage for checkpoints and state
- **Database Migrations**: Alembic-managed schema migrations
- **LangGraph Integration**: Agent workflow execution engine
- **Authentication Framework**: Extensible auth system (JWT/OAuth ready)
- **Observability**: Optional Langfuse integration for tracing

---

## CUSTOMIZATION

Optional configurations for production, scaling, and advanced use cases.

### Table of Contents

- [Configuration Options](#configuration-options)
- [Kubernetes Production Setup](#kubernetes-production-setup)
- [Authentication Configuration](#authentication-configuration)
- [Custom Agent Graphs](#custom-agent-graphs)
- [Database Configuration](#database-configuration)
- [Langfuse Integration](#langfuse-integration)
- [Ingress and TLS](#ingress-and-tls)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)
- [Resources](#resources)

---

### Configuration Options

#### Environment Variables Reference

**Core Settings:**

```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
WORKERS=4

# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/aegra
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Authentication
AUTH_TYPE=noop  # noop, custom, jwt, oauth, firebase
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
TOGETHER_API_KEY=...

# Observability
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://langfuse.example.com

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

---

### Kubernetes Production Setup

#### Complete Production Deployment

Create a production-ready Kubernetes deployment:

**1. Create Namespace and Secrets:**

```bash
# Create namespace
kubectl create namespace aegra

# Create database secret
kubectl create secret generic aegra-database \
  --namespace aegra \
  --from-literal=url="postgresql+asyncpg://user:password@postgres:5432/aegra"

# Create LLM API keys secret
kubectl create secret generic aegra-llm-keys \
  --namespace aegra \
  --from-literal=openai-api-key="sk-..." \
  --from-literal=anthropic-api-key="sk-..."

# Create Langfuse secret (optional)
kubectl create secret generic aegra-langfuse \
  --namespace aegra \
  --from-literal=public-key="pk-..." \
  --from-literal=secret-key="sk-..." \
  --from-literal=host="https://langfuse.example.com"

# Create JWT secret (if using JWT auth)
kubectl create secret generic aegra-auth \
  --namespace aegra \
  --from-literal=jwt-secret="$(openssl rand -hex 32)"
```

**2. Deploy PostgreSQL (if not using external database):**

```yaml
# postgres-deployment.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: aegra
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: aegra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: aegra
        - name: POSTGRES_USER
          value: aegra
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: aegra
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

**3. Deploy Aegra Application:**

```yaml
# aegra-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aegra
  namespace: aegra
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aegra
  template:
    metadata:
      labels:
        app: aegra
    spec:
      containers:
      - name: aegra
        image: ghcr.io/rhossi/aegra:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: aegra-database
              key: url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: aegra-llm-keys
              key: openai-api-key
        - name: AUTH_TYPE
          value: "jwt"
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: aegra-auth
              key: jwt-secret
        - name: LANGFUSE_PUBLIC_KEY
          valueFrom:
            secretKeyRef:
              name: aegra-langfuse
              key: public-key
              optional: true
        - name: LANGFUSE_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: aegra-langfuse
              key: secret-key
              optional: true
        - name: LANGFUSE_HOST
          valueFrom:
            secretKeyRef:
              name: aegra-langfuse
              key: host
              optional: true
        - name: HOST
          value: "0.0.0.0"
        - name: PORT
          value: "8000"
        - name: DEBUG
          value: "false"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: aegra
  namespace: aegra
spec:
  selector:
    app: aegra
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

**4. Apply Deployments:**

```bash
kubectl apply -f postgres-deployment.yaml
kubectl apply -f aegra-deployment.yaml
```

---

### Authentication Configuration

Aegra supports multiple authentication backends:

#### No Authentication (Development Only)

```bash
AUTH_TYPE=noop
```

#### JWT Authentication

```bash
AUTH_TYPE=jwt
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

#### OAuth 2.0

```bash
AUTH_TYPE=oauth
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_AUTHORIZE_URL=https://auth.example.com/authorize
OAUTH_TOKEN_URL=https://auth.example.com/token
```

#### Firebase Authentication

```bash
AUTH_TYPE=firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=/path/to/credentials.json
```

#### Custom Authentication

Implement your own authentication by extending `src/agent_server/auth.py`:

```python
from src.agent_server.auth import AuthBackend

class CustomAuthBackend(AuthBackend):
    async def authenticate(self, request):
        # Your authentication logic
        pass
```

---

### Custom Agent Graphs

#### Define Your Own Agent

1. **Create a new graph file:**

```python
# graphs/my_agent/graph.py
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI

def create_graph():
    workflow = StateGraph(dict)
    
    def agent_node(state):
        llm = ChatOpenAI(model="gpt-4")
        response = llm.invoke(state["messages"])
        return {"messages": [response]}
    
    workflow.add_node("agent", agent_node)
    workflow.set_entry_point("agent")
    workflow.set_finish_point("agent")
    
    return workflow.compile()

graph = create_graph()
```

1. **Register in `aegra.json`:**

```json
{
  "graphs": {
    "agent": "./graphs/react_agent/graph.py:graph",
    "my_agent": "./graphs/my_agent/graph.py:graph"
  }
}
```

1. **Restart Aegra to load the new graph:**

```bash
# Podman Compose
podman-compose restart aegra

# Kubernetes
kubectl rollout restart deployment/aegra -n aegra
```

---

### Database Configuration

#### Use External PostgreSQL (Recommended for Production)

Update your database connection to use a managed PostgreSQL instance:

```bash
# OCI Autonomous Database
DATABASE_URL=postgresql+asyncpg://user:password@host.oraclecloud.com:1522/dbname

# AWS RDS
DATABASE_URL=postgresql+asyncpg://user:password@mydb.abc123.us-east-1.rds.amazonaws.com:5432/aegra

# Google Cloud SQL
DATABASE_URL=postgresql+asyncpg://user:password@/aegra?host=/cloudsql/project:region:instance
```

#### Connection Pool Configuration

```bash
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
```

#### Database Migrations

```bash
# Check current version
python3 scripts/migrate.py current

# Upgrade to latest
python3 scripts/migrate.py upgrade

# Downgrade one version
python3 scripts/migrate.py downgrade -1

# Create new migration
python3 scripts/migrate.py revision --autogenerate -m "Add new feature"
```

---

### Langfuse Integration

Aegra integrates seamlessly with Langfuse for observability and tracing.

#### Enable Langfuse

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://langfuse.example.com
```

#### Configure in Kubernetes

Use the Langfuse secret created in the production setup:

```yaml
env:
- name: LANGFUSE_PUBLIC_KEY
  valueFrom:
    secretKeyRef:
      name: aegra-langfuse
      key: public-key
- name: LANGFUSE_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: aegra-langfuse
      key: secret-key
- name: LANGFUSE_HOST
  valueFrom:
    secretKeyRef:
      name: aegra-langfuse
      key: host
```

#### View Traces

1. Access your Langfuse instance
2. Navigate to **Traces** section
3. Filter by project/tags to see Aegra traces
4. Analyze agent performance, costs, and latency

---

### Ingress and TLS

#### Configure Ingress with cert-manager

```yaml
# aegra-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aegra-ingress
  namespace: aegra
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/websocket-services: "aegra"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - aegra.yourdomain.com
    secretName: aegra-tls
  rules:
  - host: aegra.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: aegra
            port:
              number: 8000
```

Apply the ingress:

```bash
kubectl apply -f aegra-ingress.yaml
```

#### Access Aegra

```python
from langgraph_sdk import get_client

client = get_client(url="https://aegra.yourdomain.com")
```

---

### Scaling

#### Horizontal Pod Autoscaling

```yaml
# aegra-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aegra-hpa
  namespace: aegra
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aegra
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

Apply autoscaling:

```bash
kubectl apply -f aegra-hpa.yaml
```

#### Adjust Resource Limits

For high-traffic scenarios:

```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "2000m"
  limits:
    memory: "8Gi"
    cpu: "8000m"
```

#### Database Scaling

- Use PostgreSQL read replicas for read-heavy workloads
- Enable connection pooling with PgBouncer
- Use managed database services with automatic scaling

---

### Troubleshooting

#### Pods Not Starting

Check pod status and logs:

```bash
kubectl get pods -n aegra
kubectl describe pod -n aegra <pod-name>
kubectl logs -n aegra <pod-name>
```

Common issues:

- **ImagePullBackOff**: Verify image name and registry access
- **CrashLoopBackOff**: Check environment variables and secrets
- **Pending**: Check resource availability and storage class

#### Database Connection Issues

Test database connectivity:

```bash
kubectl exec -n aegra <aegra-pod> -- \
  python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('$DATABASE_URL'))"
```

Verify secrets:

```bash
kubectl get secret -n aegra aegra-database -o yaml
```

#### API Errors

Check application logs:

```bash
kubectl logs -n aegra -l app=aegra --tail=100 -f
```

Enable debug mode temporarily:

```bash
kubectl set env deployment/aegra -n aegra DEBUG=true
```

#### Migration Failures

Check migration status:

```bash
# From local machine with DATABASE_URL set
python3 scripts/migrate.py current
python3 scripts/migrate.py history
```

Force migration:

```bash
python3 scripts/migrate.py stamp head
```

#### Health Check Failures

Test health endpoint:

```bash
kubectl port-forward -n aegra svc/aegra 8000:8000
curl http://localhost:8000/health
```

#### LLM API Key Issues

Verify secrets are correctly set:

```bash
kubectl get secret -n aegra aegra-llm-keys -o jsonpath='{.data.openai-api-key}' | base64 -d
```

---

### Maintenance

#### Updating Aegra

```bash
# Podman Compose
podman-compose pull aegra
podman-compose up -d aegra

# Kubernetes
kubectl set image deployment/aegra -n aegra \
  aegra=ghcr.io/rhossi/aegra:latest
kubectl rollout status deployment/aegra -n aegra
```

#### Backup Database

```bash
# Create backup
kubectl exec -n aegra postgres-0 -- \
  pg_dump -U aegra aegra > aegra-backup-$(date +%Y%m%d).sql

# Restore from backup
kubectl exec -i -n aegra postgres-0 -- \
  psql -U aegra aegra < aegra-backup-20250101.sql
```

#### View Logs

```bash
# All Aegra pods
kubectl logs -n aegra -l app=aegra --tail=100

# Follow logs
kubectl logs -n aegra -l app=aegra -f

# Specific pod
kubectl logs -n aegra <pod-name>
```

#### Monitor Resource Usage

```bash
# Pod resource usage
kubectl top pods -n aegra

# Node resource usage
kubectl top nodes
```

#### Export Configuration

```bash
# Export deployments
kubectl get deployment -n aegra aegra -o yaml > aegra-deployment-backup.yaml

# Export secrets (store securely!)
kubectl get secrets -n aegra -o yaml > aegra-secrets-backup.yaml
```

#### Uninstalling

**Podman Compose:**

```bash
podman-compose down -v  # -v removes volumes
```

**Kubernetes:**

```bash
# Delete all resources
kubectl delete namespace aegra
```

> **Warning**: This permanently deletes all data. Backup important data first!

---

### Resources

#### Official Documentation

- [Aegra GitHub Repository](https://github.com/rhossi/aegra)
- [Aegra Developer Guide](https://github.com/rhossi/aegra/blob/main/docs/developer-guide.md)
- [Migration Cheatsheet](https://github.com/rhossi/aegra/blob/main/docs/migration-cheatsheet.md)
- [Agent Protocol Specification](https://github.com/microsoft/agent-protocol)

#### LangGraph Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Client SDK](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/)
- [LangGraph Examples](https://github.com/langchain-ai/langgraph/tree/main/examples)

#### Agent Chat UI

- [Agent Chat UI Repository](https://github.com/langchain-ai/agent-chat-ui)
- [Agent Chat UI Setup Guide](https://github.com/rhossi/aegra/blob/main/docs/agent-chat-ui.md)

#### Observability

- [Langfuse Documentation](https://langfuse.com/docs)
- [Langfuse Python SDK](https://langfuse.com/docs/sdk/python)

#### Community

- [Aegra GitHub Discussions](https://github.com/rhossi/aegra/discussions)
- [Aegra Issues](https://github.com/rhossi/aegra/issues)
- [LangChain Discord](https://discord.gg/langchain)

#### Integration Examples

**Python Client Example:**

```bash
pip install langgraph-sdk
```

```python
from langgraph_sdk import get_client
import asyncio

async def main():
    client = get_client(url="https://aegra.yourdomain.com")
    
    # List available assistants
    assistants = await client.assistants.list()
    print(f"Available assistants: {assistants}")
    
    # Create and use thread
    thread = await client.threads.create()
    response = await client.runs.create(
        thread_id=thread["thread_id"],
        assistant_id="agent",
        input={"messages": [{"type": "human", "content": "Hello"}]}
    )

asyncio.run(main())
```

**JavaScript/TypeScript Client Example:**

```bash
npm install @langchain/langgraph-sdk
```

```typescript
import { Client } from "@langchain/langgraph-sdk";

const client = new Client({
  apiUrl: "https://aegra.yourdomain.com"
});

// Create thread and run agent
const thread = await client.threads.create();
const response = await client.runs.stream(
  thread.thread_id,
  "agent",
  {
    input: {
      messages: [{ type: "human", content: "Hello" }]
    }
  }
);

for await (const chunk of response) {
  console.log(chunk);
}
```

#### Files in This Directory

- **`README.md`** (this file): Complete setup and configuration guide
- **`aegra.md`**: Original installation notes (reference)

#### Architecture Diagram

```text
Client → Aegra API → LangGraph SDK → PostgreSQL
  ↓         ↓            ↓              ↓
SDK     FastAPI     State Mgmt    Checkpoints
```

#### Key Features

- ✅ **Agent Protocol Compliant**: Standard REST API for LLM agents
- ✅ **LangGraph SDK Compatible**: Drop-in replacement for LangGraph Platform
- ✅ **Self-Hosted**: Run on your infrastructure
- ✅ **Zero Vendor Lock-in**: Apache 2.0 license
- ✅ **Production Ready**: PostgreSQL persistence, streaming, authentication
- ✅ **Extensible**: Custom auth, graphs, and integrations
- ✅ **Observable**: Built-in Langfuse integration

#### Comparison with LangGraph Cloud

| Feature | LangGraph Cloud | Aegra |
|---------|----------------|-------|
| **Hosting** | SaaS (managed) | Self-hosted |
| **Cost** | $$$+ per month | Infrastructure cost only |
| **Data Control** | Third-party | Your infrastructure |
| **Customization** | Limited | Full control |
| **Authentication** | Platform-managed | Custom (JWT/OAuth/Firebase) |
| **Database** | Managed | BYO PostgreSQL |
| **Observability** | LangSmith (forced) | Your choice (Langfuse/None) |
| **API Compatibility** | LangGraph SDK | ✅ Same SDK |

#### Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting) above
2. Review [Aegra documentation](https://github.com/rhossi/aegra)
3. Search [GitHub issues](https://github.com/rhossi/aegra/issues)
4. Open a new issue with detailed information
5. Ask in [GitHub Discussions](https://github.com/rhossi/aegra/discussions)

---

Happy Agent Building! 🤖🚀
