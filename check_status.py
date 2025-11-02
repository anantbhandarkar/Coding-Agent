#!/usr/bin/env python3
"""
Utility to check execution status of a running conversion
"""

import sys
from src.agents.orchestrator import get_execution_status

def main():
    status = get_execution_status()
    
    print("=" * 60)
    print("Conversion Execution Status")
    print("=" * 60)
    
    print(f"\nCurrent Phase: {status['current_phase'] or 'Not Started'}")
    print(f"Progress: {status['progress_percentage']}%")
    
    if status['current_file']:
        print(f"Current File: {status['current_file']}")
    
    print(f"\nFiles: {status['files_processed']}/{status['files_total']}")
    
    if status['safety_blocks']:
        print(f"\n⚠️  Safety Blocks: {len(status['safety_blocks'])}")
        print("\nFiles with safety blocks:")
        for i, block in enumerate(status['safety_blocks'][:10], 1):
            print(f"  {i}. {block['file']} ({block['category']})")
            # Show triggering words if available in error message
            error = block.get('error', '')
            if 'triggering words' in error.lower():
                trigger_line = [line for line in error.split('\n') if 'triggering words' in line.lower()]
                if trigger_line:
                    print(f"     {trigger_line[0][:80]}...")
        if len(status['safety_blocks']) > 10:
            print(f"  ... and {len(status['safety_blocks']) - 10} more")
    
    if status['errors']:
        print(f"\n❌ Errors: {len(status['errors'])}")
        for i, error in enumerate(status['errors'][:5], 1):
            print(f"  {i}. {error[:100]}...")
    
    if not status['current_phase'] and status['files_total'] > 0:
        print("\n✅ Conversion appears to be completed or not running")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()



