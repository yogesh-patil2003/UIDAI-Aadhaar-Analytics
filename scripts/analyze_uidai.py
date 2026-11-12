"""Reproducible UIDAI Aadhaar Enrolment, Demographic & Biometric EDA Pipeline."""
import argparse
import glob
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_category(data_dir: str, subfolder: str) -> pd.DataFrame:
    pattern = os.path.join(data_dir, subfolder, "*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No CSV files found under {pattern}")
    return pd.concat((pd.read_csv(f) for f in files), ignore_index=True)


def run_analysis(data_dir: str, out_dir: str = "assets") -> dict:
    os.makedirs(out_dir, exist_ok=True)
    bio = load_category(data_dir, "api_data_aadhar_biometric")
    demo = load_category(data_dir, "api_data_aadhar_demographic")
    enr = load_category(data_dir, "api_data_aadhar_enrolment")

    age_cols = ["age_0_5", "age_5_17", "age_18_greater"]
    for col in age_cols:
        enr[col] = pd.to_numeric(enr[col], errors="coerce").fillna(0)
    enr["total_enr"] = enr[age_cols].sum(axis=1)
    enr["dt"] = pd.to_datetime(enr["date"], dayfirst=True, errors="coerce")

    enr_by_state = enr.groupby("state")["total_enr"].sum().sort_values(ascending=False)

    # Chart 1: Top 10 states & age cohort totals
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.5))
    top_states = enr_by_state.head(10).iloc[::-1]
    axes[0].barh(top_states.index, top_states.values / 1e5, color="#2563EB")
    axes[0].set_title("Top 10 States by Total Aadhaar Enrolments")
    axes[0].set_xlabel("Enrolments (Lakhs / 100K)")
    axes[0].grid(axis="x", alpha=0.3)

    age_totals = enr[age_cols].sum()
    bars = axes[1].bar(
        ["Age 0-5", "Age 5-17", "Age 18+"],
        age_totals.values / 1e6,
        color=["#0EA5E9", "#10B981", "#F59E0B"],
    )
    axes[1].set_title(f"Enrolment Age Cohort Distribution (n={len(enr):,} records)")
    axes[1].set_ylabel("Total Enrolments (Millions)")
    axes[1].grid(axis="y", alpha=0.3)
    for b in bars:
        h = b.get_height()
        axes[1].text(
            b.get_x() + b.get_width() / 2, h + 0.05, f"{h:.2f}M",
            ha="center", va="bottom", fontsize=10, fontweight="bold"
        )
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, "uidai_state_and_age_summary.png"), dpi=150)
    plt.close(fig)

    # Chart 2: Monthly enrolment trend
    monthly = enr.dropna(subset=["dt"]).groupby(enr["dt"].dt.to_period("M"))[age_cols].sum()
    monthly.index = monthly.index.astype(str)
    fig, ax = plt.subplots(figsize=(11, 4.8))
    monthly.plot(kind="line", marker="o", ax=ax, linewidth=2.2)
    ax.set_title("Monthly UIDAI Aadhaar Enrolment Trend by Age Group")
    ax.set_xlabel("Month")
    ax.set_ylabel("Enrolment Count")
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, "uidai_monthly_enrolment_trend.png"), dpi=150)
    plt.close(fig)

    return {
        "biometric_rows": len(bio),
        "demographic_rows": len(demo),
        "enrolment_rows": len(enr),
        "total_rows": len(bio) + len(demo) + len(enr),
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze UIDAI Aadhaar CSV shards.")
    parser.add_argument("--data-dir", default="data", help="Root folder containing UIDAI CSV subdirectories.")
    parser.add_argument("--out-dir", default="assets", help="Output directory for generated charts.")
    args = parser.parse_args()
    summary = run_analysis(args.data_dir, args.out_dir)
    print("Analysis complete:", summary)


if __name__ == "__main__":
    main()
