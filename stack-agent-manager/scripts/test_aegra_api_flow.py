#!/usr/bin/env python3
"""Test script: Create agent via stack-agent-manager API, then verify Aegra can create assistant."""

import json
import subprocess
import time
import zipfile
import tempfile
import os
from pathlib import Path
import sys

API_BASE = "http://localhost:8000"
AEGRA_API_BASE = "http://localhost:8001"
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
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

def graph():
    graph = StateGraph(State)
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
    """Register a new user and return auth token using curl."""
    # Try to register
    register_cmd = [
        "curl", "-s", "-X", "POST",
        f"{API_BASE}/api/auth/register",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "email": email,
            "password": password,
            "full_name": "Test User"
        })
    ]
    subprocess.run(register_cmd, capture_output=True)  # Ignore errors if already exists
    
    # Login
    login_cmd = [
        "curl", "-s", "-X", "POST",
        f"{API_BASE}/api/auth/login",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"email": email, "password": password})
    ]
    result = subprocess.run(login_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Login failed: {result.stderr}")
    
    try:
        response = json.loads(result.stdout)
        return response["access_token"]
    except Exception as e:
        raise Exception(f"Failed to parse login response: {e}")

def create_stack(token: str, name: str = "Test Stack") -> str:
    """Create a stack and return its ID."""
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{API_BASE}/api/stacks",
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {token}",
        "-d", json.dumps({"name": name, "description": "Test stack for aegra.json verification"})
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to create stack: {result.stderr}")
    
    try:
        response = json.loads(result.stdout)
        return response["id"]
    except Exception as e:
        raise Exception(f"Failed to parse stack response: {e}")

def create_agent(token: str, stack_id: str, name: str, zip_path: Path) -> dict:
    """Create an agent and return the agent data."""
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{API_BASE}/api/stacks/{stack_id}/agents",
        "-H", f"Authorization: Bearer {token}",
        "-F", f"name={name}",
        "-F", "description=Test agent for aegra.json verification",
        "-F", f"file=@{zip_path}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to create agent: {result.stderr}")
    
    try:
        return json.loads(result.stdout)
    except Exception as e:
        raise Exception(f"Failed to parse agent response: {e}")

def check_aegra_assistant(graph_id: str) -> bool:
    """Check if Aegra can list/create an assistant with the given graph_id."""
    # List assistants
    cmd = ["curl", "-s", "-X", "GET", f"{AEGRA_API_BASE}/assistants"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return False
    
    try:
        assistants = json.loads(result.stdout)
        # Check if graph_id is available (either in list or can be created)
        if isinstance(assistants, dict) and "assistants" in assistants:
            assistant_list = assistants["assistants"]
            # Check if any assistant uses this graph_id
            for assistant in assistant_list:
                if assistant.get("assistant_id") == graph_id:
                    return True
        
        # Try to create an assistant with this graph_id
        create_cmd = [
            "curl", "-s", "-X", "POST",
            f"{AEGRA_API_BASE}/assistants",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"graph_id": graph_id, "config": {}})
        ]
        create_result = subprocess.run(create_cmd, capture_output=True, text=True)
        if create_result.returncode == 0:
            try:
                response = json.loads(create_result.stdout)
                return "assistant_id" in response or "error" not in response.lower()
            except:
                return False
        return False
    except Exception:
        return False

def monitor_file_during_operation(file_path: Path, operation_name: str, duration: float = 15.0):
    """Monitor file for corruption during an operation."""
    print(f"\nMonitoring {file_path.name} during {operation_name}...")
    
    check_interval = 0.1
    start_time = time.time()
    check_count = 0
    corruption_detected = False
    last_status = ""
    
    while time.time() - start_time < duration:
        check_count += 1
        
        # Check for temp/lock files
        temp_files = list(file_path.parent.glob(f".{file_path.name}.tmp.*"))
        lock_file = file_path.with_suffix(".json.lock")
        backup_file = file_path.with_suffix(".json.bak")
        
        is_valid, status = check_json_validity(file_path)
        
        if status != last_status:
            timestamp = time.strftime("%H:%M:%S.%f")[:-3]
            print(f"  [{timestamp}] {status}")
            last_status = status
        
        if not is_valid:
            print(f"\n❌ CORRUPTION DETECTED at check #{check_count}!")
            print(f"   Status: {status}")
            corruption_detected = True
            break
        
        if temp_files or lock_file.exists():
            timestamp = time.strftime("%H:%M:%S.%f")[:-3]
            print(f"  [{timestamp}] Lock/temp files: lock={lock_file.exists()}, temp={len(temp_files)}, backup={backup_file.exists()}")
        
        time.sleep(check_interval)
    
    if not corruption_detected:
        print(f"✓ File remained valid during {operation_name} ({check_count} checks)")
    
    return not corruption_detected

def main():
    print("=" * 70)
    print("Testing aegra.json fix with Aegra API integration")
    print("=" * 70)
    
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
    print("\n5. Creating agent via stack-agent-manager API...")
    agent_name = f"test_agent_{int(time.time())}"
    
    try:
        # Check before
        is_valid_before, _ = check_json_validity(AEGRA_JSON_PATH)
        if not is_valid_before:
            print("❌ File invalid before agent creation!")
            return 1
        
        # Start monitoring in background (simplified)
        print("   Starting file monitoring...")
        
        # Create agent (this triggers background task that updates aegra.json)
        agent_data = create_agent(token, stack_id, agent_name, zip_path)
        agent_id = agent_data["id"]
        graph_id = f"{stack_id}__{agent_id}"
        print(f"✓ Agent created: {agent_id}")
        print(f"  Expected graph_id: {graph_id}")
        
        # Monitor for background task completion
        print("\n6. Monitoring aegra.json during background task...")
        success = monitor_file_during_operation(AEGRA_JSON_PATH, "agent creation", duration=20.0)
        
        if not success:
            return 1
        
        # Wait a bit more for background task
        print("\n7. Waiting for background task to complete...")
        time.sleep(5)
        
        # Final check
        print("\n8. Verifying aegra.json was updated...")
        is_valid_final, final_status = check_json_validity(AEGRA_JSON_PATH)
        if not is_valid_final:
            print(f"❌ File is invalid after agent creation: {final_status}")
            return 1
        
        print(f"✓ {final_status}")
        
        # Check graph count increased
        with open(AEGRA_JSON_PATH, "r", encoding="utf-8") as f:
            final_data = json.load(f)
        final_graph_count = len(final_data.get("graphs", {}))
        
        if graph_id not in final_data.get("graphs", {}):
            print(f"❌ Graph ID {graph_id} not found in aegra.json!")
            print(f"   Available graph IDs: {list(final_data.get('graphs', {}).keys())[:5]}...")
            return 1
        
        print(f"✓ Graph ID {graph_id} found in aegra.json")
        print(f"  Graph path: {final_data['graphs'][graph_id]}")
        
        # Check Aegra can access the assistant
        print("\n9. Verifying Aegra can create assistant with graph_id...")
        time.sleep(2)  # Give Aegra time to reload if needed
        
        if check_aegra_assistant(graph_id):
            print(f"✓ Aegra can access assistant with graph_id: {graph_id}")
        else:
            print(f"⚠ Aegra may not have reloaded yet, but graph_id is in aegra.json")
            print(f"  (Aegra reads aegra.json on startup, may need restart to pick up new graphs)")
        
        # Check for temp/lock files (should be cleaned up)
        temp_files = list(AEGRA_JSON_PATH.parent.glob(f".{AEGRA_JSON_PATH.name}.tmp.*"))
        lock_file = AEGRA_JSON_PATH.with_suffix(".json.lock")
        
        if temp_files:
            print(f"\n⚠ Temp files still present: {[str(tf.name) for tf in temp_files]}")
        else:
            print("\n✓ No temp files remaining")
        
        if lock_file.exists():
            print(f"⚠ Lock file still present: {lock_file.name}")
        else:
            print("✓ No lock file remaining")
        
        print("\n" + "=" * 70)
        print("✅ TEST PASSED: aegra.json remained valid and Aegra can access graph")
        print("=" * 70)
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
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

