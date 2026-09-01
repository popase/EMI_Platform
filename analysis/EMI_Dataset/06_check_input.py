from common import discover_series, load_config, load_metadata, resolve_path


def main():
    config = load_config()
    metadata = load_metadata()
    root = resolve_path(config["input_root"])

    print(f"Input root: {root}")
    print("\nMetadata:")
    print(metadata.to_string(index=False))

    df = discover_series(config, metadata)

    print("\nInput validation OK.")
    print(f"Rows: {len(df):,}")
    print(f"Series: {df['series_id'].nunique()}")
    print("\nColumns used:")
    print("  timestamp")
    print("  SPM72_Wm2")
    print("  PV_Rear")

    print("\nRows per series:")
    print(df.groupby(["series_id", "category"]).size().to_string())


if __name__ == "__main__":
    main()
