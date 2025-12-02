#!/usr/bin/env python3
"""Monitor aegra.json file for corruption during agent creation."""

import json
import time
from pathlib import Path
import sys

def check_json_validity(file_path: Path) -> tuple[bool, str]:
    """Check if JSON file is valid and return status."""
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

def monitor_file(file_path: Path, check_interval: float = 0.1):
    """Monitor file for changes and corruption."""
    print(f"Monitoring {file_path}")
    print(f"Check interval: {check_interval}s")
    print("-" * 60)
    
    last_size = file_path.stat().st_size if file_path.exists() else 0
    check_count = 0
    
    try:
        while True:
            check_count += 1
            
            # Check for temp files
            temp_files = list(file_path.parent.glob(f".{file_path.name}.tmp.*"))
            lock_file = file_path.with_suffix(".json.lock")
            backup_file = file_path.with_suffix(".json.bak")
            
            # Check file validity
            is_valid, status = check_json_validity(file_path)
            current_size = file_path.stat().st_size if file_path.exists() else 0
            
            # Detect changes
            size_changed = current_size != last_size
            
            timestamp = time.strftime("%H:%M:%S.%f")[:-3]
            
            if size_changed or not is_valid or temp_files or lock_file.exists():
                print(f"[{timestamp}] Check #{check_count}")
                print(f"  Valid: {is_valid} - {status}")
                print(f"  Size: {current_size} bytes {'(changed)' if size_changed else ''}")
                if temp_files:
                    print(f"  Temp files: {[str(tf.name) for tf in temp_files]}")
                if lock_file.exists():
                    print(f"  Lock file exists: {lock_file.name}")
                if backup_file.exists():
                    print(f"  Backup file exists: {backup_file.name}")
                print()
            
            if not is_valid:
                print(f"ERROR: File is corrupted at {timestamp}!")
                print(f"Status: {status}")
                return False
            
            last_size = current_size
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print(f"\nMonitoring stopped after {check_count} checks")
        return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        file_path = Path("stack-agent-manager/data/agent-platform/aegra/aegra.json")
    
    if not file_path.exists():
        print(f"Error: File does not exist: {file_path}")
        sys.exit(1)
    
    # Initial check
    is_valid, status = check_json_validity(file_path)
    print(f"Initial state: {status}")
    print()
    
    # Start monitoring
    success = monitor_file(file_path)
    sys.exit(0 if success else 1)

