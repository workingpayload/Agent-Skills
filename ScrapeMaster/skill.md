---
name: scrapemaster
description: Build resilient web scrapers using a static-vs-JS-rendered decision tree, Playwright/Cheerio/BeautifulSoup, robots.txt compliance, retry/backoff, pagination handling, and structured output schemas. Use when a user needs to extract data from websites, build a scraper, or parse HTML/DOM content.
---

# ScrapeMaster

## Overview

ScrapeMaster builds production-grade scrapers with the right tool for the rendering environment, ethical compliance checks, resilience patterns, and clean output schemas.

## Workflow

### 1. Static vs. JS-Rendered Decision Tree

Before writing any code, determine how the target page renders its content:

```
Does the data appear in `curl https://example.com` raw HTML?
  YES → Static page → use Cheerio (JS) or BeautifulSoup (Python)
  NO  → JS-rendered → use Playwright (preferred) or Puppeteer

Is the data returned by a JSON API call?
  YES → Call the API directly (inspect Network tab in DevTools → XHR/Fetch)
       → Reverse-engineer the API endpoint instead of scraping the DOM
  NO  → Scrape the rendered DOM
```

Checking for an API endpoint first saves 90% of the work and produces more stable output.

### 2. Compliance Check (Do This Before Writing Code)

1. **Check `robots.txt`**: `https://example.com/robots.txt`. Honor `Disallow` rules for your scraper's User-Agent. If the target explicitly disallows scraping, inform the user and stop.
2. **Check Terms of Service**: look for sections on automated access, data scraping, or commercial use.
3. **Rate limiting**: never hit a site faster than ~1 request/second without explicit permission. Use `Crawl-delay` from robots.txt if specified.
4. **Set a descriptive User-Agent**: `MyCompanyScraper/1.0 (+https://mycompany.com/bot)`.

### 3. Choose the Right Tool

**Static HTML (no JS required):**

*Python — BeautifulSoup + httpx:*
```python
import httpx
from bs4 import BeautifulSoup

async def fetch_page(url: str) -> BeautifulSoup:
    async with httpx.AsyncClient(headers={"User-Agent": "MyScraper/1.0"}) as client:
        r = await client.get(url, follow_redirects=True)
        r.raise_for_status()
        return BeautifulSoup(r.text, "lxml")

soup = await fetch_page("https://example.com/products")
items = soup.select("div.product-card")  # CSS selectors preferred over find_all
```

*Node.js — Cheerio + got:*
```js
import * as cheerio from 'cheerio';
import got from 'got';

const { body } = await got('https://example.com/products');
const $ = cheerio.load(body);
const items = $('div.product-card').map((_, el) => ({
  title: $(el).find('h2').text().trim(),
  price: $(el).find('.price').text().trim(),
})).get();
```

**JS-rendered pages (React/Vue/Angular SPA):**

*Python — Playwright:*
```python
from playwright.async_api import async_playwright

async def scrape_spa(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        # Wait for the specific element that contains your data
        await page.wait_for_selector("div.product-card", timeout=10_000)
        items = await page.eval_on_selector_all(
            "div.product-card",
            "els => els.map(el => ({ title: el.querySelector('h2').textContent.trim() }))"
        )
        await browser.close()
        return items
```

### 4. Retry & Backoff Pattern

Wrap all network calls in retry logic with exponential backoff:

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30),
       retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TransportError)))
async def fetch_with_retry(client, url):
    r = await client.get(url)
    if r.status_code == 429:
        await asyncio.sleep(int(r.headers.get("Retry-After", 60)))
        r.raise_for_status()
    r.raise_for_status()
    return r
```

In Node.js: `got(url, { retry: { limit: 3, methods: ['GET'] } })`.

### 5. Pagination & Infinite Scroll

**Offset pagination:** Increment `?page=N` until `parse_items()` returns empty.

**Cursor/next-link:** Follow `a[rel="next"]` href until absent.

**Infinite scroll (Playwright):** Simulate scrolling and wait for new network requests:
```python
async def scrape_infinite_scroll(page):
    results = []
    prev_count = 0
    while True:
        items = await page.eval_on_selector_all(".item", "els => els.map(e => e.textContent)")
        results = items
        if len(items) == prev_count:
            break
        prev_count = len(items)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        # Wait for new content to load
        await page.wait_for_timeout(1500)
    return results
```
For API-backed infinite scroll, intercept XHR/fetch via `page.on("response", ...)` and collect JSON payloads directly — no DOM parsing needed.

### 6. Define the Output Schema

Always define a Pydantic model before parsing. Store prices as integer cents (not float). Export as JSON Lines (`.jsonl`) for large datasets, CSV for tabular consumers, SQLite for queryable output.

### 7. Deliver the Output

Provide:
1. Decision tree result (static/JS-rendered/API) with evidence.
2. Complete scraper script with retry logic and polite delay.
3. Output schema (Pydantic model or TypeScript type).
4. Sample output (5 records in the schema format).
5. robots.txt compliance status.
6. Notes on fragility: which CSS selectors are likely to break if the site redesigns.

## Edge Cases

**1. Anti-bot detection (Cloudflare, DataDome, PerimeterX).** Do not bypass security controls without explicit permission — this may violate the CFAA. Inform the user; suggest an official API or data partnership. If the user has explicit permission, `playwright-extra` + `puppeteer-extra-plugin-stealth` reduces fingerprinting signals.

**2. CAPTCHA walls.** CAPTCHAs are a hard blocker. Surface this clearly to the user. If they have explicit legal permission and a legitimate use case, third-party solving services such as 2captcha or Anti-Captcha can integrate via API. Never attempt to bypass CAPTCHAs on sites where scraping is prohibited.

**3. Brittle selectors.** Prefer stability order: `data-testid` > `aria-label`/`role` > meaningful class names > positional selectors. Add record-count validation to catch silent DOM changes.

**4. Login-gated content.** Use Playwright `page.fill` + `page.click` for auth, then `context.storage_state(path="state.json")` to reuse sessions across runs. Never hardcode credentials — use environment variables.
