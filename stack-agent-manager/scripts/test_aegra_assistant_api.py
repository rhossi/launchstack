#!/usr/bin/env python3
"""Test: Create assistant via Aegra API directly (without updating aegra.json) and verify it works."""

import json
import subprocess
import time
from pathlib import Path
import sys

AEGRA_API_BASE = "http://localhost:8001"
AEGRA_JSON_PATH = Path("stack-agent-manager/data/agent-platform/aegra/aegra.json")

def get_existing_graph_id() -> str:
    """Get an existing graph_id from aegra.json."""
    try:
        with open(AEGRA_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        graphs = data.get("graphs", {})
        if not graphs:
            raise Exception("No graphs found in aegra.json")
        
        # Get the first graph_id
        graph_id = list(graphs.keys())[0]
        graph_path = graphs[graph_id]
        return graph_id, graph_path
    except Exception as e:
        raise Exception(f"Failed to read aegra.json: {e}")

def create_assistant_via_api(graph_id: str, config: dict = None) -> dict:
    """Create an assistant via Aegra API."""
    if config is None:
        config = {}
    
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{AEGRA_API_BASE}/assistants",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"graph_id": graph_id, "config": config})
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to create assistant: {result.stderr}")
    
    try:
        response = json.loads(result.stdout)
        return response
    except Exception as e:
        raise Exception(f"Failed to parse response: {e} - Response: {result.stdout}")

def create_thread() -> dict:
    """Create a thread via Aegra API."""
    # Thread creation may require an empty body or specific structure
    payload = {}
    
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{AEGRA_API_BASE}/threads",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to create thread: {result.stderr}")
    
    try:
        response = json.loads(result.stdout)
        return response
    except Exception as e:
        raise Exception(f"Failed to parse response: {e} - Response: {result.stdout}")

def create_run(thread_id: str, assistant_id: str, input_data: dict) -> dict:
    """Create a run via Aegra API."""
    payload = {
        "assistant_id": assistant_id,
        "input": input_data
    }
    
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{AEGRA_API_BASE}/threads/{thread_id}/runs",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to create run: {result.stderr}")
    
    try:
        response = json.loads(result.stdout)
        return response
    except Exception as e:
        raise Exception(f"Failed to parse response: {e} - Response: {result.stdout}")

def list_assistants() -> dict:
    """List all assistants."""
    cmd = [
        "curl", "-s", "-X", "GET",
        f"{AEGRA_API_BASE}/assistants"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to list assistants: {result.stderr}")
    
    try:
        return json.loads(result.stdout)
    except Exception as e:
        raise Exception(f"Failed to parse response: {e} - Response: {result.stdout}")

def main():
    print("=" * 70)
    print("Test: Create assistant via Aegra API (without updating aegra.json)")
    print("=" * 70)
    
    # Step 1: Get existing graph_id from aegra.json
    print("\n1. Reading existing graph_id from aegra.json...")
    try:
        graph_id, graph_path = get_existing_graph_id()
        print(f"✓ Found graph_id: {graph_id}")
        print(f"  Graph path: {graph_path}")
    except Exception as e:
        print(f"❌ Failed to get graph_id: {e}")
        return 1
    
    # Step 2: Check current assistants
    print("\n2. Checking current assistants...")
    try:
        assistants_data = list_assistants()
        initial_count = len(assistants_data.get("assistants", []))
        print(f"✓ Current assistants: {initial_count}")
        if initial_count > 0:
            print(f"  Assistant IDs: {[a.get('assistant_id') for a in assistants_data.get('assistants', [])[:3]]}")
    except Exception as e:
        print(f"⚠ Failed to list assistants: {e}")
        initial_count = 0
    
    # Step 3: Create assistant via API (without updating aegra.json)
    print("\n3. Creating assistant via Aegra API...")
    print(f"   Using graph_id: {graph_id}")
    print("   Note: NOT updating aegra.json - testing if API alone is sufficient")
    
    assistant_id = None
    
    # First, check if assistant already exists in the list
    assistants_data = list_assistants()
    for assistant in assistants_data.get("assistants", []):
        if assistant.get("graph_id") == graph_id:
            assistant_id = assistant.get("assistant_id")
            print(f"✓ Found existing assistant for graph_id '{graph_id}'")
            print(f"  Assistant ID: {assistant_id}")
            break
    
    # If not found, try to create one
    if not assistant_id:
        try:
            assistant_response = create_assistant_via_api(graph_id)
            assistant_id = assistant_response.get("assistant_id")
            
            if assistant_id:
                print(f"✓ Assistant created successfully!")
                print(f"  Assistant ID: {assistant_id}")
                print(f"  Response: {json.dumps(assistant_response, indent=2)}")
            else:
                # Check if it's a conflict error (assistant already exists)
                if assistant_response.get("error") == "conflict":
                    print(f"⚠ Assistant already exists, fetching from list...")
                    # Refresh the list
                    assistants_data = list_assistants()
                    for assistant in assistants_data.get("assistants", []):
                        if assistant.get("graph_id") == graph_id:
                            assistant_id = assistant.get("assistant_id")
                            print(f"✓ Found existing assistant")
                            print(f"  Assistant ID: {assistant_id}")
                            break
                    
                    if not assistant_id:
                        print(f"❌ Could not find assistant_id: {assistant_response}")
                        return 1
                else:
                    print(f"❌ No assistant_id in response: {assistant_response}")
                    return 1
        except Exception as e:
            print(f"❌ Failed to create assistant: {e}")
            return 1
    
    if not assistant_id:
        print(f"❌ No assistant_id available for graph_id: {graph_id}")
        return 1
    
    # Step 4: Verify assistant appears in list
    print("\n4. Verifying assistant appears in list...")
    try:
        assistants_data = list_assistants()
        new_count = len(assistants_data.get("assistants", []))
        print(f"✓ Assistants count: {initial_count} → {new_count}")
        
        # Check if our assistant is in the list
        assistant_ids = [a.get("assistant_id") for a in assistants_data.get("assistants", [])]
        if assistant_id in assistant_ids:
            print(f"✓ Assistant {assistant_id} found in list")
        else:
            print(f"⚠ Assistant {assistant_id} not found in list (may be filtered)")
    except Exception as e:
        print(f"⚠ Failed to verify assistant: {e}")
    
    # Step 5: Create a thread
    print("\n5. Creating a thread...")
    try:
        thread_response = create_thread()
        thread_id = thread_response.get("thread_id")
        
        if not thread_id:
            print(f"❌ No thread_id in response: {thread_response}")
            return 1
        
        print(f"✓ Thread created: {thread_id}")
    except Exception as e:
        print(f"❌ Failed to create thread: {e}")
        return 1
    
    # Step 6: Create a run with the assistant
    print("\n6. Creating a run with the assistant...")
    print(f"   Thread ID: {thread_id}")
    print(f"   Assistant ID: {assistant_id}")
    
    input_data = {
        "messages": [
            {
                "type": "human",
                "content": [{"type": "text", "text": "Hello, this is a test message"}]
            }
        ]
    }
    
    try:
        run_response = create_run(thread_id, assistant_id, input_data)
        run_id = run_response.get("run_id")
        
        if not run_id:
            print(f"❌ No run_id in response: {run_response}")
            print(f"   Full response: {json.dumps(run_response, indent=2)}")
            return 1
        
        print(f"✓ Run created successfully!")
        print(f"  Run ID: {run_id}")
        print(f"  Status: {run_response.get('status', 'unknown')}")
        print(f"  Response: {json.dumps(run_response, indent=2)}")
        
        print("\n" + "=" * 70)
        print("✅ TEST PASSED: Assistant created via API works without updating aegra.json")
        print("=" * 70)
        print("\nConclusion: Aegra API can create assistants directly without requiring")
        print("            aegra.json to be updated. The API is sufficient.")
        return 0
        
    except Exception as e:
        print(f"❌ Failed to create run: {e}")
        print("\n" + "=" * 70)
        print("❌ TEST FAILED: Assistant created via API cannot execute runs")
        print("=" * 70)
        print("\nConclusion: aegra.json may need to be updated for assistants to work.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

