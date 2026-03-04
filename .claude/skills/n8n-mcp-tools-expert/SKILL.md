---
name: n8n-mcp-tools-expert
description: >
  Expert guide for using n8n-mcp MCP tools effectively. Use when searching for
  n8n nodes, validating configurations, accessing templates, managing workflows,
  or using any n8n-mcp tool. Provides tool selection guidance, parameter formats,
  common patterns, and critical nodeType format differences.
  Triggers: n8n mcp, n8n node, n8n workflow, n8n template, n8n validate,
  search nodes, n8n configuration, n8n automation, workflow builder.
user-invokable: true
argument-hint: "<n8n topic or tool name>"
metadata:
  origin: "https://github.com/czlonkowski/n8n-skills"
---

# n8n MCP Tools Expert

Master guide for using n8n-mcp MCP server tools to build workflows.

## When to Use

- Searching for n8n nodes or understanding their configuration
- Validating n8n node or workflow configurations
- Managing n8n workflows via API
- Accessing the n8n template library
- Need guidance on tool selection or parameter formats

---

## Tool Categories

| Category | Key Tools | Guide |
|----------|-----------|-------|
| **Node Discovery** | `search_nodes`, `get_node` | [SEARCH_GUIDE.md](SEARCH_GUIDE.md) |
| **Validation** | `validate_node`, `validate_workflow` | [VALIDATION_GUIDE.md](VALIDATION_GUIDE.md) |
| **Workflow Mgmt** | `n8n_create_workflow`, `n8n_update_partial_workflow` | [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) |
| **Templates** | `search_templates`, `get_template`, `n8n_deploy_template` | See below |
| **Docs & Health** | `tools_documentation`, `ai_agents_guide`, `n8n_health_check` | See below |

---

## Quick Reference — Most Used Tools

| Tool | Use When | Speed |
|------|----------|-------|
| `search_nodes` | Finding nodes by keyword | <20ms |
| `get_node` | Understanding node operations | <10ms |
| `validate_node` | Checking configurations | <100ms |
| `n8n_update_partial_workflow` | Editing workflows (most used!) | 50-200ms |
| `n8n_deploy_template` | Deploy template to instance | 200-500ms |

---

## CRITICAL: nodeType Formats

Two different prefixes for different tools:

### Search/Validate Tools — Short prefix

```javascript
"nodes-base.slack"
"nodes-base.httpRequest"
"nodes-langchain.agent"
```

Used by: `search_nodes`, `get_node`, `validate_node`, `validate_workflow`

### Workflow Tools — Full prefix

```javascript
"n8n-nodes-base.slack"
"n8n-nodes-base.httpRequest"
"@n8n/n8n-nodes-langchain.agent"
```

Used by: `n8n_create_workflow`, `n8n_update_partial_workflow`

### Conversion

```javascript
// search_nodes returns both formats
{
  "nodeType": "nodes-base.slack",              // For search/validate
  "workflowNodeType": "n8n-nodes-base.slack"   // For workflow tools
}
```

---

## Common Workflows

### 1. Find and Understand a Node

```javascript
// Step 1: Search
search_nodes({ query: "slack" })
// Returns: nodes-base.slack, nodes-base.slackTrigger

// Step 2: Get details (standard detail, covers 95% of cases)
get_node({ nodeType: "nodes-base.slack" })

// Step 3 (optional): Get readable docs
get_node({ nodeType: "nodes-base.slack", mode: "docs" })
```

### 2. Validate Configuration

```javascript
// Step 1: Quick check
validate_node({ nodeType: "nodes-base.slack", config: {...}, mode: "minimal" })

// Step 2: Full validation
validate_node({ nodeType: "nodes-base.slack", config: {...}, profile: "runtime" })

// Step 3: Fix errors and validate again
```

**Validation profiles**: `minimal` (lenient), `runtime` (recommended), `ai-friendly` (for AI workflows), `strict` (production)

### 3. Build a Workflow Iteratively

```javascript
// Create
n8n_create_workflow({ name: "My Workflow", nodes: [...], connections: {...} })

// Edit (iterate — avg 56s between edits)
n8n_update_partial_workflow({
  id: "workflow-id",
  intent: "Add error handling",
  operations: [{ type: "addNode", node: {...} }]
})

// Validate
n8n_validate_workflow({ id: "workflow-id" })

// Activate
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{ type: "activateWorkflow" }]
})
```

---

## Common Mistakes

### 1. Wrong nodeType Format

```javascript
// WRONG
get_node({ nodeType: "slack" })                    // Missing prefix
get_node({ nodeType: "n8n-nodes-base.slack" })     // Wrong prefix for get_node

// CORRECT
get_node({ nodeType: "nodes-base.slack" })
```

### 2. Using detail="full" by Default

```javascript
// WRONG — 3-8K tokens, wasteful
get_node({ nodeType: "nodes-base.slack", detail: "full" })

// CORRECT — 1-2K tokens, covers 95% of cases
get_node({ nodeType: "nodes-base.slack" })                    // standard (default)
get_node({ nodeType: "nodes-base.slack", mode: "docs" })      // readable docs
get_node({ nodeType: "nodes-base.slack", mode: "search_properties", propertyQuery: "auth" })
```

### 3. Not Using Validation Profiles

```javascript
// WRONG — uses default, may miss issues
validate_node({ nodeType, config })

// CORRECT — explicit profile
validate_node({ nodeType, config, profile: "runtime" })
```

### 4. Not Using Smart Parameters

```javascript
// OLD (manual sourceIndex)
{ type: "addConnection", source: "IF", target: "Handler", sourceIndex: 0 }

// NEW (semantic)
{ type: "addConnection", source: "IF", target: "True Handler", branch: "true" }
{ type: "addConnection", source: "Switch", target: "Handler A", case: 0 }
```

### 5. Missing intent Parameter

```javascript
// WRONG — no context
n8n_update_partial_workflow({ id: "abc", operations: [...] })

// CORRECT — better AI responses
n8n_update_partial_workflow({
  id: "abc",
  intent: "Add error handling for API failures",
  operations: [...]
})
```

---

## get_node Reference

**Detail levels** (mode="info"):
- `minimal` (~200 tokens) — metadata only
- `standard` (~1-2K tokens) — operations + properties (recommended)
- `full` (~3-8K tokens) — complete schema (use sparingly)

**Operation modes**:
- `info` (default) — node schema
- `docs` — readable markdown
- `search_properties` — find specific properties (use `propertyQuery`)
- `versions` — list versions with breaking changes

---

## Template Usage

```javascript
// Search templates
search_templates({ query: "webhook slack", limit: 20 })
search_templates({ searchMode: "by_nodes", nodeTypes: ["n8n-nodes-base.httpRequest"] })
search_templates({ searchMode: "by_metadata", complexity: "simple", maxSetupMinutes: 15 })

// Get template details
get_template({ templateId: 2947, mode: "structure" })   // nodes+connections
get_template({ templateId: 2947, mode: "full" })          // complete JSON

// Deploy to instance
n8n_deploy_template({ templateId: 2947, name: "My Workflow", autoFix: true })
```

---

## Tool Availability

**Always available** (no n8n API needed):
`search_nodes`, `get_node`, `validate_node`, `validate_workflow`,
`search_templates`, `get_template`, `tools_documentation`, `ai_agents_guide`

**Requires n8n API** (N8N_API_URL + N8N_API_KEY):
`n8n_create_workflow`, `n8n_update_partial_workflow`, `n8n_validate_workflow`,
`n8n_list_workflows`, `n8n_get_workflow`, `n8n_test_workflow`,
`n8n_executions`, `n8n_deploy_template`, `n8n_workflow_versions`

---

## Auto-Sanitization

When you update ANY workflow, all nodes are automatically sanitized:
- Binary operators (equals, contains) — removes `singleValue`
- Unary operators (isEmpty, isNotEmpty) — adds `singleValue: true`
- IF/Switch nodes — adds missing metadata

Cannot auto-fix: broken connections, branch count mismatches.

---

## Best Practices

**Do:**
- Use `detail: "standard"` (default) for most node lookups
- Specify validation profile explicitly (`profile: "runtime"`)
- Use smart parameters (`branch`, `case`) for clarity
- Include `intent` in workflow updates
- Build workflows iteratively, not in one shot
- Validate after every significant change

**Don't:**
- Use `detail: "full"` unless debugging (wastes tokens)
- Forget the `nodes-base.*` prefix on search/validate tools
- Skip validation profiles
- Try to build entire workflows in one API call
- Ignore auto-sanitization behavior

---

## Detailed Guides

- [SEARCH_GUIDE.md](SEARCH_GUIDE.md) — Node discovery, detail levels, modes
- [VALIDATION_GUIDE.md](VALIDATION_GUIDE.md) — Profiles, modes, error handling
- [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) — 17 operation types, smart params, activation
