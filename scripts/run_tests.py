# scripts/run_tests.py
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
