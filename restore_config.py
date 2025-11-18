#!/usr/bin/env python3
"""
Script to restore original config.py after build.
This restores the version that reads from environment variables.
"""

import sys
from pathlib import Path


def main():
    """Restore original config.py from backup."""
    
    config_path = Path('app/config.py')
    backup_path = Path('app/config.py.backup')
    
    if not backup_path.exists():
        print("⚠️  No backup found at", backup_path)
        print("   Nothing to restore.")
        return 1
    
    # Restore from backup
    with open(backup_path, 'r') as f:
        original_content = f.read()
    
    with open(config_path, 'w') as f:
        f.write(original_content)
    
    print(f"✓ Restored original {config_path} from backup")
    
    # Remove backup
    backup_path.unlink()
    print(f"✓ Removed backup file {backup_path}")
    print()
    print("✓ config.py restored to version that reads from environment variables")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

