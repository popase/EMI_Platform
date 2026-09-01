#!/usr/bin/env python3

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

# ============================================================
# SPM72 <-> EMI nearest-neighbor synchronization
# ============================================================

MAX_TIME_DIFFERENCE = 15.0  # seconds


def parse_timestamp(value):
    """Parse ISO-8601 timestamp and return a UTC-aware datetime."""
    value = value.strip()

    if value.endswith("Z"):
        value = value[:-1] + "+00:00"

    dt = datetime.fromisoformat(value)

    if dt.tzinfo is None:
        raise ValueError(f"Timestamp has no timezone: {value}")

    return dt.astimezone(timezone.utc)


def iso_utc(dt):
    """Return UTC timestamp in the format used by the EMI database."""
    return (
        dt.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def read_csv_rows(path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not reader.fieldnames:
        raise RuntimeError(f"Empty CSV: {path}")

    if "timestamp" not in reader.fieldnames:
        raise RuntimeError(f"Missing 'timestamp' column in {path}")

    return rows, reader.fieldnames


def load_spm72(path):
    rows, fields = read_csv_rows(path)

    result = []

    for row in rows:
        status = row.get("status", "").strip()

        # Only valid OCR readings are calibration candidates.
        if status != "VALID":
            continue

        try:
            timestamp = parse_timestamp(row["timestamp"])
            value = float(row["spm72_wm2"])
        except (ValueError, TypeError, KeyError):
            continue

        result.append({
            "timestamp": timestamp,
            "timestamp_original": row["timestamp"],
            "spm72_wm2": value,
            "image": row.get("image", ""),
            "status": status,
        })

    result.sort(key=lambda r: r["timestamp"])
    return result


def load_emi(path):
    rows, fields = read_csv_rows(path)

    result = []

    for row in rows:
        try:
            timestamp = parse_timestamp(row["timestamp"])
        except (ValueError, TypeError, KeyError):
            continue

        result.append({
            "timestamp": timestamp,
            "timestamp_original": row["timestamp"],
            "row": row,
        })

    result.sort(key=lambda r: r["timestamp"])
    return result, fields


def nearest_emi(spm_timestamp, emi_rows):
    """Return the closest EMI row and its signed time difference."""
    if not emi_rows:
        return None, None

    # Binary search without requiring external dependencies.
    lo = 0
    hi = len(emi_rows)

    while lo < hi:
        mid = (lo + hi) // 2

        if emi_rows[mid]["timestamp"] < spm_timestamp:
            lo = mid + 1
        else:
            hi = mid

    candidates = []

    if lo < len(emi_rows):
        candidates.append(emi_rows[lo])

    if lo > 0:
        candidates.append(emi_rows[lo - 1])

    # Deterministic tie-breaking: earlier EMI sample wins.
    best = min(
        candidates,
        key=lambda r: (
            abs((r["timestamp"] - spm_timestamp).total_seconds()),
            r["timestamp"],
        ),
    )

    difference = (
        best["timestamp"] - spm_timestamp
    ).total_seconds()

    return best, difference


def synchronize(series_dir):
    series_dir = Path(series_dir)

    spm_file = series_dir / "spm72_readings.csv"
    emi_file = series_dir / "emi_measurements.csv"
    output_file = series_dir / "synchronized_measurements.csv"

    if not spm_file.exists():
        raise RuntimeError(f"Missing file: {spm_file}")

    if not emi_file.exists():
        raise RuntimeError(f"Missing file: {emi_file}")

    spm_rows = load_spm72(spm_file)
    emi_rows, emi_fields = load_emi(emi_file)

    if not emi_rows:
        raise RuntimeError("No valid EMI measurements found.")

    matched = []
    rejected = []

    for spm in spm_rows:
        emi, difference = nearest_emi(spm["timestamp"], emi_rows)

        if emi is None:
            rejected.append((spm, None))
            continue

        if abs(difference) <= MAX_TIME_DIFFERENCE:
            matched.append((spm, emi, difference))
        else:
            rejected.append((spm, difference))

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    output_fields = [
        "timestamp",
        "spm72_wm2",
        "image",
        "spm72_status",
        "emi_timestamp",
        "time_difference_s",
    ]

    # Keep every EMI measurement variable, except its original
    # timestamp, which is represented as emi_timestamp above.
    for field in emi_fields:
        if field != "timestamp":
            output_fields.append(field)

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()

        for spm, emi, difference in matched:
            out = {
                "timestamp": iso_utc(spm["timestamp"]),
                "spm72_wm2": spm["spm72_wm2"],
                "image": spm["image"],
                "spm72_status": spm["status"],
                "emi_timestamp": iso_utc(emi["timestamp"]),
                "time_difference_s": f"{difference:.3f}",
            }

            for field in emi_fields:
                if field != "timestamp":
                    out[field] = emi["row"].get(field, "")

            writer.writerow(out)

    # --------------------------------------------------------
    # Console report
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("SPM72 <-> EMI NEAREST-NEIGHBOR SYNCHRONIZATION")
    print("=" * 60)
    print(f"Series              : {series_dir}")
    print(f"SPM72 VALID         : {len(spm_rows)}")
    print(f"EMI records         : {len(emi_rows)}")
    print(f"Tolerance           : ±{MAX_TIME_DIFFERENCE:.1f} s")
    print(f"Matched             : {len(matched)}")
    print(f"Rejected            : {len(rejected)}")
    print(f"Output              : {output_file}")
    print()

    if matched:
        print("Matches:")
        print("-" * 60)

        for spm, emi, difference in matched:
            print(
                f"{iso_utc(spm['timestamp'])} | "
                f"SPM72={spm['spm72_wm2']:7.2f} W/m² | "
                f"EMI={iso_utc(emi['timestamp'])} | "
                f"Δt={difference:+7.3f} s"
            )

    if rejected:
        print()
        print("Rejected SPM72 readings:")
        print("-" * 60)

        for item in rejected:
            spm = item[0]
            difference = item[1]

            if difference is None:
                reason = "no EMI measurement"
            else:
                reason = f"nearest EMI Δt={difference:+.3f} s"

            print(
                f"{iso_utc(spm['timestamp'])} | "
                f"SPM72={spm['spm72_wm2']:7.2f} W/m² | "
                f"{reason}"
            )

    print()
    print("Synchronization completed.")
    print()


def main():
    if len(sys.argv) != 2:
        print(
            "Usage:\n"
            "  python3 sync_series.py ~/FSM/series/YYYYMMDD_HHMMSS"
        )
        sys.exit(1)

    try:
        synchronize(sys.argv[1])
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
