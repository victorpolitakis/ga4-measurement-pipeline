-- Window function 2 (LAG): hours between a returning user's consecutive sessions.
WITH session_starts AS (
  SELECT user_pseudo_id, TIMESTAMP_MICROS(event_timestamp) AS ts
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
    AND event_name = 'session_start'
),
gaps AS (
  SELECT
    TIMESTAMP_DIFF(ts, LAG(ts) OVER (PARTITION BY user_pseudo_id ORDER BY ts), MINUTE) / 60 AS hours_since_previous
  FROM session_starts
)
SELECT
  COUNT(*) AS returning_sessions,
  ROUND(APPROX_QUANTILES(hours_since_previous, 100)[OFFSET(50)], 1) AS median_hours,
  ROUND(APPROX_QUANTILES(hours_since_previous, 100)[OFFSET(90)], 1) AS p90_hours,
  ROUND(COUNTIF(hours_since_previous <= 24) / COUNT(*), 3) AS share_within_a_day
FROM gaps
WHERE hours_since_previous IS NOT NULL;
