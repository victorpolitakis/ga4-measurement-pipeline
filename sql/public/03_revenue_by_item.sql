-- Units and revenue by item. items is a repeated field (an array per event),
-- so UNNEST turns each purchase into one row per item line.
SELECT
  item.item_name,
  item.item_category,
  SUM(item.quantity) AS units,
  ROUND(SUM(item.item_revenue_in_usd), 2) AS revenue_usd
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
  UNNEST(items) AS item
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
  AND event_name = 'purchase'
GROUP BY item.item_name, item.item_category
ORDER BY revenue_usd DESC
LIMIT 15;
