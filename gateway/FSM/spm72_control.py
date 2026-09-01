#!/usr/bin/env python3

import csv
import re
import subprocess
import time
import sqlite3
#from datetime import datetime
from datetime import datetime, timezone
from pathlib import Path

# =================================================
# Configuration
# =================================================

BASE_DIR = Path.home() / "FSM"
IMAGE_DIR = BASE_DIR / "images"
SERIES_DIR = BASE_DIR / "series"

CAMERA = "/dev/video0"
WIDTH = 640
HEIGHT = 480

INTERVAL = 30  # seconds

# Validated OCR configuration
CROP_X = 40
CROP_Y = 20
CROP_W = 540
CROP_H = 350

# EMI Platform database
DB_FILE = Path.home() / ".node-red" / "emi_platform.db"
EXPECTED_NODE_ID = 1
MAX_RECORD_AGE = 30  # seconds

# EMI Node
MODBUS_PORT = "/dev/ttyUSB0"
MODBUS_UNIT_ID = 1

# =================================================
# States
# =================================================

IDLE = "IDLE"
OCR_CHECK = "OCR CHECK"
EMI_NODE_CHECK = "EMI NODE CHECK"
MEASUREMENT = "MEASUREMENT"
STOP = "STOP"


# =================================================
# Directories
# =================================================

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
SERIES_DIR.mkdir(parents=True, exist_ok=True)


# =================================================
# OCR functions
# =================================================

def capture_image(image_path):
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-f", "v4l2",
        "-video_size", f"{WIDTH}x{HEIGHT}",
        "-i", CAMERA,
        "-frames:v", "1",
        "-y",
        str(image_path)
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        raise RuntimeError(f"Camera capture failed: {result.stderr.strip()}")


def read_spm72(image_path):
    cmd = [
        "ssocr",
        "-d", "3",
        "-F", "crop",
        str(CROP_X),
        str(CROP_Y),
        str(CROP_W),
        str(CROP_H),
        "dilation",
        "-M", "30x50",
        str(image_path)
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=10
    )

    output = result.stdout.strip()
    matches = re.findall(r"\b\d{3}\b", output)

    if not matches:
        raise RuntimeError(f"OCR failed: {output}")

    return int(matches[-1])


def ocr_check():
    now = datetime.now().astimezone()
    image_path = IMAGE_DIR / (
        now.strftime("check_%Y%m%d_%H%M%S") + ".jpg"
    )

    try:
        capture_image(image_path)
        value = read_spm72(image_path)

        print()
        print(f"Timestamp : {now.isoformat(timespec='seconds')}")
        print(f"OCR       : {value:03d} W/m²")
        print(f"Image     : {image_path}")
        print()
        print("Verify visually that the display is correctly framed.")
        answer = input("Accept OCR configuration? [y/N]: ").strip().lower()

        return answer == "y"

    except Exception as exc:
        print(f"\nOCR CHECK ERROR: {exc}")
        return False


# =================================================
# EMI Node check
# =================================================

def emi_node_check():
    print()
    print("Checking EMI Node...")

    if not DB_FILE.exists():
        print(f"FAIL: database not found: {DB_FILE}")
        return False

    try:
        conn = sqlite3.connect(str(DB_FILE), timeout=5)
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT
                timestamp,
                node_id,
                temp_front,
                temp_rear,
                temp_pv_bifacial,
                current_front,
                current_rear,
                bme_temperature,
                bme_humidity,
                bme_pressure,
                arduino_uptime
            FROM measurements
            ORDER BY id DESC
            LIMIT 2
        """).fetchall()

        conn.close()

    except Exception as e:
        print(f"FAIL: SQLite error: {e}")
        return False

    if len(rows) < 2:
        print("FAIL: fewer than 2 measurements available.")
        return False

    latest = rows[0]
    previous = rows[1]

    # -------------------------------------------------
    # 1. Node ID
    # -------------------------------------------------

    if latest["node_id"] != EXPECTED_NODE_ID:
        print(
            f"FAIL: unexpected node_id = "
            f"{latest['node_id']}"
        )
        return False

    print("[OK] Node ID = 1")

    # -------------------------------------------------
    # 2. Timestamp
    # -------------------------------------------------

    try:
        latest_time = datetime.fromisoformat(
            latest["timestamp"].replace("Z", "+00:00")
        )

        now = datetime.now(latest_time.tzinfo)
        age = (now - latest_time).total_seconds()

    except Exception as e:
        print(f"FAIL: invalid timestamp: {e}")
        return False

    if age < 0 or age > MAX_RECORD_AGE:
        print(
            f"FAIL: latest measurement is "
            f"{age:.1f} s old"
        )
        return False

    print(f"[OK] Latest measurement: {age:.1f} s old")

    # -------------------------------------------------
    # 3. Sensor values present
    # -------------------------------------------------

    sensor_fields = [
        "temp_front",
        "temp_rear",
        "temp_pv_bifacial",
        "current_front",
        "current_rear",
        "bme_temperature",
        "bme_humidity",
        "bme_pressure",
        "arduino_uptime"
    ]

    for field in sensor_fields:
        if latest[field] is None:
            print(f"FAIL: {field} = NULL")
            return False

    print("[OK] All sensor values present")

    # -------------------------------------------------
    # 4. Arduino uptime
    # -------------------------------------------------

    if (
        previous["arduino_uptime"] is None
        or latest["arduino_uptime"] is None
    ):
        print("FAIL: Arduino uptime unavailable")
        return False

    if latest["arduino_uptime"] <= previous["arduino_uptime"]:
        print(
            "FAIL: Arduino uptime is not increasing "
            f"({previous['arduino_uptime']} -> "
            f"{latest['arduino_uptime']})"
        )
        return False

    print(
        "[OK] Arduino uptime increasing: "
        f"{previous['arduino_uptime']} -> "
        f"{latest['arduino_uptime']}"
    )

    # -------------------------------------------------
    # 5. Display current values
    # -------------------------------------------------

    print()
    print("EMI Node:")
    print(f"  Timestamp        : {latest['timestamp']}")
    print(f"  Temp Front       : {latest['temp_front']}")
    print(f"  Temp Rear        : {latest['temp_rear']}")
    print(f"  Temp PV Bifacial : {latest['temp_pv_bifacial']}")
    print(f"  Current Front    : {latest['current_front']}")
    print(f"  Current Rear     : {latest['current_rear']}")
    print(f"  BME Temperature  : {latest['bme_temperature']}")
    print(f"  BME Humidity     : {latest['bme_humidity']}")
    print(f"  BME Pressure     : {latest['bme_pressure']}")
    print(f"  Arduino Uptime   : {latest['arduino_uptime']}")

    print()
    print("EMI NODE CHECK: PASS")

    return True


# =================================================
# Measurement
# =================================================
def utc_timestamp(dt):
    """
    Convert timezone-aware datetime to UTC ISO-8601 timestamp,
    matching the format used by SQLite.
    """
    return (
        dt.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )

def start_series():
    now = datetime.now().astimezone()
    series_id = now.strftime("%Y%m%d_%H%M%S")

    series_dir = SERIES_DIR / series_id
    series_dir.mkdir(parents=True, exist_ok=True)

    csv_file = series_dir / "spm72_readings.csv"

    with open(csv_file, "w", newline="") as f:
        csv.writer(f).writerow([
            "timestamp",
            "spm72_wm2",
            "image",
            "status"
        ])

    print()
    print("=" * 48)
    print(f"SERIES STARTED: {series_id}")
    print(f"Interval       : {INTERVAL} s")
    print(f"CSV            : {csv_file}")
    print("=" * 48)

    return series_id, series_dir, csv_file, now


def measurement_cycle(series_dir, csv_file):
    now = datetime.now().astimezone()
    timestamp = now.isoformat(timespec="seconds")

    image_path = series_dir / (
        now.strftime("%Y%m%d_%H%M%S") + ".jpg"
    )

    try:
        capture_image(image_path)
        value = read_spm72(image_path)

        with open(csv_file, "a", newline="") as f:
            csv.writer(f).writerow([
                timestamp,
                value,
                str(image_path.relative_to(BASE_DIR)),
                "VALID"
            ])

        print(
            f"{timestamp} | "
            f"SPM72 = {value:03d} W/m² | VALID"
        )

        return True

    except Exception as exc:

        # Keep the measurement series running.
        # Record the OCR/capture failure.

        with open(csv_file, "a", newline="") as f:
            csv.writer(f).writerow([
                timestamp,
                "",
                str(image_path.relative_to(BASE_DIR))
                if image_path.exists() else "",
                "OCR_ERROR"
            ])

        print(
            f"{timestamp} | "
            f"OCR_ERROR | {exc}"
        )

        return False

    except Exception as exc:
        print(f"{timestamp} | ERROR | {exc}")
        return False


# =================================================
# Main menu
# =================================================

def print_menu(state):
    print()
    print("=" * 48)
    print("       EMI PLATFORM - SPM72 CONTROL")
    print("=" * 48)
    print(f"State: {state}")
    print()
    print("1. OCR CHECK")
    print("2. EMI NODE CHECK")
    print("3. START MEASUREMENT")
    print("4. STOP")
    print("5. EXIT")
    print("=" * 48)

def export_emi_measurements(series_dir, series_start, series_stop):
    output_file = series_dir / "emi_measurements.csv"

    try:
        conn = sqlite3.connect(str(DB_FILE))
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT
                timestamp,
                node_id,
                temp_front,
                temp_rear,
                temp_pv_bifacial,
                current_front,
                current_rear,
                bme_temperature,
                bme_humidity,
                bme_pressure,
                arduino_uptime
            FROM measurements
            WHERE timestamp >= ?
              AND timestamp <= ?
            ORDER BY timestamp
        """, (
            series_start,
            series_stop
        )).fetchall()

        conn.close()

        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)

            writer.writerow([
                "timestamp",
                "node_id",
                "temp_front",
                "temp_rear",
                "temp_pv_bifacial",
                "current_front",
                "current_rear",
                "bme_temperature",
                "bme_humidity",
                "bme_pressure",
                "arduino_uptime"
            ])

            for row in rows:
                writer.writerow([
                    row["timestamp"],
                    row["node_id"],
                    row["temp_front"],
                    row["temp_rear"],
                    row["temp_pv_bifacial"],
                    row["current_front"],
                    row["current_rear"],
                    row["bme_temperature"],
                    row["bme_humidity"],
                    row["bme_pressure"],
                    row["arduino_uptime"]
                ])

        print(f"EMI measurements exported: {len(rows)} records")
        print(f"File: {output_file}")

        return True

    except Exception as e:
        print(f"EMI export ERROR: {e}")
        return False

def main():
    ocr_validated = False
    emi_node_validated = False
    state = IDLE
    series_dir = None
    csv_file = None
    measurement_running = False

    print("\nSPM72 Control started")

    while True:

        print_menu(state)
        choice = input("Select: ").strip()

        # -----------------------------------------
        # OCR CHECK
        # -----------------------------------------
        if choice == "1":
            if state != IDLE:
                print("OCR CHECK is available only from IDLE.")
                continue

            state = OCR_CHECK
            print(f"\nSTATE -> {state}")

            if ocr_check():
                print("OCR CHECK: PASS")
                ocr_validated = True
                state = IDLE
            else:
                print("OCR CHECK: NOT ACCEPTED")
                ocr_validated = False
                state = IDLE

        # -----------------------------------------
        # EMI NODE CHECK
        # -----------------------------------------
        elif choice == "2":
            if state != IDLE:
                print("EMI NODE CHECK is available only from IDLE.")
                continue

            state = EMI_NODE_CHECK
            print(f"\nSTATE -> {state}")

            if emi_node_check():
                emi_node_validated = True
                print("EMI NODE CHECK: PASS")
            else:
                emi_node_validated = False
                print("EMI NODE CHECK: NOT ACCEPTED")

            state = IDLE

        # -----------------------------------------
        # START MEASUREMENT
        # -----------------------------------------
        elif choice == "3":
            if state != IDLE:
                print("START MEASUREMENT is available only from IDLE.")
                continue

            print("\nBefore starting measurement:")
            print("  - OCR CHECK must have been performed.")
            print("  - EMI NODE CHECK must have been performed.")
            answer = input("Start measurement? [y/N]: ").strip().lower()

            if answer != "y":
                continue
            if not ocr_validated:
                print("Cannot start: OCR CHECK not passed.")
                continue

            if not emi_node_validated:
                print("Cannot start: EMI NODE CHECK not passed.")
                continue


            state = MEASUREMENT
            print(f"\nSTATE -> {state}")

            #_, series_dir, csv_file = start_series()
            series_id, series_dir, csv_file, series_start = start_series()
            measurement_running = True

            print("\nPress ENTER to stop the measurement series.")

            while measurement_running:
                start = time.monotonic()

                measurement_cycle(series_dir, csv_file)

                elapsed = time.monotonic() - start
                sleep_time = max(0, INTERVAL - elapsed)

                # Allow STOP by waiting in short intervals.
                for _ in range(int(sleep_time)):
                    time.sleep(1)
                    if input_available():
                        input()
                        measurement_running = False
                        break

                if measurement_running:
                    remaining = sleep_time - int(sleep_time)
                    if remaining > 0:
                        time.sleep(remaining)

            series_stop = datetime.now().astimezone()

            state = STOP
            print(f"\nSTATE -> {state}")
            print("Measurement series stopped.")

            export_emi_measurements(
                series_dir,
                utc_timestamp(series_start),
                utc_timestamp(series_stop)
            )

            state = IDLE
        # -----------------------------------------
        # STOP
        # -----------------------------------------

        elif choice == "4":
            if state == MEASUREMENT:
                measurement_running = False
            else:
                print("No active measurement.")
            state = STOP
            print(f"\nSTATE -> {state}")
            ocr_validated = False
            emi_node_validated = False
            state = IDLE

        
        # -----------------------------------------
        # EXIT
        # -----------------------------------------
        elif choice == "5":
            if state == MEASUREMENT:
                print("Stop the measurement before exiting.")
                continue

            print("Exiting.")
            break

        else:
            print("Invalid selection.")



def input_available():
    """
    Non-blocking stdin check for Linux/Pi.
    """
    import select
    ready, _, _ = select.select([__import__("sys").stdin], [], [], 0)
    return bool(ready)


if __name__ == "__main__":
    main()
