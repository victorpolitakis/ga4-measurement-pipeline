"""Make Playwright-driven Chromium behave like a normal browser on page unload.

GA4 batches events for a few seconds and sends the batch when the page fires
`pagehide`. A normal browser fires it before leaving the page; the Chromium that
Playwright drives does not deliver it in time, so any event pushed shortly before
a navigation (cta_click, add_to_cart) was lost. Checked on 2026-10-24: in a normal
browser the same click sent cta_click on navigation; under Playwright it never left.

The window listener runs after the page's own click handlers (document listeners
come first in the bubble phase), so the data layer push has happened by then.
"""

FLUSH_ON_CLICK = """
window.addEventListener('click', () => {
  window.dispatchEvent(new PageTransitionEvent('pagehide', { persisted: false }));
});
"""

FLUSH_NOW = "window.dispatchEvent(new PageTransitionEvent('pagehide', { persisted: false }))"


def install(context):
    context.add_init_script(FLUSH_ON_CLICK)
