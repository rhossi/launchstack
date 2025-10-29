terraform {
  required_version = ">= 1.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

provider "oci" {
  region           = var.region
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
}

# Get availability domains
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

# VCN
resource "oci_core_vcn" "oke_vcn" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = [var.vcn_cidr]
  display_name   = "${var.cluster_name}-vcn"
  dns_label      = var.vcn_dns_label
}

# Internet Gateway
resource "oci_core_internet_gateway" "oke_ig" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.oke_vcn.id
  display_name   = "${var.cluster_name}-ig"
  enabled        = true
}

# NAT Gateway
resource "oci_core_nat_gateway" "oke_nat" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.oke_vcn.id
  display_name   = "${var.cluster_name}-nat"
}

# Service Gateway
data "oci_core_services" "all_services" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}

resource "oci_core_service_gateway" "oke_sg" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.oke_vcn.id
  display_name   = "${var.cluster_name}-sg"

  services {
    service_id = data.oci_core_services.all_services.services[0].id
  }
}

# Route Table for Public Subnet
resource "oci_core_route_table" "oke_public_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.oke_vcn.id
  display_name   = "${var.cluster_name}-public-rt"

  route_rules {
    network_entity_id = oci_core_internet_gateway.oke_ig.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
}

# Route Table for Private Subnets
resource "oci_core_route_table" "oke_private_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.oke_vcn.id
  display_name   = "${var.cluster_name}-private-rt"

  route_rules {
    network_entity_id = oci_core_nat_gateway.oke_nat.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }

  route_rules {
    network_entity_id = oci_core_service_gateway.oke_sg.id
    destination       = data.oci_core_services.all_services.services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
  }
}

# Security List for Load Balancers (Public)
resource "oci_core_security_list" "oke_lb_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.oke_vcn.id
  display_name   = "${var.cluster_name}-lb-sl"

  # Ingress rules - Allow inbound traffic from internet
  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 80
      max = 80
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 443
      max = 443
    }
  }

  # Egress rules
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

# Security List for Worker Nodes (Private)
resource "oci_core_security_list" "oke_worker_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.oke_vcn.id
  display_name   = "${var.cluster_name}-worker-sl"

  # Ingress - Allow all traffic from VCN
  ingress_security_rules {
    protocol = "all"
    source   = var.vcn_cidr
  }

  # Ingress - Allow inbound SSH from bastion (optional)
  ingress_security_rules {
    protocol = "6" # TCP
    source   = var.vcn_cidr
    tcp_options {
      min = 22
      max = 22
    }
  }

  # Ingress - Path discovery
  ingress_security_rules {
    protocol = "1" # ICMP
    source   = var.vcn_cidr
    icmp_options {
      type = 3
      code = 4
    }
  }

  # Egress - Allow all outbound
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

# Security List for Kubernetes API Endpoint (Private)
resource "oci_core_security_list" "oke_api_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.oke_vcn.id
  display_name   = "${var.cluster_name}-api-sl"

  # Ingress - Allow Kubernetes API access from worker nodes
  ingress_security_rules {
    protocol = "6" # TCP
    source   = var.worker_subnet_cidr
    tcp_options {
      min = 6443
      max = 6443
    }
  }

  # Ingress - Allow Kubernetes API access from public (for kubectl access)
  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 6443
      max = 6443
    }
  }

  # Ingress - Allow all from VCN
  ingress_security_rules {
    protocol = "all"
    source   = var.vcn_cidr
  }

  # Ingress - Path discovery
  ingress_security_rules {
    protocol = "1" # ICMP
    source   = var.vcn_cidr
    icmp_options {
      type = 3
      code = 4
    }
  }

  # Egress - Allow all outbound
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

# Public Subnet for Load Balancers
resource "oci_core_subnet" "oke_lb_subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.oke_vcn.id
  cidr_block                 = var.lb_subnet_cidr
  display_name               = "${var.cluster_name}-lb-subnet"
  dns_label                  = "lb"
  prohibit_public_ip_on_vnic = false
  route_table_id             = oci_core_route_table.oke_public_rt.id
  security_list_ids          = [oci_core_security_list.oke_lb_sl.id]
}

# Private Subnet for Worker Nodes
resource "oci_core_subnet" "oke_worker_subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.oke_vcn.id
  cidr_block                 = var.worker_subnet_cidr
  display_name               = "${var.cluster_name}-worker-subnet"
  dns_label                  = "workers"
  prohibit_public_ip_on_vnic = true
  route_table_id             = oci_core_route_table.oke_private_rt.id
  security_list_ids          = [oci_core_security_list.oke_worker_sl.id]
}

# Private Subnet for Kubernetes API Endpoint
resource "oci_core_subnet" "oke_api_subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.oke_vcn.id
  cidr_block                 = var.api_subnet_cidr
  display_name               = "${var.cluster_name}-api-subnet"
  dns_label                  = "api"
  prohibit_public_ip_on_vnic = false
  route_table_id             = oci_core_route_table.oke_public_rt.id
  security_list_ids          = [oci_core_security_list.oke_api_sl.id]
}

# OKE Cluster
resource "oci_containerengine_cluster" "oke_cluster" {
  compartment_id     = var.compartment_ocid
  kubernetes_version = var.kubernetes_version
  name               = var.cluster_name
  vcn_id             = oci_core_vcn.oke_vcn.id

  cluster_pod_network_options {
    cni_type = "FLANNEL_OVERLAY"
  }

  endpoint_config {
    is_public_ip_enabled = true
    subnet_id            = oci_core_subnet.oke_api_subnet.id
  }

  options {
    service_lb_subnet_ids = [oci_core_subnet.oke_lb_subnet.id]

    add_ons {
      is_kubernetes_dashboard_enabled = false
      is_tiller_enabled               = false
    }

    kubernetes_network_config {
      pods_cidr     = var.pods_cidr
      services_cidr = var.services_cidr
    }

    persistent_volume_config {
      defined_tags  = var.defined_tags
      freeform_tags = var.freeform_tags
    }

    service_lb_config {
      defined_tags  = var.defined_tags
      freeform_tags = var.freeform_tags
    }
  }

  type = "ENHANCED_CLUSTER"

  # Enable workload identity
  image_policy_config {
    is_policy_enabled = var.enable_image_policy
  }

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# Node Pool
resource "oci_containerengine_node_pool" "oke_node_pool" {
  cluster_id         = oci_containerengine_cluster.oke_cluster.id
  compartment_id     = var.compartment_ocid
  kubernetes_version = var.kubernetes_version
  name               = "${var.cluster_name}-node-pool"

  node_config_details {
    placement_configs {
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
      subnet_id           = oci_core_subnet.oke_worker_subnet.id
    }

    placement_configs {
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[1].name
      subnet_id           = oci_core_subnet.oke_worker_subnet.id
    }

    placement_configs {
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[2].name
      subnet_id           = oci_core_subnet.oke_worker_subnet.id
    }

    size = var.node_pool_size

    node_pool_pod_network_option_details {
      cni_type = "FLANNEL_OVERLAY"
    }

    defined_tags  = var.defined_tags
    freeform_tags = var.freeform_tags
  }

  node_shape = var.node_shape

  node_shape_config {
    memory_in_gbs = var.node_memory_in_gbs
    ocpus         = var.node_ocpus
  }

  node_source_details {
    image_id    = var.node_image_id
    source_type = "IMAGE"
  }

  initial_node_labels {
    key   = "name"
    value = var.cluster_name
  }

  ssh_public_key = var.ssh_public_key

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

