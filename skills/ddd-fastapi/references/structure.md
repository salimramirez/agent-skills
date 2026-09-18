# Project structure

The tree of a project, the module table, and what each layer may import.

## One package per bounded context, four layers inside

Every bounded context is a top-level package next to `main.py`, and every one of them has the same four layers. Inside each layer there is **one module per kind of thing** — not one file per class. A context with one aggregate has one `entities.py`; a context with three aggregates still has one `entities.py`, until it grows past a few hundred lines and is split into a package of the same name (`entities/__init__.py` re-exporting what it holds), so that no import changes.

```
quickbite-platform/                       the project root
├── main.py                               FastAPI app, routers, exception handlers, lifespan
├── pyproject.toml
├── alembic.ini
├── alembic/
│   ├── env.py                            imports every context's infrastructure.models
│   └── versions/                         one migration per schema change
├── .env                                  local settings, never committed (.env.example is)
├── ordering/                             a bounded context
│   ├── __init__.py                       what the context owns, in two sentences
│   ├── domain/
│   │   ├── entities.py                   Order (aggregate root), OrderLine
│   │   ├── value_objects.py              OrderStatus, CustomerId, Money
│   │   ├── events.py                     OrderPlaced, OrderCancelled
│   │   ├── exceptions.py                 OrderNotFoundError, CustomerNotFoundError
│   │   ├── repositories.py               OrderRepository (the port, an ABC)
│   │   └── services.py                   domain services, only when a rule spans aggregates
│   ├── application/
│   │   ├── services.py                   OrderApplicationService
│   │   ├── event_handlers.py             reactions to events, and register_event_handlers()
│   │   └── acl.py                        ExternalCustomerService, when this context consumes another
│   ├── infrastructure/
│   │   ├── models.py                     OrderModel, OrderLineModel (SQLAlchemy)
│   │   └── repositories.py               SqlAlchemyOrderRepository
│   └── interfaces/
│       ├── routes.py                     router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])
│       ├── schemas.py                    OpenOrderRequest, OrderResponse, …
│       ├── dependencies.py               get_order_service, OrderServiceDep
│       └── acl.py                        <Context>ContextFacade, when this context is a provider
├── customers/                            another bounded context, same shape
├── iam/                                  the identity context, same shape (see iam.md)
└── shared/                               the shared kernel — see shared-kernel.md
    ├── domain/                           entities.py (AggregateRoot), events.py, exceptions.py
    ├── application/                      unit_of_work.py, events.py (EventBus)
    ├── infrastructure/                   settings.py, database.py, models.py (Base)
    └── interfaces/                       exception_handlers.py, schemas.py
```

Only the modules a context needs exist: no empty `services.py` in a domain without domain services, no `acl.py` in a context nobody consults. Every package has an `__init__.py` with a one-line docstring naming the layer and the context; the context's own `__init__.py` says what it owns.

Two things about the tree that are decisions, not accidents:

- **The contexts sit next to `main.py`, not under an `app/` package.** Each one is a top-level import (`from ordering.domain.entities import Order`), which keeps the context name at the front of every import line — reading the imports of a module tells you which contexts it touches. `fastapi dev main.py` and Alembic (`prepend_sys_path = .`) both run from the root.
- **The routes module is `routes.py`.** In FastAPI a "service" is something else; the module that holds the `APIRouter` is named after it.

## Module and class names

| Kind | Module | Class or name | Example |
| --- | --- | --- | --- |
| Aggregate root, entity | `domain/entities.py` | the noun | `Order`, `OrderLine` |
| Value object, enum | `domain/value_objects.py` | the noun | `Money`, `CustomerId`, `OrderStatus` |
| Domain event | `domain/events.py` | past tense | `OrderPlaced` |
| Domain exception | `domain/exceptions.py` | `…Error` | `OrderNotFoundError` |
| Repository port | `domain/repositories.py` | `<Aggregate>Repository` | `OrderRepository` |
| Domain service | `domain/services.py` | what it decides | `DeliveryFeePolicy` |
| Application service | `application/services.py` | `<Aggregate>ApplicationService` | `OrderApplicationService` |
| Event handler | `application/event_handlers.py` | a verb | `notify_kitchen` |
| Outbound ACL | `application/acl.py` | `External<Context>Service` | `ExternalCustomerService` |
| ORM model | `infrastructure/models.py` | `<Thing>Model` | `OrderModel`, `OrderLineModel` |
| Repository adapter | `infrastructure/repositories.py` | `SqlAlchemy<Aggregate>Repository` | `SqlAlchemyOrderRepository` |
| Router | `interfaces/routes.py` | `router` | `router`, or `<purpose>_router` when a context has several |
| Request / response | `interfaces/schemas.py` | `<Action><Thing>Request`, `<Thing>Response` | `OpenOrderRequest`, `OrderResponse` |
| Wiring | `interfaces/dependencies.py` | `get_<aggregate>_service`, `<Aggregate>ServiceDep` | `OrderServiceDep` |
| Inbound facade | `interfaces/acl.py` | `<Context>ContextFacade` | `CustomersContextFacade` |
| Table | — | plural snake_case | `orders`, `order_lines` |
| Path | — | `/api/v1/` + plural kebab-case | `/api/v1/menu-items` |

The `Model` suffix is what lets `Order` and `OrderModel` live in the same repository module without an alias. The `Request`/`Response` suffixes are what keep a schema from ever being mistaken for the entity.

## What each layer may import

Dependencies point inward: `interfaces` and `infrastructure` know `application` and `domain`; `application` knows `domain`; `domain` knows nothing outside itself and `shared.domain`.

| Layer | Holds | Imports | Never imports |
| --- | --- | --- | --- |
| `domain` | aggregates, entities, value objects, events, exceptions, repository ports, domain services | the standard library, `shared.domain` | `fastapi`, `pydantic`, `sqlalchemy`, another context |
| `application` | application services, event handlers, outbound ACL services | its own `domain`, `shared.domain`, `shared.application`, another context's `interfaces.acl` (only from `acl.py`) | `fastapi`, `sqlalchemy`, its own `infrastructure` |
| `infrastructure` | ORM models, repository adapters, clients for the outside world | `sqlalchemy`, its own `domain` and `application` ports, `shared.infrastructure` | `fastapi`, another context's anything |
| `interfaces` | routes, schemas, dependency wiring, the inbound facade, the context's exception handler | everything of its own context, `fastapi`, `pydantic`, `shared` | another context's `domain` or `infrastructure` |

`interfaces/dependencies.py` is the only module outside `infrastructure` that names an adapter class: it is where the ports meet their implementations. The one cross-context import in each direction is through an ACL — see `anti-corruption-layer.md` — and `iam.interfaces.dependencies`, which every context's router uses to authenticate a request.

A quick check for the rule that matters most:

```bash
grep -rnE "^(from|import) (fastapi|pydantic|sqlalchemy)" */domain/
```

It should print nothing.
