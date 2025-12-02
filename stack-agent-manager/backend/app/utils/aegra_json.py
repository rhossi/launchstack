"""Centralized helper module for aegra.json I/O operations.

This module provides safe, atomic operations on aegra.json with file locking
to prevent corruption during concurrent access.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Tuple
from filelock import FileLock, Timeout

logger = logging.getLogger(__name__)

# Path constants - these match the docker-compose mount paths
# Backend service sees: /var/agent-platform/aegra/aegra.json
# Aegra service sees: /app/aegra-data/aegra.json
# Both map to the same host file: ./data/agent-platform/aegra/aegra.json
AEGRA_DATA_DIR = Path("/var/agent-platform/aegra")
AEGRA_JSON_FILE = AEGRA_DATA_DIR / "aegra.json"
LOCK_FILE = AEGRA_JSON_FILE.with_suffix(".json.lock")


def get_aegra_json_path() -> Path:
    """Get the path to aegra.json file.
    
    Returns:
        Path object pointing to aegra.json
    """
    return AEGRA_JSON_FILE


def ensure_aegra_json_exists() -> None:
    """Ensure the aegra.json directory and file exist.
    
    Creates the directory if missing and initializes an empty file
    with the correct structure if the file doesn't exist or is empty.
    """
    AEGRA_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if not AEGRA_JSON_FILE.exists():
        # Create empty file with correct structure
        with open(AEGRA_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump({"graphs": {}}, f, indent=2)
        logger.info(f"Created initial aegra.json at {AEGRA_JSON_FILE}")
    else:
        # Check if file is empty or invalid, initialize if needed
        try:
            with open(AEGRA_JSON_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    # File exists but is empty
                    with open(AEGRA_JSON_FILE, "w", encoding="utf-8") as f:
                        json.dump({"graphs": {}}, f, indent=2)
                    logger.info(f"Initialized empty aegra.json at {AEGRA_JSON_FILE}")
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"aegra.json exists but is invalid: {e}, reinitializing")
            with open(AEGRA_JSON_FILE, "w", encoding="utf-8") as f:
                json.dump({"graphs": {}}, f, indent=2)
            logger.info(f"Reinitialized corrupted aegra.json at {AEGRA_JSON_FILE}")


def read_aegra_json(use_lock: bool = True) -> Dict:
    """Read and parse aegra.json.
    
    Args:
        use_lock: If True, acquire file lock before reading (default: True)
        
    Returns:
        Dictionary containing the JSON data, or {"graphs": {}} if file is missing/empty
        
    Raises:
        json.JSONDecodeError: If file contains invalid JSON (and use_lock=False)
    """
    ensure_aegra_json_exists()
    
    if use_lock:
        lock = FileLock(str(LOCK_FILE), timeout=10)
        try:
            with lock:
                return _read_json_unlocked()
        except Timeout:
            logger.error(f"Timeout acquiring lock to read aegra.json")
            raise Exception("Timeout acquiring lock to read aegra.json")
    else:
        return _read_json_unlocked()


def _read_json_unlocked() -> Dict:
    """Internal function to read JSON without locking (caller must hold lock)."""
    if not AEGRA_JSON_FILE.exists():
        return {"graphs": {}}
    
    try:
        with open(AEGRA_JSON_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"graphs": {}}
            data = json.loads(content)
            # Ensure "graphs" key exists
            if "graphs" not in data:
                data["graphs"] = {}
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse aegra.json: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading aegra.json: {e}")
        raise


def _write_aegra_json_unlocked(data: Dict) -> None:
    """Internal function to write data to aegra.json atomically without acquiring lock.
    
    Caller must hold the lock. Uses atomic write pattern: write to temp file, flush, fsync, then replace.
    
    Args:
        data: Dictionary to write (must have "graphs" key)
        
    Raises:
        ValueError: If data doesn't have "graphs" key
        Exception: If write fails
    """
    if "graphs" not in data:
        raise ValueError("Data must have 'graphs' key")
    
    ensure_aegra_json_exists()
    
    # Create temp file in same directory for atomic replace
    temp_file = AEGRA_JSON_FILE.parent / f".{AEGRA_JSON_FILE.name}.tmp.{os.getpid()}"
    
    try:
        # Write to temp file
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk
        
        # Validate temp file before replacing
        try:
            with open(temp_file, "r", encoding="utf-8") as f:
                json.load(f)  # Validate JSON
        except json.JSONDecodeError as e:
            raise Exception(f"Temp file contains invalid JSON: {e}")
        
        # Atomic replace
        os.replace(temp_file, AEGRA_JSON_FILE)
        
        # Sync directory to ensure change is visible (important for Docker mounts)
        try:
            dir_fd = os.open(AEGRA_JSON_FILE.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except (OSError, AttributeError):
            pass  # Directory sync not critical on all systems
        
        logger.debug(f"Successfully wrote aegra.json")
        
    except Exception as e:
        # Clean up temp file on error
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass
        raise


def write_aegra_json(data: Dict) -> None:
    """Write data to aegra.json atomically.
    
    Uses atomic write pattern: write to temp file, flush, fsync, then replace.
    
    Args:
        data: Dictionary to write (must have "graphs" key)
        
    Raises:
        ValueError: If data doesn't have "graphs" key
        Exception: If write fails after retries
    """
    lock = FileLock(str(LOCK_FILE), timeout=30)
    try:
        with lock:
            _write_aegra_json_unlocked(data)
    except Timeout:
        logger.error(f"Timeout acquiring lock to write aegra.json")
        raise Exception("Timeout acquiring lock to write aegra.json")


def update_graph_entry(graph_id: str, graph_path: str) -> None:
    """Add or update a graph entry in aegra.json.
    
    Args:
        graph_id: Graph ID to register (e.g., "stack123__agent456")
        graph_path: Graph path relative to Aegra working dir
        
    Raises:
        Exception: If update fails
    """
    lock = FileLock(str(LOCK_FILE), timeout=30)
    try:
        with lock:
            data = _read_json_unlocked()
            data["graphs"][graph_id] = graph_path
            _write_aegra_json_unlocked(data)
            logger.info(f"Updated aegra.json with graph_id: {graph_id}")
    except Timeout:
        logger.error(f"Timeout acquiring lock to update aegra.json")
        raise Exception("Timeout acquiring lock to update aegra.json")


def remove_graph_entry(graph_id: str) -> None:
    """Remove a graph entry from aegra.json.
    
    Args:
        graph_id: Graph ID to remove
        
    Raises:
        Exception: If removal fails
    """
    lock = FileLock(str(LOCK_FILE), timeout=30)
    try:
        with lock:
            data = _read_json_unlocked()
            if graph_id in data.get("graphs", {}):
                del data["graphs"][graph_id]
                _write_aegra_json_unlocked(data)
                logger.info(f"Removed graph_id {graph_id} from aegra.json")
            else:
                logger.debug(f"Graph ID {graph_id} not found in aegra.json, nothing to remove")
    except Timeout:
        logger.error(f"Timeout acquiring lock to remove from aegra.json")
        raise Exception("Timeout acquiring lock to remove from aegra.json")


def validate_aegra_json() -> Tuple[bool, str]:
    """Validate that aegra.json is valid JSON and has the correct structure.
    
    Returns:
        Tuple of (is_valid, error_message)
        is_valid: True if file is valid JSON with correct structure
        error_message: Error description if invalid, empty string if valid
    """
    if not AEGRA_JSON_FILE.exists():
        return False, "File does not exist"
    
    try:
        data = read_aegra_json(use_lock=False)  # Read without lock for validation
        
        # Check structure
        if not isinstance(data, dict):
            return False, "JSON is not a dictionary"
        
        if "graphs" not in data:
            return False, "Missing 'graphs' key"
        
        if not isinstance(data["graphs"], dict):
            return False, "'graphs' is not a dictionary"
        
        return True, ""
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

