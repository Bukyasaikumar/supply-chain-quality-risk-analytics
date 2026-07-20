import pandas as pd
import numpy as np
from datetime import datetime

# extends the sql project (supply_chain_analysis.sql) - doing the same
# supplier/product risk analysis but in python so it's re-runnable instead
# of a one-off query. same dataset as the mysql version.

DATA_FILE = "supply_chain_raw.csv"


def check_data_quality(df):
    # basic sanity checks before trusting the numbers - completeness, dupes,
    # anything that shouldn't be negative
    nulls = df.isnull().sum().sum()
    dupes = df.duplicated().sum()
    dupe_skus = df.duplicated(subset=["SKU"]).sum()
    neg_price = (df["Price"] < 0).sum()
    neg_cost = (df["Costs"] < 0).sum()
    bad_defect_rate = ((df["Defect rates"] < 0) | (df["Defect rates"] > 100)).sum()

    print("Data quality checks:")
    print(f"  nulls: {nulls}")
    print(f"  duplicate rows: {dupes}")
    print(f"  duplicate SKUs: {dupe_skus}")
    print(f"  negative price rows: {neg_price}")
    print(f"  negative cost rows: {neg_cost}")
    print(f"  defect rate out of 0-100 range: {bad_defect_rate}")

    total_issues = nulls + dupes + dupe_skus + neg_price + neg_cost + bad_defect_rate
    print("  -> clean, no issues" if total_issues == 0 else f"  -> {total_issues} issues found, check above")
    return total_issues


def find_outliers(df, col, group_by):
    # IQR method, but done per group rather than across the whole dataset -
    # a 3% defect rate is fine for one supplier and way off for another so a
    # single global cutoff doesn't really work here
    flagged = []
    for name, group in df.groupby(group_by):
        q1 = group[col].quantile(0.25)
        q3 = group[col].quantile(0.75)
        iqr = q3 - q1
        low = q1 - 1.5 * iqr
        high = q3 + 1.5 * iqr
        outliers = group[(group[col] < low) | (group[col] > high)]
        if len(outliers) > 0:
            flagged.append(outliers)

    if flagged:
        return pd.concat(flagged)
    return pd.DataFrame(columns=df.columns)  # nothing found, empty df same shape


def get_risky_combos(df, defect_cutoff=3.0, revenue_cutoff=1000.0):
    # same logic as the "corrective action priority" query in the SQL file,
    # just written so the thresholds can be changed without touching a query
    grouped = df.groupby(["Product type", "Supplier name"]).agg(
        avg_defect_rate=("Defect rates", "mean"),
        total_revenue=("Revenue generated", "sum"),
        n=("SKU", "count"),
    ).reset_index()

    grouped["revenue_at_risk"] = (grouped["total_revenue"] * grouped["avg_defect_rate"] / 100).round(2)

    risky = grouped[(grouped["avg_defect_rate"] >= defect_cutoff) | (grouped["revenue_at_risk"] >= revenue_cutoff)].copy()

    # both conditions = critical, only one = just flag for review
    risky["flag"] = "REVIEW"
    risky.loc[(risky["avg_defect_rate"] >= defect_cutoff) & (risky["revenue_at_risk"] >= revenue_cutoff), "flag"] = "CRITICAL"

    return risky.sort_values("revenue_at_risk", ascending=False)


def run_report(df):
    print(f"Exception report run - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{len(df)} rows from {DATA_FILE}")
    print("-" * 60)

    check_data_quality(df)

    print("\nOutliers in defect rate (by product type):")
    outliers = find_outliers(df, "Defect rates", "Product type")
    if len(outliers) == 0:
        print("  none flagged")
    else:
        print(outliers[["Product type", "Supplier name", "SKU", "Defect rates"]].to_string(index=False))

    print(f"\nHigh risk supplier/product combos (defect >= 3% or revenue at risk >= £1000):")
    risky = get_risky_combos(df)
    print(risky.to_string(index=False))

    risky.to_csv("exception_report.csv", index=False)
    print("\nsaved to exception_report.csv")

    return risky


if __name__ == "__main__":
    df = pd.read_csv(DATA_FILE)
    run_report(df)
