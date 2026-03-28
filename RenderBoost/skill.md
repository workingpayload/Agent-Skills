---
name: renderboost
description: Optimize frontend rendering performance by improving Core Web Vitals (LCP, CLS, INP), reducing reflows/repaints, and applying lazy loading, IntersectionObserver, and requestAnimationFrame patterns. Use when a user needs to improve page speed, fix janky animations, or boost Lighthouse scores.
---

# RenderBoost

## Overview

RenderBoost diagnoses and fixes frontend rendering bottlenecks using measurement-first methodology, Core Web Vitals targets, and browser-native performance APIs.

## Workflow

### 1. Measure First — Always

Never optimize without a baseline. Collect real metrics before making any changes:

**Lab measurements (Lighthouse / WebPageTest):**
```bash
npx lighthouse https://example.com --output html --output-path report.html
# Or via Chrome DevTools: Lighthouse tab → Mobile preset → Analyze page load
```

**Field data (Chrome User Experience Report / web-vitals library):**
```js
import { onLCP, onCLS, onINP } from 'web-vitals';
onLCP(console.log);
onCLS(console.log);
onINP(console.log);
```

**Target thresholds (Google "Good" tier):**
| Metric | Good | Needs Improvement | Poor |
|---|---|---|---|
| LCP (Largest Contentful Paint) | ≤ 2.5s | ≤ 4.0s | > 4.0s |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | ≤ 0.25 | > 0.25 |
| INP (Interaction to Next Paint) | ≤ 200ms | ≤ 500ms | > 500ms |

### 2. Diagnose the Bottleneck

Open Chrome DevTools → Performance tab → Record a page load or interaction.

**LCP bottlenecks** (slow largest image/text paint):
- Network: large unoptimized hero image; missing `<link rel="preload">` for above-the-fold image.
- Render-blocking: CSS/JS in `<head>` without `defer`/`async`.
- TTFB: slow server response; missing CDN caching.

**CLS bottlenecks** (unexpected layout shifts):
- Images without explicit `width`/`height` attributes (or `aspect-ratio` CSS).
- Fonts causing FOUT/FOIT: missing `font-display: optional` or `swap`.
- Dynamically injected banners/ads above existing content.
- Late-loading iframes without reserved space.

**INP bottlenecks** (slow input response):
- Long tasks (> 50ms) on the main thread blocking input processing.
- Synchronous DOM reads that force reflow (`offsetHeight`, `getBoundingClientRect`) inside event handlers.
- Heavy React re-renders triggered by every keystroke.

### 3. Apply Targeted Fixes

**LCP — Image optimization:**
```html
<!-- Add width/height, use WebP/AVIF, preload the LCP image -->
<link rel="preload" as="image" href="hero.webp" fetchpriority="high">
<img src="hero.webp" width="1200" height="600" loading="eager" decoding="async">

<!-- Lazy load below-the-fold images -->
<img src="card.webp" loading="lazy" decoding="async" width="400" height="300">
```

**LCP — Critical resource loading:**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preload" href="/fonts/Inter.woff2" as="font" crossorigin>
<script src="app.js" defer></script>   <!-- non-critical JS -->
```

**CLS — Reserve layout space:**
```css
/* Always set aspect-ratio on image containers */
.hero-image { aspect-ratio: 16 / 9; width: 100%; }

/* Fonts */
@font-face { font-display: optional; }  /* for CLS=0 */
/* or font-display: swap; for visibility at cost of slight shift */
```

**INP — Break up long tasks:**
```js
// Replace synchronous loops with yielding chunks
async function processLargeList(items) {
  for (let i = 0; i < items.length; i++) {
    processItem(items[i]);
    if (i % 50 === 0) {
      await new Promise(resolve => setTimeout(resolve, 0)); // yield to browser
    }
  }
}

// Or use scheduler.postTask() (Chrome 94+)
scheduler.postTask(() => heavyWork(), { priority: 'background' });
```

**Reflow/repaint reduction:** Batch all DOM reads before writes. Reading `offsetHeight` then immediately writing `style.height` in a loop causes layout thrash — collect all reads first, then do all writes.

**Lazy loading with IntersectionObserver:** Use `rootMargin: '200px'` to preload images 200px before they enter the viewport. Call `observer.unobserve(img)` after loading to free resources.

**Animation on the compositor thread (no reflow):**
```css
/* Use transform and opacity — these run on GPU compositor, not main thread */
.slide-in { transform: translateX(-100%); transition: transform 0.3s ease; }
.slide-in.active { transform: translateX(0); }

/* Add will-change for elements that animate frequently */
.animated { will-change: transform; }
```

Use `requestAnimationFrame` for JS-driven animations:
```js
function animate(timestamp) {
  element.style.transform = `translateX(${calcPosition(timestamp)}px)`;
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
```

### 4. Deliver the Output

Provide:
1. Baseline metrics (Lighthouse scores, specific CWV values with units).
2. Root cause for each metric that misses the "Good" threshold.
3. Code changes with before/after snippets.
4. Verification steps: which Lighthouse audit or DevTools panel to use to confirm the fix.
5. Expected metric improvement (estimate based on the type of fix).

## Edge Cases

**1. CLS caused by third-party embeds.** Wrap ads/chat widgets in a container with explicit `min-height` and `width`, and load them after the `load` event or via `IntersectionObserver`.

**2. INP is high only on low-end mobile devices.** Use Chrome DevTools CPU throttling (6× slowdown) to reproduce. Fix: code-split large JS bundles and defer non-critical analytics scripts.

**3. LCP element changes based on personalization.** Use a skeleton screen with a reserved container. Fetch the personalized image with `fetchpriority="high"` as soon as JS knows which variant to show.

**4. Service Worker cache invalidation.** Call `self.skipWaiting()` inside `install` to activate the new SW immediately, then `clients.claim()` in `activate`. Version your cache names (`cache-v2`) and delete old caches in `activate`. Without this, stale assets persist until the user closes all tabs.

**5. `<video>` as a CLS source.** Video elements without explicit `width` and `height` attributes (or `aspect-ratio` CSS) cause layout shifts when metadata loads. Always set both attributes or use `.video-container { aspect-ratio: 16/9; }` with `width: 100%`.

**6. React hydration INP.** Server-rendered HTML that hydrates synchronously blocks the main thread. Use `startTransition` to defer non-critical state updates during hydration. With React 18 selective hydration (`<Suspense>`), interactive components hydrate first on user interaction, reducing INP on content-heavy pages.
