-- FC Supply Chain Quality Analytics
-- Database: SUPPLY_CHAIN_DATA_BASE (MySQL)
-- Source table: supply_chain_raw (100 rows, cleaned column names, no nulls/duplicates)

USE SUPPLY_CHAIN_DATA_BASE;

-- Query 1: Defect rate by product type
SELECT
  product_type,
  ROUND(AVG(defect_rate), 2) AS avg_defect_rate,
  COUNT(*) AS total_products,
  SUM(CASE WHEN inspection_result = 'Fail' THEN 1 ELSE 0 END) AS failed,
  SUM(CASE WHEN inspection_result = 'Pass' THEN 1 ELSE 0 END) AS passed,
  SUM(CASE WHEN inspection_result = 'Pending' THEN 1 ELSE 0 END) AS pending
FROM supply_chain_raw
GROUP BY product_type
ORDER BY avg_defect_rate DESC;

-- Query 2: Supplier quality ranking
SELECT
  supplier_name,
  ROUND(AVG(defect_rate), 2) AS avg_defect_rate,
  COUNT(*) AS total_products,
  SUM(CASE WHEN inspection_result = 'Fail' THEN 1 ELSE 0 END) AS failed,
  ROUND(SUM(CASE WHEN inspection_result = 'Fail' THEN 1 ELSE 0 END) / COUNT(*) * 100, 1) AS failure_rate_pct
FROM supply_chain_raw
GROUP BY supplier_name
ORDER BY failure_rate_pct DESC;

-- Query 3: Stock risk classification
-- Thresholds (stock < 30, defect > 3 = HIGH; stock < 60, defect > 2 = MEDIUM) are set from
-- this dataset's own distribution: stock ranges 0-100 (avg 48), defect rate ranges 0.02%-4.94% (avg 2.28%)
SELECT
  product_type,
  supplier_name,
  ROUND(AVG(stock_level), 0) AS avg_stock,
  ROUND(AVG(order_lead_time), 0) AS avg_lead_time,
  ROUND(AVG(defect_rate), 2) AS avg_defect_rate,
  CASE
    WHEN AVG(stock_level) < 30 AND AVG(defect_rate) > 3 THEN 'HIGH RISK'
    WHEN AVG(stock_level) < 60 AND AVG(defect_rate) > 2 THEN 'MEDIUM RISK'
    ELSE 'LOW RISK'
  END AS stockout_risk_level
FROM supply_chain_raw
GROUP BY product_type, supplier_name
ORDER BY avg_defect_rate DESC;

-- Query 4: Transportation mode impact on defects
SELECT
  transport_mode,
  ROUND(AVG(defect_rate), 2) AS avg_defect_rate,
  COUNT(*) AS total_shipments,
  ROUND(AVG(shipping_cost), 2) AS avg_shipping_cost,
  SUM(CASE WHEN inspection_result = 'Fail' THEN 1 ELSE 0 END) AS failed_inspections
FROM supply_chain_raw
GROUP BY transport_mode
ORDER BY avg_defect_rate DESC;

-- Query 5: Revenue vs. defect rate by product type
SELECT
  product_type,
  ROUND(SUM(revenue), 0) AS total_revenue,
  ROUND(AVG(defect_rate), 2) AS avg_defect_rate,
  ROUND(AVG(order_qty), 0) AS avg_order_qty,
  ROUND(SUM(revenue) / COUNT(*), 0) AS revenue_per_product,
  SUM(CASE WHEN inspection_result = 'Fail' THEN 1 ELSE 0 END) AS total_failures
FROM supply_chain_raw
GROUP BY product_type
ORDER BY total_revenue DESC;

-- Query 6: Revenue at risk by supplier
SELECT
  supplier_name,
  ROUND(SUM(revenue), 0) AS total_revenue,
  ROUND(AVG(defect_rate), 2) AS avg_defect_rate_pct,
  ROUND(SUM(revenue * (defect_rate / 100)), 0) AS revenue_at_risk,
  ROUND(SUM(revenue * (defect_rate / 100)) / SUM(revenue) * 100, 1) AS pct_revenue_at_risk
FROM supply_chain_raw
GROUP BY supplier_name
ORDER BY revenue_at_risk DESC;

-- Query 7: Revenue at risk by transport mode
SELECT
  transport_mode,
  COUNT(*) AS total_shipments,
  ROUND(AVG(defect_rate), 2) AS avg_defect_rate_pct,
  ROUND(SUM(revenue), 0) AS total_revenue,
  ROUND(SUM(revenue * (defect_rate / 100)), 0) AS revenue_at_risk
FROM supply_chain_raw
GROUP BY transport_mode
ORDER BY revenue_at_risk DESC;

-- Query 8: Corrective action priority table
-- This is what you hand to an ops manager
SELECT
  product_type,
  supplier_name,
  ROUND(AVG(defect_rate), 2) AS defect_rate_pct,
  ROUND(SUM(revenue), 0) AS total_revenue,
  ROUND(SUM(revenue * (defect_rate / 100)), 0) AS revenue_at_risk,
  CASE
    WHEN AVG(defect_rate) >= 3 THEN 'CRITICAL'
    WHEN AVG(defect_rate) >= 2 THEN 'HIGH'
    WHEN AVG(defect_rate) >= 1 THEN 'MEDIUM'
    ELSE 'LOW'
  END AS priority,
  CASE
    WHEN AVG(defect_rate) >= 3 THEN 'Immediate CAP + supplier audit + incoming inspection gate'
    WHEN AVG(defect_rate) >= 2 THEN 'Increase cycle count frequency on this SKU range'
    WHEN AVG(defect_rate) >= 1 THEN 'Flag for next ops review'
    ELSE 'Standard process -- monitor only'
  END AS recommended_action
FROM supply_chain_raw
GROUP BY product_type, supplier_name
ORDER BY revenue_at_risk DESC;
