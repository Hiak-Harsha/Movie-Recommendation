#!/usr/bin/env python3
import os
import re
import sys

# Hard-coded facts that were present in Round 1 (Finding F5)
BANNED_NUMBERS = [
    "591", "20,706", "20706", "100,836", "100836", "9,742", "9742",
    "35 ms", "1.4 ms", "47 / 47"
]

SRC_DIR = os.path.join("apps", "web", "src")
violations = []

for root, _, files in os.walk(SRC_DIR):
    # Tab 5 of About is allowed to display data from API/eval_results, but surface components are not
    for f in files:
        if f.endswith(".tsx"):
            full_path = os.path.join(root, f)
            with open(full_path, "r", encoding="utf-8") as fh:
                for line_num, line in enumerate(fh, 1):
                    for num in BANNED_NUMBERS:
                        if num in line:
                            violations.append(f"{full_path}:{line_num} -> Contains hard-coded fact '{num}': {line.strip()}")

if violations:
    print(f"[FAIL] Found {len(violations)} hard-coded numeric fact(s) in JSX:")
    for v in violations:
        print("  ", v)
    sys.exit(1)
else:
    print(f"[PASS] Zero hardcoded dataset or evaluation metrics found in JSX. All facts generated dynamically!")
