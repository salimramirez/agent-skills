---
name: ddd-aspnet-core
description: Write Domain-Driven Design code in ASP.NET Core / C# — bounded contexts as folders with four layers, aggregate roots with behavior mapped by EF Core, value objects as records, command and query services that return results, repositories, domain events, anti-corruption layers, and the REST interface with resources, assemblers and problem details. Use when implementing or refactoring an ASP.NET Core or .NET Web API around business rules, structuring a new bounded context in C#, or pulling business logic out of controllers into a domain model. It carries the DDD design rules it depends on, so it works on its own. Not for ASP.NET Core configuration, Blazor, deployment, or framework questions unrelated to domain modeling.
license: MIT
metadata:
  version: "1.0.0"
  author: Copyright 2026 Salim Ramirez
---

# DDD in ASP.NET Core

Write the actual code for a Domain-Driven Design model in **ASP.NET Core / C#**. The core rules below say *what* the building blocks are and when to reach for each; the references say *how to express them idiomatically* in ASP.NET Core and EF Core, and the assets and scripts write the parts that should come out the same every time.

This is an **opinionated** house style: for every decision it names one convention and says what that convention buys, rather than listing options. It is one coherent way to do this, not the only correct one; where a choice is genuinely open, the reference says so. Examples use the **QuickBite** food-delivery domain — an `Order` in the `Ordering` bounded context, a `Customer` in `Customers`.

The idioms are ASP.NET Core controllers, EF Core over MySQL (Oracle's `MySql.EntityFrameworkCore`, the provider that supports EF Core 10), C# records for everything that has no identity, primary constructors for injection, and Swashbuckle for the API description. The shipped code targets **.NET 10** and was run on .NET 10.0.3 with EF Core 10.0.12 against MySQL 8.0 — and, after the four edits `project-setup.md` lists, against PostgreSQL 17.

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

- **A bounded context is a folder** next to `Program.cs`, with `Domain/`, `Application/`, `Infrastructure/` and `Interfaces/` inside it, always with the same subfolders. The namespace follows the folder. `Shared/` is the kernel and stays small.
- **Commands and queries are records in `Domain/Model`.** A `PlaceOrderCommand` is a sentence in the ubiquitous language, not a DTO.
- **Service interfaces live in `Application/CommandServices` and `Application/QueryServices`; every method is `Handle`**, overloaded on the command or query. The implementations live in `Application/Internal`.
- **The aggregate root extends `AuditableAggregateRoot`** and gets a database-generated `int Id`, `CreatedAt`, `UpdatedAt`, a `Version` that turns the second of two concurrent saves into a 409, and its domain events from it. References to *other* aggregates are typed records (`CustomerId`), never a navigation property.
- **The aggregate has behavior and private setters.** `order.Place()` checks what must be true and records the event; a service never checks the status first.
- **Value objects are records that validate in their constructor**, with their limits as constants the mapping reuses. One value maps through a converter, several through a complex property; enums are stored by name.
- **A broken rule is an exception, an expected outcome is a result.** The domain throws its own `InvalidValueException` (400) or `BusinessRuleViolationException` (409); a command service returns `Result<T>` for not found, conflict, invalid or unauthorized; a query service returns `T?`. Every failure leaves as problem details (RFC 9457).
- **The repository interface is in `Domain/Repositories`**, one per aggregate root, with finders that take value objects; the implementation extends `BaseRepository` and the entities inside the aggregate load with it, always.
- **The unit of work commits, then dispatches the domain events** to `IEventHandler<T>` implementations in `Application/Internal/EventHandlers`. No mediator library.
- **Another context is reached only through its facade**, wrapped in an `External<Context>Service` that translates primitives into this context's value objects.
- **Controllers are plural, thin, and answer with resources.** Resources are records of primitives; assemblers are static and one per direction; a transition is a `POST` to a plural noun that returns the resource.
- **Each context registers itself** in one `Add<Context>Context` extension method; `Program.cs` adds a line per context.
- **Every public type and member carries an XML comment**; implementations carry `<inheritdoc />`. The comments are also the API description.
- **Tables are plural snake_case** by convention, never by attribute.

## Implementation references

The rules above are stack-agnostic. Everything below is how ASP.NET Core and EF Core express them. Read the file that matches the task at hand.

**Starting a piece of work**

- **Adding a resource, end to end** — the order to write the files in, the scaffold, and the checklist. Read [adding-a-resource.md](references/adding-a-resource.md)
- **Project structure** — the tree of a bounded context, the naming table, and what each layer may reference. Read [structure.md](references/structure.md)
- **House style** — XML comments, injection, records, cancellation tokens, and the smells by layer. Read [house-style.md](references/house-style.md)
- **Project setup** — the `.csproj`, `Program.cs` piece by piece, settings and secrets, MySQL, migrations, and switching to PostgreSQL or to Scalar. Read [project-setup.md](references/project-setup.md)
- **The shared kernel** — the classes every context shares, and what each is for. Read [shared-kernel.md](references/shared-kernel.md)

**Modeling the domain**

- **Value objects** — records that validate, their limits, references to other aggregates, money, enums, and how each maps. Read [value-objects.md](references/value-objects.md)
- **Aggregates and entities** — the root with behavior, the entities inside it, and the typed-key alternative. Read [aggregates.md](references/aggregates.md)

**Orchestrating use cases**

- **Commands, queries, and their services** — the records, the `Handle` overloads, what each returns, and the shape of a use case. Read [application-services.md](references/application-services.md)
- **Domain events** — recorded on the aggregate, dispatched after the commit, handled in the application layer. Read [domain-events.md](references/domain-events.md)
- **Anti-corruption layer** — the facade a context exposes and the external service that consumes it. Read [anti-corruption-layer.md](references/anti-corruption-layer.md)

**Reaching the outside**

- **Repositories and persistence** — the database context, configurations, conventions, loading an aggregate whole, and what the MySQL provider gets wrong. Read [persistence.md](references/persistence.md)
- **REST** — controllers, resources, assemblers, status codes and the API description. Read [rest.md](references/rest.md)
- **State transitions and nested resources** — placing, cancelling, adding a part, filtering a collection. Read [state-transitions.md](references/state-transitions.md)
- **Errors and problem details** — the kinds of failure, where each becomes a status code, and the two writers of RFC 9457. Read [exceptions.md](references/exceptions.md)

**Identity and access**

- **The IAM context** — sign-up, sign-in and bearer tokens as a complete, installable context, and what to adapt. Read [iam.md](references/iam.md)

## Copy instead of retyping

Four things ship as code, because they should come out the same every time.

**Run the commands from inside the project**, with `$SKILL` pointing at the directory this skill was installed into — `.claude/skills/ddd-aspnet-core` in a standard install:

```bash
SKILL=.claude/skills/ddd-aspnet-core
```

Each script writes under the project root — the nearest directory, from the current one upward, that holds the web project's `.csproj` — so it works from any directory of the project; `install.py project` is the exception and writes into the current directory, which should be a new, empty one. The root namespace is read from `<RootNamespace>` in the `.csproj`, or is its file name. The scripts refuse to write inside the skill itself or outside a project, and to overwrite a file unless given `--force`. Add `--dry-run` to see what would be written, `--into` to name the root, `--namespace` to override the namespace.

- **`assets/project/`** — a new project: the `.csproj`, `Program.cs`, the settings, the launch profile, the `dotnet-ef` tool manifest, and the shared kernel. Install the skill into the new, empty directory first, then:

  ```bash
  python3 "$SKILL/scripts/install.py" project --name "QuickBite Platform"
  ```

  The skill's own `.cs` files stay out of the build: the SDK skips folders whose name starts with a dot, such as `.claude/`.

- **`assets/shared-kernel/`** — only the kernel, into a project that already exists:

  ```bash
  python3 "$SKILL/scripts/install.py" shared-kernel
  ```

  It prints the packages to add and points at the `Program.cs` to copy from.

- **`scripts/new-context.py`** — scaffolds a whole bounded context wired for one CRUD aggregate, deriving every spelling of the name from two arguments:

  ```bash
  python3 "$SKILL/scripts/new-context.py" --context Ordering --entity Order
  ```

  Add `--plural People` when the naive plural is wrong. It refuses names that would not compile — a context named like its entity, an entity named `Task` or `Event` — and an entity another context already has, whose table and route would collide; it prints the line for `Program.cs` and the migration command. What it writes is ordinary code — read it, then model the real aggregate; the generated one has a single `Name` property as a placeholder.

- **`assets/iam-context/`** — a complete identity context: `User`, roles, sign-up, sign-in, JWT, and the policy that protects every other endpoint:

  ```bash
  python3 "$SKILL/scripts/install.py" iam-context
  ```

  It prints the packages, the `Program.cs` line, the secret to set and the migration.

For ASP.NET Core questions the references do not cover, read the documentation at `https://learn.microsoft.com/aspnet/core/`; for EF Core, `https://learn.microsoft.com/ef/core/`.

For the strategic side — discovering the domain, finding bounded contexts, EventStorming, context mapping — use the `ddd-playbook` skill. For the frontend that consumes this API, use `ddd-angular`, `ddd-vue` or `ddd-react`.
