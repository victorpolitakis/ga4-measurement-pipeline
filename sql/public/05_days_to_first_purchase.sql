-- Window function 1 (ROW_NUMBER): each buyer's first purchase, and how many days
-- after their first visit it happened.
WITH events AS (
  SELECT user_pseudo_id, event_name, TIMESTAMP_MICROS(event_timestamp) AS ts
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),
first_seen AS (
  SELECT user_pseudo_id, MIN(ts) AS first_ts FROM events GROUP BY user_pseudo_id
),
ranked_purchases AS (
  SELECT user_pseudo_id, ts,
    ROW_NUMBER() OVER (PARTITION BY user_pseudo_id ORDER BY ts) AS purchase_number
  FROM events
  WHERE event_name = 'purchase'
)
SELECT
  DATE_DIFF(DATE(p.ts), DATE(f.first_ts), DAY) AS days_to_first_purchase,
  COUNT(*) AS buyers
FROM ranked_purchases p
JOIN first_seen f USING (user_pseudo_id)
WHERE p.purchase_number = 1
GROUP BY days_to_first_purchase
ORDER BY days_to_first_purchase
LIMIT 15;
