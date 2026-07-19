# Supply Chain Quality & Revenue-at-Risk Analytics

## Overview

Supply chain quality and risk analytics — SQL + Power BI. Analyzes defect patterns, supplier performance, transportation impact, and revenue at risk across a product/supplier base, producing a prioritized corrective action plan that turns a quality metric into a financial exposure figure.

## Tools Used

- **MySQL** — data storage and query design
- **Power BI** — interactive dashboard with product type slicer
- **HTML/Chart.js** — web-based dashboard (no licence required, see `dashboard/index.html`)
- **Dataset**: [Supply Chain Analysis — Kaggle](https://www.kaggle.com/datasets/harshsingh2209/supply-chain-analysis)

## Key Findings

- Total revenue at risk identified across the supply chain: **£12,656**
- Haircare has the highest average defect rate (2.48%) across all product types
- Supplier 4 has the worst inspection failure rate at 66.7% — a sourcing reliability risk
- Supplier 2 carries the highest absolute revenue at risk (£2,866) due to volume exposure
- Road transport produces ~44% higher defect rates than Air, putting £1,082 more revenue at risk
- Rail transport is nearly as costly as Road — £3,928 vs £3,953 at risk
- Skincare generates the highest revenue (£241,628) but carries elevated defect risk
- Stockout risk and defect risk don't always align: the highest single defect rate in the dataset (cosmetics / Supplier 3, 3.87%) is classified LOW stockout risk because stock levels are high enough to absorb it — while lower-defect combinations with thinner stock rank higher on stockout risk
- Two CRITICAL product-supplier combinations identified requiring immediate corrective action:
  - Skincare / Supplier 5 — 3.47% defect rate, £1,513 at risk
  - Cosmetics / Supplier 3 — 3.87% defect rate (highest in dataset), £298 at risk

## Business Impact

The analysis goes beyond finding defect rates — it quantifies financial exposure and produces a prioritized corrective action plan an ops manager can act on directly.

| Finding | Revenue at Risk | Recommended Action |
|---|---|---|
| Supplier 2 (highest volume risk) | £2,866 | Defect reduction CAP at process level |
| Supplier 4 (66.7% inspection failure) | £2,049 | Sourcing review — procurement escalation |
| Road vs Air transport gap | £1,082 additional | Targeted damage assessment gate at inbound receive for road shipments |
| Skincare / Supplier 5 (CRITICAL) | £1,513 | Immediate CAP + supplier audit + incoming inspection gate |
| Cosmetics / Supplier 3 (CRITICAL) | £298 | Immediate CAP + supplier audit + incoming inspection gate |
| High priority SKU combinations | Various | Increase cycle count frequency on those SKU ranges |

**Key operational insight:** Priority-based cycle counting — directing quality-inspection resource to high-risk SKU ranges rather than counting all stock equally — means the same headcount delivers higher inventory accuracy across the whole FC.

## Files

| File | Description |
|---|---|
| `sql/supply_chain_analysis.sql` | 8 SQL queries covering defect analysis, supplier ranking, stock risk, transport impact, revenue vs defects, revenue at risk by supplier, revenue at risk by transport mode, and corrective action priority table |
| `dashboard/index.html` | Interactive web dashboard with a working product-type filter — open in any browser |
| `dashboard/power_bi.pbix` | Power BI dashboard with slicer filtering by product type |
| `data/supply_chain_raw.csv` | Cleaned dataset used for analysis (100 rows, 24 columns, no nulls/duplicates) |
| `query_results/` | Screenshot of each query's output from MySQL Workbench |

## SQL Queries Covered

1. Defect rate by product type
2. Supplier quality ranking with inspection failure rate %
3. Stock risk classification — HIGH / MEDIUM / LOW stockout risk
4. Transportation mode impact on defect rates
5. Revenue vs. defect rate by product type
6. Revenue at risk by supplier (revenue × defect rate)
7. Revenue at risk by transportation mode
8. Corrective action priority table — product-supplier combinations ranked by risk with recommended actions

## Query Results

| Query | Result |
|---|---|
| Defect rate by product type | [Q1](query_results/query1_defect_rate_by_product_type.png) |
| Supplier quality ranking | [Q2](query_results/query2_supplier_quality_ranking.png) |
| Stock risk classification | [Q3](query_results/query3_stock_risk_analysis.png) |
| Transport mode vs defect rate | [Q4](query_results/query4_transport_mode_vs_defect_rate.png) |
| Revenue vs defect rate | [Q5](query_results/query5_revenue_vs_defect_rate.png) |
| Revenue at risk by supplier | [Q6](query_results/query6_revenue_at_risk_by_supplier.png) |
| Revenue at risk by transport | [Q7](query_results/query7_revenue_at_risk_by_transport.png) |
| Corrective action priority | [Q8](query_results/query8_corrective_action_priority.png) |
