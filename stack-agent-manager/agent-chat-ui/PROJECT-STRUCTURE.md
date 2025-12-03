# Project Structure

```
agent-chat-ui/
├── deployments/          # Deployment automation scripts
│   ├── README.md         # Scripts documentation
│   ├── build-push.sh     # Build and push image to OCIR
│   └── deploy.sh         # Deploy to Kubernetes
│
├── docker/               # Docker/Podman build configuration
│   ├── Dockerfile        # Multi-stage build for Next.js
│   ├── Containerfile     # Symlink to Dockerfile (Podman convention)
│   ├── .dockerignore     # Files to exclude from build
│   ├── .containerignore  # Files to exclude from build (Podman)
│   └── README.md         # Docker build documentation
│
├── k8s/                  # Kubernetes manifests
│   ├── 01-namespace.yaml # Namespace definition
│   ├── 02-secret.yaml    # Secrets (OAuth credentials)
│   ├── 03-configmap.yaml # ConfigMap (application config)
│   ├── 04-deployment.yaml # Deployment definition
│   ├── 05-service.yaml   # LoadBalancer service
│   ├── PODMAN-GUIDE.md   # Podman-specific guide
│   └── README.md         # Kubernetes documentation
│
├── src/                  # Next.js application source
│   ├── app/              # App router
│   │   ├── api/          # API routes
│   │   │   ├── auth/     # NextAuth configuration
│   │   │   └── health/   # Health check endpoint
│   │   ├── components/   # App-level components
│   │   ├── login/        # Login page
│   │   ├── globals.css   # Global styles
│   │   ├── layout.tsx    # Root layout
│   │   └── page.tsx      # Home page
│   ├── components/       # Shared components
│   │   ├── thread/       # Chat thread components
│   │   ├── ui/           # UI components (shadcn)
│   │   └── ...
│   ├── hooks/            # React hooks
│   ├── lib/              # Utility libraries
│   ├── providers/        # Context providers
│   ├── types/            # TypeScript types
│   └── middleware.ts     # Next.js middleware
│
├── public/               # Static assets
│   ├── logo.svg
│   └── oci-logo.png
│
├── BUILD-DEPLOY.md       # Quick build & deploy guide
├── DEPLOYMENT.md         # Complete deployment documentation
├── README-DEPLOYMENT.md  # Deployment documentation index
├── PROJECT-STRUCTURE.md  # This file
├── README.md             # Main project README
│
├── package.json          # Dependencies
├── pnpm-lock.yaml        # Dependency lock file
├── tsconfig.json         # TypeScript configuration
├── next.config.mjs       # Next.js configuration
├── tailwind.config.js    # Tailwind CSS configuration
├── postcss.config.mjs    # PostCSS configuration
└── ...                   # Other config files
```

## Directory Purposes

### `/deployments` - Deployment Scripts

Contains automation scripts for building and deploying:
- **build-push.sh**: Builds container image and pushes to OCIR
- **deploy.sh**: Deploys application to Kubernetes
- **README.md**: Script documentation and usage

**When to use**: For automated deployment workflows

### `/docker` - Container Build

Contains Dockerfile and build configuration:
- **Dockerfile**: Multi-stage build for production
- **.dockerignore**: Excludes files from build context
- **README.md**: Build documentation

**When to use**: When customizing container build process

### `/k8s` - Kubernetes Configuration

Contains Kubernetes manifests numbered in deployment order:
1. **01-namespace.yaml**: Creates namespace
2. **02-secret.yaml**: Stores sensitive config
3. **03-configmap.yaml**: Stores non-sensitive config
4. **04-deployment.yaml**: Deploys application pods
5. **05-service.yaml**: Exposes via LoadBalancer

**When to use**: For manual deployment or customizing K8s resources

### `/src` - Application Code

Next.js application source code:
- **app/**: App router with pages and API routes
- **components/**: Reusable React components
- **hooks/**: Custom React hooks
- **lib/**: Utility functions
- **providers/**: Context providers
- **types/**: TypeScript definitions

**When to use**: Application development

## Quick Reference

### Build Image
```bash
./deployments/build-push.sh
```

### Deploy to K8s
```bash
./deployments/deploy.sh
```

### Run Locally
```bash
pnpm install
pnpm dev
```

### Manual Docker Build
```bash
podman build -f docker/Dockerfile -t agent-chat-ui .
```

### Manual K8s Deploy
```bash
kubectl apply -f k8s/
```

## Configuration Files

### Root Level
- **package.json**: Dependencies and scripts
- **tsconfig.json**: TypeScript configuration
- **next.config.mjs**: Next.js configuration
- **tailwind.config.js**: Tailwind CSS configuration
- **eslint.config.js**: ESLint configuration
- **prettier.config.js**: Prettier configuration

### Environment Variables
Not stored in repository. Configure in:
- `k8s/02-secret.yaml` - Sensitive variables
- `k8s/03-configmap.yaml` - Non-sensitive variables

## Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Main project documentation |
| `BUILD-DEPLOY.md` | Quick deployment guide |
| `DEPLOYMENT.md` | Complete deployment guide |
| `README-DEPLOYMENT.md` | Deployment docs index |
| `PROJECT-STRUCTURE.md` | This file |
| `docker/README.md` | Docker build docs |
| `k8s/README.md` | Kubernetes docs |
| `k8s/PODMAN-GUIDE.md` | Podman-specific guide |
| `deployments/README.md` | Scripts documentation |

## Workflow

### First Time Setup
1. Clone repository
2. Configure k8s manifests (`k8s/02-secret.yaml`, `k8s/03-configmap.yaml`)
3. Run `./deployments/build-push.sh`
4. Run `./deployments/deploy.sh`

### Making Changes
1. Edit source code in `src/`
2. Test locally with `pnpm dev`
3. Build new image: `./deployments/build-push.sh v1.0.1`
4. Update `k8s/04-deployment.yaml` with new image tag
5. Deploy: `./deployments/deploy.sh`

## Related Documentation

- **Getting Started**: See `README.md`
- **Deployment**: See `BUILD-DEPLOY.md` or `DEPLOYMENT.md`
- **Scripts**: See `deployments/README.md`
- **Docker**: See `docker/README.md`
- **Kubernetes**: See `k8s/README.md`

