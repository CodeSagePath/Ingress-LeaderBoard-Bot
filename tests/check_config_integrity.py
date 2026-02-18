import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config.stats_config import STATS_DEFINITIONS, get_stat_by_idx

def check_integrity():
    print("Checking STATS_DEFINITIONS integrity...")
    
    # Check for duplicate indices
    seen_indices = {}
    for stat in STATS_DEFINITIONS:
        idx = stat['idx']
        name = stat['name']
        if idx in seen_indices:
            print(f"FAIL: Duplicate index {idx} found for '{name}' and '{seen_indices[idx]}'")
            return False
        seen_indices[idx] = name
        
    print(f"Verified {len(seen_indices)} unique indices.")

    # Check key stats
    checks = [
        (22, 'XM Recharged'),
        (20, 'Longest Link Ever Created'),
        (16, 'Resonators Deployed'),
        (14, 'Portal Scans Uploaded')
    ]
    
    for idx, expected_name in checks:
        stat = get_stat_by_idx(idx)
        if not stat:
            print(f"FAIL: Stat {idx} not found!")
            return False
        if stat['name'] != expected_name:
            print(f"FAIL: Stat {idx} is '{stat['name']}', expected '{expected_name}'")
            return False
        print(f"OK: Stat {idx} is '{stat['name']}'")

    print("Integrity Check PASSED")
    return True

if __name__ == "__main__":
    if not check_integrity():
        sys.exit(1)
