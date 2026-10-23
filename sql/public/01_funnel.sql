-- Ecommerce funnel by session: view_item, add_to_cart, begin_checkout, purchase.
-- A GA4 session is identified by user_pseudo_id plus the ga_session_id event parameter;
-- ga_session_id alone is only unique per user.
-- "open" counts every session that had the step; "closed" also requires every earlier step,
-- which is what a funnel exploration in GA4 shows by default.
WITH sessions AS (
  SELECT
    CONCAT(user_pseudo_id, '.',
      CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)) AS session_id,
    LOGICAL_OR(event_name = 'view_item') AS viewed,
    LOGICAL_OR(event_name = 'add_to_cart') AS added,
    LOGICAL_OR(event_name = 'begin_checkout') AS checked_out,
    LOGICAL_OR(event_name = 'purchase') AS purchased
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
  GROUP BY session_id
)
SELECT
  COUNT(*) AS sessions,
  COUNTIF(viewed) AS view_item_open,
  COUNTIF(added) AS add_to_cart_open,
  COUNTIF(checked_out) AS begin_checkout_open,
  COUNTIF(purchased) AS purchase_open,
  COUNTIF(viewed AND added) AS add_to_cart_closed,
  COUNTIF(viewed AND added AND checked_out) AS begin_checkout_closed,
  COUNTIF(viewed AND added AND checked_out AND purchased) AS purchase_closed,
  ROUND(SAFE_DIVIDE(COUNTIF(checked_out), COUNTIF(viewed)), 4) AS view_to_checkout_open,
  ROUND(SAFE_DIVIDE(COUNTIF(purchased), COUNTIF(checked_out)), 4) AS checkout_to_purchase_open
FROM sessions;
