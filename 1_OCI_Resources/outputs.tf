output "cluster_id" {
  description = "The OCID of the OKE cluster"
  value       = oci_containerengine_cluster.oke_cluster.id
}

output "cluster_name" {
  description = "The name of the OKE cluster"
  value       = oci_containerengine_cluster.oke_cluster.name
}

output "cluster_kubernetes_version" {
  description = "The Kubernetes version of the cluster"
  value       = oci_containerengine_cluster.oke_cluster.kubernetes_version
}

output "cluster_endpoints" {
  description = "The Kubernetes API endpoints"
  value = {
    public_endpoint  = oci_containerengine_cluster.oke_cluster.endpoints[0].public_endpoint
    private_endpoint = oci_containerengine_cluster.oke_cluster.endpoints[0].private_endpoint
  }
}

output "vcn_id" {
  description = "The OCID of the VCN"
  value       = oci_core_vcn.oke_vcn.id
}

output "node_pool_id" {
  description = "The OCID of the node pool"
  value       = oci_containerengine_node_pool.oke_node_pool.id
}

output "node_pool_nodes" {
  description = "Information about the nodes in the node pool"
  value = {
    size   = oci_containerengine_node_pool.oke_node_pool.node_config_details[0].size
    shape  = oci_containerengine_node_pool.oke_node_pool.node_shape
    ocpus  = oci_containerengine_node_pool.oke_node_pool.node_shape_config[0].ocpus
    memory = oci_containerengine_node_pool.oke_node_pool.node_shape_config[0].memory_in_gbs
  }
}

output "dynamic_groups" {
  description = "The dynamic groups created for workload identity"
  value = {
    cluster_dynamic_group           = oci_identity_dynamic_group.oke_cluster_dynamic_group.name
    nodes_dynamic_group             = oci_identity_dynamic_group.oke_nodes_dynamic_group.name
    workload_identity_dynamic_group = oci_identity_dynamic_group.oke_workload_identity_group.name
  }
}

output "kubeconfig_command" {
  description = "Command to generate kubeconfig for cluster access"
  value       = "oci ce cluster create-kubeconfig --cluster-id ${oci_containerengine_cluster.oke_cluster.id} --file $HOME/.kube/config --region ${var.region} --token-version 2.0.0 --kube-endpoint PUBLIC_ENDPOINT"
}

output "kubectl_test_command" {
  description = "Command to test cluster access"
  value       = "kubectl get nodes"
}

output "setup_instructions" {
  description = "Step-by-step instructions to access the cluster"
  value       = <<-EOT
    1. Install kubectl if not already installed
    2. Ensure OCI CLI is configured with proper credentials
    3. Generate kubeconfig:
       ${self.kubeconfig_command}
    4. Test cluster access:
       ${self.kubectl_test_command}
    5. To use workload identity in your pods, add these annotations to your ServiceAccount:
       metadata:
         annotations:
           oci.oraclecloud.com/workload-identity: "true"
  EOT
}

