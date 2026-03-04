---
name: react-ui-patterns
description: >
  Modern React UI patterns for loading states, error handling, empty states,
  button states, and data fetching. Use when building UI components that handle
  async data, managing UI state transitions, or implementing form submissions.
  Covers the golden rule of loading states, error hierarchies, and anti-patterns.
  Triggers: loading state, error handling, empty state, button loading,
  skeleton, spinner, toast, form submission, optimistic update,
  react ui state, data fetching ui.
user-invokable: true
argument-hint: "<UI pattern or state>"
---

# React UI Patterns

Patterns for building robust UI components that handle loading, error, empty, and success states.

## When to Use

- Building components that fetch or mutate data
- Handling async UI state transitions
- Implementing form submissions
- Reviewing UI for missing states

---

## Core Principles

1. **Never show stale UI** — Loading indicators only when actually loading
2. **Always surface errors** — Users must know when something fails
3. **Optimistic updates** — Make the UI feel instant where safe
4. **Progressive disclosure** — Show content as it becomes available
5. **Graceful degradation** — Partial data is better than no data

---

## Loading States

### The Golden Rule

**Show loading indicator ONLY when there's no data to display.**

```tsx
const { data, loading, error } = useQuery(GET_ITEMS);

if (error) return <ErrorState error={error} onRetry={refetch} />;
if (loading && !data) return <LoadingSkeleton />;
if (!data?.items.length) return <EmptyState />;

return <ItemList items={data.items} />;
```

```tsx
// WRONG — flashes spinner on refetch when cached data exists
if (loading) return <Spinner />;

// CORRECT — only show loading when no cached data
if (loading && !data) return <Spinner />;
```

### Decision Tree

```
Error? ──> Yes ──> Show error state with retry
  │
  No
  │
Loading AND no data? ──> Yes ──> Show skeleton/spinner
  │
  No
  │
Has data? ──> Yes, with items ──> Show data
  │            Yes, empty ──────> Show empty state
  No ──────────────────────────> Show loading (fallback)
```

### Skeleton vs Spinner

| Use Skeleton | Use Spinner |
|-------------|-------------|
| Known content shape (lists, cards) | Unknown content shape |
| Initial page load | Modal/dialog actions |
| Content placeholders | Button submissions |
| Dashboard layouts | Inline operations |

---

## Error Handling

### Error Hierarchy

| Level | When | Example |
|-------|------|---------|
| **Inline** | Field-level validation | "Email is required" under input |
| **Toast** | Recoverable, user can retry | "Failed to save — try again" |
| **Banner** | Page-level, partial data usable | "Some data couldn't load" |
| **Full screen** | Unrecoverable, needs action | "Session expired — sign in" |

### Always Surface Errors

```tsx
// CORRECT — error shown to user
const [createItem] = useMutation(CREATE_ITEM, {
  onCompleted: () => toast.success('Item created'),
  onError: (error) => {
    console.error('createItem failed:', error);
    toast.error('Failed to create item');
  },
});

// WRONG — error swallowed silently
const [createItem] = useMutation(CREATE_ITEM, {
  onError: (error) => console.error(error),  // User sees nothing!
});
```

### Error State Component

```tsx
interface ErrorStateProps {
  error: Error;
  onRetry?: () => void;
  title?: string;
}

function ErrorState({ error, onRetry, title }: ErrorStateProps) {
  return (
    <div role="alert" className="error-state">
      <AlertCircleIcon />
      <h3>{title ?? 'Something went wrong'}</h3>
      <p>{error.message}</p>
      {onRetry && <Button onClick={onRetry}>Try Again</Button>}
    </div>
  );
}
```

---

## Button States

### Loading State

```tsx
<Button
  onClick={handleSubmit}
  disabled={!isValid || isSubmitting}
  isLoading={isSubmitting}
>
  Submit
</Button>
```

### Critical Rule

**Always disable buttons during async operations.**

```tsx
// CORRECT — disabled and shows loading
<Button disabled={isSubmitting} isLoading={isSubmitting} onClick={submit}>
  Submit
</Button>

// WRONG — user can click multiple times
<Button onClick={submit}>
  {isSubmitting ? 'Submitting...' : 'Submit'}
</Button>
```

---

## Empty States

Every list or collection MUST have an empty state.

```tsx
// WRONG — blank screen when no items
<FlatList data={items} renderItem={renderItem} />

// CORRECT — explicit empty state
{items.length === 0 ? (
  <EmptyState
    icon={<PlusCircleIcon />}
    title="No items yet"
    description="Create your first item to get started"
    action={{ label: 'Create Item', onClick: handleCreate }}
  />
) : (
  <ItemList items={items} />
)}
```

### Contextual Empty States

| Context | Icon | Title | Action |
|---------|------|-------|--------|
| Search no results | Search | "No results found" | "Try different terms" |
| Empty collection | PlusCircle | "No items yet" | "Create Item" button |
| Filtered empty | Filter | "No matches" | "Clear filters" button |
| Error empty | AlertTriangle | "Couldn't load" | "Retry" button |

---

## Form Submission

```tsx
function CreateItemForm() {
  const [submit, { loading }] = useMutation(CREATE_ITEM, {
    onCompleted: () => {
      toast.success('Item created');
      router.push('/items');
    },
    onError: (error) => {
      console.error('Create failed:', error);
      toast.error('Failed to create item');
    },
  });

  const handleSubmit = async (values: FormValues) => {
    if (!isValid) {
      toast.error('Please fix errors before submitting');
      return;
    }
    await submit({ variables: { input: values } });
  };

  return (
    <form onSubmit={handleSubmit}>
      <Input
        name="name"
        value={values.name}
        onChange={handleChange}
        error={touched.name ? errors.name : undefined}
      />
      <Button
        type="submit"
        disabled={!isValid || loading}
        isLoading={loading}
      >
        Create Item
      </Button>
    </form>
  );
}
```

---

## Anti-Patterns

### Loading

```tsx
// WRONG — spinner when cached data exists (causes flash)
if (loading) return <Spinner />;

// CORRECT — only show loading without data
if (loading && !data) return <Spinner />;
```

### Errors

```tsx
// WRONG — error swallowed
try { await mutation(); } catch (e) { console.log(e); }

// CORRECT — error surfaced
onError: (error) => {
  console.error('operation failed:', error);
  toast.error('Operation failed');
}
```

### Buttons

```tsx
// WRONG — not disabled during submission
<Button onClick={submit}>Submit</Button>

// CORRECT — disabled and loading
<Button onClick={submit} disabled={loading} isLoading={loading}>Submit</Button>
```

---

## UI State Checklist

Before shipping any UI component:

**States:**
- [ ] Error state handled and shown to user
- [ ] Loading state shown only when no data exists
- [ ] Empty state provided for collections
- [ ] Buttons disabled during async operations
- [ ] Buttons show loading indicator

**Data:**
- [ ] Mutations have `onError` handler
- [ ] All user actions have feedback (toast / visual change)
- [ ] Optimistic updates where appropriate
- [ ] Stale data doesn't flash on refetch
