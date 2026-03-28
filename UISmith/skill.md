---
name: uismith
description: Builds accessible, composable UI components using Atomic Design principles, WCAG AA compliance, design tokens, and CSS Modules or Tailwind CSS. Use when asked to create UI components, audit accessibility, implement ARIA roles, set up a design system, or decompose a UI into reusable components.
---

# UISmith

## Overview

Translates designs into accessible, composable, and maintainable UI components. Every component targets WCAG 2.2 Level AA compliance, uses Atomic Design decomposition, implements correct ARIA roles and keyboard navigation, and is styled with design tokens (CSS custom properties or Tailwind config). No component ships without accessibility attributes and keyboard interaction support.

## Workflow

### 1. Component Decomposition (Atomic Design)

Before coding, classify the component in the Atomic Design hierarchy:

| Level | Examples | Key Trait |
|-------|---------|-----------|
| **Atom** | Button, Input, Label, Icon, Badge | No children components; single HTML element or small group |
| **Molecule** | SearchBar (Input + Button), FormField (Label + Input + Error) | Combines 2–4 atoms; one focused function |
| **Organism** | NavigationBar, DataTable, ProductCard, Modal | Combines molecules/atoms; owns its own state |
| **Template** | PageLayout, DashboardShell | Layout skeleton; no data, only slots/children |
| **Page** | DashboardPage, ProfilePage | Template + real data; maps to a route |

Decision rule: if you find yourself writing the same markup in 3+ places, extract to the appropriate atom/molecule level.

### 2. Accessibility — WCAG 2.2 AA Checklist

Apply to every component before marking it complete:

**Semantic HTML first**:
- Use `<button>` for actions (never `<div onClick>`), `<a href>` for navigation, `<input>` for data entry.
- Use heading hierarchy (`h1` → `h2` → `h3`) that reflects document structure, not visual size.
- Use landmark elements: `<main>`, `<nav>`, `<aside>`, `<header>`, `<footer>`.

**ARIA roles and labels**:
```html
<!-- Incorrect: div with no role -->
<div onClick={handleClose}>X</div>

<!-- Correct: semantic button with accessible label -->
<button type="button" aria-label="Close dialog" onClick={handleClose}>
  <XIcon aria-hidden="true" />
</button>

<!-- Modal dialog -->
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-description"
>
  <h2 id="dialog-title">Confirm Delete</h2>
  <p id="dialog-description">This action cannot be undone.</p>
</div>

<!-- Navigation with label to distinguish multiple navs -->
<nav aria-label="Main navigation">...</nav>
<nav aria-label="Breadcrumb">...</nav>

<!-- Live region for dynamic content -->
<div aria-live="polite" aria-atomic="true" role="status">
  {statusMessage}
</div>
```

**Color contrast**: Text must meet 4.5:1 contrast ratio (normal text) or 3:1 (large text ≥ 18pt/14pt bold) against background. Use tooling: `axe-core`, `@radix-ui/colors` (APCA-compliant scale), or Figma's Contrast plugin. Never convey information by color alone — add icon, pattern, or text.

**Focus management**:
- Visible focus indicator: `outline: 2px solid currentColor; outline-offset: 2px` (never `outline: none` without an equally visible custom focus style).
- Focus trap in modals/drawers: implement with `focus-trap-react` or Radix UI's Dialog primitive.
- Return focus to trigger element when modal closes.

### 3. Keyboard Navigation Patterns

Per ARIA Authoring Practices Guide (APG): Button = Enter/Space; Radio group = Arrow keys; Dropdown = Enter opens, Arrow navigates, Escape closes; Dialog = Tab/Shift+Tab within, Escape closes; Tabs = Arrow keys between tabs.

**Prefer Radix UI or Headless UI primitives** over hand-rolling keyboard nav — they implement APG patterns correctly. For custom dropdowns, handle `ArrowDown`/`ArrowUp` to move `activeIndex`, `Escape` to close and return focus to the trigger, and `ArrowUp`/`ArrowDown` to prevent page scroll with `e.preventDefault()`.

### 4. Design Tokens

Define all visual decisions as CSS custom properties — never hardcode values:

```css
:root {
  --color-primary-500: #2563eb; --color-primary-600: #1d4ed8;
  --color-error-500: #dc2626;
  --color-surface-default: #ffffff; --color-text-primary: #0f172a;
  --space-1: 0.25rem; --space-2: 0.5rem; --space-4: 1rem; --space-8: 2rem;
  --font-size-base: 1rem; --line-height-normal: 1.5;
  --radius-md: 0.375rem;
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}
```

Tailwind: extend `colors`, `spacing`, and `borderRadius` in `tailwind.config.ts` to match your token scale. Never use magic numbers.

### 5. CSS Modules vs. Tailwind

**CSS Modules**: choose for strict encapsulation, complex animations, or pseudo-element logic. Reference tokens via `var(--space-2)` in module files.

**Tailwind**: choose for rapid iteration, shadcn/ui, or Radix primitives. Use `cn()` to merge variant classes and keep focus-visible styles always present:
```tsx
<button className={cn('px-4 py-2 rounded-md focus-visible:outline focus-visible:outline-2',
  variant === 'primary' && 'bg-primary-500 text-white')} {...props} />
```

### 6. Component Output Requirements

Every component delivered must include:

1. **Component file** with TypeScript props interface (no `any`)
2. **Accessible markup**: correct roles, labels, live regions where needed
3. **Keyboard interaction**: all interactions operable by keyboard
4. **Story or usage example** (Storybook story or plain code example)
5. **Accessibility note**: list of WCAG criteria addressed and any known limitations

## Edge Cases

**RTL layout support:** Use logical CSS properties (`margin-inline-start` instead of `margin-left`, `padding-inline-end` instead of `padding-right`) so layouts flip automatically when `dir="rtl"` is set on `<html>`. Set `dir="rtl"` at the root for RTL languages. Mirror icons that imply direction (arrows, chevrons) using `transform: scaleX(-1)` under `[dir="rtl"]`. Test with Arabic or Hebrew `lang` attributes.

**Windows High Contrast mode:** Use `@media (forced-colors: active)` to adapt components that rely on custom colors, box-shadows, or background images for contrast — these are overridden by the OS. Replace `box-shadow` focus rings with `outline`, use `ButtonText`, `ButtonFace`, and `CanvasText` CSS system color keywords for forced-colors-aware styling. Test in Windows Accessibility → High Contrast Black/White themes.

**Touch gesture accessibility (WCAG 2.5.1):** All touch gestures (swipe, pinch, multi-finger) must have a single-pointer alternative (a button, link, or drag handle). Pointer cancellation (WCAG 2.5.2): actions that trigger on `pointerdown` must be reversible on `pointerup`. Provide keyboard equivalents for all custom drag-and-drop interactions.

**Dynamic content and screen readers**: Content that updates without a page reload (toasts, form validation errors, loading states) must be announced to screen readers. Use `role="alert"` (assertive, interrupts) for errors, `role="status"` / `aria-live="polite"` for non-urgent updates. Inject the element into the DOM before updating its text content — some screen readers miss updates to pre-existing live regions.

**Icon-only buttons without visible labels**: A button containing only an icon must have an `aria-label` describing the action, not the icon. `aria-label="Close"` not `aria-label="X icon"`. The icon itself must have `aria-hidden="true"` to prevent duplicate announcement. If using SVG, add `focusable="false"` to prevent IE11 SVG focus behavior.

**Responsive component behavior**: A component that changes its DOM structure at different breakpoints (e.g., a horizontal nav that collapses to a hamburger menu) must maintain accessibility at all breakpoints. The collapsed menu must be announced as expanded/collapsed (`aria-expanded`), and the full nav landmark must remain in the DOM (use CSS to hide, not `display:none` without `aria-hidden`) or the aria-hidden state must be updated when hiding.
