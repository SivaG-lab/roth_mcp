---
name: backend-patterns
description: >
  Backend architecture patterns for Node.js, Express, and Next.js API routes.
  Covers RESTful API design, repository pattern, database optimization,
  caching, authentication, rate limiting, and error handling. Use when building
  server-side applications, designing APIs, or optimizing backend performance.
  Triggers: backend patterns, api design, repository pattern, middleware,
  database optimization, rate limiting, error handling, node.js backend.
user-invokable: true
argument-hint: "<backend pattern or API design task>"
metadata:
  model: sonnet
---

# Backend Development Patterns

Backend architecture patterns and best practices for scalable Node.js/Next.js applications.

## When to Use

- Designing RESTful or GraphQL APIs
- Implementing repository, service, or middleware patterns
- Optimizing database queries (N+1, indexing, transactions)
- Adding authentication, rate limiting, or caching layers
- Structuring backend code for maintainability

## When NOT to Use

- Python/FastAPI backends (use fastapi-pro)
- Frontend/React patterns (use react-patterns)
- Infrastructure/DevOps (use multi-cloud-architecture)

---

## API Design

### RESTful Resource URLs

```typescript
GET    /api/markets          // List resources
GET    /api/markets/:id      // Get single resource
POST   /api/markets          // Create resource
PUT    /api/markets/:id      // Replace resource
PATCH  /api/markets/:id      // Partial update
DELETE /api/markets/:id      // Delete resource

// Query params for filtering, sorting, pagination
GET /api/markets?status=active&sort=volume&limit=20&offset=0
```

### Repository Pattern

```typescript
interface MarketRepository {
  findAll(filters?: MarketFilters): Promise<Market[]>
  findById(id: string): Promise<Market | null>
  create(data: CreateMarketDto): Promise<Market>
  update(id: string, data: UpdateMarketDto): Promise<Market>
  delete(id: string): Promise<void>
}

class SupabaseMarketRepository implements MarketRepository {
  async findAll(filters?: MarketFilters): Promise<Market[]> {
    let query = supabase.from('markets').select('*')
    if (filters?.status) query = query.eq('status', filters.status)
    if (filters?.limit) query = query.limit(filters.limit)
    const { data, error } = await query
    if (error) throw new Error(error.message)
    return data
  }
}
```

### Service Layer

```typescript
class MarketService {
  constructor(private repo: MarketRepository) {}

  async search(query: string, limit = 10): Promise<Market[]> {
    const embedding = await generateEmbedding(query)
    const results = await this.vectorSearch(embedding, limit)
    const markets = await this.repo.findByIds(results.map(r => r.id))
    return markets.sort((a, b) =>
      (results.find(r => r.id === a.id)?.score || 0) -
      (results.find(r => r.id === b.id)?.score || 0)
    )
  }
}
```

### Middleware Pattern

```typescript
export function withAuth(handler: NextApiHandler): NextApiHandler {
  return async (req, res) => {
    const token = req.headers.authorization?.replace('Bearer ', '')
    if (!token) return res.status(401).json({ error: 'Unauthorized' })
    try {
      req.user = await verifyToken(token)
      return handler(req, res)
    } catch {
      return res.status(401).json({ error: 'Invalid token' })
    }
  }
}
```

---

## Database Patterns

### Query Optimization

```typescript
// Select only needed columns
const { data } = await supabase
  .from('markets')
  .select('id, name, status, volume')
  .eq('status', 'active')
  .order('volume', { ascending: false })
  .limit(10)
```

### N+1 Prevention

```typescript
// BAD: N+1 queries
for (const market of markets) {
  market.creator = await getUser(market.creator_id)
}

// GOOD: Batch fetch
const creatorIds = markets.map(m => m.creator_id)
const creators = await getUsers(creatorIds)
const map = new Map(creators.map(c => [c.id, c]))
markets.forEach(m => { m.creator = map.get(m.creator_id) })
```

### Transactions

```typescript
const { data, error } = await supabase.rpc(
  'create_market_with_position',
  { market_data: marketData, position_data: positionData }
)
```

---

## Caching

### Cache-Aside Pattern

```typescript
class CachedRepo<T> {
  constructor(private base: Repository<T>, private redis: RedisClient) {}

  async findById(id: string): Promise<T | null> {
    const cached = await this.redis.get(`item:${id}`)
    if (cached) return JSON.parse(cached)

    const item = await this.base.findById(id)
    if (item) await this.redis.setex(`item:${id}`, 300, JSON.stringify(item))
    return item
  }

  async invalidate(id: string): Promise<void> {
    await this.redis.del(`item:${id}`)
  }
}
```

---

## Error Handling

### Centralized Error Handler

```typescript
class ApiError extends Error {
  constructor(public statusCode: number, message: string) {
    super(message)
  }
}

export function errorHandler(error: unknown): Response {
  if (error instanceof ApiError) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: error.statusCode }
    )
  }
  if (error instanceof z.ZodError) {
    return NextResponse.json(
      { success: false, error: 'Validation failed', details: error.errors },
      { status: 400 }
    )
  }
  console.error('Unexpected:', error)
  return NextResponse.json(
    { success: false, error: 'Internal server error' },
    { status: 500 }
  )
}
```

### Retry with Backoff

```typescript
async function fetchWithRetry<T>(fn: () => Promise<T>, retries = 3): Promise<T> {
  let lastError: Error
  for (let i = 0; i < retries; i++) {
    try { return await fn() }
    catch (e) {
      lastError = e as Error
      if (i < retries - 1) await new Promise(r => setTimeout(r, 2 ** i * 1000))
    }
  }
  throw lastError!
}
```

---

## Authentication

### JWT + RBAC

```typescript
export function verifyToken(token: string): JWTPayload {
  return jwt.verify(token, process.env.JWT_SECRET!) as JWTPayload
}

const rolePermissions: Record<string, string[]> = {
  admin: ['read', 'write', 'delete', 'admin'],
  moderator: ['read', 'write', 'delete'],
  user: ['read', 'write'],
}

export function requirePermission(permission: string) {
  return async (request: Request) => {
    const user = await requireAuth(request)
    if (!rolePermissions[user.role]?.includes(permission))
      throw new ApiError(403, 'Insufficient permissions')
    return user
  }
}
```

---

## Rate Limiting

```typescript
class RateLimiter {
  private requests = new Map<string, number[]>()

  checkLimit(id: string, max: number, windowMs: number): boolean {
    const now = Date.now()
    const recent = (this.requests.get(id) || [])
      .filter(t => now - t < windowMs)
    if (recent.length >= max) return false
    recent.push(now)
    this.requests.set(id, recent)
    return true
  }
}
```

---

## Structured Logging

```typescript
class Logger {
  log(level: string, message: string, ctx?: Record<string, unknown>) {
    console.log(JSON.stringify({
      timestamp: new Date().toISOString(), level, message, ...ctx
    }))
  }
  info(msg: string, ctx?: Record<string, unknown>) { this.log('info', msg, ctx) }
  error(msg: string, err: Error, ctx?: Record<string, unknown>) {
    this.log('error', msg, { ...ctx, error: err.message, stack: err.stack })
  }
}
```

---

## Anti-Patterns

| Don't | Do |
|-------|-----|
| `select('*')` everywhere | Select only needed columns |
| N+1 queries in loops | Batch fetch with `WHERE IN` |
| Business logic in routes | Service layer separation |
| Catch and swallow errors | Centralized error handler |
| Hardcode secrets | Environment variables |
| Skip input validation | Zod/Joi at API boundary |

---

## Checklist

- [ ] RESTful resource-based URLs
- [ ] Repository pattern separates data access
- [ ] Service layer contains business logic
- [ ] N+1 queries eliminated (batch fetching)
- [ ] Caching layer for hot data
- [ ] Centralized error handling with proper status codes
- [ ] JWT authentication with RBAC
- [ ] Rate limiting on public endpoints
- [ ] Structured JSON logging
- [ ] Input validation at API boundary
