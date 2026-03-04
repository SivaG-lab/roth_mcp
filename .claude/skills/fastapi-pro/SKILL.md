---
name: fastapi-pro
description: >
  Build high-performance async APIs with FastAPI, SQLAlchemy 2.0, and
  Pydantic V2. Covers async patterns, dependency injection, middleware,
  WebSockets, testing, and production deployment. Use when building FastAPI
  services, designing async APIs, or optimizing Python web applications.
  Triggers: fastapi, async api, pydantic, sqlalchemy async, uvicorn,
  python api, fastapi websocket, fastapi middleware.
user-invokable: true
argument-hint: "<FastAPI endpoint, pattern, or architecture task>"
metadata:
  model: opus
---

# FastAPI Pro

High-performance, async-first API development with modern Python patterns.

## When to Use

- Building REST or GraphQL APIs with FastAPI
- Implementing async database access (SQLAlchemy 2.0, Motor)
- Designing WebSocket or SSE real-time endpoints
- Adding authentication, rate limiting, or middleware
- Optimizing FastAPI performance for production

## When NOT to Use

- Node.js/Express backends (use backend-patterns)
- General Python development (use python-pro)
- Django or Flask projects

---

## Core Patterns

### Async Endpoint with Dependency Injection

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

@app.get("/items/{item_id}")
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    return item
```

### Pydantic V2 Models

```python
from pydantic import BaseModel, Field, ConfigDict

class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    tags: list[str] = []

class ItemCreate(ItemBase):
    pass

class ItemResponse(ItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
```

### Middleware & Lifespan

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB pool, cache, etc.
    await init_db()
    yield
    # Shutdown: cleanup
    await close_db()

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = uuid4().hex
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response
```

### Authentication (JWT + OAuth2)

```python
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = await get_user(payload["sub"])
        if not user:
            raise HTTPException(401, "User not found")
        return user
    except JWTError:
        raise HTTPException(401, "Invalid token")
```

### WebSocket Endpoint

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    async def broadcast(self, message: str):
        for conn in self.connections:
            await conn.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.connections.remove(ws)
```

---

## Database (SQLAlchemy 2.0 Async)

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@host/db",
    pool_size=20,
    max_overflow=10,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Repository pattern
class ItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: int) -> Item | None:
        return await self.session.get(Item, id)

    async def list(self, limit: int = 20, offset: int = 0) -> list[Item]:
        result = await self.session.execute(
            select(Item).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
```

---

## Testing

```python
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_get_item(client: AsyncClient):
    response = await client.get("/items/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Item"
```

---

## Production Deployment

```bash
# Uvicorn with Gunicorn (production)
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120

# Docker multi-stage
FROM python:3.12-slim AS builder
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY . /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Sync `def` for I/O endpoints | `async def` with async drivers |
| Create DB session per query | Use `Depends()` with session factory |
| Return SQLAlchemy models directly | Use Pydantic response models |
| Skip input validation | Pydantic models with Field constraints |
| Blocking calls in async handlers | Use `run_in_executor` for sync libs |
| Hardcode config values | `pydantic-settings` with `.env` |

---

## Checklist

- [ ] All I/O endpoints use `async def`
- [ ] Pydantic V2 models for request/response
- [ ] Dependency injection for DB sessions and auth
- [ ] Lifespan handler for startup/shutdown
- [ ] Structured error handling with HTTPException
- [ ] Request ID middleware for tracing
- [ ] Async tests with httpx + pytest-asyncio
- [ ] Production: Gunicorn + Uvicorn workers
- [ ] Health check endpoint (`/health`)
- [ ] OpenAPI docs auto-generated and accurate
