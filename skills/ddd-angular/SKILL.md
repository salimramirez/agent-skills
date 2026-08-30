---
name: ddd-angular
description: Structure an Angular frontend with Domain-Driven Design: bounded-context feature folders, a domain layer of entities and commands, DTOs and assemblers as an anti-corruption layer against the backend API, signal stores, and a presentation layer of views and components. Use when organizing or refactoring an Angular app by business domain rather than by technical type, isolating API contracts from the app's own model, or deciding where business logic belongs on the frontend. It carries the DDD design rules it depends on, so it works on its own. Not for styling, Angular framework how-to, or backend domain modeling.
license: MIT
metadata:
  version: "1.0.0"
  author: Copyright 2026 Salim Ramirez
---

# DDD in Angular

Structure an **Angular** app around a domain. Start with the honest part below — DDD on the frontend is *adapted*, not the same as on the backend — and then apply the structure and idioms in the references. Examples use the **QuickBite** food-delivery domain (an `ordering` feature). Idioms follow the Angular 20+ style (standalone components, signals, `inject()`) and apply unchanged on Angular 21 and 22.

> **Angular 22 note.** Everything here stays supported; v22 only *adds* modern alternatives you can opt into without changing this structure: **`@Service()`** as a shorter form of `@Injectable({ providedIn: 'root' })` (root-provided, `inject()`-only) for stores and context APIs; **Signal Forms** alongside the reactive forms shown here; and **`resource()` / `httpResource()`** as a signal-native data-fetching option in place of the manual `subscribe` in the store. Signals also pair naturally with OnPush — the default change detection from v22.

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
- **Loosens:** repositories are API endpoints rather than aggregate stores; aggregates and value objects are lighter or skipped (the UI rarely needs them); "domain events" are usually signal/observable updates.
- **Doesn't apply:** authoritative invariants and transactional consistency — those belong to the backend. Client-side checks are UX, and the server validates again.

## Implementation references

Read the file that matches the task at hand.

**Laying out the app**

- **Folder structure** — bounded contexts as feature folders, and the four layers inside each. Read [structure.md](references/structure.md)
- **The shared kernel** — the base classes and app-wide pieces every context reuses. Read [shared-kernel.md](references/shared-kernel.md)

**Modeling the domain**

- **Entities and commands** — entities as classes with private fields and accessors; commands for non-CRUD intents. Read [domain-model.md](references/domain-model.md)

**Talking to the backend**

- **DTOs, assemblers, endpoints, and the context API** — the API boundary, with assemblers as the anti-corruption layer. Read [infrastructure.md](references/infrastructure.md)

**Holding state**

- **The signal store** — per-operation loading and error state, and how a store talks to its context API. Read [state-store.md](references/state-store.md)

**Building the UI**

- **Views, components, and routing** — routed smart views, reusable dumb components, and per-context lazy routes. Read [presentation.md](references/presentation.md)
- **Reactive forms and writes** — building an entity from a form for CRUD, and the command path for everything else. Read [forms.md](references/forms.md)

For Angular questions the references do not cover, read the documentation at `https://angular.dev`.

For the strategic side — discovering the domain, finding bounded contexts, EventStorming, context mapping — use the `ddd-playbook` skill. For the backend that owns the invariants, use `ddd-spring-boot`.
