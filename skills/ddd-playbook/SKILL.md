---
name: ddd-playbook
description: Apply Domain-Driven Design (DDD) when modeling a business domain or structuring code around business logic, on the backend or the frontend. Use whenever the user is designing or refactoring a domain model, pulling business rules out of controllers or UI components, organizing a backend service or an Angular app by domain or bounded context, or mentions DDD, bounded contexts, ubiquitous language, aggregates, entities, value objects, domain events, repositories, domain or application services, anti-corruption layers, or CQRS — even if they never say "DDD". It covers strategic design and collaborative modeling (context mapping, EventStorming), tactical patterns (aggregate boundaries, invariants, value objects), and idiomatic implementation in Spring Boot/Java or Angular. Prefer it over ad-hoc modeling whenever non-trivial business rules or invariants are involved. It does not apply to plain CRUD with no business rules, UI styling, DevOps or infrastructure, database query tuning, or framework API how-to questions.
license: MIT
metadata:
  version: "1.0.1"
  author: Salim Ramirez
---

# Domain-Driven Design (DDD)

Domain-Driven Design tackles complex software by putting the **business domain** — its language, rules, and invariants — at the center of the design, instead of letting the database schema, the framework, or the UI drive the model.

Apply this whenever you model a domain or write code around business logic. Follow the decision rules in this file; open a reference file when you need depth on a specific area. The rules matter more than any single example — understand *why* each exists so you can apply it to cases the examples don't spell out.

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

→ For the full catalog with detailed rules, trade-offs, and worked examples, read `references/tactical-patterns.md`.

## Strategic design — essentials

Before tactical modeling, get the big picture right:

- **Bounded Context** — an explicit boundary within which a model and its ubiquitous language stay consistent. The same word can mean different things in different contexts (a "Customer" in Sales ≠ in Support); don't force one model across the whole system.
- **Subdomains** — distinguish the **core** (your competitive advantage — invest most here), **supporting**, and **generic** (buy/reuse) subdomains, so effort goes where it matters.
- **Context Mapping** — define the relationships between bounded contexts (e.g., an **Anti-Corruption Layer** to protect your model from an external one).

→ For the strategic concepts in depth, read `references/strategic-design.md`. For the collaborative modeling process and tools (EventStorming, Domain Message Flow, Bounded Context Canvas, the context-map pattern catalog, the modeling recipe), read `references/modeling-process.md`.

## CQRS

Command Query Responsibility Segregation separates the model that **changes** state (commands) from the model that **reads** it (queries). Reach for it when read and write needs genuinely diverge — complex queries, very different read/write load, or read models that span aggregates. Treat it as a deliberate choice, not a default: it adds moving parts, and many domains are well served by a single model.

→ For depth (read models, eventual consistency, relationship to event sourcing), read `references/tactical-patterns.md`.

## How to approach a DDD task

1. **Establish the language** — clarify the domain terms with the user; use them verbatim in the model.
2. **Locate the bounded context** — which context are we in, and what is its model?
3. **Find the aggregates and their invariants** — what must always be true, and what is the consistency boundary?
4. **Model tactically** — choose value objects, entities, and aggregate roots; push rules into them; keep the domain pure.
5. **Place each piece in the right layer** — rules in domain, orchestration in application, I/O in interfaces, technical detail in infrastructure.
6. **Implement for the stack** — read the matching implementation reference and follow its idioms.

## Implementation references (by stack)

The principles above are stack-agnostic, but the idioms (keeping persistence out of the domain, publishing domain events, etc.) differ. When writing code, read the file for the project's stack:

- **Spring Boot / Java** → `references/spring-boot.md`
- **Angular (frontend, DDD-adapted)** → `references/angular.md`

If no reference exists for the project's stack, apply the rules above idiomatically for that technology.
