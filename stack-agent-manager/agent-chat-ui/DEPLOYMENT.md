# Deployment Guide - Agent Chat UI on OCI OKE

This guide provides step-by-step instructions for deploying the Agent Chat UI application to Oracle Cloud Infrastructure (OCI) Kubernetes Engine (OKE).

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Building the Docker Image](#building-the-docker-image)
- [Deploying to OKE](#deploying-to-oke)
- [Post-Deployment Configuration](#post-deployment-configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### 1. OCI Setup
- OCI account with active tenancy
- OKE cluster running (minimum 2 worker nodes recommended)
- OCI CLI installed and configured
- kubectl installed and configured to access your OKE cluster

### 2. OCI Identity Domain OAuth Application

Create an OAuth application in your OCI Identity Domain:

1. Navigate to: **OCI Console** → **Identity & Security** → **Domains**
2. Select your domain
3. Go to **Applications** → **Add application** → **Confidential Application**
4. Configure:
   - **Name**: Agent Chat UI
   - **Allowed Grant Types**: ✓ Authorization Code
   - **Redirect URL**: `https://your-domain.com/api/auth/callback/oci`
   - **Post Logout Redirect URL**: `https://your-domain.com`
5. **Activate** the application
6. Note down:
   - Client ID
   - Client Secret
   - Issuer URL (found in domain overview)

### 3. Required Tools

Ensure you have the following installed:
- kubectl (configured to access your OKE cluster)
- podman
- oci CLI (optional)

## Environment Setup

### 1. Generate NextAuth Secret

```bash
openssl rand -base64 32
```

Save this value - you'll need it for the Kubernetes secret.

### 2. Configure OCIR Access

```bash
# Set variables (replace with your values)
export OCI_REGION="us-ashburn-1"  # Your OCI region
export OCI_TENANCY_NAMESPACE="your-tenancy-namespace"
export OCI_USERNAME="your-oci-username"
export OCI_AUTH_TOKEN="your-auth-token"

# Login to OCIR
echo $OCI_AUTH_TOKEN | podman login ${OCI_REGION}.ocir.io -u ${OCI_TENANCY_NAMESPACE}/${OCI_USERNAME} --password-stdin
```

To create an auth token:
1. OCI Console → User Settings → Auth Tokens → Generate Token

## Building the Container Image

### 1. Build the Image

```bash
# Navigate to project root
cd /path/to/agent-chat-ui

# Build the image with Podman
podman build -t agent-chat-ui:latest .

# Alternative: Build with specific platform (if needed)
# podman build --platform linux/amd64 -t agent-chat-ui:latest .
```

### 2. Tag and Push to OCIR

```bash
# Tag the image
podman tag agent-chat-ui:latest ${OCI_REGION}.ocir.io/${OCI_TENANCY_NAMESPACE}/agent-chat-ui:latest

# Push to OCIR
podman push ${OCI_REGION}.ocir.io/${OCI_TENANCY_NAMESPACE}/agent-chat-ui:latest
```

### 3. Verify Image in OCIR

Navigate to: **OCI Console** → **Developer Services** → **Container Registry**

You should see your `agent-chat-ui` repository with the `latest` tag.

## Deploying to OKE

### 1. Update Configuration Files

#### Update k8s/04-deployment.yaml

Replace the image placeholder:

```yaml
image: us-ashburn-1.ocir.io/your-tenancy-namespace/agent-chat-ui:latest
```

#### Update k8s/02-secret.yaml

```yaml
stringData:
  NEXTAUTH_SECRET: "your-generated-secret-from-openssl"
  OCI_ISSUER: "https://idcs-xxxxxxxx.identity.oraclecloud.com"
  OCI_CLIENT_ID: "your-client-id"
  OCI_CLIENT_SECRET: "your-client-secret"
```

#### Update k8s/03-configmap.yaml

```yaml
data:
  NEXTAUTH_URL: "https://your-domain.com"
  # Add LangGraph config if needed
  # NEXT_PUBLIC_API_URL: "https://your-domain.com/api"
  # NEXT_PUBLIC_ASSISTANT_ID: "agent"
```

### 2. Create Image Pull Secret

```bash
kubectl create secret docker-registry ocir-secret \
  --docker-server=${OCI_REGION}.ocir.io \
  --docker-username="${OCI_TENANCY_NAMESPACE}/${OCI_USERNAME}" \
  --docker-password="${OCI_AUTH_TOKEN}" \
  --docker-email="your-email@example.com" \
  --namespace=agent-chat-ui \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 3. Update Deployment to Use Image Pull Secret

Uncomment these lines in `k8s/04-deployment.yaml`:

```yaml
imagePullSecrets:
- name: ocir-secret
```

### 4. Deploy to Kubernetes

```bash
# Apply in order (or just apply all at once)
kubectl apply -f k8s/01-namespace.yaml
kubectl apply -f k8s/02-secret.yaml
kubectl apply -f k8s/03-configmap.yaml
kubectl apply -f k8s/04-deployment.yaml
kubectl apply -f k8s/05-service.yaml

# Or apply all at once (files are numbered in correct order)
kubectl apply -f k8s/
```

## Post-Deployment Configuration

### 1. Get Load Balancer IP

```bash
kubectl get svc agent-chat-ui -n agent-chat-ui

# Watch for EXTERNAL-IP to be assigned
kubectl get svc agent-chat-ui -n agent-chat-ui -w
```

This may take a few minutes as OCI provisions the load balancer.

### 2. Update DNS

Once you have the EXTERNAL-IP:

1. Go to your DNS provider
2. Create an A record pointing your domain to the Load Balancer IP
3. Example: `agent-chat.example.com` → `XXX.XXX.XXX.XXX`

### 3. Update OCI Identity Domain Redirect URLs

Update your OAuth application with the actual domain:

1. OCI Console → Identity & Security → Domains → Your Domain → Applications
2. Edit your application
3. Update:
   - **Redirect URL**: `https://agent-chat.example.com/api/auth/callback/oci`
   - **Post Logout Redirect URL**: `https://agent-chat.example.com`
4. Save and ensure application is **Active**

### 4. Update ConfigMap with Actual URL

```bash
kubectl edit configmap agent-chat-ui-config -n agent-chat-ui
```

Update `NEXTAUTH_URL` to your actual domain, then restart pods:

```bash
kubectl rollout restart deployment/agent-chat-ui -n agent-chat-ui
```

## Verification

### 1. Check Pod Status

```bash
# View pods
kubectl get pods -n agent-chat-ui

# Expected output:
# NAME                             READY   STATUS    RESTARTS   AGE
# agent-chat-ui-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
# agent-chat-ui-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
```

### 2. Check Logs

```bash
# View logs from all pods
kubectl logs -n agent-chat-ui -l app=agent-chat-ui --tail=50

# Follow logs in real-time
kubectl logs -n agent-chat-ui -l app=agent-chat-ui -f
```

Look for:
- ✓ "Ready on port 3000"
- ✓ No errors about missing environment variables
- ✗ OAuth configuration errors

### 3. Test Health Endpoint

```bash
# Get the service IP
export LB_IP=$(kubectl get svc agent-chat-ui -n agent-chat-ui -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test health endpoint
curl http://${LB_IP}/api/health

# Expected response:
# {"status":"ok","timestamp":"...","uptime":...}
```

### 4. Access the Application

Open your browser and navigate to: `https://your-domain.com`

You should see the Agent Chat UI login page with "Sign in with OCI Identity Domain" option.

## Optional: Configure HTTPS with Ingress

If you want to use an Ingress controller instead of LoadBalancer:

### 1. Install NGINX Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
```

### 2. Install cert-manager

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

### 3. Create ClusterIssuer

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

### 4. Update and Apply Ingress

Edit `k8s/ingress.yaml` with your domain and apply:

```bash
kubectl apply -f k8s/ingress.yaml
```

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod for events
kubectl describe pod <pod-name> -n agent-chat-ui

# Common issues:
# - ImagePullBackOff: Check image name and pull secret
# - CrashLoopBackOff: Check logs for application errors
```

### OAuth Authentication Errors

Check the following:

1. **Environment Variables**:
```bash
kubectl get secret agent-chat-ui-secret -n agent-chat-ui -o yaml
```

2. **Redirect URLs match** in OCI Identity Domain
3. **Domain is accessible** via NEXTAUTH_URL

### Load Balancer Not Provisioning

```bash
# Check service events
kubectl describe svc agent-chat-ui -n agent-chat-ui

# Common issues:
# - Quota exceeded: Check OCI service limits
# - IAM policies: Ensure cluster has LB creation permissions
```

### Application Not Accessible

```bash
# Check if pods are ready
kubectl get pods -n agent-chat-ui

# Check service endpoints
kubectl get endpoints agent-chat-ui -n agent-chat-ui

# Test from within cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n agent-chat-ui -- curl http://agent-chat-ui/api/health
```

## Monitoring

### View Deployment Status

```bash
# Deployment status
kubectl get deployment agent-chat-ui -n agent-chat-ui

# Replica status
kubectl get replicaset -n agent-chat-ui

# HPA status (if enabled)
kubectl get hpa -n agent-chat-ui
```

### View Resource Usage

```bash
# Pod resource usage
kubectl top pods -n agent-chat-ui

# Node resource usage
kubectl top nodes
```

## Scaling

### Manual Scaling

```bash
# Scale to 3 replicas
kubectl scale deployment agent-chat-ui -n agent-chat-ui --replicas=3

# Verify
kubectl get pods -n agent-chat-ui
```

## Updating the Application

### Rolling Update

```bash
# Build new version
podman build -t agent-chat-ui:v2 .

# Tag and push
podman tag agent-chat-ui:v2 ${OCI_REGION}.ocir.io/${OCI_TENANCY_NAMESPACE}/agent-chat-ui:v2
podman push ${OCI_REGION}.ocir.io/${OCI_TENANCY_NAMESPACE}/agent-chat-ui:v2

# Update deployment
kubectl set image deployment/agent-chat-ui agent-chat-ui=${OCI_REGION}.ocir.io/${OCI_TENANCY_NAMESPACE}/agent-chat-ui:v2 -n agent-chat-ui

# Watch rollout
kubectl rollout status deployment/agent-chat-ui -n agent-chat-ui
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/agent-chat-ui -n agent-chat-ui

# View rollout history
kubectl rollout history deployment/agent-chat-ui -n agent-chat-ui
```

## Clean Up

To remove the deployment:

```bash
# Delete all resources
kubectl delete namespace agent-chat-ui

# Or delete individually
kubectl delete -f k8s/
```

## Next Steps

1. **Set up monitoring**: Use OCI Monitoring or Prometheus/Grafana
2. **Configure backups**: If using persistent volumes
3. **Set up CI/CD**: Automate build and deployment
4. **Enable logging**: Use OCI Logging or ELK stack
5. **Security hardening**: Implement Network Policies, Pod Security Standards

## Support

For issues specific to:
- **OCI OKE**: [OCI Documentation](https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm)
- **Application**: [Agent Chat UI GitHub](https://github.com/langchain-ai/agent-chat-ui)
- **Kubernetes**: Check logs and events as shown in troubleshooting section

