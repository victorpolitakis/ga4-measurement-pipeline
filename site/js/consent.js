// Consent Mode v2 (advanced) for the Northwind Outdoor demo.
// Loaded synchronously in <head>, BEFORE the GTM snippet: the default consent
// state must be in the dataLayer before any Google tag can read it.
// A real site would use a certified CMP; this banner is a demo stand-in.

window.dataLayer = window.dataLayer || [];
function gtag() { window.dataLayer.push(arguments); }

const CONSENT_KEY = "nw_consent";

const CONSENT_CHOICES = {
  all: { analytics_storage: "granted", ad_storage: "granted", ad_user_data: "granted", ad_personalization: "granted" },
  analytics: { analytics_storage: "granted", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" },
  none: { analytics_storage: "denied", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" },
};

// 1. Default: everything denied until the visitor chooses.
gtag("consent", "default", Object.assign({}, CONSENT_CHOICES.none, {
  // How long Google tags wait for a consent update before sending with the default.
  // The saved choice is restored synchronously below, so this only matters on a
  // first visit where a CMP loads asynchronously; kept for that pattern.
  wait_for_update: 500,
}));
// With ad_storage denied, ad click IDs (gclid etc.) are redacted from requests.
gtag("set", "ads_data_redaction", true);

// 2. Returning visitor: apply the saved choice right away, still before GTM loads.
function readConsent() {
  try {
    return localStorage.getItem(CONSENT_KEY);
  } catch (e) {
    return null;
  }
}

const savedChoice = readConsent();
if (CONSENT_CHOICES[savedChoice]) gtag("consent", "update", CONSENT_CHOICES[savedChoice]);

// 3. Banner: shown when there is no saved choice, or when "Cookie settings" is clicked.
function saveConsent(choice) {
  gtag("consent", "update", CONSENT_CHOICES[choice]);
  try {
    localStorage.setItem(CONSENT_KEY, choice);
  } catch (e) {}
  const banner = document.getElementById("consent-banner");
  if (banner) banner.remove();
}

function showBanner() {
  if (document.getElementById("consent-banner")) return;
  const banner = document.createElement("div");
  banner.id = "consent-banner";
  banner.className = "consent";
  banner.innerHTML = `<p>We use cookies to measure how the shop is used and, if you allow it, to measure our ads.
      Rejecting keeps the shop fully usable.</p>
    <div class="consent-buttons">
      <button class="btn" data-consent="all">Accept all</button>
      <button class="btn secondary" data-consent="analytics">Analytics only</button>
      <button class="btn secondary" data-consent="none">Reject all</button>
    </div>`;
  banner.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-consent]");
    if (btn) saveConsent(btn.dataset.consent);
  });
  document.body.appendChild(banner);
}

document.addEventListener("DOMContentLoaded", () => {
  if (!CONSENT_CHOICES[readConsent()]) showBanner();
  const link = document.getElementById("cookie-settings");
  if (link) link.addEventListener("click", (e) => { e.preventDefault(); showBanner(); });
});
