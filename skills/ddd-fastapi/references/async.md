# Async

What is `async`, what never is, and the one mistake that stalls every request at once.

## The rule: async at the edges, sync in the middle

| Layer | `async`? | Why |
| --- | --- | --- |
| `interfaces` — routes, dependencies | yes, even a dependency that awaits nothing | FastAPI runs a `def` route or dependency in the thread pool, an `async def` one on the event loop |
| `application` — services, event handlers | yes | they await the repository and the other ports |
| `infrastructure` — repositories, clients | yes | they do the I/O |
| `domain` — entities, value objects, domain services | **never** | a rule does not wait for anything |
| `domain/repositories.py` — the ports | the methods are `async def` | the signature says the implementation does I/O; nothing in the domain calls them |

An aggregate that needs data to decide something gets it as an argument — the application service loads it first — instead of loading it itself. That keeps every rule a plain, synchronous, testable method.

## What `async def` buys, and what it costs

FastAPI runs an `async def` route on the event loop, and a plain `def` route in a thread pool. Both handle concurrent requests; they fail differently.

Measured with five concurrent requests to a route that waits one second, and an unrelated `/ping` sent meanwhile:

| The route does | 5 requests take | `/ping` meanwhile waits |
| --- | --- | --- |
| `async def` + `await asyncio.sleep(1)` | 1.0 s | 0.006 s |
| `def` + `time.sleep(1)` (thread pool) | 1.0 s | 0.003 s |
| `async def` + `time.sleep(1)` | **5.0 s** | **5.0 s** |

The third row is the trap. A blocking call inside `async def` does not block one request; it blocks the event loop, and with it **every** request the process is serving, including the ones that have nothing to do with it. It survives testing because one request at a time looks fine.

This skill uses `async def` throughout because the database driver is async (`asyncpg`) and the session is `AsyncSession`: every wait for PostgreSQL releases the loop to other requests. The price is the rule above — inside `async def`, everything that waits must be awaited.

## What blocks, and what to do with it

| Blocking | Instead |
| --- | --- |
| a synchronous database driver or `Session` | `AsyncSession` and an async driver (`asyncpg`) — the kernel already does this |
| `requests`, `urllib` | `httpx.AsyncClient`, awaited |
| `time.sleep` | `await asyncio.sleep` |
| `open(...).read()` on a large file | `await asyncio.to_thread(path.read_bytes)` |
| CPU-heavy work: password hashing, image resizing, a big computation | `await asyncio.to_thread(function, *args)` |
| a library that only has a sync API | wrap each call in `asyncio.to_thread` |

Ruff's `ASYNC` rules (enabled in the project's `pyproject.toml`) catch the first kind: they flag `time.sleep`, `requests` and `open` inside `async def`. They **do not** catch CPU-bound calls. Hashing is the case this project actually has: measured with twenty concurrent Argon2 hashes, an unrelated request waited 0.54 s with the hash on the loop and 0.08 s with it in a thread. That is why the IAM context's hashing adapter runs `pwdlib` through `asyncio.to_thread`:

```python
class Argon2HashingService(HashingService):
    def __init__(self) -> None:
        self._hasher = PasswordHash.recommended()

    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(self._hasher.hash, password)

    async def verify(self, password: str, password_hash: str) -> bool:
        return await asyncio.to_thread(self._hasher.verify, password, password_hash)
```

The port is `async` for the same reason a repository is: the caller should not have to know that the implementation needs a thread.

## Two things an async session will not do for you

Both fail with the same error, `sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called`, which says nothing about the cause. Both are measured.

**It will not refresh an object after a commit.** With the default `expire_on_commit=True`, a commit expires every loaded object, and the next attribute read triggers a refresh — an implicit query, which an async session cannot run implicitly. The kernel's session factory sets it off:

```python
session_factory = async_sessionmaker(engine, expire_on_commit=False)
```

**It will not lazy-load a relationship.** Touching `order_model.lines` when the lines were not loaded is the same implicit query. The house style never gives it the chance: a collection that belongs to the aggregate is declared with `lazy="selectin"`, so every load of the root loads its parts in the same `await`:

```python
lines: Mapped[list["OrderLineModel"]] = relationship(
    cascade="all, delete-orphan", lazy="selectin", order_by="OrderLineModel.id"
)
```

This is also the DDD answer: an aggregate is loaded whole or not at all. See `persistence.md`.

## Event loop etiquette in the rest of the code

- **Do not create an event loop.** No `asyncio.run` inside the application; FastAPI owns the loop. (`alembic/env.py` does call `asyncio.run` — it is a separate process.)
- **Do not share an `AsyncSession` between concurrent tasks.** One session per request, from `get_session`; `asyncio.gather` over two queries on the same session raises.
- **Background work that must survive the request** is not a `asyncio.create_task` fired from a route — nothing keeps a reference to it, and if it fails the only trace is a `Task exception was never retrieved` log line, printed whenever the task happens to be garbage-collected. For short follow-ups use FastAPI's `BackgroundTasks`; for anything that matters, a queue.
