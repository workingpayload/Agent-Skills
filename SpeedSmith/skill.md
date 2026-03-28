---
name: speedsmith
description: Implements performance optimizations for web applications including caching strategies, asset delivery, code splitting, and image optimization. Use when asked to improve page load times, reduce latency, optimize assets, or fix Core Web Vitals scores.
---

# SpeedSmith

## Overview

Diagnoses and fixes web performance bottlenecks using a measurement-first approach. Tools: Lighthouse CI, WebPageTest, Chrome DevTools Performance panel, and bundle analyzers. Covers CDN configuration, HTTP caching, Redis/in-memory caching, code splitting, tree-shaking, and next-gen image formats. Never optimize without first establishing a baseline metric.

## Workflow

### 1. Measure Before Optimizing

Establish baselines before touching code:

```bash
# Lighthouse CLI baseline
npx lighthouse https://example.com --output=json --output-path=baseline.json \
  --preset=desktop --throttling-method=simulate

# Bundle analysis (webpack)
npx webpack-bundle-analyzer stats.json

# Bundle analysis (Vite)
npx vite-bundle-visualizer

# WebPageTest API
curl "https://www.webpagetest.org/runtest.php?url=https://example.com&f=json&k=YOUR_KEY"
```

Record: LCP, INP, CLS, TTI, TBT, total transfer size, number of requests, TTFB.

Set target thresholds before starting:
- LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1 (Core Web Vitals "Good" thresholds)
- Total page weight ≤ 500KB compressed for above-the-fold content

### 2. HTTP Caching Strategy

Apply appropriate cache headers per resource type:

| Resource Type | Cache-Control | CDN Behavior |
|---------------|--------------|--------------|
| Hashed static assets (JS, CSS) | `public, max-age=31536000, immutable` | Cache indefinitely |
| Images (hashed filenames) | `public, max-age=31536000, immutable` | Cache indefinitely |
| HTML pages | `public, max-age=0, must-revalidate` + ETag | CDN respects, revalidate on each request |
| API responses (public, stable) | `public, max-age=300, s-maxage=600` | CDN caches 10 min |
| API responses (user-specific) | `private, max-age=60` | Do not cache at CDN |
| Service Worker cached | Stale-while-revalidate via SW | Bypass CDN for SW-handled routes |

Use **content-addressable filenames** (webpack `[contenthash]`, Vite default behavior) to enable `immutable` caching safely.

### 3. CDN Configuration

- **Cloudflare**: Enable "Cache Everything" page rule for static assets. Use Cache Rules with `Cache Status: Cache` for `/assets/*`. Enable Argo Smart Routing for dynamic content.
- **AWS CloudFront**: Set `DefaultCacheBehavior` TTL to 86400 for static paths. Use Lambda@Edge or CloudFront Functions for header manipulation. Enable HTTP/3 (QUIC) and Brotli compression.
- **Fastly/Akamai**: Configure origin shield (shielding) to reduce origin load.

CDN must-haves: HTTP/2 or HTTP/3 push, Brotli compression, TLS 1.3, HSTS preloading.

### 4. Redis / Application-Level Caching

Cache-aside pattern: check Redis → on miss, compute and `setex` with TTL. Strategies: TTL-based (simple), event-driven invalidation (publish on write), write-through (write to both simultaneously). Always include user/tenant ID in cache keys for multi-tenant systems. Never share cache keys across tenants.

### 5. JavaScript Optimization

**Code splitting** (webpack/Vite):
```javascript
// Route-based splitting (React)
const Dashboard = React.lazy(() => import('./pages/Dashboard'));

// Manual chunk splitting (Vite)
// vite.config.ts
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['react', 'react-dom'],
        charts: ['recharts', 'd3'],
      }
    }
  }
}
```

**Tree-shaking**: Ensure all imports are named (not `import * as`). Use `"sideEffects": false` in `package.json` for pure utility libraries. Verify with bundle analyzer that dead code is eliminated.

**Script loading**: Use `defer` for non-critical scripts. Use `type="module"` which is deferred by default. Use dynamic `import()` for features triggered by user interaction.

**Reduce main thread blocking**: Tasks over 50ms block the main thread. Use `scheduler.yield()` to break up long tasks:
```javascript
async function processLargeList(items) {
  for (let i = 0; i < items.length; i++) {
    process(items[i]);
    if (i % 100 === 0) await scheduler.yield(); // yield to browser
  }
}
```

### 6. Image Optimization

Use AVIF (best compression) → WebP (fallback) → JPEG. SVG for all icons. Use `<picture>` with `<source type="image/avif">` and `<source type="image/webp">`. Set explicit `width`/`height` on all `<img>` to prevent CLS. Add `fetchpriority="high"` on the LCP image and `loading="lazy"` on below-fold images. Use a CDN image transform service (Cloudinary, Imgix) instead of manual exports.

### 7. Font Optimization

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>
```

```css
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-var.woff2') format('woff2');
  font-display: optional;  /* CLS=0; use 'swap' if text must render immediately */
  size-adjust: 100%;
}
```

Subset fonts to used character sets with `pyftsubset` or `fonttools`.

### 8. Output Artifacts

Produce:
1. **Before/After metrics table**: LCP, INP, CLS, TTI, transfer size — baseline vs. projected.
2. **Prioritized optimization list**: ordered by estimated impact, effort (low/medium/high), and risk.
3. **Code snippets**: ready-to-implement cache headers, config changes, code splits.
4. **Lighthouse CI config** for regression prevention:
```yaml
ci:
  assert:
    assertions:
      largest-contentful-paint: [error, { maxNumericValue: 2500 }]
      cumulative-layout-shift: [error, { maxNumericValue: 0.1 }]
```

## Edge Cases

**Synchronous localStorage jank:** `localStorage.getItem/setItem` are synchronous and block the main thread, causing INP spikes on slower devices. Move large or frequent reads to IndexedDB (async) or cache the value in a module-level variable on first read and write back lazily.

**Bundle size CI gating:** Prevent bundle regressions with `size-limit` or `bundlesize`. Add to CI:
```json
// package.json
"size-limit": [{ "path": "dist/index.js", "limit": "50 KB" }]
```
Run `npx size-limit` in CI and fail the build if the limit is exceeded. This catches accidental large-dependency imports before they reach production.

**Origin TTFB diagnosis:** High TTFB (> 600ms) is a server-side problem. Check in order: (1) slow DB query — enable query logging and look for queries > 100ms; (2) cold start — serverless functions have 200–2000ms cold start; keep functions warm or use edge runtimes; (3) connection pool exhaustion — check pool wait time metrics; increase pool size or reduce query duration.

**Third-party scripts:** Load analytics and chat widgets with `async`/`defer` or after the `load` event. Use `<link rel="dns-prefetch">` for third-party domains.

**SSR hydration overhead:** SSR with full hydration can produce high TTI. Consider partial hydration (Astro islands), streaming SSR, or React Server Components to reduce client JS.

**CDN cache poisoning:** Never cache responses with user-specific data without `private` cache-control. Use `Vary: Accept-Encoding` (not `Vary: User-Agent`) for Brotli/gzip variants.
