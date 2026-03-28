---
name: seomancer
description: Optimizes technical SEO including structured data (JSON-LD/Schema.org), meta tags, Open Graph, canonical/hreflang tags, Core Web Vitals, and crawlability. Use when asked to audit SEO, fix meta tags, add structured data, improve Lighthouse scores, or configure robots.txt/sitemap.xml.
---

# SEOMancer

## Overview

Diagnoses and fixes technical SEO issues across on-page metadata, structured data markup, crawl configuration, internationalization signals, and Core Web Vitals. Every recommendation is grounded in Google Search Central documentation, Schema.org specifications, and measurable Lighthouse/CrUX metrics.

## Workflow

### 1. Audit Scope Assessment

Determine which SEO layers need attention:
- **Crawlability**: robots.txt, sitemap.xml, canonical tags, noindex/nofollow directives
- **On-page metadata**: `<title>`, `<meta name="description">`, hreflang, canonical
- **Social/Open Graph**: og:title, og:description, og:image, og:url, Twitter Card tags
- **Structured data**: JSON-LD Schema.org markup (Organization, Article, Product, BreadcrumbList, FAQPage, etc.)
- **Core Web Vitals**: LCP, INP, CLS — measure first with Lighthouse or PageSpeed Insights API
- **International SEO**: hreflang attributes, language/region targeting

Run Lighthouse CLI for baseline: `npx lighthouse https://example.com --output=json --output-path=report.json`

### 2. On-Page Metadata Standards

Every page must have:

```html
<!-- Primary SEO -->
<title>Primary Keyword – Brand Name</title> <!-- 50-60 chars -->
<meta name="description" content="..."> <!-- 120-158 chars, include CTA -->
<link rel="canonical" href="https://example.com/page/">

<!-- Open Graph (Facebook, LinkedIn) -->
<meta property="og:type" content="website">
<meta property="og:title" content="...">
<meta property="og:description" content="...">
<meta property="og:image" content="https://example.com/og-image.jpg"> <!-- 1200x630px -->
<meta property="og:url" content="https://example.com/page/">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="...">
<meta name="twitter:description" content="...">
<meta name="twitter:image" content="https://example.com/twitter-image.jpg">
```

Rules:
- Title: unique per page, primary keyword near the front, brand suffix separated by `–` or `|`.
- Description: not a ranking factor but affects CTR; include the target keyword naturally.
- Never use the same canonical URL on two different pages with different content.

### 3. Structured Data (JSON-LD)

Prefer JSON-LD over Microdata. Place in `<head>` or end of `<body>`. Validate with Google's Rich Results Test.

**Article example** (for blog posts):
```json
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Page Title Here",
  "datePublished": "2024-01-15T08:00:00+00:00",
  "dateModified": "2024-03-20T10:00:00+00:00",
  "author": { "@type": "Person", "name": "Author Name" },
  "publisher": {
    "@type": "Organization",
    "name": "Brand Name",
    "logo": { "@type": "ImageObject", "url": "https://example.com/logo.png" }
  },
  "image": "https://example.com/featured.jpg"
}
</script>
```

**BreadcrumbList** (for navigational context):
```json
{
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com/" },
    { "@type": "ListItem", "position": 2, "name": "Blog", "item": "https://example.com/blog/" },
    { "@type": "ListItem", "position": 3, "name": "Article Title" }
  ]
}
```

Schema types by page intent: `Product` + `Review` + `AggregateRating` for e-commerce, `FAQPage` for FAQ sections, `HowTo` for tutorials, `LocalBusiness` for location pages, `Event` for events.

### 4. Crawlability Configuration

**robots.txt** rules:
```
User-agent: *
Disallow: /admin/
Disallow: /api/
Disallow: /?*  # Block faceted URLs if not canonical
Allow: /

Sitemap: https://example.com/sitemap.xml
```

**sitemap.xml** requirements:
- Max 50,000 URLs or 50MB per sitemap file; use sitemap index for larger sites.
- Include `<lastmod>` in ISO 8601 format; omit `<changefreq>` and `<priority>` (Google ignores them).
- Exclude noindex pages, paginated pages (except page 1), and URLs with canonical pointing elsewhere.
- Submit to Google Search Console and Bing Webmaster Tools.

### 5. Hreflang for Internationalization

For multilingual/multiregional sites:
```html
<link rel="alternate" hreflang="en-us" href="https://example.com/en-us/page/">
<link rel="alternate" hreflang="en-gb" href="https://example.com/en-gb/page/">
<link rel="alternate" hreflang="fr" href="https://example.com/fr/page/">
<link rel="alternate" hreflang="x-default" href="https://example.com/page/">
```

Rules: hreflang must be reciprocal (each URL in the set must reference all others). Use ISO 639-1 language + ISO 3166-1 region codes. `x-default` points to the language-selector or fallback page.

### 6. Core Web Vitals Targets

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP (Largest Contentful Paint) | ≤ 2.5s | 2.5–4.0s | > 4.0s |
| INP (Interaction to Next Paint) | ≤ 200ms | 200–500ms | > 500ms |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | 0.1–0.25 | > 0.25 |

LCP fixes: preload hero image (`<link rel="preload" as="image">`), use `fetchpriority="high"` on LCP image, eliminate render-blocking resources.

CLS fixes: set explicit `width`/`height` on images and iframes, avoid inserting DOM above existing content, use `font-display: optional` or `swap` with `size-adjust`.

INP fixes: break up long tasks with `scheduler.yield()`, defer non-critical JS, move heavy computation to Web Workers.

### 7. Output Artifacts

Produce:
1. **Audit findings table**: URL, issue type, severity (Critical/High/Medium/Low), current value, recommended value.
2. **Ready-to-paste code snippets** for each fix (meta tags, JSON-LD, robots.txt entries).
3. **Lighthouse score delta estimate** where measurable.
4. **Search Console monitoring checklist**: coverage errors to resolve, enhancements to validate.

## Edge Cases

**JavaScript-rendered content**: Googlebot renders JS but with a delay. Critical metadata and structured data must be in the initial HTML response (SSR or SSG), not injected after hydration. Use `next/head`, Nuxt's `useHead()`, or equivalent server-side head management.

**Canonicalization conflicts**: A page may have conflicting signals (canonical tag says URL A, but sitemap lists URL B, and internal links point to URL C). Audit all three signals and make them consistent. The canonical tag is the strongest signal but Google may override it.

**Paginated series**: Use `?page=N` with self-referencing canonicals on each paginated page. Only include page 1 in sitemaps.

**Site migration SEO:** Before launch, build a 1:1 redirect map from old URLs to new URLs. Implement 301 redirects (not 302). After launch, monitor Google Search Console → Coverage and URL Inspection weekly for 90 days. Watch for index drops, crawl errors, and lost impressions. Preserve backlink equity: never redirect an old high-authority URL to the homepage — redirect to the closest equivalent page.

**Programmatic meta generation at scale:** For sites with thousands of pages (e-commerce, real estate, directories), generate `<title>` and `<meta name="description">` from templates using page-specific data fields: `"{Category} {Brand} – Buy Online | {SiteName}"`. Ensure no two pages share identical meta. Set up automated checks (`sitemap.xml` fetch + scrape) to detect duplicate or missing tags across the full page set.
