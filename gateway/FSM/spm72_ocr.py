#!/usr/bin/env python3

import csv
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

# -------------------------------------------------
# Configuration
# -------------------------------------------------

BASE_DIR = Path.home() / "spm72_ocr"
IMAGE_DIR = BASE_DIR / "images"
CSV_FILE = BASE_DIR / "spm72_readings.csv"

CAMERA = "/dev/video0"

WIDTH = 640
HEIGHT = 480

INTERVAL = 30  # seconds

# Validated crop for current camera position
CROP_X = 40
CROP_Y = 20
CROP_W = 540
CROP_H = 350

# -------------------------------------------------
# Directories
# -------------------------------------------------

IMAGE_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------
# CSV initialization
# -------------------------------------------------

def initialize_csv():
    if not CSV_FILE.exists():
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "spm72_wm2",
                "image"
            ])


# -------------------------------------------------
# Capture image
# -------------------------------------------------

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
        raise RuntimeError(
            f"Camera capture failed:\n{result.stderr}"
        )


# -------------------------------------------------
# OCR
# -------------------------------------------------

def read_spm72(image_path):
    cmd = [
        "ssocr",
        "-d", "3",
	"-F",
        "crop",
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

    # Find three-digit OCR result
    matches = re.findall(r"\b\d{3}\b", output)

    if not matches:
        raise RuntimeError(
            f"OCR failed: {output}"
        )

    return int(matches[-1])


# -------------------------------------------------
# Save result to CSV
# -------------------------------------------------

def save_reading(timestamp, value, image_path):
    # Store image path relative to BASE_DIR
    relative_image = image_path.relative_to(BASE_DIR)

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            value,
            str(relative_image)
        ])


# -------------------------------------------------
# One measurement cycle
# -------------------------------------------------

def measurement_cycle():

    now = datetime.now().astimezone()

    timestamp = now.isoformat(timespec="seconds")

    filename = now.strftime("%Y%m%d_%H%M%S") + ".jpg"
    image_path = IMAGE_DIR / filename

    try:
        capture_image(image_path)

        value = read_spm72(image_path)

        save_reading(
            timestamp,
            value,
            image_path
        )

        print(
            f"{timestamp} | "
            f"SPM72 = {value:03d} W/m² | "
            f"{image_path}"
        )

    except Exception as e:

        print(
            f"{timestamp} | ERROR | {e}"
        )


# -------------------------------------------------
# Main loop
# -------------------------------------------------

def main():

    initialize_csv()

    print("SPM72 OCR started")
    print(f"Interval: {INTERVAL} s")
    print(f"Images:   {IMAGE_DIR}")
    print(f"CSV:      {CSV_FILE}")
    print()

    while True:

        start = time.monotonic()

        measurement_cycle()

        elapsed = time.monotonic() - start

        sleep_time = max(
            0,
            INTERVAL - elapsed
        )

        time.sleep(sleep_time)


if __name__ == "__main__":
    main()
