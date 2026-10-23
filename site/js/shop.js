// Shared logic for the Northwind Outdoor demo shop.
// The site never talks to GA4 directly: it only pushes events to the dataLayer.
// Google Tag Manager reads those pushes and decides which tags to fire.

window.dataLayer = window.dataLayer || [];

const CURRENCY = "EUR";

const CATALOG = {
  "NW-TENT-2P": { item_name: "Ridgeline 2-Person Tent", item_category: "Tents", price: 189.0 },
  "NW-PACK-45": { item_name: "Summit 45L Backpack", item_category: "Backpacks", price: 119.0 },
  "NW-BOOT-GTX": { item_name: "Trailhead Waterproof Boots", item_category: "Footwear", price: 149.0 },
};

// ---------- dataLayer helpers ----------

// Ecommerce pushes clear the previous ecommerce object first. GTM merges every
// push into one data model, so without this, items from an earlier event
// (for example view_item) could leak into the next one (add_to_cart).
function pushEcommerce(eventName, ecommerce) {
  window.dataLayer.push({ ecommerce: null });
  window.dataLayer.push({ event: eventName, ecommerce: ecommerce });
}

function toItem(itemId, quantity) {
  const p = CATALOG[itemId];
  return { item_id: itemId, item_name: p.item_name, item_category: p.item_category, price: p.price, quantity: quantity };
}

function cartValue(items) {
  // Rounded to cents so floating-point sums like 0.1 + 0.2 never reach GA4.
  return Math.round(items.reduce((sum, i) => sum + i.price * i.quantity, 0) * 100) / 100;
}

// ---------- cart (kept in localStorage, demo only) ----------

function readCart() {
  try {
    return JSON.parse(localStorage.getItem("nw_cart")) || [];
  } catch (e) {
    return [];
  }
}

function writeCart(cart) {
  try {
    localStorage.setItem("nw_cart", JSON.stringify(cart));
  } catch (e) {}
  renderCartCount();
}

function addToCart(itemId, quantity) {
  const cart = readCart();
  const line = cart.find((l) => l.item_id === itemId);
  if (line) line.quantity += quantity;
  else cart.push({ item_id: itemId, quantity: quantity });
  writeCart(cart);

  const item = toItem(itemId, quantity);
  pushEcommerce("add_to_cart", { currency: CURRENCY, value: cartValue([item]), items: [item] });
}

function cartItems() {
  // Valid JSON can still hold a bad line (unknown product, missing or broken quantity).
  // Dropping it here keeps value from becoming NaN in begin_checkout and purchase.
  return readCart()
    .filter((l) => CATALOG[l.item_id] && Number.isInteger(l.quantity) && l.quantity > 0)
    .map((l) => toItem(l.item_id, l.quantity));
}

function renderCartCount() {
  const el = document.getElementById("cart-count");
  if (el) el.textContent = readCart().reduce((n, l) => n + l.quantity, 0);
}

// ---------- generic custom event for promo buttons ----------

// Any element with data-cta-id sends cta_click. Adding a new tracked button
// needs only an HTML attribute, no new JavaScript and no GTM change.
document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-cta-id]");
  if (!el) return;
  window.dataLayer.push({ event: "cta_click", cta_id: el.dataset.ctaId, cta_text: el.textContent.trim() });
});

document.addEventListener("DOMContentLoaded", renderCartCount);
