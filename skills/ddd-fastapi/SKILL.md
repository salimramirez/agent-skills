---
name: ddd-fastapi
description: Write Domain-Driven Design code in FastAPI / Python — bounded contexts as packages with four layers, aggregates as plain classes with behavior, value objects as frozen dataclasses, application services, repository ports with async SQLAlchemy adapters and Alembic migrations, domain events, anti-corruption layers, and the REST interface with Pydantic schemas. Use when implementing or refactoring a FastAPI service around business rules, structuring a new bounded context in Python, or pulling business logic out of route handlers into a domain model. It carries the DDD design rules it depends on, so it works on its own. Not for FastAPI configuration, deployment, or framework questions unrelated to domain modeling.
license: MIT
metadata:
  version: "1.0.0"
  author: Copyright 2026 Salim Ramirez
---

# DDD in FastAPI

Write the actual code for a Domain-Driven Design model in **FastAPI / Python**. The core rules below say *what* the building blocks are and when to reach for each; the references say *how to express them idiomatically* in FastAPI, and the assets and scripts write the parts that should come out the same every time.

This is an **opinionated** house style: for every decision it names one convention and says what that convention buys, rather than listing options. It is one coherent way to do this, not the only correct one; where a choice is genuinely open, the reference says so. Python leaves more to taste than Java does, and the house style respects that: it fixes the decisions that make every bounded context look alike — where a file goes, what it is called, which layer may import which — and leaves the rest to the code in front of it. Examples use the **QuickBite** food-delivery domain — an `Order` in the `ordering` bounded context, a `Customer` in `customers`.

The idioms are FastAPI with `async` routes, Pydantic v2 for the request and response schemas and the settings, SQLAlchemy 2 with its asyncio extension over PostgreSQL (`asyncpg`), Alembic for the schema, and plain Python — classes and frozen dataclasses — for the domain. The shipped code targets **Python 3.12+** and was run on 3.12 and 3.13, from the lowest versions `pyproject.toml` allows (FastAPI 0.122, SQLAlchemy 2.0.0, Alembic 1.16) to the current ones. The one floor that is behavior and not just API: before FastAPI 0.122, a request with no bearer token was answered **403**, not 401.

<!-- ddd:core:start -->

## Prime directive: model the domain, and protect it

- Put business rules and invariants **inside the domain model itself**, not scattered across controllers, services, or SQL. A model that only holds data while the logic lives elsewhere is an *anemic domain model* — the most common DDD failure, and the main thing DDD exists to prevent.
- Speak the **ubiquitous language**: use the exact terms domain experts use, in the code (class, method, variable names) and in conversation. If the business says "policy", the class is `Policy`, not `InsuranceRecord`. A gap between code and language is a defect waiting to happen.
- Keep the **domain pure**: the domain layer expresses business concepts and must not depend on frameworks, persistence, web, or messaging concerns. Those belong at the edges.

## Layered architecture (4 layers)

Organize code into four layers. Dependencies point **inward**, toward the domain; the domain depends on nothing outside itself.

1. **Interfaces** — the **inbound adaptors**: entry points where the outside world drives the context (REST/GraphQL controllers, CLI, message/event listeners, schedulers). Translate external input into application calls and the result back out. No business logic.
2. **Application** — orchestrates use cases (application services, often split into **command services** and **query services**): loads aggregates, invokes domain behavior, manages transactions and security. Coordinates, but holds **no business rules** itself.
3. **Domain** — the heart: entities, value objects, aggregates, domain events, domain services, and the repository and service *interfaces* (**ports**). All business rules and invariants live here. Depends on nothing but itself.
4. **Infrastructure** — the **outbound adaptors**: the technical implementations the context uses to reach the outside (persistence/ORM and repository implementations, messaging, external API clients). Implements the ports the inner layers declare.

The inner layers declare **ports** (interfaces) and the adaptors implement them — an *inbound* adaptor brings a request into the context, an *outbound* adaptor lets it reach out. This is the classic DDD layered model; it does **not** require hexagonal, onion, or "clean" architecture — those are compatible refinements, but the non-negotiables are domain purity and the inward dependency rule.

## Bounded contexts

A **bounded context** is an explicit boundary within which a model and its ubiquitous language stay consistent. The same word can mean different things in different contexts (a "Customer" in Sales ≠ in Support); don't force one model across the whole system.

## Tactical building blocks — how to decide

When modeling, choose the right block deliberately:

- **Value Object** — no identity; defined entirely by its attributes; immutable. Use liberally: money, date ranges, addresses, quantities, identifiers. Prefer a value object over a primitive whenever a concept carries rules (e.g., `Money` bundles amount + currency and forbids mixing currencies). They make invalid states unrepresentable.
- **Entity** — has a distinct identity that persists through changes to its attributes (a `Customer` stays the same customer even if their name changes). Use when identity and a lifecycle matter.
- **Aggregate** — a cluster of entities and value objects treated as one consistency unit, accessed only through its **aggregate root**. Key rules, each with a reason:
  - Keep aggregates **small** — large ones cause contention and load too much data.
  - One aggregate = **one transaction**. Don't modify two aggregates in the same transaction; it couples their consistency.
  - Reference **other aggregates by identity (ID)**, never by holding their object — this keeps boundaries and transactions clean.
  - Enforce the aggregate's invariants inside the root, so it is always internally consistent.
- **Domain Event** — a statement that something meaningful happened in the domain (e.g., `OrderPlaced`). Use it to achieve **eventual consistency across aggregates** and to decouple side effects from the action that caused them.
- **Domain Service** — stateless domain logic that doesn't naturally belong to a single entity or value object (e.g., a transfer between two accounts). Keep it in the domain layer; don't confuse it with an application service.
- **Repository** — collection-like access to aggregates by their root. Define **one repository per aggregate root**, with the interface in the domain layer and the implementation in infrastructure.
- **Factory** — encapsulates complex creation of an aggregate or value object when a plain constructor would be unclear or would leak rules.

## CQRS

Command Query Responsibility Segregation separates the model that **changes** state (commands) from the model that **reads** it (queries). It comes in two strengths, and conflating them is a common source of over-engineering:

- **The light form** — split the application layer along the command/query line (command services and query services). One model, one store, no eventual consistency. It is cheap, it keeps write orchestration from tangling with read orchestration, and it is a reasonable default.
- **The full form** — give each side its own *model*: a write model (the aggregates, enforcing invariants) and a separate read model shaped for how the data is queried, kept up to date from domain events. It buys queries that span aggregates and independent scaling; it costs projection machinery and eventual consistency. Treat it as a deliberate choice per bounded context, not a default.

## How to approach a DDD task

1. **Establish the language** — clarify the domain terms with the user; use them verbatim in the model.
2. **Locate the bounded context** — which context are we in, and what is its model?
3. **Find the aggregates and their invariants** — what must always be true, and what is the consistency boundary?
4. **Model tactically** — choose value objects, entities, and aggregate roots; push rules into them; keep the domain pure.
5. **Place each piece in the right layer** — rules in domain, orchestration in application, I/O in interfaces, technical detail in infrastructure.
6. **Implement for the stack** — follow the stack's implementation idioms; see the routing below.

<!-- ddd:core:end -->
## The house style in one screen

The rules this skill applies by default. Each one is expanded, with its reason, in the reference that owns it.

- **A bounded context is a top-level package** next to `main.py`, with `domain/`, `application/`, `infrastructure/` and `interfaces/` inside it, and **one module per kind** in each: `entities.py`, `value_objects.py`, `repositories.py`, `services.py`, `models.py`, `schemas.py`, `routes.py`. `shared/` is the kernel and stays small.
- **The domain is plain Python.** Aggregates are classes with behavior and read-only properties; value objects are `@dataclass(frozen=True, slots=True)` validating in `__post_init__`. Nothing in `domain/` imports FastAPI, Pydantic or SQLAlchemy.
- **One application service per aggregate, one `async` method per use case** — `open_order`, `place_order`, `get_order_by_id`. It loads, asks the aggregate to act, saves, **commits through the `UnitOfWork` port**, and publishes the events. It holds no rule.
- **The repository is a port in `domain/repositories.py`** (an `ABC` with `async` methods) and an adapter in `infrastructure/repositories.py` that maps between the aggregate and **separate ORM models**. The domain never sees a model; a route never sees a repository.
- **Async at the edges, sync in the middle.** Routes, services and repositories are `async`; the domain never awaits. Anything blocking — CPU-heavy hashing, a sync client — goes to a thread.
- **The failure says what kind it is.** `DomainError` → 400, `ConflictError` → 409, `NotFoundError` → 404, from one shared handler; a context registers a handler only for an exception of its own. The body is always `{"detail": "..."}`, FastAPI's own shape.
- **Pydantic lives in `interfaces/`.** `XxxRequest` checks the shape of the input; `XxxResponse.from_entity(...)` is the only way out. The domain rules are never repeated in a schema.
- **Wiring is a dependency function per service** in `interfaces/dependencies.py`, exposed as an `Annotated` alias (`OrderServiceDep`). It is the one place that picks the adapters.
- **Another context is reached only through its facade**, in the provider's `interfaces/acl.py`, wrapped in an `External<Context>Service` in the consumer's `application/acl.py`.
- **Routers are plural, under `/api/v1/`, thin, and return a response schema.** A transition is a `POST` to a plural noun (`/orders/{order_id}/placements`) returning the updated resource.
- **Every schema change is an Alembic migration**, autogenerated and read before it is applied. Constraint names come from the naming convention in the kernel.
- **Every module, class and public function carries a Google-style docstring**; the implementation of a port method carries none, because the port documents it.

## Implementation references

The rules above are stack-agnostic. Everything below is how FastAPI expresses them. Read the file that matches the task at hand.

**Starting a piece of work**

- **Adding a resource, end to end** — the order to write the files in, the scaffold, and the checklist. Read [adding-a-resource.md](references/adding-a-resource.md)
- **Project structure** — the tree of a bounded context, the module table, and what each layer may import. Read [structure.md](references/structure.md)
- **House style** — docstrings, type hints, naming, and the smells by layer. Read [house-style.md](references/house-style.md)
- **Project setup** — `pyproject.toml`, the virtual environment with uv or pip, settings, `main.py`, PostgreSQL and the Alembic workflow. Read [project-setup.md](references/project-setup.md)
- **Async** — what is `async` and what never is, the call that stalls every request, and loading an aggregate whole. Read [async.md](references/async.md)
- **The shared kernel** — the modules every context shares, and what each is for. Read [shared-kernel.md](references/shared-kernel.md)

**Modeling the domain**

- **Value objects** — frozen dataclasses, enums, references to other aggregates, money. Read [value-objects.md](references/value-objects.md)
- **Aggregates and entities** — the root with behavior, the entities inside it, and when a domain service is right. Read [aggregates.md](references/aggregates.md)

**Orchestrating use cases**

- **Application services** — the methods, the unit of work, what each returns. Read [application-services.md](references/application-services.md)
- **Domain events** — recorded on the aggregate, published after the commit, handled in the application layer. Read [domain-events.md](references/domain-events.md)
- **Anti-corruption layer** — the facade a context exposes and the service that consumes it. Read [anti-corruption-layer.md](references/anti-corruption-layer.md)

**Reaching the outside**

- **Repositories and persistence** — ORM models, the mapping, saving an aggregate with its parts, migrations. Read [persistence.md](references/persistence.md)
- **REST** — routers, schemas, dependencies, status codes and the OpenAPI description. Read [rest.md](references/rest.md)
- **State transitions and nested resources** — placing, cancelling, adding a part, filtering a collection. Read [state-transitions.md](references/state-transitions.md)
- **Domain exceptions and error handling** — the three kinds of failure and where each becomes a status code. Read [exceptions.md](references/exceptions.md)

**Identity and access**

- **The IAM context** — sign-up, sign-in and bearer tokens as a complete, installable context, and what to adapt. Read [iam.md](references/iam.md)

## Copy instead of retyping

Four things ship as code, because they should come out the same every time.

**Run the commands from inside the project**, with `$SKILL` pointing at the directory this skill was installed into — `.claude/skills/ddd-fastapi` in a standard install, a path relative to the project root:

```bash
SKILL=.claude/skills/ddd-fastapi
```

Each script writes under the project root — the nearest directory, from the current one upward, that holds `pyproject.toml` — so it works from any directory of the project; `install.py project` is the exception and writes into the current directory, which should be a new, empty one. The scripts refuse to write inside the skill itself or outside a project, and to overwrite a file unless given `--force`. Add `--dry-run` to see what would be written, `--into` to name the root explicitly.

- **`assets/project/`** — a new project: `pyproject.toml`, `main.py`, Alembic configured for async and for the application's settings, `.env.example`, and the shared kernel:

  ```bash
  python3 "$SKILL/scripts/install.py" project --name "QuickBite Platform"
  ```

- **`assets/shared-kernel/`** — only the kernel, into a project that already exists:

  ```bash
  python3 "$SKILL/scripts/install.py" shared-kernel
  ```

- **`scripts/new-context.py`** — scaffolds a whole bounded context wired for one CRUD aggregate, deriving every spelling of the name from two arguments:

  ```bash
  python3 "$SKILL/scripts/new-context.py" --context ordering --entity Order
  ```

  Add `--plural People` when the naive plural is wrong. It prints the two lines for `main.py` and the one for `alembic/env.py`. What it writes is ordinary code — read it, then model the real aggregate; the generated one has a single `name` field as a placeholder.

- **`assets/iam-context/`** — a complete identity context: `User`, roles, sign-up, sign-in, JWT, and the dependency that protects every other router:

  ```bash
  python3 "$SKILL/scripts/install.py" iam-context
  ```

  It prints the dependencies, the settings and the `main.py` wiring to add.

For FastAPI questions the references do not cover, read the documentation at `https://fastapi.tiangolo.com/`; for SQLAlchemy, `https://docs.sqlalchemy.org/en/20/`.

For the strategic side — discovering the domain, finding bounded contexts, EventStorming, context mapping — use the `ddd-playbook` skill. For the frontend that consumes this API, use `ddd-angular`, `ddd-vue` or `ddd-react`.
