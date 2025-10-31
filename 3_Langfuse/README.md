# Langfuse - LLM Observability Platform

Langfuse is an open-source LLM engineering platform that provides observability and analytics for Large Language Model applications. Deploy it to your Kubernetes cluster using the official Langfuse Helm chart.

> **📖 [Back to Launchstack Overview](../README.md)** | This component is part of the [Launchstack](https://github.com/yourusername/launchstack) infrastructure stack.

---

## QUICKSTART

Everything you need to get Langfuse running in your cluster.

### Prerequisites

Before installing, ensure you have:

- A running Kubernetes cluster
- `kubectl` configured to access your cluster
- `helm` CLI installed (v3.x or later)
- `openssl` available for generating secure secrets
- Sufficient cluster resources (recommended: at least 8GB RAM, 4 CPUs available)

### Installation Steps

#### Step 1: Add Helm Repository

```bash
helm repo add langfuse https://langfuse.github.io/langfuse-k8s
helm repo update
```

#### Step 2: Create Langfuse Namespace

```bash
kubectl create namespace langfuse
```

#### Step 3: Generate and Apply Secrets

Create secure secrets for all Langfuse components:

```bash
cat > langfuse-secrets.yaml <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: langfuse-general
  namespace: langfuse
type: Opaque
stringData:
  salt: $(openssl rand -hex 32)
---
apiVersion: v1
kind: Secret
metadata:
  name: langfuse-nextauth-secret
  namespace: langfuse
type: Opaque
stringData:
  nextauth-secret: $(openssl rand -hex 32)
---
apiVersion: v1
kind: Secret
metadata:
  name: langfuse-postgresql-auth
  namespace: langfuse
type: Opaque
stringData:
  password: $(openssl rand -hex 32)
  postgres-password: $(openssl rand -hex 32)
---
apiVersion: v1
kind: Secret
metadata:
  name: langfuse-clickhouse-auth
  namespace: langfuse
type: Opaque
stringData:
  password: $(openssl rand -hex 32)
---
apiVersion: v1
kind: Secret
metadata:
  name: langfuse-redis-auth
  namespace: langfuse
type: Opaque
stringData:
  password: $(openssl rand -hex 32)
---
apiVersion: v1
kind: Secret
metadata:
  name: langfuse-s3-auth
  namespace: langfuse
type: Opaque
stringData:
  rootUser: admin
  rootPassword: $(openssl rand -hex 32)
EOF
```

Apply the secrets:

```bash
kubectl apply -f langfuse-secrets.yaml
```

> **Important**: Keep `langfuse-secrets.yaml` secure and never commit it to version control.

#### Step 4: Generate Langfuse Values Configuration

Create your basic configuration file:

```bash
cat > langfuse-values.yaml <<'EOF'
langfuse:
  salt:
    secretKeyRef:
      name: langfuse-general
      key: salt
  
  nextauth:
    url: "http://localhost:3000"  # Change this to your domain for production
    secret:
      secretKeyRef:
        name: langfuse-nextauth-secret
        key: nextauth-secret
  
  web:
    image:
      repository: "docker.io/langfuse/langfuse"
    
    resources:
      requests:
        memory: "512Mi"
        cpu: "500m"
      limits:
        memory: "2Gi"
        cpu: "2000m"
    
    pod:
      additionalEnv:
        - name: DATABASE_URL
          value: "postgresql://$(DATABASE_USERNAME):$(DATABASE_PASSWORD)@$(DATABASE_HOST):5432/$(DATABASE_NAME)"
  
  worker:
    image:
      repository: "docker.io/langfuse/langfuse-worker"
    
    resources:
      requests:
        memory: "512Mi"
        cpu: "500m"
      limits:
        memory: "2Gi"
        cpu: "2000m"

postgresql:
  auth:
    username: langfuse
    database: postgres_langfuse
    existingSecret: langfuse-postgresql-auth
    secretKeys:
      userPasswordKey: password
      adminPasswordKey: postgres-password
  
  primary:
    persistence:
      enabled: true
      size: 10Gi

clickhouse:
  auth:
    existingSecret: langfuse-clickhouse-auth
    existingSecretKey: password
  
  persistence:
    enabled: true
    size: 20Gi

redis:
  auth:
    existingSecret: langfuse-redis-auth
    existingSecretPasswordKey: password
  
  master:
    persistence:
      enabled: true
      size: 8Gi

s3:
  auth:
    existingSecret: langfuse-s3-auth
    rootUserSecretKey: rootUser
    rootPasswordSecretKey: rootPassword
  
  persistence:
    enabled: true
    size: 50Gi
EOF
```

#### Step 5: Install Langfuse with Helm

```bash
helm install langfuse langfuse/langfuse \
  --namespace langfuse \
  --values langfuse-values.yaml
```

#### Step 6: Monitor the Deployment

Watch pods starting:

```bash
kubectl get pods -n langfuse -w
```

Press `Ctrl+C` once all pods are `Running`.

### Accessing Langfuse

#### Local Access

```bash
kubectl port-forward -n langfuse svc/langfuse 3000:3000
```

Open **<http://localhost:3000>** in your browser.

#### First Time Setup

1. Navigate to your Langfuse URL
2. Create an admin account (first user becomes admin)
3. Set up your organization
4. Generate API keys for your applications

### What's Included

The installation deploys:

- **Langfuse Web Application**: Main web interface
- **Langfuse Worker**: Background job processor
- **PostgreSQL**: Primary database for application data
- **ClickHouse**: Analytics database for fast queries
- **Redis**: Caching layer
- **MinIO (S3-compatible)**: Object storage for traces

---

## Integration with Other Components

### Aegra Integration

Langfuse integrates seamlessly with [Aegra](../4_Aegra/README.md) to provide complete observability for your LLM agents.

#### Why Integrate?

- **Complete Visibility**: Track all agent workflows, LLM calls, and tool executions
- **Performance Monitoring**: Monitor latency, throughput, and error rates
- **Cost Tracking**: Analyze costs per agent execution and identify optimization opportunities
- **Debugging**: Trace agent execution paths and identify bottlenecks
- **Team Collaboration**: Share traces and insights with your team

#### How It Works

Aegra sends traces to Langfuse automatically when configured. Each agent execution creates a trace that includes:
- LLM model calls (OpenAI, Anthropic, etc.)
- Tool invocations
- Agent state transitions
- Error messages and stack traces
- Latency and token usage metrics

#### Setup Instructions

After deploying both Langfuse and Aegra:

1. **Get Langfuse API Keys:**
   ```bash
   # Port forward to Langfuse
   kubectl port-forward -n langfuse svc/langfuse 3000:3000
   ```
   - Open http://localhost:3000
   - Create an account and navigate to Settings → API Keys
   - Generate a new API key pair (public key and secret key)

2. **Configure Aegra Secrets:**
   ```bash
   cd ../4_Aegra/deployments/k8s
   # Edit 03-secrets.yaml and add:
   # LANGFUSE_PUBLIC_KEY: <base64-encoded-public-key>
   # LANGFUSE_SECRET_KEY: <base64-encoded-secret-key>
   # LANGFUSE_HOST: <base64-encoded-service-url>
   ```

3. **Use Kubernetes Service DNS:**
   ```yaml
   # In Aegra ConfigMap or environment variables
   LANGFUSE_HOST: "http://langfuse.langfuse.svc.cluster.local:3000"
   ```

4. **Restart Aegra:**
   ```bash
   kubectl rollout restart deployment/aegra-app -n aegra
   ```

5. **Verify Integration:**
   - Create and run an agent through Aegra
   - Check Langfuse UI - traces should appear automatically
   - Explore performance metrics and cost analysis

📖 **Full integration guide:** See the [Launchstack Integration Guide](../README.md#integration-guide) for detailed steps.

---

## CUSTOMIZATION

Optional configurations for production, scaling, and advanced use cases.

### Table of Contents

- [Deployment Scenarios](#deployment-scenarios)
- [Configuration Options](#configuration-options)
- [Common Customizations](#common-customizations)
- [External Databases](#external-databases)
- [Production Setup](#production-setup)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)
- [Resources](#resources)

---

### Deployment Scenarios

Choose the configuration that matches your use case:

| Scenario | Resources | Storage | Configuration | Use Case |
|----------|-----------|---------|---------------|----------|
| **Development/Testing** | 2 CPU, 4GB RAM | 50GB total | Basic values (Step 4) | Local testing, proof of concept |
| **Small Team** | 4 CPU, 8GB RAM | 100GB total | Basic + persistent storage | <10 users, moderate usage |
| **Production (Small)** | 8 CPU, 16GB RAM | 200GB total | Add ingress, TLS, backups | <50 users, regular usage |
| **Production (Large)** | 16+ CPU, 32GB+ RAM | 500GB+ total | HA setup, replicas, external DBs | 50+ users, high volume |
| **Enterprise** | 32+ CPU, 64GB+ RAM | 1TB+ total | Multi-region, managed services | Thousands of traces/day |

**Key Decision Points:**

- **Use in-cluster databases** when: Starting out, lower traffic, simpler management
- **Use external/managed databases** when: Production workloads, need HA, compliance requirements
- **Enable autoscaling** when: Variable load, cost optimization important
- **Use OCI Object Storage** when: Large trace volumes, need long-term retention, disaster recovery, cost optimization

---

### Configuration Options

#### Viewing All Available Options

To see all configuration options from the Helm chart:

```bash
helm show values langfuse/langfuse > full-values.yaml
```

#### Applying Configuration Changes

After modifying `langfuse-values.yaml`:

```bash
helm upgrade langfuse langfuse/langfuse \
  --namespace langfuse \
  --values langfuse-values.yaml
```

---

### Common Customizations

#### 1. Update Production URL

For production, update the NextAuth URL:

```bash
# Edit the file and change the nextauth URL
sed -i '' 's|http://localhost:3000|https://langfuse.yourdomain.com|g' langfuse-values.yaml
```

#### 2. Pin Version for Stability

In your `langfuse-values.yaml`, uncomment and set specific image tags:

```yaml
langfuse:
  web:
    image:
      tag: "v2.38.0"  # Use specific version
  worker:
    image:
      tag: "v2.38.0"  # Use same version
```

#### 3. Adjust Storage Sizes

Modify storage based on your needs:

```yaml
postgresql:
  primary:
    persistence:
      size: 50Gi  # Main application data

clickhouse:
  persistence:
    size: 100Gi  # Analytics data (grows with trace volume)

redis:
  master:
    persistence:
      size: 16Gi  # Caching

s3:
  persistence:
    size: 200Gi  # Trace artifacts (size based on retention)
```

#### 4. Specify Storage Class

```yaml
postgresql:
  primary:
    persistence:
      storageClass: "fast-ssd"  # Your cluster's storage class
```

#### 5. Enable Ingress with TLS

```yaml
langfuse:
  web:
    ingress:
      enabled: true
      className: "nginx"
      annotations:
        cert-manager.io/cluster-issuer: "letsencrypt-prod"
      hosts:
        - host: langfuse.yourdomain.com
          paths:
            - path: /
              pathType: Prefix
      tls:
        - secretName: langfuse-tls
          hosts:
            - langfuse.yourdomain.com
```

#### 6. Scale for High Availability

```yaml
langfuse:
  web:
    replicas: 3
    autoscaling:
      enabled: true
      minReplicas: 3
      maxReplicas: 10
      targetCPUUtilizationPercentage: 70
  
  worker:
    replicas: 2
    autoscaling:
      enabled: true
      minReplicas: 2
      maxReplicas: 5
      targetCPUUtilizationPercentage: 70

postgresql:
  architecture: replication
  readReplicas:
    replicaCount: 2
```

#### 7. Adjust Resource Limits

For light usage (testing/small teams):

```yaml
langfuse:
  web:
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "1Gi"
        cpu: "1000m"
```

For heavy usage (large teams/high volume):

```yaml
langfuse:
  web:
    resources:
      requests:
        memory: "2Gi"
        cpu: "2000m"
      limits:
        memory: "8Gi"
        cpu: "8000m"
  worker:
    resources:
      requests:
        memory: "2Gi"
        cpu: "2000m"
      limits:
        memory: "8Gi"
        cpu: "8000m"
```

#### 8. Add Custom Environment Variables

```yaml
langfuse:
  web:
    pod:
      additionalEnv:
        - name: LANGFUSE_ENABLE_EXPERIMENTAL_FEATURES
          value: "true"
        - name: LOG_LEVEL
          value: "debug"
        - name: LANGFUSE_TRACE_RETENTION_DAYS
          value: "90"
```

#### 9. Configure Node Affinity

For dedicated node pools:

```yaml
langfuse:
  web:
    pod:
      nodeSelector:
        workload: langfuse
      tolerations:
        - key: "langfuse"
          operator: "Equal"
          value: "true"
          effect: "NoSchedule"
```

---

### External Databases

Use managed OCI services for production workloads.

#### Using External PostgreSQL (OCI Database)

```yaml
postgresql:
  enabled: false  # Disable in-cluster PostgreSQL

langfuse:
  web:
    pod:
      additionalEnv:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: external-db-secret
              key: connection-string
```

Create secret for external database:

```bash
kubectl create secret generic external-db-secret \
  --namespace langfuse \
  --from-literal=connection-string="postgresql://user:pass@oci-db-endpoint.region.oraclecloud.com:5432/langfuse"
```

#### Using External Redis (OCI Cache)

```yaml
redis:
  enabled: false  # Disable in-cluster Redis

langfuse:
  web:
    pod:
      additionalEnv:
        - name: REDIS_HOST
          value: "redis.example.com"
        - name: REDIS_PORT
          value: "6379"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: external-redis-secret
              key: password
```

#### Using OCI Object Storage

```yaml
s3:
  enabled: false  # Disable in-cluster MinIO

langfuse:
  web:
    pod:
      additionalEnv:
        - name: S3_ENDPOINT
          value: "https://<namespace>.compat.objectstorage.<region>.oraclecloud.com"
        - name: S3_BUCKET_NAME
          value: "langfuse-traces"
        - name: S3_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: oci-object-storage-credentials
              key: access-key-id
        - name: S3_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: oci-object-storage-credentials
              key: secret-access-key
```

Create secret for OCI Object Storage:

```bash
kubectl create secret generic oci-object-storage-credentials \
  --namespace langfuse \
  --from-literal=access-key-id="<your-oci-access-key>" \
  --from-literal=secret-access-key="<your-oci-secret-key>"
```

> **Note**: OCI Object Storage is S3-compatible via the Amazon S3 Compatibility API. Generate Customer Secret Keys in OCI Console under User Settings → Customer Secret Keys.

---

### Production Setup

#### Complete Production Example

Here's a production-ready values file:

```yaml
langfuse:
  salt:
    secretKeyRef:
      name: langfuse-general
      key: salt
  
  nextauth:
    url: "https://langfuse.example.com"
    secret:
      secretKeyRef:
        name: langfuse-nextauth-secret
        key: nextauth-secret
  
  web:
    replicas: 3
    image:
      repository: "docker.io/langfuse/langfuse"
      tag: "v2.38.0"
    
    resources:
      requests:
        memory: "1Gi"
        cpu: "1000m"
      limits:
        memory: "4Gi"
        cpu: "4000m"
    
    autoscaling:
      enabled: true
      minReplicas: 3
      maxReplicas: 10
      targetCPUUtilizationPercentage: 70
    
    ingress:
      enabled: true
      className: "nginx"
      annotations:
        cert-manager.io/cluster-issuer: "letsencrypt-prod"
        nginx.ingress.kubernetes.io/rate-limit: "100"
      hosts:
        - host: langfuse.example.com
          paths:
            - path: /
              pathType: Prefix
      tls:
        - secretName: langfuse-tls
          hosts:
            - langfuse.example.com
  
  worker:
    replicas: 2
    image:
      repository: "docker.io/langfuse/langfuse-worker"
      tag: "v2.38.0"
    
    resources:
      requests:
        memory: "1Gi"
        cpu: "1000m"
      limits:
        memory: "4Gi"
        cpu: "4000m"

postgresql:
  architecture: replication
  auth:
    username: langfuse
    database: postgres_langfuse
    existingSecret: langfuse-postgresql-auth
    secretKeys:
      userPasswordKey: password
      adminPasswordKey: postgres-password
  
  primary:
    persistence:
      enabled: true
      storageClass: "fast-ssd"
      size: 50Gi
    resources:
      requests:
        memory: "2Gi"
        cpu: "1000m"
  
  readReplicas:
    replicaCount: 2
    persistence:
      enabled: true
      storageClass: "fast-ssd"
      size: 50Gi

clickhouse:
  auth:
    existingSecret: langfuse-clickhouse-auth
    existingSecretKey: password
  
  persistence:
    enabled: true
    storageClass: "fast-ssd"
    size: 100Gi
  
  resources:
    requests:
      memory: "4Gi"
      cpu: "2000m"

redis:
  auth:
    existingSecret: langfuse-redis-auth
    existingSecretPasswordKey: password
  
  master:
    persistence:
      enabled: true
      storageClass: "fast-ssd"
      size: 16Gi

s3:
  auth:
    existingSecret: langfuse-s3-auth
    rootUserSecretKey: rootUser
    rootPasswordSecretKey: rootPassword
  
  persistence:
    enabled: true
    storageClass: "standard"
    size: 200Gi
```

#### Production Considerations

**Security:**

- Change default credentials
- Use OCI Vault or HashiCorp Vault for secrets management
- Implement network policies
- Configure RBAC
- Enable SSO/OAuth integration

**High Availability:**

- Run multiple replicas of web and worker pods
- Use Pod Disruption Budgets
- Configure anti-affinity rules
- Use OCI Database (Autonomous Database) for PostgreSQL
- Use OCI Cache with Redis

**Performance:**

- Monitor and adjust resources based on actual usage
- Configure Horizontal Pod Autoscaling
- Optimize database configurations
- Use CDN for static assets

**Data Management:**

- Enable persistent volumes with appropriate storage classes
- Implement automated backups for databases
- Configure data retention policies
- Monitor storage usage and set alerts

**Networking:**

- Use production-grade ingress controller (NGINX, Traefik)
- Always use HTTPS/TLS in production
- Automate certificate management with cert-manager
- Implement rate limiting
- Use OCI WAF or CloudFlare for DDoS protection

**Compliance:**

- Ensure GDPR, CCPA compliance
- Enable audit logging
- Consider data residency requirements
- Encrypt data at rest and in transit

---

### Troubleshooting

#### Pods Not Starting

Check pod status and logs:

```bash
kubectl get pods -n langfuse
kubectl describe pod -n langfuse <pod-name>
kubectl logs -n langfuse <pod-name>
```

Common issues:

- **Image pull errors**: Check internet connectivity and image repository access
- **Insufficient resources**: Ensure your cluster has enough CPU/memory
- **PVC issues**: Verify storage class is available

#### Database Connection Issues

Check database pods:

```bash
kubectl get pods -n langfuse | grep -E "postgres|clickhouse|redis"
```

Test connectivity:

```bash
kubectl exec -n langfuse <langfuse-web-pod> -- wget -O- http://langfuse-postgresql:5432
```

#### Secrets Not Found

Verify all secrets exist:

```bash
kubectl get secrets -n langfuse
```

Expected secrets:

- langfuse-general
- langfuse-nextauth-secret
- langfuse-postgresql-auth
- langfuse-clickhouse-auth
- langfuse-redis-auth
- langfuse-s3-auth

Re-apply if needed:

```bash
kubectl apply -f langfuse-secrets.yaml
```

#### Application Errors

Check web application logs:

```bash
kubectl logs -n langfuse -l app.kubernetes.io/name=langfuse-web --tail=100
```

Check worker logs:

```bash
kubectl logs -n langfuse -l app.kubernetes.io/name=langfuse-worker --tail=100
```

---

### Maintenance

#### Updating Langfuse

```bash
# Update Helm repository
helm repo update

# Check available versions
helm search repo langfuse/langfuse --versions

# Upgrade to latest
helm upgrade langfuse langfuse/langfuse \
  --namespace langfuse \
  --values langfuse-values.yaml

# Or upgrade to specific version
helm upgrade langfuse langfuse/langfuse \
  --namespace langfuse \
  --values langfuse-values.yaml \
  --version 1.2.3
```

> **Note**: Check [Langfuse release notes](https://github.com/langfuse/langfuse/releases) for breaking changes.

#### Backup PostgreSQL

```bash
# Create backup
kubectl exec -n langfuse langfuse-postgresql-0 -- \
  pg_dump -U langfuse postgres_langfuse > langfuse-backup-$(date +%Y%m%d).sql

# Restore from backup
kubectl exec -i -n langfuse langfuse-postgresql-0 -- \
  psql -U langfuse postgres_langfuse < langfuse-backup-20250101.sql
```

#### Export Configuration

```bash
# Backup Helm values
helm get values langfuse -n langfuse > langfuse-values-backup.yaml

# Backup secrets (store securely!)
kubectl get secrets -n langfuse -o yaml > langfuse-secrets-backup.yaml
```

#### Uninstalling

```bash
# Uninstall Helm release
helm uninstall langfuse -n langfuse

# Delete namespace (removes all resources including PVCs)
kubectl delete namespace langfuse
```

> **Warning**: This permanently deletes all data. Ensure you have backups.

---

### Resources

#### Official Documentation

- [Langfuse Documentation](https://langfuse.com/docs)
- [Langfuse GitHub](https://github.com/langfuse/langfuse)
- [Langfuse Helm Chart](https://github.com/langfuse/langfuse-k8s)
- [API Reference](https://api.reference.langfuse.com/)

#### SDKs and Integrations

- [Python SDK](https://langfuse.com/docs/sdk/python)
- [JavaScript/TypeScript SDK](https://langfuse.com/docs/sdk/typescript)
- [LangChain Integration](https://langfuse.com/docs/integrations/langchain)
- [OpenAI Integration](https://langfuse.com/docs/integrations/openai)

#### Community

- [Discord Community](https://discord.gg/7NXusRtqYU)
- [GitHub Discussions](https://github.com/orgs/langfuse/discussions)

#### SDK Integration Example

**Python:**

```bash
pip install langfuse
```

```python
from langfuse import Langfuse

langfuse = Langfuse(
    public_key="pk-...",
    secret_key="sk-...",
    host="https://langfuse.yourdomain.com"
)

# Track LLM calls
trace = langfuse.trace(name="chat-completion")
generation = trace.generation(
    name="openai-call",
    model="gpt-4",
    input={"prompt": "Hello"},
    output={"completion": "Hi there!"}
)
```

**JavaScript/TypeScript:**

```bash
npm install langfuse
```

#### Files in This Directory

- **`README.md`** (this file): Complete setup and configuration guide
- **`langfuse.md`**: Original installation guide (alternative reference)
- **`langfuse-values.yaml`**:
  - Generated in Step 4 using the command above
  - Contains Helm chart configuration
  - Safe to commit to git (no sensitive data)
  - Customize for your environment
- **`langfuse-secrets.yaml`**:
  - Generated in Step 3 using the command above
  - Contains sensitive authentication credentials
  - ⚠️ **NEVER commit to git** - add to `.gitignore`
  - Store securely (password manager, vault, encrypted storage)

#### Security Note

```bash
# Add to .gitignore
echo "langfuse-secrets.yaml" >> .gitignore
echo "*-secrets.yaml" >> .gitignore
```

#### Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting) above
2. Review [Langfuse documentation](https://langfuse.com/docs)
3. Search [GitHub issues](https://github.com/langfuse/langfuse/issues)
4. Ask in the [Discord community](https://discord.gg/7NXusRtqYU)
5. Open a new GitHub issue with detailed information

---

Happy LLM Observability! 🚀
