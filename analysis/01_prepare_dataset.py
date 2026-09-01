from common import (
    add_qc_columns,
    discover_series,
    ensure_output_dirs,
    load_config,
    load_metadata,
    resolve_path,
)


def main():
    config = load_config()
    ensure_output_dirs(config)
    metadata = load_metadata()

    df = discover_series(config, metadata)
    df = add_qc_columns(df, config)

    out = resolve_path(
        str(resolve_path(config["output_root"]) / "dataset" / "analysis_dataset.csv")
    )
    df.to_csv(out, index=False, encoding="utf-8-sig")

    print(f"Prepared dataset: {out}")
    print(f"Rows: {len(df):,}")
    print("\nRows by category:")
    print(df["category"].value_counts(dropna=False).to_string())
    print("\nEligible paired observations:")
    print(int(df["analysis_eligible"].sum()))


if __name__ == "__main__":
    main()
