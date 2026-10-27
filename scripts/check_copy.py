import os
import sys
import re

BANNED_PATTERNS = [
    r"\bALS\b",
    r"\bkNN\b",
    r"\bTF-IDF\b",
    r"\bMMR\b",
    r"\bisotonic\b",
    r"\bfold-in\b",
    r"\bcollaborative\b",
    r"\bcontent-based\b",
    r"\bBayesian\b",
    r"\bcalibrated\b",
    r"\bNDCG\b",
    r"\blatency\b",
    r"MovieLens\s*#id",
    r"zero\s+synthetic\s+data",
    r"quality\s+gate",
    r"\bstrategy\b",
]

COMPILED_BANNED = [re.compile(p, re.IGNORECASE) for p in BANNED_PATTERNS]

EXCLUDED_PATHS = [
    os.path.normpath("apps/web/src/copy/about.ts"),
    os.path.normpath("apps/web/src/modules/about"),
    os.path.normpath("apps/web/src/components/AboutModal.tsx"),
]

def scan_files():
    root_src = os.path.normpath(r"c:\Users\madha\Desktop\Movie Recommendation\apps\web\src")
    violations = []

    for dirpath, _, filenames in os.walk(root_src):
        for fname in filenames:
            if not fname.endswith((".ts", ".tsx", ".js", ".jsx", ".html")):
                continue
            full_path = os.path.normpath(os.path.join(dirpath, fname))
            
            # Check exclusions
            if any(exc in full_path for exc in EXCLUDED_PATHS):
                continue
                
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        for pattern, raw_pat in zip(COMPILED_BANNED, BANNED_PATTERNS):
                            matches = pattern.findall(line)
                            if matches:
                                violations.append((full_path, idx, matches, line.strip()))
            except Exception as e:
                print(f"Error reading {full_path}: {e}")

    if violations:
        print(f"\n[FAIL] Found {len(violations)} banned word violation(s) outside About module:")
        for path, line_no, matches, line_content in violations[:20]:
            clean_content = line_content[:80].encode('ascii', errors='replace').decode('ascii')
            print(f"  {os.path.relpath(path, root_src)}:{line_no} -> {matches}: '{clean_content}'")
        if len(violations) > 20:
            print(f"  ... and {len(violations) - 20} more violations.")
        return 1
    else:
        print("\n[PASS] No banned words found in visitor-facing surface code.")
        return 0

if __name__ == "__main__":
    sys.exit(scan_files())
