---
name: flexilayout
description: Designs and debugs responsive CSS layouts using Flexbox, CSS Grid, container queries, and design tokens. Use when a user needs help with alignment bugs, breakpoint strategies, fluid typography, WCAG contrast, or building responsive UI components.
---

# FlexiLayout

## Overview

Diagnoses and fixes CSS layout problems, builds responsive component systems using Flexbox/Grid, implements container queries, enforces WCAG 2.2 contrast ratios, and structures design tokens for consistent responsive behavior.

## Workflow

### 1. Diagnose the Layout Problem

Before writing CSS, identify the layout model in use:
- Is this a **one-dimensional** flow? → Flexbox
- Is this a **two-dimensional** grid? → CSS Grid
- Does the component need to respond to its **container**, not the viewport? → Container Queries

Ask for (or inspect) the existing markup structure. Never apply layout CSS without understanding the HTML hierarchy.

### 2. Apply the Correct Layout Primitive

**Flexbox — use for:**
```css
.container {
  display: flex;
  flex-wrap: wrap;           /* prevent overflow on small screens */
  gap: var(--space-4);       /* prefer gap over margin for spacing */
  align-items: stretch;      /* default; override explicitly */
}
/* Never use margin: auto on flex children for centering — use justify-content on parent */
```

**CSS Grid — use for:**
```css
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr));
  gap: var(--space-6);
}
/* Use named grid lines or grid-template-areas for complex layouts */
.layout {
  grid-template-areas:
    "header header"
    "sidebar main"
    "footer footer";
}
```

**Container Queries — use when the component is reused at varying widths:**
```css
.card-wrapper {
  container-type: inline-size;
  container-name: card;
}
@container card (min-width: 480px) {
  .card { flex-direction: row; }
}
```

### 3. Define Breakpoint Strategy

Use a **mobile-first** `min-width` approach. Anchor breakpoints to content, not device names:

```css
/* Design tokens — define once, use everywhere */
:root {
  --bp-sm: 480px;
  --bp-md: 768px;
  --bp-lg: 1024px;
  --bp-xl: 1280px;
}

/* Usage */
@media (min-width: 768px) { ... }
```

Prefer container queries over media queries for component-level responsiveness. Reserve media queries for page-level layout shifts (e.g., collapsing a sidebar).

### 4. Fluid Typography & Spacing Tokens

```css
:root {
  /* Fluid type scale using clamp() */
  --text-base: clamp(1rem, 0.9rem + 0.5vw, 1.25rem);
  --text-lg:   clamp(1.125rem, 1rem + 0.75vw, 1.5rem);

  /* Spacing scale */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
}
```

### 5. WCAG 2.2 Contrast Compliance

- **AA minimum:** 4.5:1 for normal text, 3:1 for large text (18px+ or 14px+ bold) and UI components.
- **AAA target:** 7:1 for body text.

Verification steps:
1. Use the WebAIM Contrast Checker or browser DevTools accessibility panel.
2. Check both light and dark mode token pairs.
3. Verify focus indicators meet 3:1 against adjacent colors (WCAG 2.2 SC 2.4.11).

```css
/* Example accessible focus ring */
:focus-visible {
  outline: 3px solid var(--color-focus);
  outline-offset: 2px;
}
```

### 6. Validate & Output

Deliver:
1. Corrected/new CSS with inline comments explaining each decision.
2. A responsive behavior summary (what changes at each breakpoint).
3. Any WCAG issues found and the fix applied.
4. Browser support notes for any properties used (container queries require Chrome 105+, Firefox 110+, Safari 16+).

## Edge Cases

**RTL support:** Set `dir="rtl"` on the root element or component container. Replace physical margin/padding properties with CSS logical properties: `margin-inline-start` instead of `margin-left`, `padding-inline-end` instead of `padding-right`. Use `[dir="rtl"]` selectors for directional overrides that logical properties cannot cover (e.g., icon flip transforms).

**Subgrid progressive enhancement:** Use `@supports` to layer subgrid in where available:
```css
@supports (grid-template-rows: subgrid) {
  .card-grid > .card {
    display: grid;
    grid-row: span 3;
    grid-template-rows: subgrid;  /* align header/body/footer across cards */
  }
}
```

**Subgrid alignment across nested components:** When a card grid inside a section needs column alignment with sibling grids, use `display: subgrid` on the nested container. Fall back to matching `grid-template-columns` values if subgrid support is insufficient.

**Overflow and `min-width: 0` on flex/grid children:** Flex and grid children default to `min-width: auto`, which prevents shrinking below content size and causes overflow. Fix: add `min-width: 0` (or `overflow: hidden`) to the child that needs to shrink.

**Dark mode token conflicts:** When system `prefers-color-scheme: dark` overrides explicit theme tokens, wrap dark tokens in both `@media (prefers-color-scheme: dark)` and a `[data-theme="dark"]` selector so JavaScript-controlled theme toggling and OS-level preference both work correctly.
