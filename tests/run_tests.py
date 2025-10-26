# scripts/run_tests.py

# import sys
# from pathlib import Path
#
# # Add project root to sys.path
# sys.path.append(str(Path(__file__).resolve().parents[1]))


import subprocess
import sys


def main():
    cmd = [
        "pytest",
        "--maxfail=1",
        "--disable-warnings",
        "-q",
        "--cov=src",
        "--cov-report=term-missing",
    ]
    print("[RUN] " + " ".join(cmd))
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
