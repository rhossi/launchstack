#!/bin/bash
# Simple test script to verify aegra.json doesn't get corrupted

set -e

API_BASE="http://localhost:8000"
AEGRA_JSON="stack-agent-manager/data/agent-platform/aegra/aegra.json"

echo "============================================================"
echo "Testing aegra.json corruption fix"
echo "============================================================"

# Check initial state
echo ""
echo "1. Checking initial state of aegra.json..."
if [ ! -f "$AEGRA_JSON" ]; then
    echo "❌ File does not exist: $AEGRA_JSON"
    exit 1
fi

if ! python3 -m json.tool "$AEGRA_JSON" > /dev/null 2>&1; then
    echo "❌ File is not valid JSON"
    exit 1
fi

INITIAL_COUNT=$(python3 -c "import json; f=open('$AEGRA_JSON', 'r', encoding='utf-8'); d=json.load(f); print(len(d.get('graphs', {})))" 2>/dev/null || echo "0")
echo "✓ File is valid JSON"
echo "  Initial graph count: $INITIAL_COUNT"

# Check if backend is running
echo ""
echo "2. Checking if backend is running..."
if ! curl -s "$API_BASE/health" > /dev/null 2>&1 && ! curl -s "$API_BASE/docs" > /dev/null 2>&1; then
    echo "⚠ Backend may not be running at $API_BASE"
    echo "  Skipping API-based test. File monitoring only."
    
    echo ""
    echo "3. Monitoring file for 10 seconds..."
    echo "   (You can manually trigger agent creation in another terminal)"
    
    for i in {1..100}; do
        if ! python3 -m json.tool "$AEGRA_JSON" > /dev/null 2>&1; then
            echo "❌ CORRUPTION DETECTED at check #$i!"
            exit 1
        fi
        
        # Check for temp/lock files
        TEMP_FILES=$(ls -1 "$(dirname "$AEGRA_JSON")"/.aegra.json.tmp.* 2>/dev/null | wc -l)
        LOCK_FILE=$(dirname "$AEGRA_JSON")/aegra.json.lock
        BACKUP_FILE=$(dirname "$AEGRA_JSON")/aegra.json.bak
        
        if [ -f "$LOCK_FILE" ] || [ "$TEMP_FILES" -gt 0 ]; then
            echo "  [$(date +%H:%M:%S)] Lock/temp files: lock=$([ -f "$LOCK_FILE" ] && echo "yes" || echo "no"), temp=$TEMP_FILES, backup=$([ -f "$BACKUP_FILE" ] && echo "yes" || echo "no")"
        fi
        
        sleep 0.1
    done
    
    echo "✓ File remained valid during monitoring"
    
    # Final check
    echo ""
    echo "4. Final verification..."
    if ! python3 -m json.tool "$AEGRA_JSON" > /dev/null 2>&1; then
        echo "❌ File is invalid after monitoring"
        exit 1
    fi
    
    FINAL_COUNT=$(python3 -c "import json; f=open('$AEGRA_JSON', 'r', encoding='utf-8'); d=json.load(f); print(len(d.get('graphs', {})))" 2>/dev/null || echo "0")
    echo "✓ File is still valid JSON"
    echo "  Final graph count: $FINAL_COUNT"
    
    # Check for leftover temp/lock files
    TEMP_FILES=$(ls -1 "$(dirname "$AEGRA_JSON")"/.aegra.json.tmp.* 2>/dev/null | wc -l)
    LOCK_FILE=$(dirname "$AEGRA_JSON")/aegra.json.lock
    
    if [ "$TEMP_FILES" -gt 0 ]; then
        echo "⚠ Temp files still present: $TEMP_FILES"
    else
        echo "✓ No temp files remaining"
    fi
    
    if [ -f "$LOCK_FILE" ]; then
        echo "⚠ Lock file still present"
    else
        echo "✓ No lock file remaining"
    fi
    
    echo ""
    echo "============================================================"
    echo "✅ TEST PASSED: aegra.json remained valid"
    echo "============================================================"
    exit 0
fi

echo "✓ Backend is running"

# For full API test, we'd need Python requests or a more complex curl script
# For now, just do file monitoring
echo ""
echo "3. Backend is running. For full API test, use the Python script."
echo "   Monitoring file integrity only..."

# Monitor file
for i in {1..50}; do
    if ! python3 -m json.tool "$AEGRA_JSON" > /dev/null 2>&1; then
        echo "❌ CORRUPTION DETECTED at check #$i!"
        exit 1
    fi
    sleep 0.2
done

echo "✓ File remained valid during monitoring"

# Final check
echo ""
echo "4. Final verification..."
if ! python3 -m json.tool "$AEGRA_JSON" > /dev/null 2>&1; then
    echo "❌ File is invalid"
    exit 1
fi

echo "✓ File is still valid JSON"
echo ""
echo "============================================================"
echo "✅ BASIC TEST PASSED: aegra.json remained valid"
echo "============================================================"

