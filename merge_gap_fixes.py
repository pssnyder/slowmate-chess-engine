#!/usr/bin/env python3
"""
Merge gap fixes into the main opening book for v0.3.01
"""

import json
import os

# Load original mainlines
with open('data/openings/mainlines.json', 'r') as f:
    mainlines = json.load(f)

# Load gap fixes
with open('data/openings/mainlines_gap_fixes.json', 'r') as f:
    gap_fixes = json.load(f)

# Count original positions
original_positions = len([k for k in mainlines.keys() if not k.startswith('_')])
print(f"Original positions: {original_positions}")

# Merge the gap fixes into mainlines
for key, value in gap_fixes.items():
    if not key.startswith('_'):  # Skip comments
        mainlines[key] = value
    elif key.startswith('_') and key not in mainlines:
        mainlines[key] = value

# Count new positions
new_positions = len([k for k in mainlines.keys() if not k.startswith('_')])
print(f"Enhanced positions: {new_positions}")
print(f"Added: {new_positions - original_positions} new positions")

# Save enhanced mainlines
with open('data/openings/mainlines_enhanced_v2.json', 'w') as f:
    json.dump(mainlines, f, indent=2)

print("✅ Enhanced opening book created with gap fixes")
