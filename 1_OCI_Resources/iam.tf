# Dynamic Group for OKE Cluster
resource "oci_identity_dynamic_group" "oke_cluster_dynamic_group" {
  compartment_id = var.tenancy_ocid
  name           = "${var.cluster_name}-cluster-dynamic-group"
  description    = "Dynamic group for OKE cluster ${var.cluster_name}"

  matching_rule = "ALL {resource.type='cluster', resource.compartment.id='${var.compartment_ocid}'}"
}

# Dynamic Group for OKE Cluster Nodes
resource "oci_identity_dynamic_group" "oke_nodes_dynamic_group" {
  compartment_id = var.tenancy_ocid
  name           = "${var.cluster_name}-nodes-dynamic-group"
  description    = "Dynamic group for OKE cluster nodes in ${var.cluster_name}"

  matching_rule = "ALL {instance.compartment.id='${var.compartment_ocid}'}"
}

# Dynamic Group for Workload Identity
resource "oci_identity_dynamic_group" "oke_workload_identity_group" {
  compartment_id = var.tenancy_ocid
  name           = "${var.cluster_name}-workload-identity-group"
  description    = "Dynamic group for workload identity in OKE cluster ${var.cluster_name}"

  matching_rule = "ALL {resource.type='workloadidentityprincipal', resource.namespace='${var.workload_identity_namespace}', resource.cluster.id='${oci_containerengine_cluster.oke_cluster.id}'}"
}

# Policy for OKE Cluster Management
resource "oci_identity_policy" "oke_cluster_policy" {
  compartment_id = var.compartment_ocid
  name           = "${var.cluster_name}-cluster-policy"
  description    = "Policy for OKE cluster ${var.cluster_name} to manage resources"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_cluster_dynamic_group.name} to manage instance-family in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_cluster_dynamic_group.name} to use subnets in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_cluster_dynamic_group.name} to use vnics in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_cluster_dynamic_group.name} to inspect compartments in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_cluster_dynamic_group.name} to use network-security-groups in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_cluster_dynamic_group.name} to manage load-balancers in compartment id ${var.compartment_ocid}",
  ]
}

# Policy for OKE Nodes
resource "oci_identity_policy" "oke_nodes_policy" {
  compartment_id = var.compartment_ocid
  name           = "${var.cluster_name}-nodes-policy"
  description    = "Policy for OKE nodes in ${var.cluster_name}"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_nodes_dynamic_group.name} to use keys in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_nodes_dynamic_group.name} to use secret-family in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_nodes_dynamic_group.name} to manage objects in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_nodes_dynamic_group.name} to manage buckets in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_nodes_dynamic_group.name} to use metrics in compartment id ${var.compartment_ocid}",
  ]
}

# Policy for Workload Identity
resource "oci_identity_policy" "oke_workload_identity_policy" {
  compartment_id = var.compartment_ocid
  name           = "${var.cluster_name}-workload-identity-policy"
  description    = "Policy for workload identity in OKE cluster ${var.cluster_name}"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_workload_identity_group.name} to use secret-family in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_workload_identity_group.name} to read buckets in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_workload_identity_group.name} to read objects in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_workload_identity_group.name} to manage objects in compartment id ${var.compartment_ocid} where any {request.permission='OBJECT_CREATE', request.permission='OBJECT_INSPECT'}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_workload_identity_group.name} to use metrics in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.oke_workload_identity_group.name} to use log-content in compartment id ${var.compartment_ocid}",
  ]
}

# Additional Policy for OKE Service
resource "oci_identity_policy" "oke_service_policy" {
  compartment_id = var.tenancy_ocid
  name           = "${var.cluster_name}-service-policy"
  description    = "Policy for OKE service operations"

  statements = [
    "Allow service oke to manage all-resources in compartment id ${var.compartment_ocid}",
    "Allow service oke to use virtual-network-family in compartment id ${var.compartment_ocid}",
  ]
}

