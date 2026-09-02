import pandas as pd

INPUT = "synchronized_measurements.csv"
OUTPUT = "S08_segmented.csv"

df = pd.read_csv(INPUT)
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

segments = [
    ("S08-A", "2026-08-24 06:38:23", "2026-08-24 07:47:54"),
    ("S08-B", "2026-08-24 07:48:24", "2026-08-24 08:17:54"),
    ("S08-C", "2026-08-24 08:18:24", "2026-08-24 08:47:25"),
]

parts = []

for series_id, start, end in segments:
    start = pd.Timestamp(start, tz="UTC")
    end = pd.Timestamp(end, tz="UTC")

    part = df[
        (df["timestamp"] >= start) &
        (df["timestamp"] <= end)
    ].copy()

    part["series_id"] = series_id
    parts.append(part)

    print(
        f"{series_id}: {len(part)} observations | "
        f"{part['timestamp'].min()} -> {part['timestamp'].max()}"
    )

result = pd.concat(parts, ignore_index=True)
result.to_csv(OUTPUT, index=False)

print(f"\nSaved: {OUTPUT}")