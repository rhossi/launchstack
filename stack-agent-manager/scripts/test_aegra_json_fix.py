#!/usr/bin/env python3
"""Test script to verify aegra.json doesn't get corrupted when adding agents."""

import json
import requests
import time
import zipfile
import tempfile
import os
from pathlib import Path
import sys

API_BASE = "http://localhost:8000"
AEGRA_JSON_PATH = Path("stack-agent-manager/data/agent-platform/aegra/aegra.json")

def check_json_validity(file_path: Path) -> tuple[bool, str]:
    """Check if JSON file is valid."""
    try:
        if not file_path.exists():
            return False, "File does not exist"
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                return False, "File is empty"
            
            data = json.loads(content)
            if not isinstance(data, dict):
                return False, "JSON is not a dictionary"
            
            if "graphs" not in data:
                return False, "Missing 'graphs' key"
            
            num_graphs = len(data.get("graphs", {}))
            return True, f"Valid JSON with {num_graphs} graphs"
    except json.JSONDecodeError as e:
        return False, f"JSON decode error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def create_test_agent_zip() -> Path:
    """Create a minimal test agent zip file."""
    temp_dir = tempfile.mkdtemp()
    agent_dir = Path(temp_dir) / "test_agent"
    agent_dir.mkdir()
    
    # Create a minimal graph.py
    graph_py = agent_dir / "graph.py"
    graph_py.write_text("""
from langgraph.graph import StateGraph, START, END

def graph():
    graph = StateGraph(dict)
    graph.add_edge(START, END)
    return graph.compile()
""")
    
    # Create __init__.py
    init_py = agent_dir / "__init__.py"
    init_py.write_text("# Test agent")
    
    # Create zip file
    zip_path = Path(temp_dir) / "test_agent.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in agent_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(agent_dir)
                zf.write(file_path, arcname)
    
    return zip_path

def register_and_login(email: str, password: str) -> str:
    """Register a new user and return auth token."""
    # Try to register
    register_data = {
        "email": email,
        "password": password,
        "full_name": "Test User"
    }
    try:
        response = requests.post(f"{API_BASE}/api/auth/register", json=register_data)
        if response.status_code not in [200, 201, 400]:  # 400 = already exists
            print(f"Registration failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Registration error (may already exist): {e}")
    
    # Login
    login_data = {"email": email, "password": password}
    response = requests.post(f"{API_BASE}/api/auth/login", json=login_data)
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")
    
    return response.json()["access_token"]

def create_stack(token: str, name: str = "Test Stack") -> str:
    """Create a stack and return its ID."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {"name": name, "description": "Test stack for aegra.json verification"}
    
    response = requests.post(f"{API_BASE}/api/stacks", json=data, headers=headers)
    if response.status_code not in [200, 201]:
        raise Exception(f"Failed to create stack: {response.status_code} - {response.text}")
    
    return response.json()["id"]

def create_agent(token: str, stack_id: str, name: str, zip_path: Path) -> dict:
    """Create an agent and return the agent data."""
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(zip_path, "rb") as f:
        files = {"file": (zip_path.name, f, "application/zip")}
        data = {
            "name": name,
            "description": "Test agent for aegra.json verification"
        }
        
        response = requests.post(
            f"{API_BASE}/api/stacks/{stack_id}/agents",
            headers=headers,
            files=files,
            data=data
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create agent: {response.status_code} - {response.text}")
        
        return response.json()

def monitor_file_during_operation(file_path: Path, operation_name: str, duration: float = 10.0):
    """Monitor file for corruption during an operation."""
    print(f"\nMonitoring {file_path.name} during {operation_name}...")
    
    check_interval = 0.1
    start_time = time.time()
    check_count = 0
    corruption_detected = False
    
    while time.time() - start_time < duration:
        check_count += 1
        
        # Check for temp/lock files
        temp_files = list(file_path.parent.glob(f".{file_path.name}.tmp.*"))
        lock_file = file_path.with_suffix(".json.lock")
        backup_file = file_path.with_suffix(".json.bak")
        
        is_valid, status = check_json_validity(file_path)
        
        if not is_valid:
            print(f"\n❌ CORRUPTION DETECTED at check #{check_count}!")
            print(f"   Status: {status}")
            corruption_detected = True
            break
        
        if temp_files or lock_file.exists():
            timestamp = time.strftime("%H:%M:%S.%f")[:-3]
            print(f"  [{timestamp}] Lock/temp files present: "
                  f"lock={lock_file.exists()}, "
                  f"temp={len(temp_files)}, "
                  f"backup={backup_file.exists()}")
        
        time.sleep(check_interval)
    
    if not corruption_detected:
        print(f"✓ File remained valid during {operation_name} ({check_count} checks)")
    
    return not corruption_detected

def main():
    print("=" * 60)
    print("Testing aegra.json corruption fix")
    print("=" * 60)
    
    # Check initial state
    print("\n1. Checking initial state of aegra.json...")
    is_valid, status = check_json_validity(AEGRA_JSON_PATH)
    if not is_valid:
        print(f"❌ Initial file is invalid: {status}")
        return 1
    
    print(f"✓ {status}")
    
    # Get initial graph count
    with open(AEGRA_JSON_PATH, "r", encoding="utf-8") as f:
        initial_data = json.load(f)
    initial_graph_count = len(initial_data.get("graphs", {}))
    print(f"  Initial graph count: {initial_graph_count}")
    
    # Authenticate
    print("\n2. Authenticating...")
    try:
        token = register_and_login("test@example.com", "TestPassword123!")
        print("✓ Authenticated successfully")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return 1
    
    # Create stack
    print("\n3. Creating test stack...")
    try:
        stack_id = create_stack(token, f"Test Stack {int(time.time())}")
        print(f"✓ Stack created: {stack_id}")
    except Exception as e:
        print(f"❌ Failed to create stack: {e}")
        return 1
    
    # Create test agent zip
    print("\n4. Creating test agent zip file...")
    try:
        zip_path = create_test_agent_zip()
        print(f"✓ Test agent zip created: {zip_path}")
    except Exception as e:
        print(f"❌ Failed to create test zip: {e}")
        return 1
    
    # Create agent while monitoring
    print("\n5. Creating agent while monitoring aegra.json...")
    agent_name = f"test_agent_{int(time.time())}"
    
    # Start monitoring in background (simplified - we'll check before/after/during)
    try:
        # Check before
        is_valid_before, _ = check_json_validity(AEGRA_JSON_PATH)
        if not is_valid_before:
            print("❌ File invalid before agent creation!")
            return 1
        
        # Create agent (this triggers background task that updates aegra.json)
        agent_data = create_agent(token, stack_id, agent_name, zip_path)
        print(f"✓ Agent created: {agent_data['id']}")
        
        # Monitor for a few seconds while background task completes
        print("\n6. Monitoring file during background task completion...")
        success = monitor_file_during_operation(AEGRA_JSON_PATH, "agent creation", duration=15.0)
        
        if not success:
            return 1
        
        # Wait a bit more for background task
        print("\n7. Waiting for background task to complete...")
        time.sleep(5)
        
        # Final check
        print("\n8. Final verification...")
        is_valid_final, final_status = check_json_validity(AEGRA_JSON_PATH)
        if not is_valid_final:
            print(f"❌ File is invalid after agent creation: {final_status}")
            return 1
        
        print(f"✓ {final_status}")
        
        # Check graph count increased
        with open(AEGRA_JSON_PATH, "r", encoding="utf-8") as f:
            final_data = json.load(f)
        final_graph_count = len(final_data.get("graphs", {}))
        
        if final_graph_count > initial_graph_count:
            print(f"✓ Graph count increased: {initial_graph_count} → {final_graph_count}")
        else:
            print(f"⚠ Graph count unchanged: {initial_graph_count} → {final_graph_count}")
            print("  (Background task may still be running)")
        
        # Check for temp/lock files (should be cleaned up)
        temp_files = list(AEGRA_JSON_PATH.parent.glob(f".{AEGRA_JSON_PATH.name}.tmp.*"))
        lock_file = AEGRA_JSON_PATH.with_suffix(".json.lock")
        
        if temp_files:
            print(f"⚠ Temp files still present: {[str(tf.name) for tf in temp_files]}")
        else:
            print("✓ No temp files remaining")
        
        if lock_file.exists():
            print(f"⚠ Lock file still present: {lock_file.name}")
        else:
            print("✓ No lock file remaining")
        
        print("\n" + "=" * 60)
        print("✅ TEST PASSED: aegra.json remained valid throughout agent creation")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during agent creation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        try:
            os.unlink(zip_path)
            os.rmdir(zip_path.parent)
        except Exception:
            pass

if __name__ == "__main__":
    sys.exit(main())

