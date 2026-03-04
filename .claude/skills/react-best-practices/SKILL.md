---
name: react-best-practices
description: >
  React and Next.js performance optimization guidelines from Vercel Engineering.
  45 rules across 8 categories prioritized by impact. Covers waterfall elimination,
  bundle size, server-side performance, re-render optimization, and rendering perf.
  Use when optimizing React/Next.js apps, fixing performance issues, reviewing code
  for bottlenecks, or building high-performance frontends.
  Triggers: react performance, next.js optimization, bundle size, re-render,
  waterfall, suspense boundary, code splitting, react memo, server component,
  vercel best practices, react optimization.
user-invokable: true
argument-hint: "<performance concern or category>"
---

# React & Next.js Performance — Vercel Best Practices

45 rules across 8 categories, ordered by impact. Apply CRITICAL rules first.

## When to Use

- Optimizing React or Next.js application performance
- Reviewing code for performance bottlenecks
- Fixing waterfalls, large bundles, or unnecessary re-renders
- Building new features with performance in mind

---

## 1. Eliminating Waterfalls (CRITICAL)

Sequential async operations are the #1 performance killer.

| Rule | Pattern |
|------|---------|
| **async-defer-await** | Don't `await` unless you need the result before continuing |
| **async-parallel** | Use `Promise.all()` for independent fetches |
| **async-dependencies** | Only `await` what depends on previous result |
| **async-api-routes** | Parallel fetch in API routes, not just components |
| **async-suspense** | Wrap async components in Suspense for parallel streaming |

```tsx
// BAD: Sequential waterfall
const user = await getUser(id);
const posts = await getPosts(id);     // Waits for user unnecessarily
const comments = await getComments(id);

// GOOD: Parallel fetching
const [user, posts, comments] = await Promise.all([
  getUser(id), getPosts(id), getComments(id),
]);

// GOOD: Suspense boundaries for parallel streaming
<Suspense fallback={<UserSkeleton />}>
  <UserProfile id={id} />
</Suspense>
<Suspense fallback={<PostsSkeleton />}>
  <UserPosts id={id} />
</Suspense>
```

---

## 2. Bundle Size (CRITICAL)

| Rule | Action |
|------|--------|
| **no-barrel-imports** | Import from specific files, not barrel `index.ts` |
| **dynamic-import** | `next/dynamic` or `React.lazy()` for heavy components |
| **defer-third-party** | `@next/third-parties` or lazy-load analytics/chat/maps |
| **conditional-load** | Load features only when user needs them |
| **preload-critical** | `<link rel="preload">` for above-the-fold resources |

```tsx
// BAD: Barrel import pulls entire library
import { Button } from '@/components';

// GOOD: Direct import
import { Button } from '@/components/ui/button';

// GOOD: Dynamic import for heavy components
const Chart = dynamic(() => import('@/components/chart'), {
  loading: () => <ChartSkeleton />,
  ssr: false,
});
```

---

## 3. Server-Side Performance (HIGH)

| Rule | Action |
|------|--------|
| **react-cache** | `React.cache()` for request-scoped dedup |
| **lru-cache** | LRU cache for cross-request data (DB queries) |
| **parallel-fetch** | Fetch data in parallel in server components |
| **after()** | `next/server` `after()` for post-response work (logging) |

```tsx
// Deduplicate within a single request
const getUser = React.cache(async (id: string) => {
  return await db.user.findUnique({ where: { id } });
});

// Cross-request cache for expensive queries
import { LRUCache } from 'lru-cache';
const cache = new LRUCache<string, Product[]>({ max: 100, ttl: 60_000 });
```

---

## 4. Client-Side Data Fetching (MEDIUM-HIGH)

| Rule | Action |
|------|--------|
| **swr-dedup** | Use SWR/React Query — automatic request dedup + cache |
| **event-listeners** | Clean up listeners in useEffect return |

```tsx
const { data, isLoading } = useSWR(`/api/user/${id}`, fetcher);
```

---

## 5. Re-render Optimization (MEDIUM)

Apply only after profiling confirms re-render issues.

| Rule | Action |
|------|--------|
| **defer-reads** | Don't read context/store in parent; push reads to children |
| **memo** | `React.memo()` for expensive components with stable props |
| **check-deps** | Verify useEffect/useMemo/useCallback dependency arrays |
| **derived-state** | Compute during render, not in state + useEffect |
| **functional-setState** | `setCount(c => c + 1)` not `setCount(count + 1)` |
| **lazy-state-init** | `useState(() => expensive())` not `useState(expensive())` |
| **transitions** | `useTransition` / `useDeferredValue` for non-urgent updates |

```tsx
// BAD: Derived state in useEffect (extra render cycle)
const [items, setItems] = useState([]);
const [count, setCount] = useState(0);
useEffect(() => setCount(items.length), [items]);

// GOOD: Compute during render
const count = items.length;

// BAD: Expensive init runs every render
const [data] = useState(parseHugeJSON(raw));

// GOOD: Lazy initializer runs once
const [data] = useState(() => parseHugeJSON(raw));
```

---

## 6. Rendering Performance (MEDIUM)

| Rule | Action |
|------|--------|
| **content-visibility** | `content-visibility: auto` for off-screen sections |
| **hoist-jsx** | Extract static JSX outside component to avoid recreation |
| **svg-precision** | Round SVG coordinates to 1 decimal, strip metadata |
| **hydration** | Minimize client components; prefer Server Components |
| **conditional-render** | Early return before expensive JSX |

```tsx
// Hoist static JSX outside component
const EMPTY_STATE = <div className="empty">No results found</div>;

function SearchResults({ results }) {
  if (!results.length) return EMPTY_STATE;
  return <ResultList items={results} />;
}
```

---

## 7. JavaScript Performance (LOW-MEDIUM)

| Rule | Action |
|------|--------|
| **batch-dom** | Batch DOM reads then writes (avoid layout thrashing) |
| **index-maps** | `new Map()` for O(1) lookups instead of `.find()` |
| **cache-access** | Cache `object.deeply.nested.value` in a variable |
| **set-lookups** | `Set.has()` instead of `array.includes()` for large lists |
| **early-exit** | Return early from loops/functions when result found |
| **hoist-regexp** | Declare RegExp outside loops and hot functions |

```tsx
// BAD: O(n) lookup in render
const selected = items.find(i => i.id === selectedId);

// GOOD: O(1) lookup with Map
const itemMap = useMemo(() => new Map(items.map(i => [i.id, i])), [items]);
const selected = itemMap.get(selectedId);
```

---

## 8. Advanced Patterns (LOW)

| Rule | Action |
|------|--------|
| **event-handler-refs** | Stable callback refs to avoid child re-renders |
| **useLatest** | Ref-based hook for always-current value without deps |

```tsx
function useEventCallback<T extends (...args: any[]) => any>(fn: T): T {
  const ref = useRef(fn);
  ref.current = fn;
  return useCallback((...args: any[]) => ref.current(...args), []) as T;
}
```

---

## Optimization Order

1. **Fix waterfalls** — Parallel fetch, Suspense boundaries
2. **Reduce bundle** — Tree-shake, dynamic import, no barrel imports
3. **Server Components** — Move data fetching to server, minimize client JS
4. **Cache** — React.cache for request dedup, LRU for cross-request
5. **Profile re-renders** — React DevTools Profiler, then apply memo/transitions
6. **Micro-optimize** — Only after the above are addressed

---

## Performance Checklist

- [ ] No sequential fetches that could be parallel
- [ ] Suspense boundaries around async components
- [ ] No barrel imports from large libraries
- [ ] Heavy components lazy-loaded with dynamic()
- [ ] Third-party scripts deferred or lazy-loaded
- [ ] Server Components used where possible
- [ ] No derived state computed in useEffect
- [ ] React.memo only on profiled-slow components
- [ ] Dependency arrays correct (no missing/extra deps)
- [ ] Large lists virtualized (react-window, tanstack-virtual)
