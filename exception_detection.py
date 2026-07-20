"""
Automated Exception & Anomaly Detection — Supply Chain Quality Dataset
========================================================================
Extends the existing MySQL/Power BI analysis (see supply_chain_analysis.sql)
with Python-based automated exception testing, in the style of an internal
controls testing pipeline:

    1. Data quality / reconciliation checks   (completeness, validity, duplicates)
    2. Statistical outlier detection            (flag abnormal defect-rate spikes
                                                   by supplier-product group)
    3. Threshold-based exception flagging        (high-risk supplier/product
                                                   combinations, mirrors the SQL
                                                   corrective-action logic but as
                                                   a reusable, parameterised function)
    4. Exception report generation               (audit-trail style output —
                                                   documents test run, thresholds
                                                   used, and results, for handoff
                                                   to a reviewer)

Design intent: every function is independently testable and documents its own
assumptions, so the logic can be re-run on a refreshed extract and reproduce
the same flags — same principle as a control test that needs to be repeatable
and defensible to an auditor.

Author: Bukya Sai Kumar
Dataset: Kaggle "Supply Chain Analysis" (same source as the MySQL project)
"""

import pandas as pd
import numpy as np
from datetime import datetime

RAW_DATA_PATH = "supply_chain_raw.csv"
EXCEPTION_REPORT_PATH = "exception_report.csv"

# ---------------------------------------------------------------------------
# 1. DATA QUALITY / RECONCILIATION CHECKS
# ---------------------------------------------------------------------------
def run_data_quality_checks(df: pd.DataFrame) -> dict:
    """
    Completeness, validity and duplicate checks — the equivalent of the
    'completeness, accuracy, duplicates, mapping' checks in a control test.
    Returns a dict summary rather than printing directly, so it can feed
    into the audit-trail report.
    """
    checks = {}

    # Completeness: any nulls in critical fields
    checks["null_counts"] = df.isnull().sum().to_dict()
    checks["total_nulls"] = int(df.isnull().sum().sum())

    # Duplicates: exact row duplicates, and duplicate SKU records
    checks["exact_duplicate_rows"] = int(df.duplicated().sum())
    checks["duplicate_skus"] = int(df.duplicated(subset=["SKU"]).sum())

    # Validity: fields that should never be negative or out of a sane range
    checks["negative_price_rows"] = int((df["Price"] < 0).sum())
    checks["negative_cost_rows"] = int((df["Costs"] < 0).sum())
    checks["defect_rate_out_of_range"] = int(
        ((df["Defect rates"] < 0) | (df["Defect rates"] > 100)).sum()
    )

    return checks


# ---------------------------------------------------------------------------
# 2. STATISTICAL OUTLIER DETECTION
# ---------------------------------------------------------------------------
def detect_outliers_iqr(
    df: pd.DataFrame,
    value_col: str,
    group_cols: list,
    iqr_multiplier: float = 1.5,
) -> pd.DataFrame:
    """
    Flags rows whose value_col is a statistical outlier *within its own
    group* (e.g. within its Product type + Supplier), using the IQR method.

    Group-relative outlier detection matters here: a 3% defect rate might be
    normal for one product/supplier pairing and abnormal for another, so a
    single dataset-wide threshold would miss real anomalies and flag false
    ones. This mirrors why control testing looks at "abnormal for this
    account/entity" rather than one flat rule for every transaction.
    """
    def flag_group(group):
        q1 = group[value_col].quantile(0.25)
        q3 = group[value_col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - iqr_multiplier * iqr
        upper = q3 + iqr_multiplier * iqr
        group["is_outlier"] = (group[value_col] < lower) | (group[value_col] > upper)
        group["outlier_lower_bound"] = round(lower, 4)
        group["outlier_upper_bound"] = round(upper, 4)
        return group

    result = df.groupby(group_cols, group_keys=False).apply(flag_group)
    return result[result["is_outlier"]].copy()


# ---------------------------------------------------------------------------
# 3. THRESHOLD-BASED EXCEPTION FLAGGING (high-risk combinations)
# ---------------------------------------------------------------------------
def flag_high_risk_combinations(
    df: pd.DataFrame,
    defect_threshold_pct: float = 3.0,
    revenue_at_risk_threshold: float = 1000.0,
) -> pd.DataFrame:
    """
    Reusable, parameterised version of the "corrective action priority"
    logic from the SQL project — instead of a one-off query, this can be
    re-run with different thresholds without touching the underlying SQL,
    which is closer to how a monitoring control would actually be
    operationalised (thresholds tend to move; the query shouldn't have to).
    """
    grouped = (
        df.groupby(["Product type", "Supplier name"])
        .agg(
            avg_defect_rate=("Defect rates", "mean"),
            total_revenue=("Revenue generated", "sum"),
            record_count=("SKU", "count"),
        )
        .reset_index()
    )

    grouped["revenue_at_risk"] = round(
        grouped["total_revenue"] * (grouped["avg_defect_rate"] / 100), 2
    )

    exceptions = grouped[
        (grouped["avg_defect_rate"] >= defect_threshold_pct)
        | (grouped["revenue_at_risk"] >= revenue_at_risk_threshold)
    ].copy()

    exceptions["risk_flag"] = np.where(
        (exceptions["avg_defect_rate"] >= defect_threshold_pct)
        & (exceptions["revenue_at_risk"] >= revenue_at_risk_threshold),
        "CRITICAL",
        "REVIEW",
    )

    return exceptions.sort_values("revenue_at_risk", ascending=False)


# ---------------------------------------------------------------------------
# 4. EXCEPTION REPORT GENERATION (audit-trail style)
# ---------------------------------------------------------------------------
def generate_exception_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Runs the full pipeline and prints an audit-trail style summary:
    what was tested, what thresholds were used, and what was found — the
    same information a reviewer would need to sign off on the test without
    re-running it themselves.
    """
    print("=" * 70)
    print("AUTOMATED EXCEPTION REPORT — Supply Chain Quality Dataset")
    print(f"Run timestamp: {datetime.now().isoformat(timespec='seconds')}")
    print(f"Source: {RAW_DATA_PATH} | Rows tested: {len(df)}")
    print("=" * 70)

    # --- Data quality section ---
    dq = run_data_quality_checks(df)
    print("\n[1] DATA QUALITY CHECKS")
    print(f"    Total nulls              : {dq['total_nulls']}")
    print(f"    Exact duplicate rows     : {dq['exact_duplicate_rows']}")
    print(f"    Duplicate SKU records    : {dq['duplicate_skus']}")
    print(f"    Negative price rows      : {dq['negative_price_rows']}")
    print(f"    Negative cost rows       : {dq['negative_cost_rows']}")
    print(f"    Defect rate out of range : {dq['defect_rate_out_of_range']}")
    print("    -> Result: PASS (no exceptions found)" if sum(
        [dq['total_nulls'], dq['exact_duplicate_rows'], dq['duplicate_skus'],
         dq['negative_price_rows'], dq['negative_cost_rows'], dq['defect_rate_out_of_range']]
    ) == 0 else "    -> Result: EXCEPTIONS FOUND — see counts above")

    # --- Statistical outliers section ---
    outliers = detect_outliers_iqr(
        df, value_col="Defect rates", group_cols=["Product type"]
    )
    print(f"\n[2] STATISTICAL OUTLIER DETECTION (defect rate, IQR method, by product type)")
    print(f"    Outlier rows flagged: {len(outliers)}")
    if len(outliers) > 0:
        cols = ["Product type", "Supplier name", "SKU", "Defect rates", "Inspection results"]
        print(outliers[cols].to_string(index=False))

    # --- High-risk combinations section ---
    risk = flag_high_risk_combinations(df)
    print(f"\n[3] THRESHOLD-BASED EXCEPTION FLAGGING (defect rate >= 3.0% OR revenue at risk >= £1,000)")
    print(f"    Combinations flagged: {len(risk)}")
    if len(risk) > 0:
        print(risk.to_string(index=False))

    # --- Combine and export ---
    risk.to_csv(EXCEPTION_REPORT_PATH, index=False)
    print(f"\n[4] Exception report exported to: {EXCEPTION_REPORT_PATH}")
    print("=" * 70)

    return risk


if __name__ == "__main__":
    data = pd.read_csv(RAW_DATA_PATH)
    generate_exception_report(data)
