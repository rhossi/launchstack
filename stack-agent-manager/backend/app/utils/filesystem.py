"""File system utilities for managing agent code on disk."""

import os
import shutil
import zipfile
import tempfile
import logging
from pathlib import Path
from typing import BinaryIO
import uuid

logger = logging.getLogger(__name__)


def get_agent_base_path(base_path: str, stack_id: uuid.UUID, agent_id: uuid.UUID) -> Path:
    """
    Get the base path for an agent's code.
    
    Args:
        base_path: Base path for agent platform (e.g., /var/agent-platform)
        stack_id: UUID of the stack
        agent_id: UUID of the agent
        
    Returns:
        Path object for the agent's directory
    """
    return Path(base_path) / "stacks" / str(stack_id) / "agents" / str(agent_id)


def create_agent_directory(base_path: str, stack_id: uuid.UUID, agent_id: uuid.UUID) -> Path:
    """
    Create the directory structure for an agent.
    
    Creates: /var/agent-platform/stacks/{stack_id}/agents/{agent_id}/
    
    Args:
        base_path: Base path for agent platform
        stack_id: UUID of the stack
        agent_id: UUID of the agent
        
    Returns:
        Path object for the created directory
    """
    agent_path = get_agent_base_path(base_path, stack_id, agent_id)
    agent_path.mkdir(parents=True, exist_ok=True)
    return agent_path


def create_stack_directory(base_path: str, stack_id: uuid.UUID) -> Path:
    """
    Create the directory structure for a stack.
    
    Creates: /var/agent-platform/stacks/{stack_id}/agents/
    
    Args:
        base_path: Base path for agent platform
        stack_id: UUID of the stack
        
    Returns:
        Path object for the stack's agents directory
    """
    stack_agents_path = Path(base_path) / "stacks" / str(stack_id) / "agents"
    stack_agents_path.mkdir(parents=True, exist_ok=True)
    return stack_agents_path


def save_agent_zip(base_path: str, stack_id: uuid.UUID, agent_id: uuid.UUID, file: BinaryIO) -> Path:
    """
    Save uploaded zip file to disk.
    
    Saves to: /var/agent-platform/stacks/{stack_id}/agents/{agent_id}/agent.zip
    
    Args:
        base_path: Base path for agent platform
        stack_id: UUID of the stack
        agent_id: UUID of the agent
        file: File-like object containing the zip data
        
    Returns:
        Path object for the saved zip file
    """
    agent_path = create_agent_directory(base_path, stack_id, agent_id)
    zip_path = agent_path / "agent.zip"
    
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(file, f)
    
    return zip_path


def extract_agent_zip(base_path: str, stack_id: uuid.UUID, agent_id: uuid.UUID) -> Path:
    """
    Extract agent zip file to extracted/ directory.
    
    Extracts to: /var/agent-platform/stacks/{stack_id}/agents/{agent_id}/extracted/
    
    Args:
        base_path: Base path for agent platform
        stack_id: UUID of the stack
        agent_id: UUID of the agent
        
    Returns:
        Path object for the extracted directory
        
    Raises:
        FileNotFoundError: If agent.zip doesn't exist
        zipfile.BadZipFile: If the file is not a valid zip
    """
    agent_path = get_agent_base_path(base_path, stack_id, agent_id)
    zip_path = agent_path / "agent.zip"
    extracted_path = agent_path / "extracted"
    
    if not zip_path.exists():
        raise FileNotFoundError(f"Agent zip file not found: {zip_path}")
    
    # Remove existing extracted directory if it exists
    if extracted_path.exists():
        shutil.rmtree(extracted_path)
    
    extracted_path.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extracted_path)
    
    return extracted_path


def delete_agent_directory(base_path: str, stack_id: uuid.UUID, agent_id: uuid.UUID) -> None:
    """
    Delete an agent's directory and all its contents.
    
    Args:
        base_path: Base path for agent platform
        stack_id: UUID of the stack
        agent_id: UUID of the agent
    """
    agent_path = get_agent_base_path(base_path, stack_id, agent_id)
    if agent_path.exists():
        shutil.rmtree(agent_path)


def delete_stack_directory(base_path: str, stack_id: uuid.UUID) -> None:
    """
    Delete a stack's directory and all its contents (including all agents).
    
    Args:
        base_path: Base path for agent platform
        stack_id: UUID of the stack
    """
    stack_path = Path(base_path) / "stacks" / str(stack_id)
    if stack_path.exists():
        shutil.rmtree(stack_path)


def detect_agent_slug(extracted_path: Path) -> str:
    """
    Detect the agent slug from the extracted zip structure.
    
    The zip file always contains graph.py (but no graphs/ wrapper folder).
    Finds graph.py and uses its containing directory as the agent slug.
    
    Args:
        extracted_path: Path to the extracted directory
        
    Returns:
        Agent slug (directory name containing graph.py)
        
    Raises:
        ValueError: If graph.py is not found
    """
    # Look for graph.py in the extracted directory
    graph_files = list(extracted_path.rglob("graph.py"))
    
    if not graph_files:
        raise ValueError(f"graph.py not found in extracted zip at {extracted_path}")
    
    # Use the first graph.py found
    graph_py_path = graph_files[0]
    agent_dir = graph_py_path.parent
    
    # If graph.py is directly in extracted/, use a default name
    if agent_dir == extracted_path:
        # Check if there's a single top-level directory we can use
        top_level_dirs = [d for d in extracted_path.iterdir() if d.is_dir()]
        if len(top_level_dirs) == 1:
            return top_level_dirs[0].name
        # Otherwise, use the zip filename or a generated name
        # For now, use "agent" as default
        return "agent"
    
    # If graph.py is in a subdirectory, use that directory name
    # Find the directory that's a direct child of extracted/
    current = agent_dir
    while current.parent != extracted_path:
        current = current.parent
        if current == extracted_path:
            break
    
    return current.name

