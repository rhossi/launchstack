# Launchstack - Complete LLM Agent Infrastructure Stack

Production-ready, self-hosted infrastructure stack for deploying LLM agents on Oracle Cloud Infrastructure (OCI). Deploy everything you need to build, deploy, monitor, and observe LLM-powered applications with zero vendor lock-in.

---

## QUICKSTART

Get your complete LLM agent infrastructure running in under an hour.

### Prerequisites

Before starting, ensure you have:

#### Required

1. **OCI Account** with appropriate permissions
   - Ability to create VCNs, compute instances, and OKE clusters
   - API keys configured for Terraform

2. **Terraform** >= 1.0
   ```bash
   # macOS
   brew install terraform
   
   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

3. **OCI CLI** installed and configured
   ```bash
   bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
   oci setup config
   ```

4. **kubectl** for cluster management
   ```bash
   # macOS
   brew install kubectl
   
   # Linux
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
   ```

5. **Helm** (v3.x or later) for deploying Prometheus/Grafana and Langfuse
   ```bash
   # macOS
   brew install helm
   
   # Linux
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   ```

6. **SSH Key Pair** for node access
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/oke-nodes
   ```

#### Optional (for local development/testing)

- **Podman** or **Docker** for container builds
- **Python 3.11+** for running database migrations

### Quick Start Steps

Follow these steps in order to deploy the complete stack:

#### Step 1: Deploy OCI Infrastructure (Required)

Deploy the OKE cluster and networking infrastructure.

```bash
cd 1_OCI_Resources

# Copy and configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your OCI details

# Deploy infrastructure
terraform init
terraform plan
terraform apply
```

**What this creates:**
- OKE (Oracle Kubernetes Engine) cluster
- VCN with public/private subnets
- NAT gateway for secure internet access
- 3 worker nodes (configurable)
- Workload identity configuration for pod-level OCI authentication

**Time:** ~10-15 minutes

**Next:** Generate kubeconfig and verify cluster access:
```bash
oci ce cluster create-kubeconfig \
  --cluster-id $(terraform output -raw cluster_id) \
  --file $HOME/.kube/config \
  --region us-chicago-1 \
  --token-version 2.0.0 \
  --kube-endpoint PUBLIC_ENDPOINT

kubectl get nodes
```

📖 **Full documentation:** [`1_OCI_Resources/README.md`](1_OCI_Resources/README.md)

---

#### Step 2: Deploy Monitoring Stack (Recommended)

Set up Prometheus and Grafana for cluster and application monitoring.

```bash
cd 2_Prometheus+Grafana

# Add Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Create namespace
kubectl create namespace monitoring

# Install monitoring stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.adminPassword=admin
```

**What this creates:**
- Prometheus for metrics collection
- Grafana for visualization and dashboards
- Node Exporter for hardware metrics
- Kube State Metrics for cluster state
- Pre-configured dashboards

**Time:** ~5 minutes

**Access Grafana:**
```bash
kubectl port-forward -n monitoring svc/prometheus-grafana 3001:80
# Open http://localhost:3001 (admin/admin)
```

📖 **Full documentation:** [`2_Prometheus+Grafana/README.md`](2_Prometheus+Grafana/README.md)

---

#### Step 3: Deploy Langfuse (Optional - LLM Observability)

Deploy Langfuse for LLM observability, tracing, and analytics.

```bash
cd 3_Langfuse

# Generate secrets
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
# ... (see full guide for all secrets)
EOF

kubectl create namespace langfuse
kubectl apply -f langfuse-secrets.yaml

# Create values file (see README for complete configuration)
cat > langfuse-values.yaml <<'EOF'
# ... (see README for full config)
EOF

# Install Langfuse
helm repo add langfuse https://langfuse.github.io/langfuse-k8s
helm repo update
helm install langfuse langfuse/langfuse \
  --namespace langfuse \
  --values langfuse-values.yaml
```

**What this creates:**
- Langfuse web application
- PostgreSQL database
- ClickHouse analytics database
- Redis cache
- MinIO object storage

**Time:** ~10 minutes

**Note:** Langfuse is optional but recommended if you want LLM observability. Aegra (Step 4) can integrate with it.

📖 **Full documentation:** [`3_Langfuse/README.md`](3_Langfuse/README.md)

---

#### Step 4: Deploy Aegra (Required - Agent Platform)

Deploy Aegra, the self-hosted LangGraph Platform alternative for running LLM agents.

```bash
cd 4_Aegra/deployments/k8s

# Configure secrets
cp 03-secrets.example.yaml 03-secrets.yaml
# Edit 03-secrets.yaml with your values (base64 encoded)

# Set up OCI Container Registry
export OCI_NAMESPACE=your-namespace
export OCI_REGION=us-chicago-1
./oci-setup.sh

# Build and push image
./build-and-push.sh --push

# Update image reference in 06-aegra-app.yaml
# Then deploy
./deploy.sh
```

**What this creates:**
- Aegra API server (Agent Protocol compatible)
- PostgreSQL database for checkpoints
- Agent workflow execution engine
- Optional Langfuse integration

**Time:** ~15-20 minutes

**Access Aegra:**
```bash
kubectl port-forward -n aegra svc/aegra-service 8000:80
# Open http://localhost:8000/docs for API documentation
```

📖 **Full documentation:** [`4_Aegra/README.md`](4_Aegra/README.md)

---

#### Step 5: Deploy Agent Chat UI (Optional - Frontend)

Deploy a web-based chat interface for interacting with your agents.

**Status:** Component documentation in progress.

📖 **Documentation:** [`5_AgentChatUI/README.md`](5_AgentChatUI/README.md)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         OCI Infrastructure                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │   VCN +      │  │   OKE Cluster │  │  Workload Identity  │  │
│  │   Networking │  │   (3 nodes)   │  │  (Pod Auth)        │  │
│  └──────────────┘  └──────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Kubernetes Namespaces                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  monitoring namespace                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │ Prometheus  │  │   Grafana    │  │Node Exporter │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  langfuse namespace (Optional)                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │  Langfuse   │  │ PostgreSQL  │  │  ClickHouse  │    │   │
│  │  │    Web      │  │             │  │              │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  │  ┌─────────────┐  ┌─────────────┐                      │   │
│  │  │   Redis     │  │   MinIO     │                      │   │
│  │  └─────────────┘  └─────────────┘                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  aegra namespace                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐                      │   │
│  │  │   Aegra     │◄─┤ PostgreSQL  │                      │   │
│  │  │  API Server │  │  (State)    │                      │   │
│  │  └──────┬──────┘  └─────────────┘                      │   │
│  │         │                                               │   │
│  │         │ (optional)                                    │   │
│  │         ▼                                               │   │
│  │  ┌─────────────┐                                       │   │
│  │  │  Langfuse   │  (Tracing & Observability)            │   │
│  │  └─────────────┘                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  agent-chat-ui namespace (Optional)                      │   │
│  │  ┌─────────────┐                                       │   │
│  │  │   Chat UI   │───► Aegra API                         │   │
│  │  └─────────────┘                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Component Dependencies

| Component | Depends On | Required? | Purpose |
|-----------|-----------|-----------|---------|
| **OCI Resources** | OCI Account | ✅ Yes | Foundation - Kubernetes cluster |
| **Prometheus + Grafana** | OKE Cluster | ⚠️ Recommended | Cluster monitoring |
| **Langfuse** | OKE Cluster | ⭕ Optional | LLM observability & tracing |
| **Aegra** | OKE Cluster | ✅ Yes | Agent platform (core) |
| **Agent Chat UI** | Aegra | ⭕ Optional | User interface |

### Data Flow

1. **Agent Requests** → Agent Chat UI (or direct API calls)
2. **Agent Execution** → Aegra API processes workflows
3. **State Management** → PostgreSQL stores checkpoints
4. **Observability** → Langfuse receives traces (if configured)
5. **Monitoring** → Prometheus collects metrics, Grafana visualizes

---

## Component Overview

### 1. OCI Resources (`1_OCI_Resources/`)

Production-ready OKE cluster with:
- Enhanced OKE cluster with latest Kubernetes
- High-availability worker nodes across availability domains
- Complete networking (VCN, subnets, NAT gateway, service gateway)
- Workload identity for pod-level OCI authentication
- Security-hardened configuration

**Key Features:**
- Terraform-managed infrastructure
- Workload identity support
- Private worker nodes with secure internet access
- Configurable node shapes and sizes

📖 **Documentation:** [`1_OCI_Resources/README.md`](1_OCI_Resources/README.md)

---

### 2. Prometheus + Grafana (`2_Prometheus+Grafana/`)

Complete monitoring stack for:
- Cluster health and resource usage
- Pod and container metrics
- Node-level hardware metrics
- Pre-configured dashboards

**Key Features:**
- kube-prometheus-stack Helm chart
- Pre-configured Grafana dashboards
- Alertmanager for alerting
- Long-term metrics retention

📖 **Documentation:** [`2_Prometheus+Grafana/README.md`](2_Prometheus+Grafana/README.md)

---

### 3. Langfuse (`3_Langfuse/`)

Open-source LLM observability platform for:
- Tracing LLM calls and agent workflows
- Performance analytics and cost tracking
- Debugging and prompt evaluation
- Team collaboration

**Key Features:**
- Self-hosted on Kubernetes
- PostgreSQL + ClickHouse architecture
- Compatible with LangChain, OpenAI, and custom integrations
- API-compatible with Langfuse Cloud

📖 **Documentation:** [`3_Langfuse/README.md`](3_Langfuse/README.md)

---

### 4. Aegra (`4_Aegra/`)

Self-hosted LangGraph Platform alternative for:
- Running LLM agent workflows
- Agent Protocol-compatible API
- Stateful agent execution
- Custom agent graphs

**Key Features:**
- Drop-in replacement for LangGraph Cloud
- PostgreSQL checkpoint storage
- Streaming API support
- Optional Langfuse integration
- Multiple LLM provider support

📖 **Documentation:** [`4_Aegra/README.md`](4_Aegra/README.md)

---

### 5. Agent Chat UI (`5_AgentChatUI/`)

Web-based chat interface for interacting with agents.

**Status:** Documentation in progress.

📖 **Documentation:** [`5_AgentChatUI/README.md`](5_AgentChatUI/README.md)

---

## Integration Guide

### Connecting Aegra to Langfuse

Aegra can optionally integrate with Langfuse for observability. Here's how to connect them:

#### Step 1: Get Langfuse Credentials

After deploying Langfuse (Step 3):

```bash
# Port forward to Langfuse
kubectl port-forward -n langfuse svc/langfuse 3000:3000

# Access http://localhost:3000 and create an account
# Navigate to Settings → API Keys
# Create a new API key pair (public key and secret key)
```

#### Step 2: Configure Aegra with Langfuse

Update Aegra secrets to include Langfuse credentials:

```bash
cd 4_Aegra/deployments/k8s

# Edit 03-secrets.yaml and add:
# LANGFUSE_PUBLIC_KEY: <base64-encoded-public-key>
# LANGFUSE_SECRET_KEY: <base64-encoded-secret-key>
# LANGFUSE_HOST: <base64-encoded-langfuse-url>

# Base64 encode your values
echo -n "pk-lf-..." | base64
echo -n "sk-lf-..." | base64
echo -n "http://langfuse.langfuse.svc.cluster.local:3000" | base64
```

#### Step 3: Update Aegra ConfigMap

The Langfuse host should be accessible from Aegra pods. Use the Kubernetes service DNS:

```yaml
# In 02-configmap.yaml or via environment variables
LANGFUSE_HOST: "http://langfuse.langfuse.svc.cluster.local:3000"
```

#### Step 4: Restart Aegra

```bash
kubectl rollout restart deployment/aegra-app -n aegra
```

#### Step 5: Verify Integration

1. Create and run an agent through Aegra
2. Check Langfuse UI - you should see traces appearing
3. Monitor agent performance, costs, and latency in Langfuse

**Benefits:**
- Complete visibility into agent workflows
- Performance monitoring and optimization
- Cost tracking per agent execution
- Debugging and error analysis

---

### Monitoring Your Stack

#### View Cluster Metrics in Grafana

```bash
# Port forward to Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3001:80

# Open http://localhost:3001
# Login: admin/admin
# Browse pre-configured dashboards:
#   - Kubernetes / Compute Resources / Cluster
#   - Kubernetes / Compute Resources / Namespace (Pods)
#   - Node Exporter / Nodes
```

#### View Application Logs

```bash
# Aegra logs
kubectl logs -n aegra -l app.kubernetes.io/name=aegra -f

# Langfuse logs
kubectl logs -n langfuse -l app.kubernetes.io/name=langfuse-web -f

# Prometheus logs
kubectl logs -n monitoring -l app.kubernetes.io/name=prometheus -f
```

#### Check Resource Usage

```bash
# Pod resource usage
kubectl top pods --all-namespaces

# Node resource usage
kubectl top nodes
```

---

## Troubleshooting

### Cross-Component Issues

#### Issue: Cannot access services between namespaces

**Symptoms:** Aegra cannot connect to Langfuse, or services cannot communicate.

**Solution:**
1. Verify services are running:
   ```bash
   kubectl get svc --all-namespaces
   ```
2. Test connectivity using service DNS:
   ```bash
   kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup langfuse.langfuse.svc.cluster.local
   ```
3. Check network policies (if enabled):
   ```bash
   kubectl get networkpolicies --all-namespaces
   ```

#### Issue: Persistent volume claims pending

**Symptoms:** Pods stuck in Pending state, PVCs not binding.

**Solution:**
1. Check storage class availability:
   ```bash
   kubectl get storageclass
   ```
2. Verify node capacity:
   ```bash
   kubectl describe nodes
   ```
3. Check PVC status:
   ```bash
   kubectl get pvc --all-namespaces
   kubectl describe pvc <pvc-name> -n <namespace>
   ```

#### Issue: Images cannot be pulled from OCI Container Registry

**Symptoms:** ImagePullBackOff errors, authentication failures.

**Solution:**
1. Verify OCI registry credentials:
   ```bash
   kubectl get secrets -n aegra | grep regcred
   ```
2. Check image pull secrets are configured in deployment:
   ```bash
   kubectl describe deployment aegra-app -n aegra | grep -A 5 ImagePullSecrets
   ```
3. Create or update registry secret:
   ```bash
   kubectl create secret docker-registry regcred \
     --docker-server=us-chicago-1.ocir.io \
     --docker-username='<namespace>/<username>' \
     --docker-password='<auth-token>' \
     --docker-email='<email>' \
     -n aegra
   ```

#### Issue: Database connection failures

**Symptoms:** Aegra or Langfuse cannot connect to PostgreSQL.

**Solution:**
1. Verify PostgreSQL pods are running:
   ```bash
   kubectl get pods -n aegra | grep postgres
   kubectl get pods -n langfuse | grep postgres
   ```
2. Check database service endpoints:
   ```bash
   kubectl get endpoints -n aegra postgres
   ```
3. Test connection from a debug pod:
   ```bash
   kubectl run -it --rm postgres-client --image=postgres:15-alpine --restart=Never -- \
     psql -h postgres.aegra.svc.cluster.local -U aegra -d aegra
   ```
4. Verify secrets are correctly set:
   ```bash
   kubectl get secret -n aegra aegra-database -o yaml
   ```

#### Issue: Insufficient cluster resources

**Symptoms:** Pods not starting, OOMKilled errors, CPU throttling.

**Solution:**
1. Check current resource usage:
   ```bash
   kubectl top nodes
   kubectl top pods --all-namespaces
   ```
2. Review resource requests/limits in deployments
3. Scale up nodes (if using autoscaling):
   ```bash
   # Update node pool size in Terraform
   cd 1_OCI_Resources
   # Edit terraform.tfvars: node_pool_size = 5
   terraform apply
   ```
4. Reduce resource requests for non-critical components

### Component-Specific Troubleshooting

For detailed troubleshooting guides, see each component's README:

- **OCI Resources:** [`1_OCI_Resources/README.md#troubleshooting`](1_OCI_Resources/README.md#troubleshooting)
- **Prometheus + Grafana:** [`2_Prometheus+Grafana/README.md#troubleshooting`](2_Prometheus+Grafana/README.md#troubleshooting)
- **Langfuse:** [`3_Langfuse/README.md#troubleshooting`](3_Langfuse/README.md#troubleshooting)
- **Aegra:** [`4_Aegra/README.md#troubleshooting`](4_Aegra/README.md#troubleshooting)

---

## Quick Reference

### Access Endpoints

| Service | Namespace | Port Forward Command | URL |
|---------|-----------|---------------------|-----|
| **Grafana** | monitoring | `kubectl port-forward -n monitoring svc/prometheus-grafana 3001:80` | http://localhost:3001 |
| **Prometheus** | monitoring | `kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090` | http://localhost:9090 |
| **Langfuse** | langfuse | `kubectl port-forward -n langfuse svc/langfuse 3000:3000` | http://localhost:3000 |
| **Aegra API** | aegra | `kubectl port-forward -n aegra svc/aegra-service 8000:80` | http://localhost:8000 |

### Common Commands

```bash
# Cluster status
kubectl get nodes
kubectl get pods --all-namespaces

# Service status
kubectl get svc --all-namespaces

# Logs
kubectl logs -n <namespace> -l app.kubernetes.io/name=<app-name> -f

# Resource usage
kubectl top nodes
kubectl top pods --all-namespaces

# Restart deployments
kubectl rollout restart deployment/<deployment-name> -n <namespace>

# Scale deployments
kubectl scale deployment/<deployment-name> -n <namespace> --replicas=3
```

### Terraform Commands

```bash
# Initialize
terraform init

# Plan changes
terraform plan

# Apply changes
terraform apply

# View outputs
terraform output

# Destroy infrastructure
terraform destroy
```

### Helm Commands

```bash
# Update repositories
helm repo update

# List releases
helm list --all-namespaces

# Upgrade release
helm upgrade <release-name> <chart> --namespace <namespace> --values <values-file>

# Uninstall release
helm uninstall <release-name> --namespace <namespace>
```

---

## Maintenance

### Updating Components

#### Update OKE Cluster

```bash
cd 1_OCI_Resources
# Edit terraform.tfvars: kubernetes_version = "v1.30.0"
terraform plan
terraform apply
```

#### Update Helm Releases

```bash
# Prometheus + Grafana
helm repo update
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values custom-values.yaml

# Langfuse
helm repo update
helm upgrade langfuse langfuse/langfuse \
  --namespace langfuse \
  --values langfuse-values.yaml
```

#### Update Aegra

```bash
cd 4_Aegra/deployments/k8s
# Update image tag in 06-aegra-app.yaml
./build-and-push.sh --push
kubectl set image deployment/aegra-app aegra=<new-image> -n aegra
```

### Backup Procedures

#### Backup PostgreSQL Databases

```bash
# Aegra database
kubectl exec -n aegra postgres-0 -- \
  pg_dump -U aegra aegra > aegra-backup-$(date +%Y%m%d).sql

# Langfuse database
kubectl exec -n langfuse langfuse-postgresql-0 -- \
  pg_dump -U langfuse postgres_langfuse > langfuse-backup-$(date +%Y%m%d).sql
```

#### Backup Configuration

```bash
# Terraform state
cp 1_OCI_Resources/terraform.tfstate terraform.tfstate.backup

# Helm values
helm get values prometheus -n monitoring > prometheus-values-backup.yaml
helm get values langfuse -n langfuse > langfuse-values-backup.yaml

# Kubernetes manifests
kubectl get all --all-namespaces -o yaml > cluster-backup.yaml
```

### Monitoring Health

```bash
# Cluster health
kubectl get nodes
kubectl get pods --all-namespaces | grep -v Running

# Resource usage
kubectl top nodes
kubectl top pods --all-namespaces

# Events
kubectl get events --all-namespaces --sort-by='.lastTimestamp'
```

---

## Resources

### Component Documentation

- **OCI Resources:** [`1_OCI_Resources/README.md`](1_OCI_Resources/README.md)
- **Prometheus + Grafana:** [`2_Prometheus+Grafana/README.md`](2_Prometheus+Grafana/README.md)
- **Langfuse:** [`3_Langfuse/README.md`](3_Langfuse/README.md)
- **Aegra:** [`4_Aegra/README.md`](4_Aegra/README.md)
- **Agent Chat UI:** [`5_AgentChatUI/README.md`](5_AgentChatUI/README.md)

### External Resources

#### OCI Documentation
- [OKE Documentation](https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm)
- [Terraform OCI Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs)
- [Workload Identity](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengrantingworkloadaccesstoresources.htm)

#### Kubernetes Documentation
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [Helm Documentation](https://helm.sh/docs/)

#### Component Documentation
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Langfuse Documentation](https://langfuse.com/docs)
- [Aegra GitHub](https://github.com/rhossi/aegra)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

### Community & Support

- **Aegra:** [GitHub Issues](https://github.com/rhossi/aegra/issues) | [Discussions](https://github.com/rhossi/aegra/discussions)
- **Langfuse:** [Discord](https://discord.gg/7NXusRtqYU) | [GitHub Discussions](https://github.com/orgs/langfuse/discussions)
- **Prometheus:** [Community](https://prometheus.io/community/) | [GitHub](https://github.com/prometheus/prometheus)

---

## Getting Help

If you encounter issues:

1. **Check Troubleshooting:** Review the [Troubleshooting](#troubleshooting) section above
2. **Component-Specific Help:** See the troubleshooting section in each component's README
3. **Verify Prerequisites:** Ensure all prerequisites are met
4. **Check Logs:** Use `kubectl logs` to investigate errors
5. **Review Documentation:** Refer to component-specific documentation
6. **Community Support:** Reach out to component communities for help

---

Happy Deploying! 🚀

