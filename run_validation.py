#!/usr/bin/env python3
"""
Run validation on a converted project
"""

import os
import sys
import json
import argparse
from src.validators.conversion_validator import ConversionValidator

def main():
    parser = argparse.ArgumentParser(
        description="Validate a converted Node.js project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate with default project path:
  python run_validation.py
  
  # Validate specific project:
  python run_validation.py --project-path my-output-glm
  
  # Validate with metadata:
  python run_validation.py --metadata project-metadata.json
        """
    )
    parser.add_argument(
        "--project-path",
        default="my-output-glm",
        help="Path to the converted project directory (default: my-output-glm)"
    )
    parser.add_argument(
        "--metadata",
        help="Path to project-metadata.json file (optional)"
    )
    
    args = parser.parse_args()
    
    project_path = os.path.abspath(args.project_path)
    
    # Check if project path exists
    if not os.path.exists(project_path):
        print(f"❌ Error: Project path does not exist: {project_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("Conversion Validation")
    print("=" * 60)
    print(f"Project path: {project_path}")
    print("-" * 60)
    
    # Initialize validator
    validator = ConversionValidator()
    
    # Validate project structure
    print("\n📋 Validating project structure...")
    validation_result = validator.validate_project(project_path)
    
    # Validate metadata if provided
    metadata_validation = None
    if args.metadata:
        metadata_path = os.path.abspath(args.metadata)
        if not os.path.exists(metadata_path):
            print(f"⚠️  Warning: Metadata file not found: {metadata_path}")
        else:
            print("\n📋 Validating metadata...")
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                metadata_validation = validator.validate_metadata(metadata)
            except Exception as e:
                print(f"⚠️  Warning: Failed to load metadata: {e}")
    
    # Combine results
    errors = validation_result.get("errors", [])
    warnings = validation_result.get("warnings", [])
    
    if metadata_validation:
        errors.extend(metadata_validation.get("errors", []))
        warnings.extend(metadata_validation.get("warnings", []))
        is_valid = validation_result.get("valid", False) and metadata_validation.get("valid", False)
    else:
        is_valid = validation_result.get("valid", False)
    
    # Print results
    print("\n" + "=" * 60)
    print("Validation Results")
    print("=" * 60)
    
    # Print stats
    stats = validation_result.get("stats", {})
    if stats:
        print("\n📊 Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    # Print warnings
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for warning in warnings[:10]:  # Show first 10
            print(f"  - {warning}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more")
    
    # Print errors
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for error in errors[:10]:  # Show first 10
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    
    # Final status
    print("\n" + "=" * 60)
    if is_valid:
        print("✅ Validation passed")
    else:
        print("❌ Validation failed")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()

