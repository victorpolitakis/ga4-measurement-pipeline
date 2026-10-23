-- Event counts split by analytics consent, to compare with the traffic script's ground truth.
SELECT
  event_name,
  COUNTIF(privacy_info.analytics_storage = 'Yes') AS consented,
  COUNTIF(privacy_info.analytics_storage = 'No') AS cookieless,
  COUNT(*) AS total
FROM `{dataset}.events_*`
GROUP BY event_name
ORDER BY total DESC;
