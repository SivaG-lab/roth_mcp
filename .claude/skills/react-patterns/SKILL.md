---
name: react-patterns
description: >
  Modern React patterns and principles for production applications. Covers
  component design, hooks, state management, React 19, composition, performance,
  error handling, TypeScript, and testing. Use when building React components,
  choosing state management, applying composition patterns, or reviewing code.
  Triggers: react pattern, component design, custom hook, state management,
  compound component, render props, react 19, useActionState, useOptimistic,
  react composition, react anti-pattern, react typescript.
user-invokable: true
argument-hint: "<pattern or topic>"
---

# React Patterns

Principles for building production-ready React applications.

## When to Use

- Designing new React components or features
- Choosing state management approach
- Applying composition patterns
- Reviewing React code for anti-patterns
- Adopting React 19 patterns

---

## 1. Component Design

### Component Types

| Type | Use | State |
|------|-----|-------|
| **Server** | Data fetching, static content | None |
| **Client** | Interactivity, browser APIs | useState, effects |
| **Presentational** | UI display only | Props only |
| **Container** | Logic + state orchestration | Heavy state |

### Design Rules

- One responsibility per component
- Props down, events up
- Composition over inheritance
- Prefer small, focused components
- Colocate state with the components that use it

---

## 2. Hook Patterns

### When to Extract Custom Hooks

| Pattern | Extract When |
|---------|-------------|
| **useLocalStorage** | Same storage read/write logic repeated |
| **useDebounce** | Multiple debounced values across components |
| **useFetch** | Repeated fetch + loading + error pattern |
| **useForm** | Complex form state with validation |
| **useMediaQuery** | Responsive breakpoint detection |

### Hook Rules

- Call hooks at top level only (never in conditions/loops)
- Same order every render
- Custom hooks start with `use`
- Always return cleanup from effects

```tsx
// Custom hook example
function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}
```

---

## 3. State Management

### Selection Guide

| Complexity | Solution |
|------------|----------|
| **Simple** | `useState`, `useReducer` |
| **Shared local** | React Context |
| **Server state** | TanStack Query, SWR |
| **Complex global** | Zustand, Redux Toolkit |

### State Placement

| Scope | Where |
|-------|-------|
| Single component | `useState` |
| Parent-child | Lift state up |
| Subtree | Context provider |
| App-wide | Global store |
| URL state | Search params / router |

### Rules of Thumb

- Start with `useState`, escalate only when needed
- Server state belongs in TanStack Query / SWR (not Redux)
- Avoid putting derived data in state — compute during render
- Context is fine for low-frequency updates (theme, auth, locale)

---

## 4. React 19 Patterns

### New Hooks

| Hook | Purpose | Example |
|------|---------|---------|
| **useActionState** | Form submission state | Login form with error handling |
| **useOptimistic** | Optimistic UI updates | Add todo, show immediately |
| **use** | Read promises/context in render | Conditional context, data fetching |

### React Compiler Benefits

- Automatic memoization (less manual `useMemo`/`useCallback`)
- Focus on writing pure components
- Compiler handles re-render optimization

```tsx
// React 19: useActionState
const [state, formAction, isPending] = useActionState(
  async (prev, formData) => {
    const result = await submitForm(formData);
    return result.error ? { error: result.error } : { success: true };
  },
  { error: null }
);

// React 19: useOptimistic
const [optimisticItems, addOptimistic] = useOptimistic(
  items,
  (state, newItem) => [...state, newItem]
);
```

---

## 5. Composition Patterns

### Compound Components

```tsx
// Parent provides context, children consume it
<Tabs defaultValue="tab1">
  <Tabs.List>
    <Tabs.Trigger value="tab1">Tab 1</Tabs.Trigger>
    <Tabs.Trigger value="tab2">Tab 2</Tabs.Trigger>
  </Tabs.List>
  <Tabs.Content value="tab1">Content 1</Tabs.Content>
  <Tabs.Content value="tab2">Content 2</Tabs.Content>
</Tabs>
```

### Pattern Selection

| Use Case | Prefer |
|----------|--------|
| Reusable logic | Custom hook |
| Render flexibility | Render props |
| Slot-based UI | Compound components |
| Cross-cutting concerns | Higher-order component (rare) |

### Children as Function (Render Props)

```tsx
<DataLoader url="/api/users">
  {({ data, loading, error }) => {
    if (loading) return <Spinner />;
    if (error) return <Error error={error} />;
    return <UserList users={data} />;
  }}
</DataLoader>
```

---

## 6. Performance

### When to Optimize

| Signal | Action |
|--------|--------|
| Slow renders visible to user | Profile with React DevTools |
| Large lists (100+) | Virtualize (react-window) |
| Expensive computation | `useMemo` with correct deps |
| Stable callbacks for children | `useCallback` (or React Compiler) |

### Optimization Order

1. Check if actually slow (measure first)
2. Profile with React DevTools Profiler
3. Identify specific bottleneck
4. Apply targeted fix (not blanket memo)

### Common Fixes

```tsx
// Compute during render (not in useEffect)
const total = items.reduce((sum, i) => sum + i.price, 0);

// Lazy state initialization
const [data] = useState(() => expensiveParse(raw));

// Functional setState (stable reference)
setCount(c => c + 1);
```

---

## 7. Error Handling

### Error Boundary Placement

| Scope | Where |
|-------|-------|
| App-wide | Root layout |
| Feature-level | Around route/feature |
| Component-level | Around risky third-party component |

### Recovery Strategy

- Show fallback UI with context
- Log error to monitoring (Sentry, etc.)
- Offer retry / refresh action
- Preserve user data when possible

---

## 8. TypeScript Patterns

### Props Typing

```tsx
// Interface for component props
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  onClick?: () => void;
}

// Generic component
interface ListProps<T> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
  keyExtractor: (item: T) => string;
}
```

### Common Types

| Need | Type |
|------|------|
| Children | `React.ReactNode` |
| Event handler | `React.MouseEventHandler<HTMLButtonElement>` |
| Ref | `React.RefObject<HTMLDivElement>` |
| Style | `React.CSSProperties` |

---

## 9. Testing

| Level | Focus | Tool |
|-------|-------|------|
| **Unit** | Pure functions, hooks | Vitest / Jest |
| **Integration** | Component behavior | React Testing Library |
| **E2E** | User flows | Playwright / Cypress |

### Test Priorities

1. User-visible behavior (not implementation details)
2. Edge cases and error states
3. Accessibility (role, label queries)
4. Interaction flows (click, type, submit)

---

## 10. Anti-Patterns

| Don't | Do |
|-------|----|
| Prop drill 5+ levels deep | Context or Zustand |
| Giant 500-line components | Split into focused pieces |
| `useEffect` for derived state | Compute during render |
| Premature `React.memo` everywhere | Profile first, memo targeted |
| `index` as list key | Stable unique ID |
| Fetch in `useEffect` | TanStack Query / Server Component |
| State for everything | URL params, computed values, refs |

---

> **Remember:** React is about composition. Build small, combine thoughtfully, measure before optimizing.
