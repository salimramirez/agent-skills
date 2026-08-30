---
name: ddd-spring-boot
description: Write Domain-Driven Design code in Spring Boot / Java: the four-layer package structure, aggregate roots as JPA entities, value objects and typed ids as embeddables, command and query services, repositories, domain events, anti-corruption layers, and the REST interface with resources and assemblers. Use when implementing or refactoring a Spring Boot service around business rules, structuring a new bounded context in Java, or pulling business logic out of controllers into a domain model. It carries the DDD design rules it depends on, so it works on its own. Not for Spring configuration, security, or framework questions unrelated to domain modeling.
license: MIT
metadata:
  version: "1.0.0"
  author: Copyright 2026 Salim Ramirez
---

# DDD in Spring Boot

Write the actual code for a Domain-Driven Design model in **Spring Boot / Java**. The core rules below say *what* the building blocks are and when to reach for each; the references say *how to express them idiomatically* in Spring Boot.

No specific Spring Boot or Java version is assumed; the patterns here work on Spring Boot 3 and 4 with Java 17+ (including 21 and the 25 LTS). One caveat that does depend on the version: persistence annotations live in `jakarta.persistence.*` on Spring Boot 3 and 4 and `javax.persistence.*` on Spring Boot 2 — adjust imports accordingly. Examples use a fictional food-delivery domain, **QuickBite** (an `Order` in the Ordering context).

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

## Implementation references

The rules above are stack-agnostic. Everything below is how Spring Boot expresses them. Read the file that matches the task at hand.

**Laying out a bounded context**

- **Package structure** — the four-layer package tree and what belongs in each layer. Read [structure.md](references/structure.md)
- **The shared kernel** — base classes and types every context shares (`AuditableAbstractAggregateRoot`, `AuditableModel`, `MessageResource`). Read [shared-kernel.md](references/shared-kernel.md)

**Modeling the domain**

- **Value objects** — value objects and typed identifiers as JPA embeddables. Read [value-objects.md](references/value-objects.md)
- **Aggregates and entities** — the aggregate root as a JPA entity with real behavior and enforced invariants. Read [aggregates.md](references/aggregates.md)

**Orchestrating use cases**

- **Commands, queries, and their services** — commands and queries as records, and the command and query services that execute them. Read [application-services.md](references/application-services.md)
- **Domain events** — raising events from an aggregate and handling them in the application layer. Read [domain-events.md](references/domain-events.md)
- **Anti-corruption layer** — reaching another bounded context through a facade. Read [anti-corruption-layer.md](references/anti-corruption-layer.md)

**Reaching the outside**

- **Repositories and persistence** — repositories for aggregate roots, plus the identity and persistence trade-offs. Read [persistence.md](references/persistence.md)
- **REST** — the inbound adaptor: resources, assemblers, and controllers. Read [rest.md](references/rest.md)
- **Domain exceptions** — domain exceptions and turning them into HTTP responses in one place. Read [exceptions.md](references/exceptions.md)

For Spring Boot questions the references do not cover, read the documentation at `https://docs.spring.io/spring-boot/index.html`.

For the strategic side — discovering the domain, finding bounded contexts, EventStorming, context mapping — use the `ddd-playbook` skill.
