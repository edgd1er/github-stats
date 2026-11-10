#!/usr/bin/env python3
"""
Script to update Python dependencies to their latest versions.

This script checks for outdated packages and updates them in pyproject.toml.
It uses pip to check for outdated packages and updates the version constraints.

Usage:
    python scripts/update_deps.py [--dry-run] [--verbose]
    make update-deps
"""

import argparse
import re
import subprocess
import sys
from typing import Dict, List, Any, Optional


def get_outdated_packages() -> List[Dict[str, Any]]:
    """Get list of outdated packages from pip."""
    try:
        result = subprocess.run(
            ['pip', 'list', '--outdated', '--format=json'],
            capture_output=True,
            text=True,
            check=True
        )
        import json
        packages = json.loads(result.stdout) if result.stdout else []
        return packages
    except (subprocess.CalledProcessError, ImportError, json.JSONDecodeError) as e:
        print(f"Error getting outdated packages: {e}")
        return []


def read_pyproject() -> Dict[str, Any]:
    """Read and parse pyproject.toml"""
    try:
        import tomllib
        with open('pyproject.toml', 'rb') as f:
            return tomllib.load(f)
    except Exception as e:
        print(f"Error reading pyproject.toml: {e}")
        return {}


def write_pyproject(data: Dict[str, Any]) -> bool:
    """Write pyproject.toml"""
    try:
        import tomli_w
        with open('pyproject.toml', 'wb') as f:
            tomli_w.dump(data, f)
        return True
    except ImportError:
        # Fallback: write as text (not recommended, may lose formatting)
        print("Warning: tomli_w not installed, using fallback method")
        with open('pyproject.toml', 'w') as f:
            f.write(str(data))
        return True
    except Exception as e:
        print(f"Error writing pyproject.toml: {e}")
        return False


def update_deps_in_pyproject(packages: List[Dict[str, Any]], dry_run: bool = False) -> int:
    """Update dependency versions in pyproject.toml"""
    pyproject = read_pyproject()
    
    if 'project' not in pyproject or 'dependencies' not in pyproject['project']:
        print("No dependencies found in pyproject.toml")
        return 0
    
    deps = pyproject['project']['dependencies']
    updates_count = 0
    
    # Create a mapping of package names to current versions
    pkg_to_version: Dict[str, str] = {}
    for dep in deps:
        # Parse dependency string like "requests>=2.28.0"
        match = re.match(r'^([a-zA-Z0-9_\-\.]+)([>=<!~]=?.*$|$)', dep.strip())
        if match:
            pkg_name = match.group(1).lower()
            version_spec = match.group(2).strip()
            pkg_to_version[pkg_name] = version_spec
    
    # Update versions for outdated packages
    for pkg in packages:
        pkg_name = pkg['name'].lower()
        latest_version = pkg['latest_version']
        
        if pkg_name in pkg_to_version:
            current_spec = pkg_to_version[pkg_name]
            # Extract current version if present
            current_version = None
            if current_spec:
                version_match = re.search(r'([>=<!~]=?)\s*([0-9]+\.[0-9]+\.?)', current_spec)
                if version_match:
                    current_version = version_match.group(2)
            
            # Create new version spec
            new_spec = f">={latest_version}"
            
            if current_spec != new_spec:
                updates_count += 1
                if dry_run:
                    print(f"  [DRY-RUN] Would update {pkg['name']} from '{current_spec}' to '{new_spec}'")
                else:
                    print(f"  Updating {pkg['name']} from '{current_spec}' to '{new_spec}'")
                    # Update in the dependencies list
                    for i, dep in enumerate(deps):
                        if dep.strip().lower().startswith(pkg_name):
                            deps[i] = f"{pkg['name']}{new_spec}"
                            break
    
    if updates_count > 0 and not dry_run:
        pyproject['project']['dependencies'] = deps
        write_pyproject(pyproject)
    
    return updates_count


def main():
    parser = argparse.ArgumentParser(
        description="Update Python dependencies to latest versions"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show verbose output"
    )
    parser.add_argument(
        "--no-sync",
        action="store_true",
        help="Don't update pyproject.toml"
    )
    
    args = parser.parse_args()
    
    print("Checking for outdated Python dependencies...")
    
    # First upgrade pip itself
    if not args.dry_run:
        print("Upgrading pip...")
        subprocess.run(['pip', 'install', '--upgrade', 'pip'], check=True)
    
    packages = get_outdated_packages()
    
    if not packages:
        print("All dependencies are up to date!")
        return 0
    
    print(f"Found {len(packages)} outdated package(s):")
    for pkg in packages:
        print(f"  {pkg['name']}: {pkg['version']} -> {pkg['latest_version']}")
    
    print("\nUpdating pyproject.toml...")
    
    if args.no_sync:
        print("  Skipping pyproject.toml update (--no-sync)")
    else:
        updates_count = update_deps_in_pyproject(packages, args.dry_run)
        print(f"  Updated {updates_count} dependency(ies) in pyproject.toml")
    
    if not args.dry_run and not args.no_sync:
        print("\nConsider running 'pip install -e .' to update your environment")
    elif args.dry_run:
        print("\n[DRY-RUN] Run without --dry-run to apply changes")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
