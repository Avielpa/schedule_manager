#!/usr/bin/env python
"""
Test script for enhanced bulk-create endpoint
Demonstrates all three formats for rapid testing
"""

import os
import django
import json
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schedule_manage.settings')
django.setup()

from schedule.models import Event, Soldier

def test_enhanced_bulk_create():
    """Test all three bulk creation formats"""
    
    print("Enhanced Bulk-Create Endpoint Test")
    print("=" * 50)
    
    # Create a test event first
    test_event = Event.objects.create(
        name="Bulk Create Test Event",
        event_type="TRAINING",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        min_required_soldiers_per_day=5,
        base_days_per_soldier=15,
        home_days_per_soldier=15,
    )
    
    print(f"Created test event: {test_event.name} (ID: {test_event.id})")
    
    # Base URL
    base_url = "http://127.0.0.1:8080/api/soldiers/bulk_create/"
    
    print("\n" + "="*50)
    print("FORMAT 1: Array of Soldier Objects (Original)")
    print("="*50)
    
    format1_data = [
        {
            "event_id": test_event.id,
            "name": "Format1 Soldier A",
            "soldier_id": "F1A001",
            "rank": "PRIVATE",
            "is_exceptional_output": False,
            "is_weekend_only_soldier_flag": False
        },
        {
            "event_id": test_event.id,
            "name": "Format1 Soldier B", 
            "soldier_id": "F1B002",
            "rank": "CORPORAL",
            "is_exceptional_output": True,
            "constraints_data": [
                {
                    "constraint_date": str(test_event.start_date + timedelta(days=5)),
                    "constraint_type": "PERSONAL",
                    "description": "Leave request"
                }
            ]
        }
    ]
    
    print("JSON Request:")
    print(json.dumps(format1_data, indent=2))
    print("\nExpected: Creates 2 soldiers directly from array")
    
    print("\n" + "="*50)
    print("FORMAT 2: Object with Soldiers Array (Enhanced)")
    print("="*50)
    
    format2_data = {
        "event_id": test_event.id,
        "soldiers": [
            {
                "name": "Format2 Soldier A",
                "soldier_id": "F2A001",
                "rank": "PRIVATE"
            },
            {
                "name": "Format2 Soldier B",
                "soldier_id": "F2B002", 
                "rank": "SERGEANT",
                "is_exceptional_output": True
            },
            {
                "name": "Format2 Soldier C",
                "soldier_id": "F2C003",
                "rank": "CORPORAL",
                "is_weekend_only_soldier_flag": True
            }
        ]
    }
    
    print("JSON Request:")
    print(json.dumps(format2_data, indent=2))
    print("\nExpected: Creates 3 soldiers, auto-assigns event_id to all")
    
    print("\n" + "="*50)
    print("FORMAT 3: Rapid Testing with Auto-Generation (New)")
    print("="*50)
    
    format3_data = {
        "event_id": test_event.id,
        "count": 8,
        "base_name": "Rapid Test",
        "base_id": "RT",
        "rank": "PRIVATE", 
        "make_exceptional": [7, 8],
        "make_weekend_only": [6],
        "add_constraints": True
    }
    
    print("JSON Request:")
    print(json.dumps(format3_data, indent=2))
    print("\nExpected: Auto-generates 8 soldiers with:")
    print("  - Names: 'Rapid Test 01', 'Rapid Test 02', etc.")
    print("  - IDs: 'RT001', 'RT002', etc.")
    print("  - Soldiers 7 & 8: Exceptional (with auto-constraints)")
    print("  - Soldier 6: Weekend-only")
    print("  - Auto-generated constraints for exceptional soldiers")
    
    # API Usage Examples
    print("\n" + "="*50)
    print("API USAGE EXAMPLES")
    print("="*50)
    
    print("\n# Format 1: Direct array")
    print("curl -X POST http://127.0.0.1:8080/api/soldiers/bulk_create/ \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '[")
    print(f"    {{\"event_id\": {test_event.id}, \"name\": \"Test A\", \"soldier_id\": \"TA001\", \"rank\": \"PRIVATE\"}},")
    print(f"    {{\"event_id\": {test_event.id}, \"name\": \"Test B\", \"soldier_id\": \"TB002\", \"rank\": \"CORPORAL\"}}")
    print("  ]'")
    
    print("\n# Format 2: Object with soldiers array")
    print("curl -X POST http://127.0.0.1:8080/api/soldiers/bulk_create/ \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{")
    print(f"    \"event_id\": {test_event.id},")
    print("    \"soldiers\": [")
    print("      {\"name\": \"Test A\", \"soldier_id\": \"TA001\", \"rank\": \"PRIVATE\"},")
    print("      {\"name\": \"Test B\", \"soldier_id\": \"TB002\", \"rank\": \"CORPORAL\"}")
    print("    ]")
    print("  }'")
    
    print("\n# Format 3: Rapid testing")
    print("curl -X POST http://127.0.0.1:8080/api/soldiers/bulk_create/ \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{")
    print(f"    \"event_id\": {test_event.id},")
    print("    \"count\": 10,")
    print("    \"base_name\": \"Quick Test\",")
    print("    \"base_id\": \"QT\",")
    print("    \"rank\": \"PRIVATE\",")
    print("    \"make_exceptional\": [9, 10],")
    print("    \"make_weekend_only\": [8],")
    print("    \"add_constraints\": true")
    print("  }'")
    
    print("\n" + "="*50)
    print("TESTING BENEFITS")
    print("="*50)
    
    print("\nFormat 1 (Original): Best for precise control")
    print("  ✓ Full control over each soldier")
    print("  ✓ Individual constraints per soldier")
    print("  ✓ Mixed ranks and properties")
    
    print("\nFormat 2 (Enhanced): Best for grouped soldiers")
    print("  ✓ Single event_id for all soldiers")
    print("  ✓ Cleaner JSON structure")
    print("  ✓ Less repetition")
    
    print("\nFormat 3 (Rapid Testing): Best for quick test data")
    print("  ✓ Auto-generates realistic test data")
    print("  ✓ Automatic constraint generation")
    print("  ✓ Perfect for algorithm testing")
    print("  ✓ Configurable patterns (exceptional, weekend-only)")
    
    print(f"\nTest event ready for bulk creation: Event ID {test_event.id}")
    print("Server should be running on http://127.0.0.1:8080")
    
    return test_event

if __name__ == '__main__':
    test_enhanced_bulk_create()