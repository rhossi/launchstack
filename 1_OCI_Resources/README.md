# OKE Cluster Terraform Configuration

Production-ready Oracle Kubernetes Engine (OKE) cluster in OCI with workload identity support, deployed using Terraform.

> **📖 [Back to Launchstack Overview](../README.md)** | This is Step 1 of the [Launchstack](https://github.com/yourusername/launchstack) deployment sequence.

---

## QUICKSTART

Everything you need to deploy an OKE cluster.

### Prerequisites

1. **OCI CLI** installed and configured

   ```bash
   # Install OCI CLI
   bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
   
   # Configure OCI CLI
   oci setup config
   ```

2. **Terraform** >= 1.0

   ```bash
   # macOS
   brew install terraform
   
   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

3. **kubectl** for cluster management

   ```bash
   # macOS
   brew install kubectl
   
   # Linux
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
   ```

4. **SSH Key Pair** for node access

   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/oke-nodes
   ```

### Configuration Steps

#### Step 1: Copy Variables File

```bash
cp terraform.tfvars.example terraform.tfvars
```

#### Step 2: Edit Configuration

Edit `terraform.tfvars` with your values:

- OCI authentication details (tenancy OCID, user OCID, fingerprint, private key path)
- Compartment OCID where resources will be created
- SSH public key for node access
- Cluster name and Kubernetes version

**Find your compartment OCID:**

```bash
oci iam compartment list --all
```

**Check available Kubernetes versions:**

```bash
oci ce cluster-options get --cluster-option-id all --query 'data."kubernetes-versions"'
```

#### Step 3: Deploy

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the configuration
terraform apply
```

Type `yes` when prompted. Deployment takes ~10-15 minutes.

### Access Your Cluster

#### Generate kubeconfig

```bash
oci ce cluster create-kubeconfig \
  --cluster-id $(terraform output -raw cluster_id) \
  --file $HOME/.kube/config \
  --region us-chicago-1 \
  --token-version 2.0.0 \
  --kube-endpoint PUBLIC_ENDPOINT
```

#### Verify Access

```bash
kubectl get nodes
kubectl get pods --all-namespaces
```

### What's Included

The deployment creates:

- **Enhanced OKE Cluster**: Latest Kubernetes with enterprise features
- **3 Worker Nodes**: VM.Standard.E6.Flex (4 OCPU, 32GB RAM)
- **High Availability**: Nodes distributed across 3 availability domains
- **Complete Networking**: VCN with public/private subnets, NAT gateway, service gateway
- **Workload Identity**: IAM policies and dynamic groups for pod-level authentication
- **Security**: Private worker nodes, proper security lists and routing

---

## CUSTOMIZATION

Optional configurations for production, scaling, and advanced use cases.

### Table of Contents

- [Architecture Details](#architecture-details)
- [Workload Identity](#workload-identity)
- [Scaling](#scaling)
- [Upgrading](#upgrading)
- [Advanced Configuration](#advanced-configuration)
- [Cost Optimization](#cost-optimization)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)
- [Resources](#resources)

---

### Architecture Details

**Cluster Configuration:**

- **Type**: Enhanced OKE cluster
- **Region**: us-chicago-1
- **Node Shape**: VM.Standard.E6.Flex (4 OCPU, 32GB RAM)
- **Node Count**: 3 nodes (default)
- **Kubernetes Version**: Configurable (latest stable recommended)

**Networking:**

- **VCN**: Complete virtual cloud network
- **Subnets**: Public (load balancers) and private (worker nodes)
- **NAT Gateway**: Secure internet access for private nodes
- **Service Gateway**: Free traffic to OCI services
- **Security Lists**: Properly configured ingress/egress rules

**Features:**

- ✅ Enhanced OKE cluster
- ✅ Managed node pool with flexible shapes
- ✅ High availability across availability domains
- ✅ Private worker nodes
- ✅ Public load balancer subnet
- ✅ Workload identity with IAM policies
- ✅ Service gateway for OCI service traffic

---

### Workload Identity

Workload identity allows Kubernetes pods to authenticate with OCI services without storing credentials.

#### Enable Workload Identity for a Pod

1. **Create ServiceAccount with annotation:**

   ```yaml
   apiVersion: v1
   kind: ServiceAccount
   metadata:
     name: my-service-account
     namespace: default
     annotations:
       oci.oraclecloud.com/workload-identity: "true"
   ```

2. **Use ServiceAccount in your pod:**

   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: my-app
     namespace: default
   spec:
     serviceAccountName: my-service-account
     containers:
     - name: app
       image: myapp:latest
       # App can now use OCI SDK without credentials
   ```

3. **Pod automatically gets temporary credentials** to access OCI services based on IAM policies in `iam.tf`.

#### Configure Additional IAM Policies

Edit `iam.tf` to grant additional permissions:

```hcl
resource "oci_identity_policy" "oke_workload_identity" {
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_workload_identity.name} to read objectstorage-namespaces in compartment id ${var.compartment_id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_workload_identity.name} to manage objects in compartment id ${var.compartment_id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_workload_identity.name} to use autonomous-database-family in compartment id ${var.compartment_id}",
  ]
}
```

---

### Scaling

#### Scale Node Pool

Update `node_pool_size` in `terraform.tfvars`:

```hcl
node_pool_size = 5  # Scale to 5 nodes
```

Apply changes:

```bash
terraform apply
```

#### Change Node Shape

Update `node_shape` and resources in `terraform.tfvars`:

```hcl
node_shape = "VM.Standard.E6.Flex"
node_shape_config_ocpus = 8  # Increase to 8 OCPUs
node_shape_config_memory_in_gbs = 64  # Increase to 64GB
```

Apply changes:

```bash
terraform apply
```

#### Add Additional Node Pools

Edit `main.tf` to add another node pool resource:

```hcl
resource "oci_containerengine_node_pool" "gpu_node_pool" {
  cluster_id         = oci_containerengine_cluster.oke_cluster.id
  compartment_id     = var.compartment_id
  name               = "${var.cluster_name}-gpu-pool"
  node_shape         = "VM.GPU.A10.1"
  kubernetes_version = var.kubernetes_version
  
  node_config_details {
    size = 2
    # ... additional configuration
  }
}
```

---

### Upgrading

#### Upgrade Kubernetes Version

1. **Check available versions:**

   ```bash
   oci ce cluster-options get --cluster-option-id all --query 'data."kubernetes-versions"'
   ```

2. **Update `kubernetes_version` in `terraform.tfvars`:**

   ```hcl
   kubernetes_version = "v1.29.1"
   ```

3. **Apply upgrade:**

   ```bash
   terraform apply
   ```

> **Note**: Upgrade control plane first, then node pools. Plan for minimal downtime.

#### Update Terraform Providers

```bash
terraform init -upgrade
```

---

### Advanced Configuration

#### Enable Pod Security Policies

Add to your cluster configuration:

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  runAsUser:
    rule: MustRunAsNonRoot
```

#### Configure Cluster Autoscaler

Install cluster autoscaler:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/oci/examples/cluster-autoscaler.yaml
```

Configure in `terraform.tfvars`:

```hcl
node_pool_initial_node_labels = {
  "cluster-autoscaler" = "enabled"
}
```

#### Add Custom Node Labels

```hcl
node_pool_initial_node_labels = {
  "environment" = "production"
  "workload"    = "general"
}
```

#### Configure Node Taints

```hcl
node_pool_node_config_details_placement_configs_preemptible_node_config = {
  is_preemptible = false
}
```

---

### Cost Optimization

**Approximate Monthly Costs (3 nodes):**

- **Compute**: ~$250-300/month (VM.Standard.E6.Flex: 4 OCPU, 32GB RAM × 3)
- **Networking**: ~$20-30/month (NAT Gateway, Load Balancer)
- **Storage**: Variable based on persistent volumes

**Cost Saving Tips:**

1. **Use flexible shapes**: Adjust OCPU/memory to actual needs
2. **Right-size node pools**: Monitor usage and scale appropriately
3. **Use OCI Free Tier**: Some resources eligible for Always Free
4. **Enable cluster autoscaling**: Scale down during off-hours
5. **Use spot instances**: For non-critical workloads (preemptible nodes)
6. **Delete unused resources**: Clean up test/development clusters
7. **Use service gateway**: Free traffic to OCI services

Use [OCI Cost Estimator](https://www.oracle.com/cloud/costestimator.html) for precise estimates.

#### Configure Preemptible Nodes

For non-production workloads:

```hcl
variable "use_preemptible_nodes" {
  default = false
}

# In node pool configuration
is_pv_encryption_in_transit_enabled = true
preemptible_node_config {
  preemption_action {
    type = "TERMINATE"
  }
}
```

---

### Security Best Practices

1. **Use private subnets for worker nodes** ✅ (configured)
2. **Enable Pod Security Policies**

   ```bash
   kubectl apply -f pod-security-policy.yaml
   ```

3. **Rotate SSH keys regularly**

   ```bash
   # Generate new key
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/oke-nodes-new
   
   # Update terraform.tfvars
   # Apply changes
   terraform apply
   ```

4. **Use OCI Vault for secrets**

   ```hcl
   # Add to variables.tf
   variable "vault_secret_id" {
     description = "OCID of vault secret"
   }
   ```

5. **Enable audit logging**

   ```hcl
   # Add to main.tf
   logging_config {
     is_enabled = true
   }
   ```

6. **Restrict API endpoint access**

   Update security lists in `main.tf` to allow only specific IPs.

7. **Use workload identity** ✅ (configured)

8. **Enable network policies**

   ```bash
   kubectl apply -f network-policy.yaml
   ```

9. **Scan container images**

   Use OCI Container Scanning service.

10. **Enable RBAC**

    ```yaml
    apiVersion: rbac.authorization.k8s.io/v1
    kind: Role
    metadata:
      namespace: default
      name: pod-reader
    rules:
    - apiGroups: [""]
      resources: ["pods"]
      verbs: ["get", "watch", "list"]
    ```

---

### Troubleshooting

#### Issue: "Service error: NotAuthorizedOrNotFound"

**Solution**: Verify IAM policies allow required operations in the compartment.

```bash
# Check policies
oci iam policy list --compartment-id <compartment_ocid>
```

#### Issue: "Shape VM.Standard.E6.Flex not available"

**Solution**: Check shape availability in your region:

```bash
oci compute shape list --compartment-id <compartment_ocid> --all
```

#### Issue: "No availability domains available"

**Solution**: Ensure region supports multiple availability domains or adjust node pool placement.

```bash
# List availability domains
oci iam availability-domain list
```

#### Issue: Cannot connect to cluster

**Solution**: Verify security lists allow access from your IP to port 6443.

```bash
# Check security lists
oci network security-list get --security-list-id <security_list_ocid>
```

#### Issue: Terraform state lock error

**Solution**: Unlock Terraform state:

```bash
terraform force-unlock <lock-id>
```

#### Issue: Nodes not joining cluster

**Solution**: Check node pool status and logs:

```bash
oci ce node-pool get --node-pool-id <node_pool_ocid>
```

---

### Maintenance

#### View Outputs

```bash
# All outputs
terraform output

# Specific outputs
terraform output cluster_id
terraform output cluster_endpoints
terraform output kubeconfig_command
```

#### Update Configuration

1. Modify `terraform.tfvars` or `.tf` files
2. Run `terraform plan` to review changes
3. Run `terraform apply` to apply changes

#### Backup Terraform State

```bash
# Backup state file
cp terraform.tfstate terraform.tfstate.backup

# Use remote state (recommended for production)
terraform {
  backend "s3" {
    bucket = "terraform-state"
    key    = "oke-cluster/terraform.tfstate"
    region = "us-phoenix-1"
  }
}
```

#### Monitor Cluster Health

```bash
# Check node status
kubectl get nodes

# Check system pods
kubectl get pods -n kube-system

# Check cluster info
kubectl cluster-info

# Check events
kubectl get events --all-namespaces --sort-by='.lastTimestamp'
```

#### Cleanup

To destroy all resources:

```bash
terraform destroy
```

Type `yes` when prompted.

> **Warning**: This permanently deletes the cluster and all resources. Backup important data first!

---

### Resources

#### Official Documentation

- [OKE Documentation](https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm)
- [Terraform OCI Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs)
- [OKE Best Practices](https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengbestpractices.htm)
- [Workload Identity Documentation](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contenggrantingworkloadaccesstoresources.htm)

#### Useful Links

- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [OCI Architecture Center](https://docs.oracle.com/solutions/)

#### Community

- [OCI Forums](https://cloudcustomerconnect.oracle.com/resources/9c8fa8f96f/summary)
- [Terraform OCI Provider GitHub](https://github.com/oracle/terraform-provider-oci)

#### Support

For issues related to:

- **Terraform**: Check [Terraform OCI Provider GitHub](https://github.com/oracle/terraform-provider-oci)
- **OKE**: Contact Oracle Cloud Support or check OCI Forums
- **This Configuration**: Open an issue in this repository

---

Happy Deploying! 🚀
