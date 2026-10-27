#!/usr/bin/env python3
"""
CineMatch — Final Gap Audit (Section 9)
Executes all 10 acceptance checks and produces clean audit summary.
"""
import os
import sys
import subprocess

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(ROOT_DIR, "apps", "web")

def run_step(step_num: int, title: str, cmd: list, cwd: str = ROOT_DIR) -> bool:
    print(f"\n[{step_num}/10] {title}...", flush=True)
    try:
        # On Windows, npx and npm require shell=True
        use_shell = sys.platform.startswith("win")
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=cwd, shell=use_shell)
        if res.stdout.strip():
            print(res.stdout.strip()[:300], flush=True)
        print(f"[PASS] Check {step_num} passed.", flush=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Check {step_num} failed:\n{e.stderr or e.stdout}", flush=True)
        return False

def main():
    print("=" * 60)
    print("CINEMATCH — FINAL GAP AUDIT (SECTION 9)")
    print("=" * 60, flush=True)

    results = []

    # 1. Banned words outside About
    results.append(run_step(1, "Banned Words Scan", ["python", "scripts/check_copy.py"]))

    # 2. Numeric literals in JSX outside About
    results.append(run_step(2, "JSX Numeric Literals Check", ["python", "scripts/check_jsx_literals.py"]))

    # 3. CSS toolchain & utilities check
    results.append(run_step(3, "Tailwind v4 & Utilities Check", ["python", "scripts/check_utilities.py"]))

    # 4. Identity isolation tests
    results.append(run_step(4, "Session Isolation Verification", ["python", "scripts/verify_isolation.py"]))

    # 5. Module import boundaries (Strict isolation)
    results.append(run_step(5, "StageModule Contract Import Boundaries", ["python", "scripts/check_module_boundaries.py"]))

    # 6. Backend pytest suite (51 tests)
    results.append(run_step(6, "Full Backend Pytest Suite", ["python", "-m", "pytest", "tests"]))

    # 7. Playwright Zero-Overlap Test Suite
    results.append(run_step(7, "Playwright Automated Overlap Suite", ["npx", "playwright", "test"], cwd=WEB_DIR))

    # 8. Dynamic documentation generation
    results.append(run_step(8, "Generated Numbers & README Parity", ["python", "scripts/generate_readme.py"]))

    # 9. Next.js production build check
    results.append(run_step(9, "Next.js Production Bundle Build", ["npm", "run", "build"], cwd=WEB_DIR))

    # 10. Update distribution zip
    results.append(run_step(10, "Package Distribution Zip", ["python", "scripts/package_zip.py"]))

    print("\n" + "=" * 60)
    passed_count = sum(1 for r in results if r)
    print(f"AUDIT SUMMARY: {passed_count}/{len(results)} CHECKS PASSED")
    print("=" * 60, flush=True)

    if all(results):
        print("ALL ACCEPTANCE CRITERIA SATISFIED. READY FOR RELEASE.")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
