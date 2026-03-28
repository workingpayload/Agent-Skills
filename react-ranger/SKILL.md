---
name: react-ranger
description: Builds, debugs, and fixes React applications using TypeScript, hooks, and modern patterns (Server Components, Zustand, React Query). Includes structured debugging decision tree, testing with Vitest/RTL, accessibility checklist, and performance optimization. Use when a user asks to build, create, fix, debug, or improve React code.
---

# React Ranger

## Overview

Production-ready React development covering component architecture, structured debugging, state management decisions, testing with Vitest + React Testing Library, WCAG accessibility, and advanced patterns (RSC, bundle optimization, context performance).

## Workflow

### 1. Building Components

- Functional components with hooks only; no class components unless maintaining legacy.
- TypeScript: type all props with interfaces, never use `any`.
- One component per file; co-locate styles and tests alongside.
- `useMemo` / `useCallback` only when profiler confirms a problem — premature memoization adds complexity.
- **Pitfall**: object/array literals in JSX (`style={{ color: 'red' }}`) create new references every render; extract to a constant or `useMemo`.

### 2. Debugging Decision Tree

Follow in order — stop at the step that resolves the issue:

1. Open **React DevTools** → Profiler tab. Identify which component re-renders unexpectedly.
2. Re-render from parent → check if props are referentially stable; wrap callbacks in `useCallback`, objects in `useMemo`.
3. `useEffect` runs too often → audit dependency array. Every value used inside must be listed. Functions as deps must be wrapped in `useCallback`.
4. Stale values in `useEffect` → closure captured an old value. Add to dep array or use `useRef` for latest value without triggering re-renders.
5. List items behave incorrectly → verify stable, unique `key` props. Never use array index as key when items reorder.
6. Data fetching race conditions → use `AbortController` or `isCurrent` flag:
   ```ts
   useEffect(() => {
     let isCurrent = true;
     fetchData().then(d => { if (isCurrent) setData(d); });
     return () => { isCurrent = false; };
   }, [dep]);
   ```
7. Render-phase crash → wrap routes in `ErrorBoundary` to catch without crashing the app.
8. Hydration mismatch (SSR/RSC) → ensure server and client render identical markup. Common causes: `Date.now()`, `Math.random()`, browser-only APIs (`window`, `localStorage`) in the initial render.

### 3. State Management Decision

| Need | Solution |
|------|----------|
| Local UI state | `useState` |
| Shared subtree | `useContext` + `useReducer` |
| Server/async state | React Query (`@tanstack/react-query`) or SWR |
| Global client state | Zustand (lightweight) or Redux Toolkit (large team) |

### 4. Testing (Vitest + React Testing Library)

- Location: `src/components/Foo/Foo.test.tsx` alongside component.
- Run: `npx vitest run` (CI) or `npx vitest` (watch).
- Per component: renders without crashing, interactions trigger correct state/callback, async ops use `waitFor`/`findBy*` (never `setTimeout`), error states show error UI.
- Use `screen.getByRole` / `getByLabelText` over `getByTestId` — role-based queries validate accessibility.
- Mock: `vi.mock('module-name')`.

### 5. Accessibility (a11y) Checklist

- [ ] Interactive elements keyboard focusable and operable (Enter/Space).
- [ ] Images: descriptive `alt`; decorative images `alt=""`.
- [ ] Form inputs associated with `<label>` via `htmlFor`/`id` or `aria-label`.
- [ ] Color not sole information channel (add icon, text, or pattern).
- [ ] Focus trapped in modals; returned to trigger on close.
- [ ] Dynamic content uses `role="alert"` or `aria-live="polite"`.
- [ ] Run `npx axe-core` or axe DevTools extension; resolve critical/serious violations.

### 6. React Server Components (RSC)

- In Next.js App Router, components are Server Components by default.
- Add `"use client"` at top of files using hooks, browser APIs, or event handlers.
- RSC constraints: no `useState`, `useEffect`, `useContext`. Data fetching via async/await in component body.
- Props across server/client boundary must be serializable — no functions, class instances, or Dates.

### 7. Performance

**Bundle analysis:** `npx vite-bundle-visualizer` (Vite) or `npx webpack-bundle-analyzer`. Check tree-shaking: `import { debounce } from 'lodash'` imports everything — use `lodash-es` or `lodash/debounce`.

**Context re-render fix:** Split context by update frequency (separate `UserContext` from `CartContext`). Wrap values in `useMemo`: `const value = useMemo(() => ({ user, login }), [user])`.

**Virtualization:** For lists >100 items, use `@tanstack/react-virtual` or `react-window` to render only visible rows.

## Edge Cases

1. **Concurrent features conflict**: `useTransition` and `Suspense` can cause unexpected loading states when combined with client-side navigation. Test transitions with slow networks (Chrome DevTools throttling).
2. **Third-party scripts blocking hydration**: scripts loaded via `<Script strategy="beforeInteractive">` can delay hydration. Use `afterInteractive` or `lazyOnload` unless the script is critical.
3. **CSS-in-JS with SSR**: libraries like `styled-components` need a server-side `ServerStyleSheet` to avoid FOUC. CSS Modules or Tailwind avoid this entirely.

## Output Format

- Provide the complete updated file for changed files.
- State: (a) root cause (if debugging), (b) what changed, (c) how to verify.
