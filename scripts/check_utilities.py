import os
import sys
import re

def check_utilities():
    print("[CHECK] Validating CSS utilities and Tailwind v4 setup...")
    
    # 1. Verify postcss.config.mjs exists and uses @tailwindcss/postcss
    postcss_path = os.path.normpath(r"c:\Users\madha\Desktop\Movie Recommendation\apps\web\postcss.config.mjs")
    if not os.path.exists(postcss_path):
        print(f"[FAIL] Missing {postcss_path}")
        return 1
    with open(postcss_path, "r", encoding="utf-8") as f:
        content = f.read()
        if "@tailwindcss/postcss" not in content:
            print("[FAIL] postcss.config.mjs does not use @tailwindcss/postcss")
            return 1
            
    # 2. Verify globals.css has @import "tailwindcss" and @theme
    css_path = os.path.normpath(r"c:\Users\madha\Desktop\Movie Recommendation\apps\web\src\app\globals.css")
    if not os.path.exists(css_path):
        print(f"[FAIL] Missing {css_path}")
        return 1
    with open(css_path, "r", encoding="utf-8") as f:
        content = f.read()
        if '@import "tailwindcss";' not in content:
            print("[FAIL] globals.css missing @import \"tailwindcss\";")
            return 1
        if '@theme' not in content:
            print("[FAIL] globals.css missing @theme definition")
            return 1
            
    # 3. Check for forbidden broken classes like 'bg-radial' without radial gradient definition
    root_src = os.path.normpath(r"c:\Users\madha\Desktop\Movie Recommendation\apps\web\src")
    bad_classes = ["bg-radial", "animate-in", "fade-in-0", "zoom-in-95"]
    violations = []
    
    for dirpath, _, filenames in os.walk(root_src):
        for fname in filenames:
            if not fname.endswith((".ts", ".tsx", ".jsx", ".js")):
                continue
            fpath = os.path.join(dirpath, fname)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for line_no, line in enumerate(f, 1):
                    for bad in bad_classes:
                        # Match className="... bad ..."
                        if bad in line and "className" in line:
                            violations.append((fpath, line_no, bad, line.strip()))
                            
    if violations:
        print(f"[FAIL] Found {len(violations)} unsupported utility class usage(s):")
        for p, l, bad, text in violations:
            print(f"  {os.path.relpath(p, root_src)}:{l} -> '{bad}': {text[:80]}")
        return 1

    print("[PASS] CSS toolchain and utility check clean.")
    return 0

if __name__ == "__main__":
    sys.exit(check_utilities())
