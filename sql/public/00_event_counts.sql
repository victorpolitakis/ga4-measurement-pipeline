-- Event counts in Google's public GA4 sample (Google Merchandise Store, obfuscated).
-- events_* is one table per day; _TABLE_SUFFIX (the date part) limits which days are read,
-- and that limits the bytes BigQuery bills for.
SELECT event_name, COUNT(*) AS events
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY event_name
ORDER BY events DESC;
