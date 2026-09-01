import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def run(script):
    print("\n" + "=" * 70)
    print(f"RUNNING: {script}")
    print("=" * 70)
    result = subprocess.run(
        [sys.executable, str(BASE_DIR / script)],
        cwd=BASE_DIR,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"{script} failed with exit code {result.returncode}"
        )


def main():
    for script in [
        "01_prepare_dataset.py",
        "02_scatter_spm72_pvrear.py",
        "03_timeseries.py",
        "04_descriptive_report.py",
    ]:
        run(script)

    print("\nAll analysis outputs generated.")


if __name__ == "__main__":
    main()
