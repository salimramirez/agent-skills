---
name: ddd-spring-boot
description: Write Domain-Driven Design code in Spring Boot / Java — the four-layer package structure, aggregate roots as JPA entities, value objects and typed ids as embeddables, command and query services, repositories, domain events, anti-corruption layers, and the REST interface with resources and assemblers. Use when implementing or refactoring a Spring Boot service around business rules, structuring a new bounded context in Java, or pulling business logic out of controllers into a domain model. It carries the DDD design rules it depends on, so it works on its own. Not for Spring configuration, security, or framework questions unrelated to domain modeling.
license: MIT
metadata:
  version: "1.1.0"
  author: Copyright 2026 Salim Ramirez
---

# DDD in Spring Boot

Write the actual code for a Domain-Driven Design model in **Spring Boot / Java**. The core rules below say *what* the building blocks are and when to reach for each; the references say *how to express them idiomatically* in Spring Boot, and the assets and scripts write the parts that should come out the same every time.

This is an **opinionated** house style: for every decision it names one convention and says what that convention buys, rather than listing options. It is one coherent way to do this, not the only correct one; where a choice is genuinely open, the reference says so. Examples use the **QuickBite** food-delivery domain — an `Order` in the `ordering` bounded context, a `Customer` in `customers`.

The idioms are Spring Boot 3 with Spring Data JPA, Java records for everything that has no identity, Lombok for getters and nothing else, springdoc for the API description, and constructor injection throughout. The shipped code compiles for Java 17 and runs on Spring Boot 3.5 and 4.0 as verified; the one difference that matters between the two is the name of the web starter (`spring-boot-starter-web` on 3, `spring-boot-starter-webmvc` on 4). Persistence annotations are `jakarta.persistence.*` on both; on Spring Boot 2 they were `javax.persistence.*`.

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

- **A bounded context is a package** under the base package, with `domain/`, `application/`, `infrastructure/` and `interfaces/` inside it, always with the same sub-packages. `shared/` is the kernel and stays small.
- **Commands and queries are records in the domain** that validate themselves in the compact constructor. A `PlaceOrderCommand` is a sentence in the ubiquitous language, not a DTO.
- **The service interfaces live in `domain/services`; every method is `handle`**, overloaded on the command or query. The implementations live in `application/internal`.
- **The aggregate root extends `AuditableAbstractAggregateRoot`** and gets a generated `Long` id, `createdAt` and `updatedAt` from it. References to *other* aggregates are typed records (`CustomerId`), never bare numbers and never `@ManyToOne`.
- **The aggregate has behavior and no setters.** `order.place()` checks what must be true and raises the event; a service never checks the status first.
- **Value objects are `@Embeddable` records**, immutable, returning new instances from every operation. Enums are stored by name.
- **`IllegalArgumentException` means bad input, `IllegalStateException` means a forbidden transition**, and a domain exception means a named failure. The shared advice maps the first two to 400 and 409; each context's advice maps its own.
- **The repository is a Spring Data interface in `infrastructure`**, one per aggregate root, with finders that take value objects. Services use it directly.
- **Domain events extend `ApplicationEvent`, are registered with `addDomainEvent`, and are published on `save`.** Handlers in `application/internal/eventhandlers` react by issuing commands.
- **Another context is reached only through its facade**, wrapped in an `External<Context>Service` that translates primitives into this context's value objects.
- **Controllers are plural, thin, and re-query after a write.** Resources are records of primitives; assemblers are static and one per direction; a transition is a `POST` to a sub-resource returning a `MessageResource`.
- **Constructor injection, written out.** No `@Autowired`, no `@RequiredArgsConstructor`, no `@Setter`, no `@Data` on an entity.
- **Every type carries Javadoc** with a title line and a `@summary`; implementations carry `{@inheritDoc}`.
- **Tables are plural snake_case** by naming strategy, never by `@Table`.

## Implementation references

The rules above are stack-agnostic. Everything below is how Spring Boot expresses them. Read the file that matches the task at hand.

**Starting a piece of work**

- **Adding a resource, end to end** — the order to write the files in, the scaffold, and the checklist. Read [adding-a-resource.md](references/adding-a-resource.md)
- **Package structure** — the tree of a bounded context and the naming table. Read [structure.md](references/structure.md)
- **House style** — Javadoc, locals, injection, the annotation order on a controller, and the smells by layer. Read [house-style.md](references/house-style.md)
- **Project setup** — the `pom.xml`, the properties per profile, and the application class. Read [project-setup.md](references/project-setup.md)
- **The shared kernel** — the six classes every context shares, and what each is for. Read [shared-kernel.md](references/shared-kernel.md)

**Modeling the domain**

- **Value objects** — records as embeddables, the three kinds of identifier, enums, and the collection-owning class. Read [value-objects.md](references/value-objects.md)
- **Aggregates and entities** — the root with behavior, the entities inside it, and the typed-key alternative. Read [aggregates.md](references/aggregates.md)

**Orchestrating use cases**

- **Commands, queries, and their services** — the records, the `handle` overloads, the return-type table, and the implementations. Read [application-services.md](references/application-services.md)
- **Domain events** — raising on the aggregate, publishing on save, handling in the application layer. Read [domain-events.md](references/domain-events.md)
- **Anti-corruption layer** — the facade a context exposes and the external service that consumes it. Read [anti-corruption-layer.md](references/anti-corruption-layer.md)

**Reaching the outside**

- **Repositories and persistence** — the Spring Data interface, finders on value objects, tables. Read [persistence.md](references/persistence.md)
- **REST** — resources, assemblers, and the controller for CRUD. Read [rest.md](references/rest.md)
- **State transitions and nested resources** — placing, cancelling, adding a part, consulting by parameters. Read [state-transitions.md](references/state-transitions.md)
- **Domain exceptions and error handling** — the four kinds of failure and the two advices. Read [exceptions.md](references/exceptions.md)

**Identity and access**

- **The IAM context** — sign-up, sign-in and bearer tokens as a complete, installable context, and what to adapt. Read [iam.md](references/iam.md)

## Copy instead of retyping

Three things ship as code, because they should come out the same every time.

**Run the commands from anywhere inside the Spring Boot project**, with `$SKILL` pointing at the directory this skill was installed into — `.claude/skills/ddd-spring-boot` in a standard install:

```bash
SKILL=.claude/skills/ddd-spring-boot
```

Each script resolves `src/main/java` against the project root — the directory above the current one that holds `pom.xml` or `build.gradle` — finds the base package by reading the class annotated with `@SpringBootApplication` there, and refuses to write inside the skill itself or outside a project. Add `--dry-run` to see what would be written, `--package` to override the base package, `--into` when the sources are not under `src/main/java`.

- **`assets/shared-kernel/`** — the six classes of the shared kernel. Install them first:

  ```bash
  python3 "$SKILL/scripts/install.py" shared-kernel
  ```

  It prints the edits it cannot make: the dependencies, the properties, and `@EnableJpaAuditing` on the application class.

- **`scripts/new-context.py`** — scaffolds a whole bounded context wired for one CRUD aggregate, deriving every spelling of the name from two arguments:

  ```bash
  python3 "$SKILL/scripts/new-context.py" --context ordering --entity Order
  ```

  Add `--plural People` when the naive plural is wrong. What it writes is ordinary code — read it, then model the real aggregate; the generated one has a single `name` field as a placeholder.

- **`assets/iam-context/`** — a complete identity context: `User`, `Role`, sign-up, sign-in, JWT, and the security filter chain:

  ```bash
  python3 "$SKILL/scripts/install.py" iam-context
  ```

  It prints the dependencies and properties to add, and the two things to review before relying on it.

For Spring Boot questions the references do not cover, read the documentation at `https://docs.spring.io/spring-boot/index.html`.

For the strategic side — discovering the domain, finding bounded contexts, EventStorming, context mapping — use the `ddd-playbook` skill. For the frontend that consumes this API, use `ddd-angular`, `ddd-vue` or `ddd-react`.
