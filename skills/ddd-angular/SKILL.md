---
name: ddd-angular
description: Structure an Angular frontend with Domain-Driven Design — bounded-context feature folders, a domain layer of entities and commands, DTOs and assemblers as an anti-corruption layer against the backend API, signal stores, and a presentation layer of views and components. Use when organizing or refactoring an Angular app by business domain rather than by technical type, isolating API contracts from the app's own model, or deciding where business logic belongs on the frontend. It carries the DDD design rules it depends on, so it works on its own. Not for styling, Angular framework how-to, or backend domain modeling.
license: MIT
metadata:
  version: "1.1.0"
  author: Copyright 2026 Salim Ramirez
---

# DDD in Angular

Structure an **Angular** app around a domain. Start with the honest part below — DDD on the frontend is *adapted*, not the same as on the backend — then apply the structure and the idioms in the references.

This is an **opinionated** house style: for every decision it names one convention and says what that convention buys, rather than listing options. It is one coherent way to do this, not the only correct one; where a choice is genuinely open, the reference says so. Examples use the **QuickBite** food-delivery domain, in an `ordering` bounded context.

The idioms are standalone components, signals, and `inject()`. They work unchanged across current Angular versions; newer releases add alternatives — a signal-based forms API, signal-native data fetching, shorter service decorators — that you can adopt without changing anything about the structure here.

## What DDD means on the frontend

The backend is the **system of record**: it owns the business rules, the invariants, and the transactional consistency. The frontend cannot enforce those — a determined user can bypass any client-side check — so it should not pretend to.

What the frontend *does* gain from DDD is **structure**: organizing the app by the domain (not by technical type), speaking the same **ubiquitous language** as the backend and the experts, keeping a client-side model of the domain separate from the UI, and pushing logic out of components. So treat what follows as **DDD-inspired organization**, not as a place to re-enforce business rules.

<!-- ddd:core:start -->

## Prime directive: model the domain, and protect it

- Put business rules and invariants **inside the domain model itself**, not scattered across controllers, services, or SQL. A model that only holds data while the logic lives elsewhere is an *anemic domain model* — the most common DDD failure, and the main thing this skill exists to prevent.
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

## What carries over, loosens, or doesn't apply

- **Carries over:** the ubiquitous language; bounded contexts; the four-layer split with an isolated domain; anti-corruption via assemblers; keeping logic out of the UI.
- **Loosens:** repositories are API endpoints rather than aggregate stores; aggregates and value objects are lighter or skipped (the UI rarely needs them); "domain events" are usually signal updates.
- **Doesn't apply:** authoritative invariants and transactional consistency — those belong to the backend. Client-side checks are UX, and the server validates again.

## The house style in one screen

The rules this skill applies by default. Each one is expanded, with its reason, in the reference that owns it.

- **A bounded context is a feature folder** under `src/app/`, with `domain/`, `application/`, `infrastructure/`, and `presentation/` inside it. `shared/` is the kernel and stays small.
- **One store per context**, named after the context (`OrderingStore`), not per entity and not one for the app.
- **The store is the only thing that calls the context API**; only an endpoint touches `HttpClient`. A view calls its store, and that is the whole chain.
- **Entities are classes** in `*.entity.ts` — private fields, accessors, one options-object constructor, `implements BaseEntity`. A setter exists only where the UI genuinely changes the value.
- **Other aggregates are referenced by id.** A resolved object is stitched in by the store, and the id stays the source of truth.
- **The resource never leaves `infrastructure/`.** Assemblers are the anti-corruption layer; a snake_case field in a template means one was skipped.
- **CRUD writes send the entity; everything else sends a command.** A command is a class with no id, and it travels through its own request DTO.
- **State is private signals published read-only**, with `computed()` for anything derived. Reads use `takeUntilDestroyed`, writes use `retry(2)`, and every call sets `loading` and clears it in both branches.
- **Views are smart and routed; components are dumb and reusable** — `input()` in, `output()` out, and a dumb component never sees the store.
- **Every context owns its routes** and lazy-loads its views; the root router mounts contexts with `loadChildren`.
- **URLs are composed from `environment`**, one base URL per provider plus one path per endpoint — never a literal in an endpoint.
- **Classes, interfaces, and public methods carry JSDoc.** The domain layer is where the ubiquitous language gets written down.

## Implementation references

Read the file that matches the task at hand.

**Starting a piece of work**

- **Adding a resource end to end** — the nine files in order, plus the checklist to finish on. Start here for "add X to the app". Read [adding-a-resource.md](references/adding-a-resource.md)
- **Folder structure, naming, and environment** — contexts and layers, the file-to-class naming table, and where URLs come from. Read [structure.md](references/structure.md)
- **House style** — the JSDoc rule, member ordering, and the layer smells to avoid. Read [house-style.md](references/house-style.md)
- **The shared kernel** — the seven base classes every context builds on. Read [shared-kernel.md](references/shared-kernel.md)

**Modeling the domain**

- **Entities and commands** — entities as classes with accessors, value objects, and commands for non-CRUD intents. Read [domain-model.md](references/domain-model.md)

**Talking to the backend**

- **The CRUD path** — DTOs, assemblers, endpoints, and the context API. Read [infrastructure.md](references/infrastructure.md)
- **Commands and actions** — the non-CRUD path, and integrating an API that is not yours. Read [commands-and-actions.md](references/commands-and-actions.md)

**Holding state**

- **The signal store** — signals and computed queries, loading and error handling, stitching, and caching. Read [state-store.md](references/state-store.md)

**Building the UI**

- **Views, components, and routing** — the smart/dumb split, per-context lazy routes, and the app shell. Read [presentation.md](references/presentation.md)
- **Reactive forms and writes** — one view for create and edit, validation as UX, entity or command. Read [forms.md](references/forms.md)
- **Cross-cutting concerns** — guards and interceptors in the context that owns the rule, localization, and app bootstrap. Read [cross-cutting.md](references/cross-cutting.md)

## Copy instead of retyping

Two things ship as code, because they should come out the same every time:

- **`assets/shared-kernel/`** — the seven base files (`base-entity`, `base-response`, `base-assembler`, `error-handling-enabled-base-type`, `base-api-endpoint`, `base-api`, `base-form`). Copy them into `src/app/shared/` as they are; do not paraphrase them from the docs.
- **`scripts/new-context.py`** — scaffolds a whole bounded context wired for one CRUD aggregate, deriving every spelling of the name from two arguments:

  ```bash
  python3 scripts/new-context.py --context ordering --entity Order --into src/app
  ```

  Add `--dry-run` to see what it would write, `--plural People` when the naive plural is wrong. It prints the two edits it cannot make for you: the `environment` keys and the route in `app.routes.ts`. What it writes is ordinary code — read it, then model the real aggregate.

For Angular questions the references do not cover, read the documentation at `https://angular.dev`.

For the strategic side — discovering the domain, finding bounded contexts, EventStorming, context mapping — use the `ddd-playbook` skill. For the backend that owns the invariants, use `ddd-spring-boot`.
