-- Data quality: purchases that share a transaction_id, and purchases with no usable ID.
-- GA4 deduplicates purchases with the same transaction_id in its reports, but the
-- export keeps every event, so a duplicate here means revenue is counted twice
-- in any SQL that doesn't deduplicate.
WITH purchases AS (
  SELECT ecommerce.transaction_id AS transaction_id, ecommerce.purchase_revenue_in_usd AS revenue
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
    AND event_name = 'purchase'
)
SELECT
  COUNT(*) AS purchase_events,
  COUNTIF(transaction_id IS NULL OR transaction_id = '(not set)') AS missing_transaction_id,
  COUNT(DISTINCT IF(transaction_id = '(not set)', NULL, transaction_id)) AS distinct_transactions,
  (SELECT COUNT(*) FROM (
     SELECT transaction_id FROM purchases
     WHERE transaction_id IS NOT NULL AND transaction_id != '(not set)'
     GROUP BY transaction_id HAVING COUNT(*) > 1)) AS transaction_ids_seen_more_than_once
FROM purchases;
