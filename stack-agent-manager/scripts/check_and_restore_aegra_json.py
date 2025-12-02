#!/usr/bin/env python3
"""Check and restore aegra.json if corrupted."""

import json
import sys
from pathlib import Path

AEGRA_JSON_PATH = Path("stack-agent-manager/data/agent-platform/aegra/aegra.json")
BACKUP_PATH = AEGRA_JSON_PATH.with_suffix(".json.bak")

def check_and_restore():
    """Check if aegra.json is valid, restore from backup if corrupted."""
    if not AEGRA_JSON_PATH.exists():
        print(f"❌ aegra.json does not exist at {AEGRA_JSON_PATH}")
        if BACKUP_PATH.exists():
            print(f"✓ Found backup, restoring...")
            import shutil
            shutil.copy2(BACKUP_PATH, AEGRA_JSON_PATH)
            print(f"✓ Restored from backup")
            return 0
        else:
            print(f"❌ No backup found, creating empty file")
            AEGRA_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(AEGRA_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump({"graphs": {}}, f, indent=2)
            print(f"✓ Created empty aegra.json")
            return 0
    
    # Check if file is valid JSON
    try:
        with open(AEGRA_JSON_PATH, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                print(f"⚠️  aegra.json is empty")
                if BACKUP_PATH.exists():
                    print(f"✓ Found backup, restoring...")
                    import shutil
                    shutil.copy2(BACKUP_PATH, AEGRA_JSON_PATH)
                    print(f"✓ Restored from backup")
                    return 0
                else:
                    print(f"❌ No backup found")
                    return 1
            
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("JSON is not a dictionary")
            if "graphs" not in data:
                raise ValueError("Missing 'graphs' key")
            
            num_graphs = len(data.get("graphs", {}))
            print(f"✓ aegra.json is valid JSON with {num_graphs} graphs")
            return 0
            
    except json.JSONDecodeError as e:
        print(f"❌ aegra.json is corrupted: {e}")
        if BACKUP_PATH.exists():
            print(f"✓ Found backup, restoring...")
            try:
                # Verify backup is valid before restoring
                with open(BACKUP_PATH, "r", encoding="utf-8") as f:
                    backup_data = json.load(f)
                    if not isinstance(backup_data, dict) or "graphs" not in backup_data:
                        print(f"❌ Backup is also corrupted")
                        return 1
                
                import shutil
                shutil.copy2(BACKUP_PATH, AEGRA_JSON_PATH)
                print(f"✓ Restored from backup")
                
                # Verify restored file
                with open(AEGRA_JSON_PATH, "r", encoding="utf-8") as f:
                    restored_data = json.load(f)
                    num_graphs = len(restored_data.get("graphs", {}))
                    print(f"✓ Verified restored file: {num_graphs} graphs")
                return 0
            except Exception as restore_error:
                print(f"❌ Failed to restore from backup: {restore_error}")
                return 1
        else:
            print(f"❌ No backup found")
            return 1
    except Exception as e:
        print(f"❌ Error checking aegra.json: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(check_and_restore())

