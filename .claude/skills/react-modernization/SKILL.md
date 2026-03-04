---
name: react-modernization
description: >
  Upgrade React applications to latest versions, migrate class components to
  function components with hooks, and adopt concurrent features. Use when
  upgrading React 16/17/18 to 19, migrating classes to hooks, running codemods,
  adopting Suspense/Transitions, or modernizing legacy React patterns.
  Triggers: react upgrade, react migration, class to hooks, react codemod,
  concurrent features, react 18, react 19, legacy react, modernize react,
  migrate class component, useTransition, useDeferredValue, useActionState.
user-invokable: true
argument-hint: "<migration target or version>"
---

# React Modernization

Guide for upgrading React applications, migrating patterns, and adopting modern features.

## When to Use

- Upgrading React to 18.x or 19.x
- Migrating class components to function components with hooks
- Adopting concurrent features (Suspense, Transitions, use())
- Running codemods for automated transformations
- Modernizing legacy patterns (HOCs to hooks, lifecycle to effects)

---

## Upgrade Path

```
React 16/17 ──> React 18 ──> Adopt Concurrent Features ──> React 19
                   │                      │                     │
            createRoot migration   Suspense + Transitions   use() + Actions
            Automatic batching     useDeferredValue         useOptimistic
            StrictMode changes     Error Boundaries          React Compiler
```

---

## React 18 Migration

### Breaking Changes

- `ReactDOM.render` replaced by `createRoot` (required)
- Automatic batching in all contexts (may change behavior)
- Strict Mode double-renders effects in dev

### Install & Codemod

```bash
npm install react@18 react-dom@18 @types/react@18 @types/react-dom@18
npx codemod react/19/replace-reactdom-render
```

```tsx
// BEFORE (React 17)
import ReactDOM from 'react-dom';
ReactDOM.render(<App />, document.getElementById('root'));

// AFTER (React 18+)
import { createRoot } from 'react-dom/client';
createRoot(document.getElementById('root')!).render(<App />);
```

### TypeScript Changes

- `React.FC` no longer includes `children` — add explicitly to props
- `React.VFC` removed — use `React.FC`
- Stricter generics on `useCallback` / `useMemo`

---

## Class to Function Component Migration

### Priority Order

1. **Leaf components** (no children, simple props) — easiest wins
2. **Container components** (state + data fetching)
3. **Higher-Order Components** — extract to custom hooks
4. **Ref-forwarding components** — useRef + forwardRef
5. **Error Boundaries** — keep as class (no hook equivalent)

### Lifecycle to Hooks Mapping

| Class Lifecycle | Hook Equivalent |
|----------------|-----------------|
| `constructor` / state init | `useState(initialValue)` |
| `componentDidMount` | `useEffect(() => { ... }, [])` |
| `componentDidUpdate` | `useEffect(() => { ... }, [deps])` |
| `componentWillUnmount` | `useEffect return cleanup` |
| `shouldComponentUpdate` | `React.memo(Component)` |
| `getDerivedStateFromProps` | Compute during render or `useMemo` |
| `componentDidCatch` | No hook — keep as class Error Boundary |

### Migration Example

```tsx
// BEFORE: Class
class UserProfile extends React.Component<Props, State> {
  state = { user: null, loading: true };
  componentDidMount() {
    fetchUser(this.props.id).then(user =>
      this.setState({ user, loading: false })
    );
  }
  componentDidUpdate(prev: Props) {
    if (prev.id !== this.props.id) {
      this.setState({ loading: true });
      fetchUser(this.props.id).then(user =>
        this.setState({ user, loading: false })
      );
    }
  }
  render() {
    if (this.state.loading) return <Spinner />;
    return <div>{this.state.user?.name}</div>;
  }
}

// AFTER: Function + hooks
function UserProfile({ id }: Props) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchUser(id).then(u => { setUser(u); setLoading(false); });
  }, [id]);

  if (loading) return <Spinner />;
  return <div>{user?.name}</div>;
}
```

### HOC to Custom Hook

```tsx
// BEFORE: HOC
function withAuth(Component) {
  return (props) => {
    const user = useContext(AuthContext);
    if (!user) return <Redirect to="/login" />;
    return <Component {...props} user={user} />;
  };
}

// AFTER: Custom hook
function useAuth() {
  const user = useContext(AuthContext);
  return { user, isAuthenticated: !!user };
}
```

---

## Concurrent Features (React 18+)

### Suspense Boundaries

```tsx
<Suspense fallback={<Skeleton />}>
  <LazyComponent />
</Suspense>
```

### useTransition — Non-Urgent Updates

```tsx
const [isPending, startTransition] = useTransition();

function handleSearch(value: string) {
  setQuery(value);                                    // Urgent: update input
  startTransition(() => setResults(filter(value)));   // Deferred: filter
}
```

### useDeferredValue — Defer Expensive Renders

```tsx
const deferredQuery = useDeferredValue(query);
const results = useMemo(() => search(deferredQuery), [deferredQuery]);
```

---

## React 19 Features

### use() — Read Promises and Context

```tsx
// Suspends until promise resolves
function UserProfile({ userPromise }: { userPromise: Promise<User> }) {
  const user = use(userPromise);
  return <div>{user.name}</div>;
}

// Conditional context reading (new in 19)
function Theme({ show }: { show: boolean }) {
  if (!show) return null;
  const theme = use(ThemeContext);
  return <div style={{ color: theme.primary }}>Themed</div>;
}
```

### useActionState — Form Actions

```tsx
const [state, formAction, isPending] = useActionState(
  async (prev, formData) => {
    const result = await login(formData);
    if (result.error) return { error: result.error };
    redirect('/dashboard');
  },
  { error: null }
);

return (
  <form action={formAction}>
    <input name="email" type="email" />
    <button disabled={isPending}>
      {isPending ? 'Signing in...' : 'Sign In'}
    </button>
  </form>
);
```

### useOptimistic — Optimistic UI

```tsx
const [optimisticTodos, addOptimistic] = useOptimistic(
  todos,
  (state, newTodo: Todo) => [...state, newTodo]
);

async function addTodo(formData: FormData) {
  const todo = { id: crypto.randomUUID(), text: formData.get('text') as string };
  addOptimistic(todo);       // Instant UI update
  await saveTodo(todo);      // Server call
}
```

---

## Codemods

```bash
# All React 19 codemods at once
npx codemod@latest react/19/migration-recipe

# Individual codemods
npx codemod react/19/replace-reactdom-render     # createRoot
npx codemod react/19/replace-string-ref          # string refs to useRef
npx codemod react/19/replace-act-import          # act() import path
npx codemod react/19/replace-use-form-state      # useFormState to useActionState
```

---

## Migration Checklist

- [ ] Update react, react-dom, and @types packages
- [ ] Replace ReactDOM.render with createRoot
- [ ] Run codemods for automated fixes
- [ ] Fix TypeScript errors (FC children, etc.)
- [ ] Test with StrictMode enabled (double-render effects)
- [ ] Migrate class components (leaf first, then containers)
- [ ] Replace HOCs with custom hooks
- [ ] Add Suspense boundaries for code splitting
- [ ] Adopt useTransition for non-urgent updates
- [ ] Keep Error Boundaries as class components
- [ ] Test all forms and user flows end-to-end
