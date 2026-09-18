# Adding a resource, end to end

The order to write the files in, and what to check when you are done.

Use this when the task is "add X to the platform" — a new bounded context, or a new aggregate inside one. Work outward from the domain: each step depends only on the ones before it, so nothing is written twice.

## Before writing anything

1. **Name it in the ubiquitous language.** Ask what the domain experts call it. `Order`, not `Purchase` and not `Transaction`. Every class, module, table and path comes from this answer.
2. **Decide which bounded context it belongs to.** A new context if it has its own model and language; otherwise a new aggregate inside an existing one. When in doubt, ask whether it would share an application service with what is already there.
3. **Decide what is inside the aggregate and what is only referenced.** Lines are inside an order (`OrderLine`, reached through it); the customer is not (`CustomerId`, reached through the ACL). Getting this wrong is the expensive mistake — everything else is renaming.

## Scaffold, then model

For a new context, generate the tree instead of typing it:

```bash
SKILL=.claude/skills/ddd-fastapi       # wherever this skill was installed
python3 "$SKILL/scripts/new-context.py" --context ordering --entity Order
```

Run it from anywhere inside the project: it finds the root by the nearest `pyproject.toml` above the current directory, and writes the fourteen files of a CRUD aggregate under `ordering/`, next to `main.py`. It prints the three edits it cannot make: the router in `main.py`, the models import in `alembic/env.py`, and the migration. The naming — PascalCase and snake_case, singular and plural, class, module, function, table and path — is the error-prone part, and it is the part that is now done. `--plural People` fixes a plural the naive rule gets wrong.

Install the shared kernel first if `shared/` is not there yet: `python3 "$SKILL/scripts/install.py" shared-kernel`. See `shared-kernel.md`.

For a new aggregate in an existing context, copy the shape of the one already there, module by module, into the same files.

## The files, in the order to write them

| # | File | What to write |
| --- | --- | --- |
| 1 | `domain/value_objects.py` | Every concept with a rule and no identity — `Money`, `OrderStatus` — and the references to other aggregates — `CustomerId`. See `value-objects.md`. |
| 2 | `domain/entities.py` | The root with the real attributes and the **behavior**: `add_line()`, `place()`, `cancel()`. Every rule about an order is a method here. Then the entities inside it, `OrderLine`. See `aggregates.md`. |
| 3 | `domain/events.py` | One frozen dataclass per fact other code must react to. See `domain-events.md`. |
| 4 | `domain/exceptions.py` | `OrderNotFoundError` and whatever else has a name. See `exceptions.md`. |
| 5 | `domain/repositories.py` | The port: `save`, `find_by_id`, and the finders the use cases need, taking value objects. |
| 6 | `infrastructure/models.py` | The tables: one model for the root with `AuditableModel`, one per inner entity, the collection with `cascade="all, delete-orphan", lazy="selectin"`. See `persistence.md`. |
| 7 | `alembic/env.py`, then a migration | Import the models, `alembic revision --autogenerate`, **read** the file, `alembic upgrade head`. |
| 8 | `infrastructure/repositories.py` | The adapter: `save` as `merge` + `flush`, the finders, `_to_model` and `_to_entity`. |
| 9 | `application/acl.py` | Only if this context needs another one. See `anti-corruption-layer.md`. |
| 10 | `application/services.py` | One method per use case: build value objects, check, load, act, save, commit, publish. No rules. See `application-services.md`. |
| 11 | `application/event_handlers.py` | One `async` function per reaction, and `register_event_handlers`. |
| 12 | `interfaces/schemas.py` | One request per use case that takes a body, checking shape only; one response with `from_entity`. |
| 13 | `interfaces/dependencies.py` | `get_<aggregate>_service` and the `<Aggregate>ServiceDep` alias. |
| 14 | `interfaces/routes.py` | Thin routes: one service call, one response, `responses=error_responses(...)` from the service's `Raises:`. See `rest.md`, `state-transitions.md`. |
| 15 | `main.py` | `include_router`, with `dependencies=authenticated` unless the router is public; `register_event_handlers` in `lifespan` if step 11 exists. |

Then, only if the context is a provider for others: `interfaces/acl.py` with its facade.

Apply the migration at step 7 already: a mapping mistake — a wrong type, a missing foreign key, a model that was never imported — shows up there, before there is a route to debug through.

## Check it running

```bash
fastapi dev main.py
```

Open `/docs`, authorize with a token from sign-in, and walk the use cases in order: create, read, each transition, each failure. Every error the service can raise should come back with its status and a `detail` a client could show.

## Checklist

Before calling it done:

- [ ] Every name reads in the ubiquitous language — no `Data`, `Info`, `Manager`, `Helper`, `Util`.
- [ ] The aggregate has **behavior**; its state is private and read through properties. Any `if` on its state in a service belongs in one of its methods.
- [ ] Other aggregates are held as `XxxId` value objects, never as objects, and never as a foreign key to another context's table.
- [ ] Every value object validates in `__post_init__` and raises `DomainError`, never `ValueError`.
- [ ] `grep -rnE "^(from|import) (fastapi|pydantic|sqlalchemy)" <context>/domain/` prints nothing.
- [ ] The service imports ports, not adapters; every method that changes state commits exactly once; events are pulled before `save` and published after `commit`.
- [ ] The repository returns aggregates, never models, and its mapping has no conditions.
- [ ] Every route is one service call and one `from_entity`; no route catches a domain exception.
- [ ] The router is plural, under `/api/v1/`, tagged, included in `main.py` with authentication unless it is public.
- [ ] The migration was read before it was applied, and is committed with the models.
- [ ] `ruff check .` and `mypy .` pass.
