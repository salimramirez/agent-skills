# Tactical Patterns

Read this when you are modeling *inside* a bounded context: choosing the building blocks that make up the domain model and the rules for combining them well. These are the tools that keep business logic in the model instead of leaking into controllers, services, or SQL — the cure for the **anemic domain model**.

Do strategic design first (`references/strategic-design.md`); these patterns live inside the boundaries you found there. For how to express them in a specific stack, see the stack reference (e.g., `references/spring-boot.md`).

## Contents

- [Model-driven design, not Smart UI](#model-driven-design-not-smart-ui)
- [How the building blocks fit together](#how-the-building-blocks-fit-together)
- [Entity](#entity)
- [Value Object](#value-object)
- [Aggregate](#aggregate)
- [Domain Event](#domain-event)
- [Domain Service](#domain-service)
- [Repository](#repository)
- [Factory](#factory)
- [Choosing the right block](#choosing-the-right-block)
- [CQRS](#cqrs)

## Model-driven design, not Smart UI

The building blocks below only pay off under **model-driven design**: the domain is expressed as a rich model of objects with behavior, isolated by the layered architecture. The opposite choice is **Smart UI** — putting business logic directly in the user interface or in procedural scripts. The two are mutually exclusive: a model-driven design with logic also smeared across the UI gets the cost of both and the benefit of neither. Commit to the model.

The failure mode to watch for is the **anemic domain model**: objects that are just bags of getters and setters while all the behavior lives in "service" classes around them. It looks object-oriented but is procedural. Every pattern here exists to push behavior back into the model.

## How the building blocks fit together

A quick map of the relationships, so each block has a place:

- The domain model is expressed with **entities**, **value objects**, and **domain services**, and isolated by the **layered architecture**.
- **Entities** and **value objects** are clustered into **aggregates**; an entity usually **acts as the aggregate root** and maintains the aggregate's integrity.
- **Aggregates** are stored and retrieved through **repositories** (one repository per aggregate root).
- Complex creation of entities, value objects, and aggregates is encapsulated in **factories**.
- **Domain events** announce that something meaningful happened, so other aggregates or contexts can react.

## Entity

An **entity** is an object with a **distinct identity that runs through time** and across different representations — sometimes called a *reference object* (Fowler/Evans). It is the same thing even as its attributes change.

Use an entity when identity and a lifecycle matter. A `Customer` stays the same customer when they change their email or name; what makes them "the same" is their identity (`CustomerId`), not their current attribute values. Two customers with identical names are still different customers.

Practical notes:

- Give it a stable identifier, assigned once and never reused.
- Equality is by identity, not by attributes — two entities are equal when their identifiers are equal.
- Put behavior on the entity, not just data. A `Customer` should *do* things (`deactivate()`), not merely expose fields.

## Value Object

A **value object** has **no identity**: it is defined entirely by its attributes, and two value objects with the same attributes are interchangeable. As Ward Cunningham put it, every $5 note has its own serial number, but the cash economy relies on every $5 note being worth the same as every other — its *value*, not its identity, is what matters.

Value objects model the "magnitudes" and descriptive concepts of a domain: money, quantities, dates and date ranges, prices, weights, identifiers, email addresses, coordinates. Entities are largely *made of* value objects.

Design rules and why they matter:

- **Make them immutable.** If a value can change in place, you reintroduce identity questions and aliasing bugs. To "change" a value object, create a new one.
- **Compare by value** (structural equality): a `Money(5, "USD")` equals any other `Money(5, "USD")`.
- **Put validation and behavior inside.** `Money` should reject mixing currencies and offer `add()`; an `EmailAddress` should reject malformed input at construction. This makes invalid states unrepresentable and removes scattered checks.
- **Prefer a value object over a primitive** whenever a concept carries rules. A bare `BigDecimal amount` and `String currency` invites mistakes that a `Money` type prevents.

## Aggregate

An **aggregate** is a cluster of entities and value objects that **belong together and are treated as a single unit** — a set of objects that do not make sense alone (Fowler). The classic example is an `Order` together with its `OrderLine`s: separate objects, but it is useful to treat the order *and* its lines as one whole.

One entity in the cluster is the **aggregate root**. The outside world references and modifies the aggregate **only through its root**, which is what lets the aggregate guarantee its own consistency.

Design rules, each with a reason:

- **Enforce invariants at the root.** Anything that must always be true for the aggregate (e.g., "an order's total equals the sum of its lines", "you cannot add lines to a shipped order") is checked inside the root. Outside code cannot reach in and break it.
- **Keep aggregates small.** Large aggregates load and lock more data and create contention. Include only what must change together to satisfy an invariant.
- **One aggregate per transaction.** A single transaction should create or modify one aggregate. Needing to change several at once usually means a boundary is wrong, or that you should use eventual consistency.
- **Reference other aggregates by identity, not by object.** An `Order` holds a `CustomerId`, not a `Customer` instance. This keeps boundaries crisp, transactions small, and aggregates independently loadable.
- **Update other aggregates with eventual consistency.** When changing one aggregate must affect another, do it by publishing a domain event and updating the second aggregate in a separate transaction — not both at once.

### Designing aggregate boundaries

The hard part is choosing the boundary, and the rule is: **let the invariants drive it.** An aggregate should be exactly large enough to enforce, within a single transaction, the rules that must always hold together — and no larger. Two forces pull against each other:

- **Bigger boundaries** make more invariants enforceable in one transaction, but raise memory cost and **concurrency conflicts** — more callers compete to change the same aggregate at once.
- **Smaller boundaries** are cheaper and less contended, but some invariants can no longer be guaranteed in a single transaction.

When a rule cannot live inside one aggregate, you have two tools:

- **Eventual consistency** — change one aggregate, publish a domain event, and let a handler update the others a moment later. The default for keeping *separate* aggregates in sync.
- **Corrective policies** — if you deliberately relax an invariant (often to reduce concurrency conflicts), add a process that detects and repairs the rare inconsistency, automatically or via a human step. A pile of corrective policies is a smell that logic was pushed out of the aggregate.

*Example:* a clinic books 10-minute slots, with rules like "a slot is booked at most once" and "no more than N bookings per patient per month." Modeling each *slot* as its own aggregate makes "booked once" trivial to enforce with optimistic concurrency — but the monthly cap now spans many slots. Rather than swell the boundary to a whole month (large and heavily contended), keep the slot small and enforce the cap with an eventually-consistent counter or a corrective policy — a trade you make deliberately *with* the domain experts, not by default.

### The Aggregate Design Canvas

When a boundary is non-obvious or contended, a structured tool helps (the Aggregate Design Canvas, from the ddd-crew — a tactical counterpart to the bounded-context canvas). Work through:

- **Name** — name it well; sometimes encode the scope of its lifespan.
- **Description** — its responsibilities and purpose, *and why this boundary was chosen* and what trade-offs were accepted.
- **State transitions** — the explicit states it moves through. Too many suggests the boundary does too much (split it); too few or trivial ones suggest it is anemic (logic leaked into services).
- **Enforced invariants & corrective policies** — the rules it guarantees, plus any corrective policies for invariants you chose to relax. Listing both makes the trade-offs explicit.
- **Handled commands & created events** — every command it accepts and every event it emits; wiring them together checks nothing is missing.
- **Throughput** — how likely concurrency conflicts are: the command-handling rate and the number of clients. A shopping cart has roughly one client; a ticket-booking aggregate may have hundreds.
- **Size** — how large an instance gets, measured in events per instance and how coarse those events are. Scoping an aggregate to a time period (e.g., a billing period) keeps it bounded.

For simple aggregates the rules above are enough; reach for the canvas when the boundary is the hard part.

## Domain Event

A **domain event** records that **something meaningful happened** in the domain — an event raised from one context carrying information that other aggregates or contexts may care about (e.g., `OrderPlaced`, `PaymentAuthorized`, `OrderShipped`).

Use domain events to:

- **Coordinate across aggregates** without violating "one aggregate per transaction": instead of modifying two aggregates together, modify one, publish an event, and let a handler update the other — reaching **eventual consistency**.
- **Decouple side effects** from the action that caused them: placing an order need not know about emailing, loyalty points, or analytics; those subscribe to `OrderPlaced`.

Name events in the **past tense** — they describe facts that already occurred, and consumers are free to react however and whenever they need.

## Domain Service

A **domain service** holds domain logic that **doesn't belong naturally to any single entity or value object** — an operation that concerns several of them, or that simply has no obvious home object. Keep it **stateless**: it holds no data of its own, just behavior over the objects passed to it.

Example: transferring funds between two accounts is about *both* accounts, so a `FundsTransferService` expresses it better than forcing the logic onto one account. Likewise, a pricing calculation that combines a cart, a customer's tier, and current promotions can live in a `PricingService`.

Two cautions:

- A domain service is not a dumping ground. Reach for one only when the behavior genuinely spans entities or has no natural owner — otherwise the behavior belongs *on* an entity or value object, and over-using services is how you end up with an anemic model.
- Do not confuse it with an **application service** (see `SKILL.md`): the domain service expresses business rules and lives in the domain layer; the application service orchestrates a use case (transactions, loading aggregates) and holds no business rules.

## Repository

A **repository** gives **collection-like access to aggregates by their root** — you `save` an aggregate and `find` it again later, getting back an object in the same state. Mentally, treat it like an in-memory collection (`add`/`get`) even though the implementation is usually a database.

Rules:

- **One repository per aggregate root.** Repositories deal in whole aggregates, retrieved and stored through the root — not in arbitrary inner entities.
- **Interface in the domain, implementation in infrastructure.** The domain declares what it needs (`OrderRepository` with `findById`, `save`); the infrastructure layer implements it against a real database. This keeps the domain pure and lets you swap the storage technology.
- Keep the interface in the **ubiquitous language** (`findOpenOrdersFor(customerId)`), not in storage terms.

## Factory

A **factory** encapsulates the **creation of complex objects** — aggregates or value objects whose construction involves real logic or invariants that a plain constructor would obscure. In practice these are the GoF creation patterns (Factory Method, Abstract Factory, Builder): an interface or class whose responsibility is to build well-formed objects.

Use one when:

- Building a valid object requires assembling several parts or enforcing rules (e.g., turning a cart into a valid `Order` with its lines, totals, and initial state).
- You want creation logic in one place and named in domain terms, instead of duplicated `new` calls scattered around.

If a constructor is clear and sufficient, you do not need a factory — reach for it when creation itself is a meaningful, rule-bearing step.

## Choosing the right block

A quick decision guide when modeling:

- Does the concept have an identity you track over time? → **Entity** (often an aggregate root).
- Is it defined purely by its values and interchangeable? → **Value Object** (make it immutable).
- Do several objects have to stay consistent together? → group them into an **Aggregate** behind a root.
- Does some logic span entities or have no natural home? → **Domain Service** (stateless).
- Does something happen that others must react to? → **Domain Event**.
- Need to persist and retrieve an aggregate? → **Repository** (one per root).
- Is constructing a valid object itself complex? → **Factory**.

## CQRS

Command Query Responsibility Segregation separates the model that **changes** state from the model that **reads** it. Start from the distinction:

- A **command** is any operation that changes an aggregate's state (`PlaceOrder`, `CancelOrder`). The change itself lives in the domain model (an aggregate method); an application service orchestrates and persists it.
- A **query** is any operation that only retrieves state and changes nothing.

In an ordinary design a single model serves both. **CQRS is the deliberate step of giving each its own model:** a **write model** (the aggregates, enforcing invariants) and a separate **read model** shaped for how the data is actually queried and displayed.

**How it works:**

- The write side accepts commands, changes aggregates, and publishes domain events.
- The read side maintains **read models** (also called *projections*): denormalized views built and kept up to date from those events, optimized for querying. Queries hit the read models, never the aggregates. In QuickBite, an "order history" screen spanning orders, payments, and deliveries can read from one projection instead of querying three aggregates.
- Because the read model is updated from events, it is **eventually consistent** with the write side — expect a small lag, and design the UX for it.

**When to use it:**

- Read and write needs genuinely diverge — reports or screens that span aggregates, or very different read-vs-write load you want to scale independently.
- Forcing one model to serve both is making the aggregate awkward (queries dragging in data the invariants don't need).

**Cost and caution:** CQRS adds moving parts — a second model, projection machinery, and eventual consistency to reason about. Treat it as a deliberate choice, not a default; many bounded contexts are well served by a single model with ordinary queries. Apply it **per bounded context**, where it earns its keep, not across the whole system.

**Relationship to event sourcing:** CQRS is often paired with *event sourcing* (storing an aggregate as its sequence of events and rebuilding it by replay), but the two are independent — you can use CQRS without event sourcing.
