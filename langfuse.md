# Langfuse Installation Guide

This guide will walk you through installing Langfuse on Kubernetes using Helm.

## Prerequisites

Before starting, ensure you have:
- `kubectl` configured and connected to your Kubernetes cluster
- `helm` installed on your machine
- `openssl` available (for generating secure random secrets)
- The Langfuse Helm repository added:
  ```bash
  helm repo add langfuse https://langfuse.github.io/langfuse-k8s
  helm repo update
  ```

---

## Installation Steps

### Step 1: Create the Langfuse Namespace

First, create a dedicated namespace for Langfuse resources:

```bash
kubectl create namespace langfuse
```

This isolates Langfuse components from other workloads in your cluster.

---

### Step 2: Generate and Apply Kubernetes Secrets

Langfuse requires several secrets for its components. Run the following command to create a secrets file with randomly generated secure values:

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

**What this creates:**
- `langfuse-general`: Salt for application encryption
- `langfuse-nextauth-secret`: Secret for NextAuth.js authentication
- `langfuse-postgresql-auth`: PostgreSQL database credentials
- `langfuse-clickhouse-auth`: ClickHouse database credentials
- `langfuse-redis-auth`: Redis cache credentials
- `langfuse-s3-auth`: S3-compatible storage credentials (MinIO)

Now apply the secrets to your cluster:

```bash
kubectl apply -f langfuse-secrets.yaml
```

---

### Step 3: Configure Langfuse Values

Edit the `langfuse-values.yaml` file to customize your installation. This file should contain your specific configuration such as:
- Domain/ingress settings
- Resource limits and requests
- Storage class preferences
- Any environment-specific overrides

> **Note**: A sample `langfuse-values.yaml` file should be present in this directory.

---

### Step 4: Install Langfuse with Helm

Deploy Langfuse to your cluster using Helm:

```bash
helm install langfuse langfuse/langfuse \
  --namespace langfuse \
  --values langfuse-values.yaml
```

This command:
- Installs the Langfuse Helm chart
- Uses the `langfuse` namespace we created
- Applies your custom values from `langfuse-values.yaml`

---

### Step 5: Monitor the Deployment

Watch the pods as they start up:

```bash
kubectl get pods -n langfuse -w
```

Press `Ctrl+C` to stop watching once all pods are in `Running` state.

You can also check the status with:

```bash
# View all resources in the namespace
kubectl get all -n langfuse

# Check pod logs if needed
kubectl logs -n langfuse <pod-name>

# Check service endpoints
kubectl get svc -n langfuse
```

---

## Accessing Langfuse

Once all pods are running, you can access Langfuse based on your ingress configuration in `langfuse-values.yaml`.

If you need to access it locally for testing:

```bash
kubectl port-forward -n langfuse svc/langfuse 3000:3000
```

Then visit `http://localhost:3000` in your browser.

---

## Troubleshooting

### Pods not starting
- Check pod events: `kubectl describe pod -n langfuse <pod-name>`
- View logs: `kubectl logs -n langfuse <pod-name>`

### Secrets not found
- Verify secrets exist: `kubectl get secrets -n langfuse`
- Re-apply if needed: `kubectl apply -f langfuse-secrets.yaml`

### Helm installation failed
- Check Helm release status: `helm list -n langfuse`
- View Helm history: `helm history -n langfuse langfuse`
- Uninstall and retry: `helm uninstall -n langfuse langfuse`

---

## Updating Langfuse

To update your Langfuse installation:

```bash
# Update Helm repository
helm repo update

# Upgrade the installation
helm upgrade langfuse langfuse/langfuse \
  --namespace langfuse \
  --values langfuse-values.yaml
```

---

## Uninstalling Langfuse

To completely remove Langfuse:

```bash
# Uninstall the Helm release
helm uninstall langfuse -n langfuse

# Delete the namespace (optional - removes all resources)
kubectl delete namespace langfuse
```