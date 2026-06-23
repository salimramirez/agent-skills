# Strategic Design

Read this when doing the **strategic** part of DDD: shaping the ubiquitous language, discovering subdomains, and drawing and mapping bounded contexts. This is where the architecture of a domain gets decided — do it before tactical modeling.

For the tactical building blocks (entities, value objects, aggregates, etc.) see `references/tactical-patterns.md`. For the layered architecture see the main `SKILL.md`. When implementing, see the stack reference (e.g., `references/spring-boot.md`).

## Contents

- [Why strategic design comes first](#why-strategic-design-comes-first)
- [Domain and domain model](#domain-and-domain-model)
- [Ubiquitous language](#ubiquitous-language)
- [Domain storytelling](#domain-storytelling)
- [Subdomains](#subdomains)
- [Bounded contexts](#bounded-contexts)
- [Context mapping](#context-mapping)
- [Characteristics of a strong domain model](#characteristics-of-a-strong-domain-model)
- [Worked example: a food-delivery platform](#worked-example-a-food-delivery-platform)
- [A practical workflow](#a-practical-workflow)

## Why strategic design comes first

DDD has two halves: **strategic** (the big picture — language, subdomains, boundaries) and **tactical** (the building blocks inside a model). A common mistake is to jump straight into tactical work — creating entities, repositories, and value objects — before the boundaries are clear. Resist that. Strategic design is where you decide *how the system is divided and how the parts relate*, and getting it wrong is far more expensive to fix later than any single class. Spend the time here first.

## Domain and domain model

- The **domain** is the subject area the software is about — the business itself and the activity around it. In a payments app the domain is payments; in a hospital app it is care.
- The **domain model** is the code that represents that business: the concepts, rules, and relationships, expressed so the team can reason about them and the software can enforce them.
- What many developers call **business logic** is exactly this: the higher-level rules for how the domain's concepts behave and interact. In DDD it belongs *in the domain model*, not scattered across controllers or queries.

Keep the mental equation: **domain = your business; domain model = the code that represents it.**

## Ubiquitous language

The single most important strategic practice. The **ubiquitous language** is one shared language, built around the domain model, that the *whole* team uses everywhere — in conversation with domain experts, in documentation, and in the code itself. There is no separate "business language" and "developer language": the team speaks one language, and the code reflects it.

Why it matters: most defects in complex systems come from misunderstanding, not from typos. When a domain expert says "policy" and the code says `InsuranceRecord`, every translation between the two is a chance to get the rules wrong. Name things in the code the way the business names them, and keep the names honest as your understanding evolves.

### Keep technical detail out of the language

The language should describe *what happens in the business*, not how the software does it. Technical words — flags, tables, queues, gateways — hide the domain and pull the model toward an anemic, procedural design. When you hear them, dig for the real domain concept underneath.

**Before** (leaks implementation):
> "When the user submits the cart, set `paid = true` in the orders table and push a row onto the queue for the driver service."

The obstructions: `paid = true` is a storage flag, "orders table" and "queue" are persistence/transport details, "driver service" is a deployment fact. None of them are domain concepts.

**After** (reveals intention):
> "When a customer places an order and payment is authorized, the order is confirmed. A confirmed order becomes available for dispatch, and a courier can then be assigned to deliver it."

Now the sentence names real domain events and states — *placed*, *authorized*, *confirmed*, *available for dispatch*, *assigned* — and those names go straight into the model.

### Express it in BDD scenarios

A concrete way to pin the language down is to write behavior as Given/When/Then scenarios in domain terms. They double as shared understanding and as tests:

```
Story: Place an order
  As a hungry customer
  I want to order food from a nearby restaurant
  So that it gets delivered to me.

Scenario: The restaurant is closed
  Given "La Trattoria" is closed
  When I place an order from "La Trattoria"
  Then my order should be rejected
  And I should be told the restaurant is closed.
```

## Domain storytelling

Domain storytelling is a lightweight, **pictographic** technique for learning a domain *with* the domain experts. You draw a short story as actors, the work objects they act on, and the activities between them, in sequence — simple enough that a non-technical expert can look at it and say "yes, that's how it works" or "no, you misunderstood."

Use it to:

- Build and validate the ubiquitous language before writing code.
- Surface the real steps, actors, and edge cases of a process.
- Derive user stories directly — each meaningful step tends to map to a story (e.g., "As a customer, I want to track my order so that I know when it will arrive").

It is a conversation tool, not a deliverable: the value is the shared understanding it produces.

## Subdomains

A domain is rarely uniform. It divides into **subdomains** — coherent areas of the business — and each subdomain tends toward its own bounded context. Separating them lets you put the right effort in the right place. The standard distinction:

- **Core** — what makes this business different and competitive. Invest your best modeling effort here.
- **Supporting** — necessary but not differentiating; build it simply.
- **Generic** — a solved problem (payments, notifications, auth); buy or reuse rather than build.

Identifying which is which is itself a strategic decision: it tells you where deep DDD pays off and where it would be over-engineering.

## Bounded contexts

A **bounded context** is an explicit boundary within which one model and its ubiquitous language are consistent and valid. Inside the boundary, every term means exactly one thing.

Each bounded context has:

- its **own ubiquitous language**,
- its **own model**, and
- its **own, independent implementation** (its own architecture and, often, its own deployment).

The point is that the *same word can mean different things in different contexts*, and that is fine — even healthy. A "Customer" in a Sales context (a prospect with a pipeline stage) is not the same as a "Customer" in a Support context (a person with tickets and entitlements). Forcing one shared model across the whole system produces a tangle where no term is precise. Instead, give each context its own model and connect them deliberately.

A bounded context gives the team a clear answer to: **what must stay consistent here, and what can evolve independently elsewhere?**

**Benefits:** the team and the business speak one language with less risk of misunderstanding; the architecture is segregated; smaller models are easier to maintain and test; contexts (and the services behind them) can evolve independently; side effects stop being surprises.

**Considerations (the cost):** more architectural complexity; more up-front effort mapping the domain and meeting with experts; and a mindset shift — everyone must agree on vocabulary and ownership. This alignment is the hardest and most important part of adopting DDD.

## Context mapping

Real systems have several bounded contexts, and they must cooperate. A **context map** is the picture of how the contexts relate: which ones depend on which, and how they communicate across their boundaries.

The key idea: a context never reaches into another's model directly. Each context exposes an **interface** to the outside, and when two contexts interact you **translate** between their two languages at the boundary rather than leaking one model into the other. That translation is what keeps each model clean and lets each evolve at its own pace.

> The full catalog of context-mapping relationship patterns (anti-corruption layer, open host service, conformist, shared kernel, customer/supplier, partnership, published language, separate ways) and team relationships is covered in `references/modeling-process.md`. The essential rule here is: **map the relationships explicitly, and translate at the boundary.**

## Characteristics of a strong domain model

Strategic design only pays off if the domain model stays clean. Aim for a model that is:

- **Aligned** with the business's real model, strategy, and processes.
- **Isolated** from other domains and from the technical layers around it.
- **Loosely coupled** — it does not depend on the layers on either side of it (interfaces above, infrastructure below).
- **Reusable**, so concepts are not duplicated across the system.
- **Cleanly separated** as its own layer, which makes it easier to maintain, test, and version.
- **Minimal in its dependencies** on frameworks, so the model outlives them and is not tightly coupled to any one technology — close to a plain-objects design with no framework annotations bleeding into it.

This is the strategic justification for the **domain purity** rule in the main `SKILL.md`: a model that depends on infrastructure cannot be reused, tested, or reasoned about on its own.

## Worked example: a food-delivery platform

Take a fictional platform, **QuickBite**, that lets people order food from nearby restaurants and have it delivered. (This is an illustration — adapt the shape, not the specifics, to the domain in front of you.)

**Subdomains:**

- **Ordering** and **Delivery** are the **core** — placing orders and getting couriers to deliver them are what the business lives or dies on.
- **Restaurant Catalog** (menus, hours, availability) is **supporting** — needed, but not the differentiator.
- **Payments** and **Notifications** are **generic** — use a payment provider and a messaging provider rather than building them.

**Bounded contexts and language:** notice how "Order" is not one concept:

- In the **Ordering** context, an *Order* is the customer's chosen items plus its placement and payment status.
- In the **Delivery** context, the same real-world thing is a *Delivery Job*: a pickup location, a drop-off, and an assigned courier. It does not care about menu items or prices.

Because the language differs, each context keeps its **own** model. They do not share one `Order` class.

**A small context map:**

```
[ Catalog Context ] --menus/availability--> [ Ordering Context ]
                                                   |
                                            order is confirmed
                                                   v
                                            [ Delivery Context ]
```

- Ordering reads menus and availability from Catalog.
- When Ordering confirms an order, Delivery learns of it and creates its own *Delivery Job* — translating Ordering's "confirmed order" into Delivery's language at the boundary, instead of importing Ordering's model.

This separation is exactly what lets the Delivery team change how dispatching works without touching how orders are placed.

## A practical workflow

When you are doing strategic design on a real problem:

1. **Talk to the domain experts.** Treat them as the source of truth about the business, and interact intensely — this is where the language comes from.
2. **Build the ubiquitous language** as you go. Use domain storytelling and BDD scenarios to capture it and check your understanding out loud.
3. **Identify the subdomains** and label each core, supporting, or generic, so effort lands where it matters.
4. **Draw the bounded contexts** — one consistent model and language per context; let the same word differ across contexts.
5. **Map the contexts** — make the relationships explicit and translate at every boundary.
6. **Only then go tactical** — model entities, value objects, and aggregates inside each context (see `references/tactical-patterns.md`).
