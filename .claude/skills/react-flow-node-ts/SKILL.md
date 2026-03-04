---
name: react-flow-node-ts
description: >
  Create React Flow node components with TypeScript types, handles, and Zustand
  integration. Use when building custom nodes for React Flow canvas, creating
  visual workflow editors, node-based UIs, or implementing drag-and-drop flow
  builders. Covers node patterns, type definitions, handle configuration,
  resizing, and store integration.
  Triggers: react flow, custom node, node component, workflow editor, flow
  builder, node-based UI, react flow node, handle, zustand store, canvas.
user-invokable: true
argument-hint: "<node name or type>"
---

# React Flow Node Components

Patterns for building custom React Flow node components with TypeScript and Zustand.

## When to Use

- Building custom nodes for a React Flow canvas
- Creating visual workflow / pipeline editors
- Implementing node-based UIs with typed data
- Adding new node types to an existing React Flow project

---

## Quick Start

1. Copy the patterns below and replace placeholders:
   - `{{NodeName}}` — PascalCase component name (e.g., `VideoNode`)
   - `{{nodeType}}` — kebab-case type identifier (e.g., `video-node`)
   - `{{NodeData}}` — Data interface name (e.g., `VideoNodeData`)

---

## Node Component Pattern

```tsx
import { memo } from 'react';
import { Handle, Position, NodeResizer, type NodeProps } from '@xyflow/react';
import { useAppStore } from '@/store/app-store';
import type { {{NodeName}}Data } from '@/types';

type {{NodeName}}Props = NodeProps<Node<{{NodeName}}Data, '{{nodeType}}'>>;

export const {{NodeName}} = memo(function {{NodeName}}({
  id,
  data,
  selected,
  width,
  height,
}: {{NodeName}}Props) {
  const updateNode = useAppStore((s) => s.updateNode);
  const canvasMode = useAppStore((s) => s.canvasMode);

  return (
    <>
      <NodeResizer
        isVisible={selected && canvasMode === 'editing'}
        minWidth={200}
        minHeight={100}
      />
      <div className="node-container">
        <Handle type="target" position={Position.Top} />

        <div className="node-header">
          <span className="node-title">{data.title}</span>
        </div>

        <div className="node-body">
          {/* Node-specific content */}
        </div>

        <Handle type="source" position={Position.Bottom} />
      </div>
    </>
  );
});
```

---

## Type Definition Pattern

```typescript
import type { Node } from '@xyflow/react';

// Data interface — must extend Record<string, unknown>
export interface {{NodeName}}Data extends Record<string, unknown> {
  title: string;
  description?: string;
  // Add node-specific fields here
}

// Typed node alias
export type {{NodeName}} = Node<{{NodeName}}Data, '{{nodeType}}'>;
```

### Union Type for All Nodes

```typescript
export type AppNode =
  | Node<TextNodeData, 'text-node'>
  | Node<VideoNodeData, 'video-node'>
  | Node<{{NodeName}}Data, '{{nodeType}}'>;
```

---

## Handle Configuration

```tsx
// Single input, single output (most common)
<Handle type="target" position={Position.Top} />
<Handle type="source" position={Position.Bottom} />

// Multiple named handles
<Handle type="target" position={Position.Left} id="input-a" />
<Handle type="target" position={Position.Left} id="input-b" style={{ top: '75%' }} />
<Handle type="source" position={Position.Right} id="output" />

// Conditional handle (only show in editing mode)
{canvasMode === 'editing' && (
  <Handle type="source" position={Position.Bottom} />
)}
```

---

## Store Integration (Zustand)

```typescript
// In app-store.ts
interface AppState {
  nodes: AppNode[];
  updateNode: (id: string, data: Partial<AppNode['data']>) => void;
  // ... other actions
}

export const useAppStore = create<AppState>((set, get) => ({
  nodes: [],
  updateNode: (id, data) =>
    set({
      nodes: get().nodes.map((n) =>
        n.id === id ? { ...n, data: { ...n.data, ...data } } : n
      ),
    }),
}));
```

### Default Node Data

```typescript
// defaults.ts
export const DEFAULT_NODE_DATA: Record<string, () => AppNode['data']> = {
  '{{nodeType}}': () => ({
    title: 'New {{NodeName}}',
    description: '',
  }),
};
```

---

## Registration

```tsx
// nodeTypes.ts — register all custom nodes
import { {{NodeName}} } from '@/components/nodes/{{NodeName}}';

export const nodeTypes = {
  '{{nodeType}}': {{NodeName}},
  // ... other node types
} as const;

// Canvas.tsx
import { ReactFlow } from '@xyflow/react';
import { nodeTypes } from './nodeTypes';

<ReactFlow
  nodes={nodes}
  edges={edges}
  nodeTypes={nodeTypes}
  onNodesChange={onNodesChange}
  onEdgesChange={onEdgesChange}
/>
```

---

## Integration Steps

1. **Add type** — Define `{{NodeName}}Data` interface in `types/index.ts`
2. **Create component** — Build node in `components/nodes/{{NodeName}}.tsx`
3. **Export** — Add to `components/nodes/index.ts` barrel export
4. **Add defaults** — Register default data in `store/app-store.ts`
5. **Register** — Add to `nodeTypes` object for React Flow
6. **Add to menus** — Include in AddBlockMenu and ConnectMenu

---

## Common Patterns

### Editable Title

```tsx
<input
  className="node-title-input"
  value={data.title}
  onChange={(e) => updateNode(id, { title: e.target.value })}
  onBlur={() => /* save */}
/>
```

### Status Indicator

```tsx
<div className={`status-dot status-${data.status}`} />
```

### Validation Badge

```tsx
{data.errors?.length > 0 && (
  <span className="error-badge">{data.errors.length}</span>
)}
```

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Heavy computation in node render | Blocks canvas interaction | useMemo or move to store |
| Inline styles for layout | Inconsistent, hard to maintain | CSS classes or Tailwind |
| Forgetting `memo()` wrapper | Unnecessary re-renders on pan/zoom | Always wrap with `memo` |
| Untyped node data | Runtime errors, poor DX | Always define data interface |
| Direct DOM manipulation | Breaks React Flow internals | Use React state + handles |
