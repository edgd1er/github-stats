#!/usr/bin/env python3
"""
Script to update GitHub Actions versions in workflow files.

This script reads all YAML workflow files in .github/workflows/,
detects GitHub Actions (uses: lines), and updates them to the latest versions.

Usage:
    python scripts/update_actions.py [--dry-run] [--verbose]
    make update-actions
"""

import argparse
import os
import re
import sys
from typing import Dict, List, Tuple

# Known GitHub Actions and their latest versions
# Update this dictionary when new versions are released
# Check https://github.com/actions for latest versions
# Note: Use "v7" for actions that are at v7.x or higher
ACTION_VERSIONS: Dict[str, str] = {
    "actions/checkout": "v4",
    "actions/setup-python": "v7",
    "actions/setup-node": "v4",
    "actions/cache": "v4",
    "actions/configure-pages": "v4",
    "actions/deploy-pages": "v4",
    "actions/download-artifact": "v4",
    "actions/upload-artifact": "v4",
    "actions/github-script": "v7",
}

# Pattern to match GitHub Actions in YAML files
# Matches: uses: owner/repo@version or uses: owner/repo@ref
# Also matches lines starting with optional dash and spaces: - uses: ...
ACTION_PATTERN = re.compile(
    r"^(\s*-?\s*uses:\s*)"
    r"(actions/[a-zA-Z0-9_-]+)"  # Official actions (with hyphens and underscores)
    r"(@[a-zA-Z0-9_.-]+)?"  # Optional version/ref
    r"(\s*.*)?$",  # Rest of the line
    re.MULTILINE,
)

# Pattern for third-party actions (not in actions/ namespace)
THIRD_PARTY_PATTERN = re.compile(
    r"^(\s*uses:\s*)"
    r"([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)"  # owner/repo
    r"(@[a-zA-Z0-9_.-]+)?"  # Optional version/ref
    r"(\s*.*)?$",  # Rest of the line
    re.MULTILINE,
)


def find_workflow_files() -> List[str]:
    """Find all workflow YAML files in .github/workflows/"""
    workflow_dir = ".github/workflows"
    if not os.path.exists(workflow_dir):
        return []
    
    workflow_files = []
    for filename in os.listdir(workflow_dir):
        if filename.endswith((".yml", ".yaml")):
            workflow_files.append(os.path.join(workflow_dir, filename))
    
    return sorted(workflow_files)


def compare_versions(current: str, latest: str) -> bool:
    """
    Compare two version strings and return True if latest > current.
    
    This is a simple comparison that assumes versions are in format vN or vN.M.P
    """
    import re
    
    def extract_version_number(version: str) -> int:
        # Extract the first number after 'v'
        match = re.search(r'v(\d+)', version)
        if match:
            return int(match.group(1))
        return 0
    
    current_num = extract_version_number(current)
    latest_num = extract_version_number(latest)
    
    return latest_num > current_num


def update_file_content(content: str, filename: str, dry_run: bool = False) -> Tuple[str, int]:
    """
    Update action versions in a file's content.
    
    Returns:
        Tuple of (updated_content, number_of_updates)
    """
    original_content = content
    updates_count = 0
    
    # Update official actions (actions/*)
    def replace_official_action(match: re.Match) -> str:
        nonlocal updates_count
        prefix = match.group(1)  # "uses: " part
        action_name = match.group(2)  # "actions/checkout"
        current_version = match.group(3)  # "@v1" or None
        rest = match.group(4)  # Rest of the line
        
        if action_name in ACTION_VERSIONS:
            latest_version = ACTION_VERSIONS[action_name]
            target_version = f"@{latest_version}"
            
            if not current_version:
                # No version specified, add it
                updates_count += 1
                if dry_run:
                    print(f"  [DRY-RUN] Would add {target_version} to {action_name} in {filename}")
                return f"{prefix}{action_name}{target_version}{rest or ''}"
            elif current_version != target_version:
                # Version specified, check if we should update
                # Extract version numbers and compare
                if compare_versions(current_version, target_version):
                    updates_count += 1
                    if dry_run:
                        print(f"  [DRY-RUN] Would update {action_name} from {current_version} to {target_version} in {filename}")
                    return f"{prefix}{action_name}{target_version}{rest or ''}"
                else:
                    # Current version is same or newer
                    pass
        
        return match.group(0)
    
    content = ACTION_PATTERN.sub(replace_official_action, content)
    
    # Count how many matches we found
    if dry_run:
        official_matches = ACTION_PATTERN.findall(content)
        print(f"  Found {len(official_matches)} official action references")
    
    # For third-party actions, we just report them
    if dry_run:
        third_party_matches = THIRD_PARTY_PATTERN.findall(content)
        if third_party_matches:
            print(f"  Found third-party actions (not auto-updated):")
            for match in third_party_matches:
                action_ref = match[1] + (match[2] or "")
                print(f"    - {action_ref}")
    
    return content, updates_count


def update_actions(dry_run: bool = False, verbose: bool = False) -> int:
    """
    Update all GitHub Actions in workflow files.
    
    Returns:
        Total number of updates made
    """
    workflow_files = find_workflow_files()
    
    if not workflow_files:
        print("No workflow files found in .github/workflows/")
        return 0
    
    print(f"Found {len(workflow_files)} workflow file(s)")
    
    total_updates = 0
    
    for workflow_file in workflow_files:
        print(f"\nProcessing: {workflow_file}")
        
        with open(workflow_file, "r") as f:
            content = f.read()
        
        updated_content, updates = update_file_content(content, workflow_file, dry_run)
        total_updates += updates
        
        if not dry_run and updates > 0:
            with open(workflow_file, "w") as f:
                f.write(updated_content)
            print(f"  Updated {updates} action(s)")
        elif dry_run and updates > 0:
            print(f"  Would update {updates} action(s)")
        else:
            print(f"  No updates needed")
    
    return total_updates


def main():
    parser = argparse.ArgumentParser(
        description="Update GitHub Actions versions in workflow files"
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
        "--list-actions",
        action="store_true",
        help="List all known actions and their latest versions"
    )
    
    args = parser.parse_args()
    
    if args.list_actions:
        print("Known GitHub Actions and latest versions:")
        for action, version in sorted(ACTION_VERSIONS.items()):
            print(f"  {action}@{version}")
        return 0
    
    updates = update_actions(dry_run=args.dry_run, verbose=args.verbose)
    
    if updates > 0:
        if args.dry_run:
            print(f"\n\n[DRY-RUN] Would update {updates} action reference(s)")
        else:
            print(f"\n\nUpdated {updates} action reference(s)")
            print("Consider committing the changes:")
            print("  git add .github/workflows/")
            print("  git commit -m 'Update GitHub Actions versions'")
    else:
        print("\n\nAll actions are up to date!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
