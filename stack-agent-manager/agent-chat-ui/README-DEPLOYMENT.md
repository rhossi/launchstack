# Deployment Documentation

This directory contains comprehensive documentation for deploying the Agent Chat UI to OCI OKE.

## Quick Start

**Automated deployment**: Use the scripts in `deployments/` - see **[deployments/README.md](deployments/README.md)**

**Manual deployment**: See **[BUILD-DEPLOY.md](BUILD-DEPLOY.md)** - streamlined guide covering build, push, and deploy steps only.

## Documentation Structure

### Essential Guides

1. **[BUILD-DEPLOY.md](BUILD-DEPLOY.md)** ⚡ *Start here*
   - Build container image with Podman
   - Push to OCI Container Registry
   - Deploy to OKE cluster
   - Essential steps only

2. **[DEPLOYMENT.md](DEPLOYMENT.md)** 📘 *Complete guide*
   - Full deployment walkthrough
   - OCI Identity Domain setup
   - Environment configuration
   - Post-deployment steps
   - Troubleshooting

### Configuration Reference

3. **[k8s/README.md](k8s/README.md)** ⚙️ *Kubernetes details*
   - Manifest descriptions
   - Environment variables
   - OCI-specific configurations
   - Health checks and monitoring
   - Scaling strategies

4. **[k8s/PODMAN-GUIDE.md](k8s/PODMAN-GUIDE.md)** 🐳 *Podman advanced*
   - Platform-specific builds
   - Local testing
   - Rootless containers
   - Debugging techniques
   - CI/CD examples

## Deployment Files

All deployment files are organized under `deployments/`:

```
deployments/
├── docker/              # Docker build configuration
│   ├── Dockerfile
│   ├── Containerfile    # Symlink to Dockerfile
│   └── README.md
├── k8s/                 # Kubernetes manifests (numbered in order)
│   ├── 01-namespace.yaml
│   ├── 02-secret.yaml
│   ├── 03-configmap.yaml
│   ├── 04-deployment.yaml
│   ├── 05-service.yaml
│   ├── PODMAN-GUIDE.md
│   └── README.md
├── build-push.sh        # Build and push script
├── deploy.sh            # Kubernetes deploy script
└── README.md            # Scripts documentation
```

## Prerequisites

- **OCI OKE Cluster**: Running Kubernetes cluster
- **Podman**: Container engine installed
- **kubectl**: Configured to access your cluster
- **OCIR Access**: OCI Container Registry credentials
- **OCI Identity Domain**: OAuth application configured

## Common Workflows

### First Time Deployment
```bash
# 1. Build and push image
podman build -t agent-chat-ui:latest .
podman push <region>.ocir.io/<tenancy>/agent-chat-ui:latest

# 2. Configure manifests (edit k8s/*.yaml files)
# 3. Deploy
kubectl apply -f k8s/
```

See [BUILD-DEPLOY.md](BUILD-DEPLOY.md) for complete steps.

### Update Existing Deployment
```bash
# Build new version
podman build -t agent-chat-ui:v2 .
podman push <region>.ocir.io/<tenancy>/agent-chat-ui:v2

# Update deployment
kubectl set image deployment/agent-chat-ui \
  agent-chat-ui=<region>.ocir.io/<tenancy>/agent-chat-ui:v2 \
  -n agent-chat-ui
```

### View Logs
```bash
kubectl logs -f -n agent-chat-ui -l app=agent-chat-ui
```

### Scale
```bash
kubectl scale deployment agent-chat-ui --replicas=5 -n agent-chat-ui
```

## Environment Variables

### Required
- `NEXTAUTH_URL` - Your application URL
- `NEXTAUTH_SECRET` - JWT secret (generate with `openssl rand -base64 32`)
- `OCI_ISSUER` - OCI Identity Domain issuer URL
- `OCI_CLIENT_ID` - OAuth client ID
- `OCI_CLIENT_SECRET` - OAuth client secret

### Optional (LangGraph)
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_ASSISTANT_ID`
- `LANGGRAPH_API_URL`
- `LANGSMITH_API_KEY`

## Support

- **Build/Deploy Issues**: Check [BUILD-DEPLOY.md](BUILD-DEPLOY.md) troubleshooting section
- **Kubernetes Issues**: See [k8s/README.md](k8s/README.md)
- **Podman Issues**: See [k8s/PODMAN-GUIDE.md](k8s/PODMAN-GUIDE.md)
- **Application Issues**: Check [main README.md](README.md)

