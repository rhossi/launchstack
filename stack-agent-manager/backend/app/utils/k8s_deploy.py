"""Kubernetes deployment utilities for creating agent deployments."""

import uuid
import asyncio
import secrets
import base64
from concurrent.futures import ThreadPoolExecutor
from kubernetes import client
from app.config import settings

# Shared executor for k8s operations (imported from k8s.py)
from app.utils.k8s import _executor


def create_deployment_manifest(
    agent_id: uuid.UUID,
    stack_id: uuid.UUID,
    namespace: str,
    disk_path: str,
    aegra_image: str = "iad.ocir.io/tenant/aegra-runtime:latest",
) -> dict:
    """
    Create a Kubernetes Deployment manifest for an agent.
    
    Args:
        agent_id: UUID of the agent
        stack_id: UUID of the stack
        namespace: Kubernetes namespace name
        disk_path: Path on host where agent code is stored (extracted directory)
        aegra_image: Docker image for the Aegra runtime
        
    Returns:
        Dictionary representing the Deployment manifest
    """
    deployment_name = f"agent-{agent_id}"
    
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": deployment_name,
            "namespace": namespace,
            "labels": {"app": deployment_name}
        },
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": deployment_name}},
            "template": {
                "metadata": {"labels": {"app": deployment_name}},
                "spec": {
                    "volumes": [
                        {
                            "name": "agent-code",
                            "hostPath": {
                                "path": disk_path,
                                "type": "Directory"
                            }
                        }
                    ],
                    "containers": [
                        {
                            "name": "aegra",
                            "image": aegra_image,
                            "ports": [{"containerPort": 8000}],
                            "volumeMounts": [
                                {
                                    "name": "agent-code",
                                    "mountPath": "/app/graphs"
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }


def create_service_manifest(agent_id: uuid.UUID, namespace: str) -> dict:
    """
    Create a Kubernetes Service manifest for an agent.
    
    Args:
        agent_id: UUID of the agent
        namespace: Kubernetes namespace name
        
    Returns:
        Dictionary representing the Service manifest
    """
    deployment_name = f"agent-{agent_id}"
    
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": deployment_name,
            "namespace": namespace,
            "labels": {"app": deployment_name}
        },
        "spec": {
            "selector": {"app": deployment_name},
            "ports": [
                {"port": 80, "targetPort": 8000, "protocol": "TCP"}
            ],
            "type": "ClusterIP"
        }
    }


def create_ingress_manifest(agent_id: uuid.UUID, stack_id: uuid.UUID, namespace: str) -> dict:
    """
    Create a Kubernetes Ingress manifest for an agent.
    
    Args:
        agent_id: UUID of the agent
        stack_id: UUID of the stack
        namespace: Kubernetes namespace name
        
    Returns:
        Dictionary representing the Ingress manifest
    """
    deployment_name = f"agent-{agent_id}"
    
    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": deployment_name,
            "namespace": namespace,
            "labels": {"app": deployment_name}
        },
        "spec": {
            "rules": [
                {
                    "host": settings.ingress_host,
                    "http": {
                        "paths": [
                            {
                                "path": f"/stacks/{stack_id}/agents/{agent_id}/",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": deployment_name,
                                        "port": {"number": 80}
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }


def get_agent_urls(stack_id: uuid.UUID, agent_id: uuid.UUID) -> tuple[str, str]:
    """
    Generate API and UI URLs for an agent.
    
    Args:
        stack_id: UUID of the stack
        agent_id: UUID of the agent
        
    Returns:
        Tuple of (api_url, ui_url)
    """
    base_url = f"https://{settings.ingress_host}/stacks/{stack_id}/agents/{agent_id}/"
    return base_url, base_url  # Same URL for now, Aegra can route internally


async def create_agent_deployment(
    apps_v1: client.AppsV1Api,
    core_v1: client.CoreV1Api,
    networking_v1: client.NetworkingV1Api,
    agent_id: uuid.UUID,
    stack_id: uuid.UUID,
    namespace: str,
    disk_path: str,
    aegra_image: str = "iad.ocir.io/tenant/aegra-runtime:latest",
) -> tuple[str, str]:
    """
    Create all Kubernetes resources for an agent (Deployment, Service, Ingress).
    
    Args:
        apps_v1: Kubernetes AppsV1Api client
        core_v1: Kubernetes CoreV1Api client
        networking_v1: Kubernetes NetworkingV1Api client
        agent_id: UUID of the agent
        stack_id: UUID of the stack
        namespace: Kubernetes namespace name
        disk_path: Path on host where agent code is stored
        aegra_image: Docker image for the Aegra runtime
        
    Returns:
        Tuple of (api_url, ui_url)
    """
    # Run synchronous k8s API calls in shared executor with timeout
    loop = asyncio.get_event_loop()
    
    # Create Deployment
    deployment_manifest = create_deployment_manifest(
        agent_id, stack_id, namespace, disk_path, aegra_image
    )
    await asyncio.wait_for(
        loop.run_in_executor(
            _executor,
            apps_v1.create_namespaced_deployment,
            namespace,
            deployment_manifest
        ),
        timeout=15.0
    )
    
    # Create Service
    service_manifest = create_service_manifest(agent_id, namespace)
    await asyncio.wait_for(
        loop.run_in_executor(
            _executor,
            core_v1.create_namespaced_service,
            namespace,
            service_manifest
        ),
        timeout=10.0
    )
    
    # Create Ingress
    ingress_manifest = create_ingress_manifest(agent_id, stack_id, namespace)
    await asyncio.wait_for(
        loop.run_in_executor(
            _executor,
            networking_v1.create_namespaced_ingress,
            namespace,
            ingress_manifest
        ),
        timeout=10.0
    )
    
    # Generate URLs
    return get_agent_urls(stack_id, agent_id)


async def delete_agent_deployment(
    apps_v1: client.AppsV1Api,
    core_v1: client.CoreV1Api,
    networking_v1: client.NetworkingV1Api,
    agent_id: uuid.UUID,
    namespace: str,
) -> None:
    """
    Delete all Kubernetes resources for an agent.
    
    Args:
        apps_v1: Kubernetes AppsV1Api client
        core_v1: Kubernetes CoreV1Api client
        networking_v1: Kubernetes NetworkingV1Api client
        agent_id: UUID of the agent
        namespace: Kubernetes namespace name
    """
    deployment_name = f"agent-{agent_id}"
    loop = asyncio.get_event_loop()
    
    # Delete Ingress
    try:
        await asyncio.wait_for(
            loop.run_in_executor(
                _executor,
                networking_v1.delete_namespaced_ingress,
                deployment_name,
                namespace
            ),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        pass  # Ignore timeout
    except client.rest.ApiException as e:
        if e.status != 404:  # Ignore not found
            raise
    
    # Delete Service
    try:
        await asyncio.wait_for(
            loop.run_in_executor(
                _executor,
                core_v1.delete_namespaced_service,
                deployment_name,
                namespace
            ),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        pass  # Ignore timeout
    except client.rest.ApiException as e:
        if e.status != 404:  # Ignore not found
            raise
    
    # Delete Deployment
    try:
        await asyncio.wait_for(
            loop.run_in_executor(
                _executor,
                apps_v1.delete_namespaced_deployment,
                deployment_name,
                namespace
            ),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        pass  # Ignore timeout
    except client.rest.ApiException as e:
        if e.status != 404:  # Ignore not found
            raise


def create_postgres_pvc_manifest(namespace: str) -> dict:
    """Create a PersistentVolumeClaim manifest for PostgreSQL."""
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": "postgres-pvc",
            "namespace": namespace,
            "labels": {"app": "postgres"}
        },
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {
                "requests": {
                    "storage": "10Gi"
                }
            }
        }
    }


def create_postgres_secret_manifest(namespace: str, password: str) -> client.V1Secret:
    """Create a Secret manifest for PostgreSQL credentials."""
    return client.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata=client.V1ObjectMeta(
            name="postgres-secret",
            namespace=namespace,
            labels={"app": "postgres"}
        ),
        type="Opaque",
        data={
            "POSTGRES_PASSWORD": base64.b64encode(password.encode()).decode()
        }
    )


def create_postgres_deployment_manifest(namespace: str) -> dict:
    """Create a Deployment manifest for PostgreSQL."""
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "postgres",
            "namespace": namespace,
            "labels": {"app": "postgres"}
        },
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": "postgres"}},
            "template": {
                "metadata": {"labels": {"app": "postgres"}},
                "spec": {
                    "containers": [
                        {
                            "name": "postgres",
                            "image": "postgres:15-alpine",
                            "ports": [{"containerPort": 5432}],
                            "env": [
                                {"name": "POSTGRES_DB", "value": "stack_db"},
                                {"name": "POSTGRES_USER", "value": "stack_user"},
                                {
                                    "name": "POSTGRES_PASSWORD",
                                    "valueFrom": {
                                        "secretKeyRef": {
                                            "name": "postgres-secret",
                                            "key": "POSTGRES_PASSWORD"
                                        }
                                    }
                                }
                            ],
                            "volumeMounts": [
                                {
                                    "name": "postgres-storage",
                                    "mountPath": "/var/lib/postgresql/data"
                                }
                            ],
                            "livenessProbe": {
                                "exec": {
                                    "command": ["pg_isready", "-U", "stack_user", "-d", "stack_db"]
                                },
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            },
                            "readinessProbe": {
                                "exec": {
                                    "command": ["pg_isready", "-U", "stack_user", "-d", "stack_db"]
                                },
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5
                            },
                            "resources": {
                                "requests": {"memory": "256Mi", "cpu": "100m"},
                                "limits": {"memory": "512Mi", "cpu": "500m"}
                            }
                        }
                    ],
                    "volumes": [
                        {
                            "name": "postgres-storage",
                            "persistentVolumeClaim": {"claimName": "postgres-pvc"}
                        }
                    ]
                }
            }
        }
    }


def create_postgres_service_manifest(namespace: str) -> dict:
    """Create a Service manifest for PostgreSQL."""
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": "postgres",
            "namespace": namespace,
            "labels": {"app": "postgres"}
        },
        "spec": {
            "selector": {"app": "postgres"},
            "ports": [
                {"port": 5432, "targetPort": 5432, "protocol": "TCP"}
            ],
            "type": "ClusterIP"
        }
    }


async def create_postgres_deployment(
    core_v1: client.CoreV1Api,
    apps_v1: client.AppsV1Api,
    namespace: str,
    password: str = None,
) -> None:
    """
    Create all Kubernetes resources for PostgreSQL (PVC, Secret, Deployment, Service).
    
    Args:
        core_v1: Kubernetes CoreV1Api client
        apps_v1: Kubernetes AppsV1Api client
        namespace: Kubernetes namespace name
        password: PostgreSQL password (defaults to random if not provided)
    """
    if password is None:
        password = secrets.token_urlsafe(16)
    
    loop = asyncio.get_event_loop()
    
    # Create PVC
    pvc_manifest = create_postgres_pvc_manifest(namespace)
    await asyncio.wait_for(
        loop.run_in_executor(
            _executor,
            core_v1.create_namespaced_persistent_volume_claim,
            namespace,
            pvc_manifest
        ),
        timeout=10.0
    )
    
    # Create Secret
    secret_manifest = create_postgres_secret_manifest(namespace, password)
    await asyncio.wait_for(
        loop.run_in_executor(
            _executor,
            lambda: core_v1.create_namespaced_secret(namespace=namespace, body=secret_manifest)
        ),
        timeout=10.0
    )
    
    # Create Deployment
    deployment_manifest = create_postgres_deployment_manifest(namespace)
    await asyncio.wait_for(
        loop.run_in_executor(
            _executor,
            apps_v1.create_namespaced_deployment,
            namespace,
            deployment_manifest
        ),
        timeout=15.0
    )
    
    # Create Service
    service_manifest = create_postgres_service_manifest(namespace)
    await asyncio.wait_for(
        loop.run_in_executor(
            _executor,
            core_v1.create_namespaced_service,
            namespace,
            service_manifest
        ),
        timeout=10.0
    )
