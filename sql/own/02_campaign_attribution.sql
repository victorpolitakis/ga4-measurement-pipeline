-- Purchases and revenue by the campaign source of the session they happened in.
-- The UTMs only arrive on the landing page view (collected_traffic_source), so the
-- session's source is taken from its first event that has one. Without consent there
-- is no stable user ID, so those purchases can't be joined to a session at all.
WITH events AS (
  SELECT
    user_pseudo_id,
    (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
    event_timestamp, event_name, ecommerce.purchase_revenue AS revenue,
    collected_traffic_source.manual_source AS source,
    collected_traffic_source.manual_medium AS medium,
    collected_traffic_source.manual_campaign_name AS campaign,
    privacy_info.analytics_storage AS analytics_storage
  FROM `{dataset}.events_*`
),
sessions AS (
  SELECT user_pseudo_id, session_id,
    ARRAY_AGG(STRUCT(source, medium, campaign) ORDER BY event_timestamp LIMIT 1)[SAFE_OFFSET(0)] AS utm
  FROM events
  WHERE source IS NOT NULL
  GROUP BY user_pseudo_id, session_id
)
SELECT
  IFNULL(s.utm.source, IF(e.analytics_storage = 'No', '(consent denied)', '(unattributed)')) AS source,
  s.utm.medium AS medium,
  s.utm.campaign AS campaign,
  COUNT(*) AS purchases,
  ROUND(SUM(e.revenue), 2) AS revenue
FROM events e
LEFT JOIN sessions s USING (user_pseudo_id, session_id)
WHERE e.event_name = 'purchase'
GROUP BY 1, 2, 3
ORDER BY purchases DESC;
