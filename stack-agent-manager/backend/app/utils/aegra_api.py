"""Aegra API client utilities for creating and deleting assistants."""

import httpx
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


async def create_assistant(graph_id: str, graph_path: str) -> Optional[str]:
    """
    Create an assistant in Aegra via API.
    
    Args:
        graph_id: The graph ID (e.g., "stack123__agent456")
        graph_path: The graph path (not used by API but kept for compatibility)
        
    Returns:
        assistant_id if successful, None otherwise
    """
    url = f"{settings.aegra_api_base_url}/assistants"
    payload = {
        "graph_id": graph_id,
        "config": {}
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            assistant_id = data.get("assistant_id")
            
            if assistant_id:
                logger.info(f"Successfully created assistant via API: graph_id={graph_id}, assistant_id={assistant_id}")
                return assistant_id
            else:
                # Check if assistant already exists (conflict)
                if response.status_code == 409 or "error" in data:
                    logger.info(f"Assistant already exists for graph_id={graph_id}")
                    # Try to get assistant_id from the response or use graph_id
                    return data.get("assistant_id") or graph_id
                else:
                    logger.warning(f"Created assistant but no assistant_id in response: {data}")
                    return graph_id  # Fallback to graph_id
                    
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 409:
            # Conflict - assistant already exists
            logger.info(f"Assistant already exists for graph_id={graph_id}")
            try:
                data = e.response.json()
                return data.get("assistant_id") or graph_id
            except Exception:
                return graph_id
        else:
            logger.error(f"Failed to create assistant via API: {e.response.status_code} - {e.response.text}")
            return None
    except httpx.RequestError as e:
        error_msg = str(e)
        if not error_msg:
            error_msg = "Connection failed - check if Aegra service is running"
        logger.error(f"Request error creating assistant via API: {error_msg}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating assistant via API: {str(e)}")
        return None


async def delete_assistant(graph_id: str, assistant_id: Optional[str] = None) -> bool:
    """
    Delete an assistant from Aegra via API.
    
    Args:
        graph_id: The graph ID (used as fallback if assistant_id not provided)
        assistant_id: The assistant ID (preferred, but can use graph_id if None)
        
    Returns:
        True if successful, False otherwise
    """
    # Use assistant_id if provided, otherwise use graph_id
    target_id = assistant_id or graph_id
    
    url = f"{settings.aegra_api_base_url}/assistants/{target_id}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(url)
            
            # 404 is acceptable (already deleted)
            if response.status_code == 404:
                logger.info(f"Assistant {target_id} not found (already deleted)")
                return True
                
            response.raise_for_status()
            logger.info(f"Successfully deleted assistant via API: {target_id}")
            return True
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.info(f"Assistant {target_id} not found (already deleted)")
            return True
        else:
            logger.error(f"Failed to delete assistant via API: {e.response.status_code} - {e.response.text}")
            return False
    except httpx.RequestError as e:
        logger.error(f"Request error deleting assistant via API: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting assistant via API: {str(e)}")
        return False

