#!/usr/bin/env python3
import os
import re
import sys

MODULES_DIR = os.path.join("apps", "web", "src", "modules")
modules = [d for d in os.listdir(MODULES_DIR) if os.path.isdir(os.path.join(MODULES_DIR, d))]

print(f"[CHECK] Verifying strict isolation between modules: {modules}")
violations = []

import_regex = re.compile(r'from\s+["\'](?:\.\./)*([^"\']+)["\']')

for mod in modules:
    mod_path = os.path.join(MODULES_DIR, mod)
    for root, _, files in os.walk(mod_path):
        for f in files:
            if f.endswith((".ts", ".tsx")):
                full_path = os.path.join(root, f)
                with open(full_path, "r", encoding="utf-8") as fh:
                    for line_num, line in enumerate(fh, 1):
                        match = import_regex.search(line)
                        if match:
                            target = match.group(1)
                            for other in modules:
                                if other == mod:
                                    continue
                                # Check if import points to another module
                                if f"modules/{other}" in target or target.startswith(f"../{other}") or target == f"../{other}":
                                    violations.append(f"{full_path}:{line_num} -> imports '{other}': {line.strip()}")

if violations:
    print(f"[FAIL] Found {len(violations)} cross-module import violation(s):")
    for v in violations:
        print("  ", v)
    sys.exit(1)
else:
    print(f"[PASS] Zero cross-module imports detected across {len(modules)} modules. Universal StageModule contract honored!")
