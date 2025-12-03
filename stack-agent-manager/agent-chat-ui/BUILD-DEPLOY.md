# Build and Deploy Guide

This guide covers the essential steps to build, push, and deploy the Agent Chat UI to OCI OKE.

## Quick Start with Scripts

For automated deployment, use the provided scripts:

```bash
# 1. Build and push image
./deployments/build-push.sh

# 2. Deploy to Kubernetes  
./deployments/deploy.sh
```

See `deployments/README.md` for detailed script documentation.

---

## Manual Deployment Steps

## Step 1: Build Container Image

```bash
# Navigate to project directory
cd /path/to/agent-chat-ui

# Build the image
podman build -f deployments/docker/Dockerfile -t agent-chat-ui:latest .

# Optional: Build for specific platform (e.g., Apple Silicon to x86_64)
podman build --platform linux/amd64 -t agent-chat-ui:latest .
```

## Step 2: Push to OCI Container Registry (OCIR)

### Configure Environment

```bash
# Set your OCI details
export OCI_REGION="us-ashburn-1"              # Your OCI region
export OCI_NAMESPACE="your-tenancy-namespace" # Your tenancy namespace
export OCI_USER="your-oci-username"           # Your OCI username
export OCI_TOKEN="your-auth-token"            # Your auth token
```

**Note**: Create an auth token in OCI Console → User Settings → Auth Tokens → Generate Token

### Login and Push

```bash
# Login to OCIR
echo $OCI_TOKEN | podman login ${OCI_REGION}.ocir.io \
  -u ${OCI_NAMESPACE}/${OCI_USER} --password-stdin

# Tag the image
podman tag agent-chat-ui:latest \
  ${OCI_REGION}.ocir.io/${OCI_NAMESPACE}/agent-chat-ui:latest

# Push to OCIR
podman push ${OCI_REGION}.ocir.io/${OCI_NAMESPACE}/agent-chat-ui:latest
```

### Verify Image

Check that your image appears in: **OCI Console** → **Developer Services** → **Container Registry**

## Step 3: Configure Kubernetes Manifests

### Update Image Reference

Edit `deployments/k8s/04-deployment.yaml` and update the image field:

```yaml
spec:
  containers:
  - name: agent-chat-ui
    image: us-ashburn-1.ocir.io/your-tenancy/agent-chat-ui:latest
```

### Configure Secrets

Edit `deployments/k8s/02-secret.yaml` with your actual values:

```yaml
stringData:
  NEXTAUTH_SECRET: "your-nextauth-secret"
  OCI_ISSUER: "https://idcs-xxxxxxxx.identity.oraclecloud.com"
  OCI_CLIENT_ID: "your-client-id"
  OCI_CLIENT_SECRET: "your-client-secret"
```

Generate `NEXTAUTH_SECRET` with:
```bash
openssl rand -base64 32
```

### Configure Application URL

Edit `deployments/k8s/03-configmap.yaml`:

```yaml
data:
  NEXTAUTH_URL: "https://your-domain.com"
```

## Step 4: Create Image Pull Secret

```bash
kubectl create secret docker-registry ocir-secret \
  --docker-server=${OCI_REGION}.ocir.io \
  --docker-username="${OCI_TENANCY}/${OCI_USER}" \
  --docker-password="${OCI_TOKEN}" \
  --docker-email="your-email@example.com" \
  -n agent-chat-ui
```

Then uncomment in `deployments/k8s/04-deployment.yaml`:

```yaml
imagePullSecrets:
- name: ocir-secret
```

## Step 5: Deploy to OKE

```bash
# Apply in order (or just apply all at once)
kubectl apply -f deployments/k8s/01-namespace.yaml
kubectl apply -f deployments/k8s/02-secret.yaml
kubectl apply -f deployments/k8s/03-configmap.yaml
kubectl apply -f deployments/k8s/04-deployment.yaml
kubectl apply -f deployments/k8s/05-service.yaml

# Or apply all at once (files are numbered in correct order)
kubectl apply -f deployments/k8s/
```

## Step 6: Verify Deployment

```bash
# Check pods are running
kubectl get pods -n agent-chat-ui

# Check pod logs
kubectl logs -f -n agent-chat-ui -l app=agent-chat-ui

# Get Load Balancer IP
kubectl get svc agent-chat-ui -n agent-chat-ui

# Wait for EXTERNAL-IP to be assigned (may take a few minutes)
kubectl get svc agent-chat-ui -n agent-chat-ui -w
```

## Step 7: Access the Application

Once the Load Balancer IP is assigned:

1. Update your DNS to point to the EXTERNAL-IP
2. Update `NEXTAUTH_URL` in `deployments/k8s/03-configmap.yaml` if needed, then apply:
   ```bash
   kubectl apply -f deployments/k8s/03-configmap.yaml
   ```
3. Restart pods to apply changes:
   ```bash
   kubectl rollout restart deployment/agent-chat-ui -n agent-chat-ui
   ```
4. Access your application at the configured domain

## Update Deployment

When you need to deploy a new version:

```bash
# Build new version
podman build -f deployments/docker/Dockerfile -t agent-chat-ui:v2 .

# Tag and push
podman tag agent-chat-ui:v2 \
  ${OCI_REGION}.ocir.io/${OCI_NAMESPACE}/agent-chat-ui:v2
podman push ${OCI_REGION}.ocir.io/${OCI_NAMESPACE}/agent-chat-ui:v2

# Update deployment
kubectl set image deployment/agent-chat-ui \
  agent-chat-ui=${OCI_REGION}.ocir.io/${OCI_NAMESPACE}/agent-chat-ui:v2 \
  -n agent-chat-ui

# Watch rollout progress
kubectl rollout status deployment/agent-chat-ui -n agent-chat-ui
```

## Rollback

If something goes wrong:

```bash
# Rollback to previous version
kubectl rollout undo deployment/agent-chat-ui -n agent-chat-ui

# Check rollout history
kubectl rollout history deployment/agent-chat-ui -n agent-chat-ui
```

## Cleanup

Remove the deployment:

```bash
# Delete all resources
kubectl delete namespace agent-chat-ui
```

## Troubleshooting

### Pods not starting
```bash
# Check pod details
kubectl describe pod <pod-name> -n agent-chat-ui

# Check logs
kubectl logs <pod-name> -n agent-chat-ui
```

### Image pull errors
- Verify image exists in OCIR
- Check image pull secret is configured correctly
- Verify auth token is still valid

### Application errors
```bash
# Check environment variables are set
kubectl exec -it <pod-name> -n agent-chat-ui -- env | grep -E 'NEXTAUTH|OCI'

# Test health endpoint
kubectl port-forward -n agent-chat-ui svc/agent-chat-ui 3000:80
curl http://localhost:3000/api/health
```

## Additional Resources

- Full deployment documentation: `DEPLOYMENT.md`
- Kubernetes configuration details: `deployments/k8s/README.md`
- Podman advanced features: `deployments/k8s/PODMAN-GUIDE.md`
- Docker build details: `deployments/docker/README.md`

