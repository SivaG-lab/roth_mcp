---
name: llm-app-patterns
description: >
  Production-ready patterns for building LLM applications. Covers RAG
  pipelines, agent architectures (ReAct, function calling, plan-execute,
  multi-agent), prompt management, and LLMOps observability. Use when
  designing AI applications, implementing RAG, building agents, or setting
  up LLM monitoring. Triggers: llm patterns, rag pipeline, agent architecture,
  llmops, prompt chaining, function calling, retrieval augmented generation.
user-invokable: true
argument-hint: "<LLM pattern or architecture to implement>"
metadata:
  model: sonnet
---

# LLM Application Patterns

Production-ready patterns for building LLM applications — RAG, agents, prompts, and observability.

## When to Use

- Designing LLM-powered applications or pipelines
- Implementing RAG (Retrieval-Augmented Generation)
- Building AI agents with tool use
- Setting up LLMOps monitoring and evaluation
- Choosing between agent architectures

## When NOT to Use

- General Python development (use python-pro)
- LangChain/LangGraph specifics (use langchain-architecture or langgraph)
- Prompt engineering techniques only (use prompt-engineering-patterns)

---

## 1. RAG Pipeline

```
Documents → [Chunk + Embed] → Vector DB → [Retrieve] → [Generate + Cite]
```

### Chunking Strategies

| Strategy | Best For | Config |
|----------|----------|--------|
| **Fixed-size** | Simple docs | 512 tokens, 50 overlap |
| **Semantic** | Articles, essays | Split on paragraphs/sections |
| **Recursive** | Mixed content | Separators: `["\n\n", "\n", ". ", " "]` |
| **Document-aware** | Structured docs | Respect headers, lists, tables |

### Vector DB Selection

| DB | Scale | Best For |
|----|-------|----------|
| **Pinecone** | Billions | Managed production, hybrid search |
| **Weaviate** | Millions | Self-hosted, multi-modal |
| **ChromaDB** | Thousands | Prototyping, dev |
| **pgvector** | Millions | Existing Postgres infra |

### Retrieval Strategies

```python
# Hybrid search (semantic + keyword)
def hybrid_search(query: str, alpha: float = 0.5):
    """alpha=1.0 pure semantic, alpha=0.0 pure BM25"""
    semantic = vector_db.similarity_search(query)
    keyword = bm25_search(query)
    return rrf_merge(semantic, keyword, alpha)

# Multi-query retrieval (better recall)
def multi_query_retrieval(query: str):
    queries = llm.generate_query_variations(query, n=3)
    results = [semantic_search(q) for q in queries]
    return deduplicate(flatten(results))
```

### Generation with Citations

```python
RAG_PROMPT = """Answer based ONLY on the context below.
If insufficient information, say so. Cite source numbers.

Context:
{context}

Question: {question}"""

def generate_with_rag(question: str):
    docs = hybrid_search(question, top_k=5)
    context = "\n\n".join(
        f"[{i+1}] {d.content}" for i, d in enumerate(docs)
    )
    response = llm.generate(RAG_PROMPT.format(
        context=context, question=question
    ))
    return {"answer": response, "sources": [d.metadata for d in docs]}
```

---

## 2. Agent Architectures

### 2.1 ReAct (Reasoning + Acting)

```
Thought → Action → Observation → ... → Final Answer
```

```python
class ReActAgent:
    def __init__(self, tools: list, llm, max_iterations=10):
        self.tools = {t.name: t for t in tools}
        self.llm = llm
        self.max_iter = max_iterations

    def run(self, question: str) -> str:
        history = []
        for _ in range(self.max_iter):
            response = self.llm.generate(
                self._build_prompt(question, history)
            )
            if "Final Answer:" in response:
                return self._extract_answer(response)
            action, args = self._parse_action(response)
            observation = self.tools[action].run(args)
            history.append((response, observation))
        return "Max iterations reached"
```

### 2.2 Function Calling

```python
# Native tool use — LLM decides when/which tool to call
TOOLS = [{
    "name": "search_web",
    "description": "Search the web for current information",
    "parameters": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"]
    }
}]

def function_calling_loop(question: str):
    messages = [{"role": "user", "content": question}]
    while True:
        response = llm.chat(messages=messages, tools=TOOLS)
        if not response.tool_calls:
            return response.content
        for call in response.tool_calls:
            result = execute_tool(call.name, call.arguments)
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": str(result)})
```

### 2.3 Plan-and-Execute

```python
class PlanExecuteAgent:
    def run(self, task: str) -> str:
        plan = self.planner.create_plan(task)  # List of steps
        results = []
        for step in plan:
            result = self.executor.execute(step, context=results)
            results.append(result)
            if self._needs_replan(task, results):
                plan = self.planner.replan(task, results)
        return self.synthesizer.summarize(task, results)
```

### 2.4 Multi-Agent Collaboration

```python
class AgentTeam:
    def __init__(self):
        self.agents = {
            "researcher": ResearchAgent(),
            "analyst": AnalystAgent(),
            "writer": WriterAgent(),
            "critic": CriticAgent(),
        }
        self.coordinator = CoordinatorAgent()

    def solve(self, task: str) -> str:
        assignments = self.coordinator.decompose(task)
        results = {}
        for a in assignments:
            results[a.id] = self.agents[a.agent].execute(
                a.subtask, context=results
            )
        critique = self.agents["critic"].review(results)
        if critique.needs_revision:
            return self.solve_with_feedback(task, results, critique)
        return self.coordinator.synthesize(results)
```

---

## 3. Prompt Management

### Templates with Variables

```python
class PromptTemplate:
    def __init__(self, template: str, variables: list[str]):
        self.template = template
        self.variables = variables

    def format(self, **kwargs) -> str:
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing: {missing}")
        return self.template.format(**kwargs)

    def with_examples(self, examples: list[dict]) -> str:
        shots = "\n\n".join(
            f"Input: {e['input']}\nOutput: {e['output']}" for e in examples
        )
        return f"{shots}\n\n{self.template}"
```

### Prompt Chaining

```python
# Research → Analyze → Summarize
chain = PromptChain([
    {"name": "research", "prompt": "Research: {input}", "key": "research"},
    {"name": "analyze",  "prompt": "Analyze:\n{research}", "key": "analysis"},
    {"name": "summarize","prompt": "3 bullets:\n{analysis}","key": "summary"},
])
result = chain.run("quantum computing trends")
```

---

## 4. LLMOps & Observability

### Key Metrics

| Category | Metrics |
|----------|---------|
| **Performance** | latency p50/p99, tokens/sec |
| **Quality** | user satisfaction, task completion, hallucination rate |
| **Cost** | $/request, tokens/request, cache hit rate |
| **Reliability** | error rate, timeout rate, retry rate |

### Caching

```python
class LLMCache:
    def __init__(self, redis, ttl=3600):
        self.redis = redis
        self.ttl = ttl

    def get_or_generate(self, prompt, model, **kwargs):
        key = sha256(f"{model}:{prompt}:{json.dumps(kwargs)}".encode())
        cached = self.redis.get(key)
        if cached:
            return cached.decode()
        response = llm.generate(prompt, model=model, **kwargs)
        if kwargs.get("temperature", 1.0) == 0:  # Only cache deterministic
            self.redis.setex(key, self.ttl, response)
        return response
```

### Fallback Strategy

```python
class LLMWithFallback:
    def __init__(self, primary: str, fallbacks: list[str]):
        self.models = [primary] + fallbacks

    def generate(self, prompt: str, **kwargs) -> str:
        for model in self.models:
            try:
                return llm.generate(prompt, model=model, **kwargs)
            except (RateLimitError, APIError) as e:
                logging.warning(f"{model} failed: {e}")
        raise AllModelsFailedError("All models exhausted")
```

---

## Architecture Decision Matrix

| Pattern | Use When | Complexity | Cost |
|---------|----------|------------|------|
| **Simple RAG** | FAQ, docs search | Low | Low |
| **Hybrid RAG** | Mixed queries | Medium | Medium |
| **ReAct Agent** | Multi-step reasoning | Medium | Medium |
| **Function Calling** | Structured tool use | Low | Low |
| **Plan-Execute** | Complex multi-step tasks | High | High |
| **Multi-Agent** | Research, review tasks | Very High | Very High |

---

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Stuff entire docs into context | Chunk, embed, retrieve relevant parts |
| Trust LLM output blindly | Validate with ground truth, add citations |
| Single monolithic prompt | Chain focused prompts with clear roles |
| Ignore token costs | Cache, use smaller models for simple tasks |
| Skip evaluation | Benchmark on test set before deploying |
| Hardcode prompts in source | Use prompt registry with versioning |

---

## Checklist

- [ ] RAG: chunking strategy matches document type
- [ ] RAG: hybrid search (semantic + keyword) for better recall
- [ ] Agent: max iteration cap prevents infinite loops
- [ ] Agent: tool descriptions are clear and specific
- [ ] Prompts: versioned and A/B testable
- [ ] LLMOps: latency, cost, and quality metrics tracked
- [ ] Caching: deterministic calls cached (temperature=0)
- [ ] Fallback: graceful degradation to cheaper models
- [ ] Evaluation: benchmark test set with ground truth
