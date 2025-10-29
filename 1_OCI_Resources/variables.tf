variable "tenancy_ocid" {
  description = "The OCID of your tenancy"
  type        = string
}

variable "user_ocid" {
  description = "The OCID of the user"
  type        = string
}

variable "fingerprint" {
  description = "The fingerprint of the API key"
  type        = string
}

variable "private_key_path" {
  description = "The path to the private key file"
  type        = string
}

variable "region" {
  description = "The OCI region where resources will be created"
  type        = string
  default     = "us-chicago-1"
}

variable "compartment_ocid" {
  description = "The OCID of the compartment where resources will be created"
  type        = string
}

variable "cluster_name" {
  description = "The name of the OKE cluster"
  type        = string
  default     = "oke-cluster"
}

variable "kubernetes_version" {
  description = "The Kubernetes version for the cluster"
  type        = string
  default     = "v1.29.1"
}

# Network Configuration
variable "vcn_cidr" {
  description = "The CIDR block for the VCN"
  type        = string
  default     = "10.0.0.0/16"
}

variable "vcn_dns_label" {
  description = "DNS label for the VCN"
  type        = string
  default     = "okecluster"
}

variable "lb_subnet_cidr" {
  description = "The CIDR block for the load balancer subnet"
  type        = string
  default     = "10.0.10.0/24"
}

variable "worker_subnet_cidr" {
  description = "The CIDR block for the worker nodes subnet"
  type        = string
  default     = "10.0.20.0/24"
}

variable "api_subnet_cidr" {
  description = "The CIDR block for the Kubernetes API endpoint subnet"
  type        = string
  default     = "10.0.30.0/24"
}

variable "pods_cidr" {
  description = "The CIDR block for Kubernetes pods"
  type        = string
  default     = "10.244.0.0/16"
}

variable "services_cidr" {
  description = "The CIDR block for Kubernetes services"
  type        = string
  default     = "10.96.0.0/16"
}

# Node Pool Configuration
variable "node_pool_size" {
  description = "The number of nodes in the node pool"
  type        = number
  default     = 3
}

variable "node_shape" {
  description = "The shape of the nodes in the node pool"
  type        = string
  default     = "VM.Standard.E6.Flex"
}

variable "node_ocpus" {
  description = "The number of OCPUs for each node"
  type        = number
  default     = 4
}

variable "node_memory_in_gbs" {
  description = "The amount of memory in GBs for each node"
  type        = number
  default     = 32
}

variable "node_image_id" {
  description = "The OCID of the image for the nodes. Leave empty to use latest Oracle Linux image."
  type        = string
  default     = ""
}

variable "ssh_public_key" {
  description = "The SSH public key for accessing the nodes"
  type        = string
}

# Workload Identity Configuration
variable "workload_identity_namespace" {
  description = "The Kubernetes namespace for workload identity"
  type        = string
  default     = "default"
}

variable "enable_image_policy" {
  description = "Enable image policy for the cluster"
  type        = bool
  default     = false
}

# Tags
variable "defined_tags" {
  description = "Defined tags for resources"
  type        = map(string)
  default     = {}
}

variable "freeform_tags" {
  description = "Freeform tags for resources"
  type        = map(string)
  default = {
    "ManagedBy" = "Terraform"
  }
}

