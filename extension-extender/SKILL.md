---
name: extension-extender
description: Creates, fixes, and debugs Manifest V3 browser extensions for Chrome and Firefox with secure permissions scoping, CSP compliance, cross-browser compatibility, storage management, and version migration. Use when a user asks to build, fix, or debug a Chrome/Firefox extension, create a popup, or handle extension manifest issues.
---

# Extension Extender

## Overview

Builds modern Manifest V3 browser extensions with secure permissions, cross-browser compatibility (Chrome + Firefox), CSP compliance, storage management, and structured debugging. Produces `chrome://extensions`-ready code.

## Workflow

### 1. Project Initialization

Use `assets/manifest.json`, `assets/popup.html`, `assets/popup.css`, `assets/popup.js` as boilerplate if available. If assets are missing, generate inline:

```json
{
  "manifest_version": 3,
  "name": "My Extension",
  "version": "1.0",
  "action": { "default_popup": "popup.html" },
  "permissions": [],
  "host_permissions": []
}
```

### 2. Permissions Scoping (Principle of Least Privilege)

1. List every browser API the extension uses (`storage`, `tabs`, `scripting`).
2. Use `optional_permissions` where possible — granted at runtime via `chrome.permissions.request()`, reduces install friction.
3. URL patterns go in `host_permissions`, not `permissions`. Be specific: `"https://example.com/*"` over `"<all_urls>"`.
4. Never request `"tabs"` just for current tab URL — use `"activeTab"` instead.
5. After editing permissions, reload in `chrome://extensions` and verify no errors.

### 3. Firefox WebExtensions Compatibility

- Replace `chrome.*` with `browser.*` using `webextension-polyfill` for cross-browser support.
- Firefox MV3 background support differs: use `"background": { "scripts": ["background.js"] }` for Firefox (check MDN for current MV3 status).
- `chrome.scripting.executeScript` → `browser.tabs.executeScript` (MV2) or `browser.scripting` (MV3 when supported).
- `browser.action` is standard in both Chrome/Firefox MV3. Do not use `browser.browserAction`.
- Test Firefox: `about:debugging#/runtime/this-firefox` → "Load Temporary Add-on".

### 4. Content Security Policy (CSP)

- No inline `<script>` or `onclick="..."` — move all JS to external `.js` files.
- No `eval()`, `new Function()`, or dynamic code execution.
- Remote resources (fonts, images): explicitly allow in manifest:
  ```json
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'; img-src 'self' https://cdn.example.com"
  }
  ```
- Never relax `script-src` beyond `'self'`. Vendor third-party code locally.

### 5. Storage Management

**`chrome.storage.sync` vs `local`:**

| Feature | `sync` | `local` |
|---------|--------|---------|
| Synced across devices | Yes (Google account) | No |
| Quota | 100KB total, 8KB/item, 512 items | 5MB default (2GB with `unlimitedStorage`) |
| Use for | Preferences, small config | Cached data, history, large datasets |

Always check `chrome.runtime.lastError` after storage calls. Batch writes to avoid hitting quota.

**Version upgrade data migration:**
```javascript
chrome.runtime.onInstalled.addListener(({ reason, previousVersion }) => {
  if (reason === 'update') {
    chrome.storage.local.get(['settings'], ({ settings }) => {
      if (settings && !settings.schemaVersion) {
        chrome.storage.local.set({
          settings: { ...settings, schemaVersion: 2, newKey: settings.oldKey }
        });
      }
    });
  }
});
```
Always track a `schemaVersion` field. Test migrations by loading the old version, saving data, then upgrading.

### 6. Styling (Beautiful UI Defaults)

- CSS custom properties for theming (`--color-primary`, `--bg-surface`).
- Dark mode: `@media (prefers-color-scheme: dark)`.
- Popup: 300–400px width, under 600px height. `rem` for fonts, `px` for borders/shadows.

### 7. Debugging Decision Workflow

1. **Manifest errors** → confirm `"manifest_version": 3`. Service worker: `"background": { "service_worker": "background.js" }` (not `"scripts"` array).
2. **Popup errors** → right-click popup → Inspect. Background errors → `chrome://extensions` → service worker → Inspect.
3. **Content script not injecting** → verify `content_scripts` in manifest or programmatic `chrome.scripting.executeScript`. Content scripts run in isolated world — can't access page JS vars.
4. **DOM not ready** → wrap logic in `document.addEventListener('DOMContentLoaded', ...)`.
5. **Message passing fails** → verify both sides use matching `type` fields in `chrome.runtime.sendMessage`/`onMessage`. Return `true` in listener if response is async.
6. **Permission denied at runtime** → add missing permission to manifest, reload, re-test.
7. **Service worker terminates mid-task** → MV3 service workers are ephemeral (30s idle timeout). Use `chrome.alarms` for periodic tasks; persist state in `chrome.storage` rather than in-memory variables.

### 8. Content Script vs Host Page

Content scripts share the DOM but not JS context (isolated world). Host page CSP does **not** block content scripts. To interact with page JS:
- Inject via `chrome.scripting.executeScript({ world: "MAIN" })` (Chrome 95+).
- Code in `MAIN` world **is** subject to host page CSP — no `eval()` or inline scripts.

## Edge Cases

1. **Service worker killed during long operation**: MV3 service workers terminate after ~30s of inactivity. For long-running work, use `chrome.offscreen.createDocument()` to get a persistent page, or break work into chunks persisted in storage.
2. **Storage quota exceeded silently**: `chrome.storage.sync.set()` fails silently if quota is exceeded. Always check `chrome.runtime.lastError` and implement a fallback to `local` storage.
3. **Cross-browser manifest differences**: Chrome requires `"service_worker"` for background; Firefox uses `"scripts"` array. Maintain two manifests or use a build step (webpack/vite) to generate platform-specific versions.

## Testing

- **Manual**: load unpacked via `chrome://extensions` (Chrome) or `about:debugging` (Firefox).
- **Automated**: use `web-ext lint` (Mozilla) for manifest/CSP validation. For E2E: Playwright supports Chrome extensions via `--load-extension` launch arg.
- **Web Store submission checklist**: single-purpose description, minimal permissions justification, privacy policy if using `host_permissions` or user data.

## Output Format

- Provide complete updated files.
- State: (a) root cause (if debugging), (b) what changed, (c) how to verify.
