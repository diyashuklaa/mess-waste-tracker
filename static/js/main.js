// Shared helpers used across pages
// (page-specific logic lives in each template's <script> block)

// Animate numbers on KPI cards
function animateCount(el, target, decimals = 0) {
  const duration = 600;
  const start    = performance.now();
  const from     = parseFloat(el.textContent) || 0;
  function tick(now) {
    const t = Math.min((now - start) / duration, 1);
    const v = from + (target - from) * t;
    el.textContent = decimals ? v.toFixed(decimals) : Math.round(v).toLocaleString();
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
