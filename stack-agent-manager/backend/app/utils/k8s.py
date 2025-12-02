"""Kubernetes client utilities for managing namespaces and resources."""

import os
import asyncio
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from kubernetes import client, config as k8s_config
from kubernetes.client.rest import ApiException
from app.config import settings

logger = logging.getLogger(__name__)

# Shared executor for k8s operations
_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="k8s")

# Cache k8s clients (they're thread-safe and stateless)
_k8s_clients: Optional[tuple[client.CoreV1Api, client.AppsV1Api, client.NetworkingV1Api]] = None


def get_k8s_client() -> tuple[client.CoreV1Api, client.AppsV1Api, client.NetworkingV1Api]:
    """
    Initialize and return Kubernetes API clients.
    
    Tries to load in-cluster config first, then falls back to kubeconfig.
    Clients are cached after first initialization for performance.
    
    Returns:
        Tuple of (CoreV1Api, AppsV1Api, NetworkingV1Api) clients
    """
    global _k8s_clients
    
    if _k8s_clients is not None:
        return _k8s_clients
    
    try:
        # Try in-cluster config first (when running in k8s)
        k8s_config.load_incluster_config()
    except k8s_config.ConfigException:
        # Fall back to kubeconfig (for local development)
        kubeconfig_path = settings.k8s_config_path or settings.kubeconfig or os.getenv("KUBECONFIG")
        context = os.getenv("K8S_CONTEXT")  # Allow specifying context via env var
        
        # If no explicit kubeconfig path, try Docker-friendly locations first
        if not kubeconfig_path:
            # Try container-specific kubeconfig in app directory (with corrected paths)
            docker_kubeconfig = "/app/.kube/config"
            if os.path.exists(docker_kubeconfig):
                kubeconfig_path = docker_kubeconfig
            # Fall back to mounted kubeconfig
            elif os.path.exists("/root/.kube/config"):
                kubeconfig_path = "/root/.kube/config"
        
        if kubeconfig_path:
            k8s_config.load_kube_config(config_file=kubeconfig_path, context=context)
        else:
            k8s_config.load_kube_config(context=context)
        
        # Fix paths and server URL if we're in Docker
        try:
            configuration = client.Configuration.get_default_copy()
            
            # Fix certificate paths (replace /Users/felipe/.minikube with /root/.minikube)
            if configuration.ssl_ca_cert and "/Users/felipe/.minikube" in configuration.ssl_ca_cert:
                configuration.ssl_ca_cert = configuration.ssl_ca_cert.replace("/Users/felipe/.minikube", "/root/.minikube")
            if configuration.cert_file and "/Users/felipe/.minikube" in configuration.cert_file:
                configuration.cert_file = configuration.cert_file.replace("/Users/felipe/.minikube", "/root/.minikube")
            if configuration.key_file and "/Users/felipe/.minikube" in configuration.key_file:
                configuration.key_file = configuration.key_file.replace("/Users/felipe/.minikube", "/root/.minikube")
            
            # Fix server URL if we're in Docker and using minikube
            # Replace 127.0.0.1 with host.docker.internal
            if context == "minikube" and configuration.host:
                current_server = configuration.host
                if "127.0.0.1" in current_server or "localhost" in current_server:
                    port_match = re.search(r':(\d+)$', current_server)
                    port = port_match.group(1) if port_match else "6443"
                    
                    # Use host.docker.internal to access host services from Docker
                    new_server = f"https://host.docker.internal:{port}"
                    configuration.host = new_server
                    logger.info(f"Updated k8s server URL from {current_server} to {new_server}")
            
            # In development, disable SSL verification for host.docker.internal
            if settings.environment == "development" and "host.docker.internal" in configuration.host:
                configuration.verify_ssl = False
                configuration.ssl_ca_cert = None
                logger.warning("SSL verification disabled for development mode with host.docker.internal")
            
            # Apply the fixed configuration
            client.Configuration.set_default(configuration)
        except Exception as e:
            # If we can't fix the config, try to continue anyway
            logger.warning(f"Could not update kubeconfig: {e}")
    
    core_v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    networking_v1 = client.NetworkingV1Api()
    
    _k8s_clients = (core_v1, apps_v1, networking_v1)
    return _k8s_clients


async def create_namespace(namespace: str) -> None:
    """
    Create a Kubernetes namespace.
    
    Args:
        namespace: Name of the namespace to create
        
    Raises:
        ApiException: If namespace creation fails
    """
    namespace_manifest = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {"name": namespace}
    }
    
    def _create():
        core_v1, _, _ = get_k8s_client()
        return core_v1.create_namespace(body=namespace_manifest)
    
    # Run synchronous k8s API call in shared executor with short timeout
    try:
        loop = asyncio.get_event_loop()
        await asyncio.wait_for(
            loop.run_in_executor(_executor, _create),
            timeout=5.0  # 5 second timeout - namespace creation should be instant
        )
    except asyncio.TimeoutError:
        raise Exception(f"Timeout creating namespace {namespace} - k8s cluster may be unreachable")
    except ApiException as e:
        if e.status == 409:  # Already exists
            # Namespace already exists, that's okay
            pass
        else:
            raise


async def delete_namespace(namespace: str) -> None:
    """
    Delete a Kubernetes namespace.
    
    This will cascade delete all resources in the namespace.
    The API call returns immediately after triggering deletion;
    Kubernetes handles the actual cleanup asynchronously.
    
    Args:
        namespace: Name of the namespace to delete
        
    Raises:
        ApiException: If namespace deletion fails
    """
    def _delete():
        core_v1, _, _ = get_k8s_client()
        # Delete namespace - API call returns immediately after triggering deletion
        # Kubernetes handles the actual cleanup asynchronously
        return core_v1.delete_namespace(name=namespace)
    
    # Run synchronous k8s API call in shared executor with short timeout
    # The API call itself should return quickly (just triggers deletion)
    try:
        loop = asyncio.get_event_loop()
        await asyncio.wait_for(
            loop.run_in_executor(_executor, _delete),
            timeout=5.0  # 5 second timeout - API call should be instant
        )
    except asyncio.TimeoutError:
        raise Exception(f"Timeout deleting namespace {namespace} - k8s cluster may be unreachable")
    except ApiException as e:
        if e.status == 404:  # Not found
            # Namespace doesn't exist, that's okay
            pass
        else:
            raise


async def namespace_exists(namespace: str) -> bool:
    """
    Check if a namespace exists.
    
    Args:
        namespace: Name of the namespace to check
    
    Returns:
        True if namespace exists, False otherwise
    """
    def _check():
        core_v1, _, _ = get_k8s_client()
        try:
            core_v1.read_namespace(name=namespace)
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            raise
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _check)

