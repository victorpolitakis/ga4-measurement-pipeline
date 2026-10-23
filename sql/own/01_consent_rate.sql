-- Consent rate: share of page views sent with analytics and ad storage granted.
-- privacy_info is 'Yes' or 'No' per event, and NULL when no consent signal was sent
-- (here: days before Consent Mode went live on 2026-10-23). NULL is left out of the rate,
-- otherwise a day without consent mode would look like a day where nobody consented.
SELECT
  event_date,
  COUNT(*) AS page_views,
  COUNTIF(privacy_info.analytics_storage IS NULL) AS no_consent_signal,
  COUNTIF(privacy_info.analytics_storage = 'Yes') AS analytics_granted,
  COUNTIF(privacy_info.ads_storage = 'Yes') AS ads_granted,
  ROUND(SAFE_DIVIDE(COUNTIF(privacy_info.analytics_storage = 'Yes'),
                    COUNTIF(privacy_info.analytics_storage IS NOT NULL)), 3) AS analytics_consent_rate,
  ROUND(SAFE_DIVIDE(COUNTIF(privacy_info.ads_storage = 'Yes'),
                    COUNTIF(privacy_info.ads_storage IS NOT NULL)), 3) AS ads_consent_rate
FROM `{dataset}.events_*`
WHERE event_name = 'page_view'
GROUP BY event_date
ORDER BY event_date;
