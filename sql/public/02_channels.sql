-- Users, sessions and purchases by first-user source / medium.
-- traffic_source in the export is the source that first acquired the user, not the
-- source of each session; the 2020 sample predates the session-level fields
-- (collected_traffic_source, session_traffic_source_last_click).
SELECT
  traffic_source.source AS first_user_source,
  traffic_source.medium AS first_user_medium,
  COUNT(DISTINCT user_pseudo_id) AS users,
  COUNTIF(event_name = 'session_start') AS sessions,
  COUNTIF(event_name = 'purchase') AS purchases,
  ROUND(SUM(IF(event_name = 'purchase', ecommerce.purchase_revenue_in_usd, 0)), 2) AS revenue_usd
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY first_user_source, first_user_medium
ORDER BY purchases DESC
LIMIT 10;
