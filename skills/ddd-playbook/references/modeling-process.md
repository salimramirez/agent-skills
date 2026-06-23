# Collaborative Modeling Process

Read this when you need to **run or structure the modeling work** of DDD: discovering the domain with experts, finding bounded contexts, designing each context, and mapping the relationships between them. Where `references/strategic-design.md` defines the strategic *concepts*, this file describes the *process and tools* used to produce them.

These are collaborative, workshop-style techniques. As an agent you will rarely run a live workshop, but use these to **structure your own analysis**, to ask the right questions, and to produce the same artifacts (event timelines, message flows, context canvases, context maps) when helping design a system.

## Contents

- [Start by understanding the business](#start-by-understanding-the-business)
- [EventStorming](#eventstorming)
- [Domain Message Flow Modelling](#domain-message-flow-modelling)
- [Bounded Context Canvas](#bounded-context-canvas)
- [Context mapping](#context-mapping)
- [Putting it together: a modeling process](#putting-it-together-a-modeling-process)

## Start by understanding the business

Modeling is a *team* activity, not a solo technical exercise. The biggest gains come from the system people work in and how they interact — far more than from any individual's technical skill. So the process starts with deeply understanding the business *with* its experts, and only then turns to software. Treat the techniques below as ways to make that shared understanding explicit and checkable.

## EventStorming

EventStorming is a collaborative modeling method built for DDD. In a workshop, developers and experts from different areas use sticky notes to build a picture of complex business processes. The picture is built **bottom-up**: write **domain events** on notes and place them on a left-to-right timeline. After a deliberately chaotic start, a story emerges as a flow of events the experts care about.

Keep the group diverse (engineers, domain experts, product, QA, UX, support) but not too large — everyone must be able to contribute, which gets hard past ~10 people.

### The 10-step process

1. **Unstructured exploration** — brainstorm domain events. A domain event is something interesting that *happened* in the business; phrase events in the **past tense** (e.g., `Order Placed`, `Payment Authorized`).
2. **Timelines** — arrange the events in the order they occur. Lay down the **happy path** first, then add alternative and exceptional flows.
3. **Pain points** — use the wide view to mark trouble spots: bottlenecks, manual steps that should be automated, missing documentation, or missing domain knowledge.
4. **Pivotal points** — find events that signal a change of phase or context, and mark them with a vertical bar dividing what comes before and after. These often reveal context boundaries.
5. **Commands** — add what *triggered* each event. A command is a system operation, phrased in the **imperative** (e.g., `Place Order`). Commands cause events.
6. **Policies** — look for commands with no specific actor: **automation policies**, where one event automatically triggers a command ("whenever X happened, do Y").
7. **Read models** — add the view of data an actor consults to decide to issue a command: a screen, a report, a notification.
8. **External systems** — add systems outside the domain being explored. They can issue commands (input) or be notified of events (output).
9. **Aggregates** — group related concepts into aggregates. An aggregate **receives commands and produces events** — a useful, behavior-first way to find them.
10. **Bounded contexts** — group aggregates that are closely related (by functionality or by being coupled through policies). These groups are natural candidates for bounded-context boundaries.

## Domain Message Flow Modelling

Loosely coupled systems need more than careful boundaries — they need carefully defined **interactions** between bounded contexts. A bounded context here is a sub-system aligned with part of the domain; it can be a microservice or a module in a monolith.

A **Domain Message Flow Diagram** is a simple visualization of the messages — **commands, events, and queries** — flowing between actors, bounded contexts, and systems, for one scenario.

- **Format 1 — separate message and contents:** the message label and its data are shown separately.
- **Format 2 — combined:** the label and contents are shown together.

**How to use it:** list your scenarios, and draw one diagram per scenario. For each:

1. Start with an actor, context, or system.
2. Create the message it wants to send.
3. Add the receiver and a line connecting sender and receiver.
4. Place the message near the line.

Repeat until the scenario is complete. Each message carries a **name**, its **significant data/contents**, and its **order** within the flow being modeled.

## Bounded Context Canvas

The Bounded Context Canvas (from the ddd-crew) is a collaborative tool to design and document a **single** bounded context. It walks you through decisions about the context's key design elements — from its name to its responsibilities, public interface, and dependencies.

Fill in these sections:

- **Name** — naming is hard; agreeing on the name as a team frames how you design the context.
- **Description** — a few sentences on the *why* and *what*, in business language, with no technical detail. Writing it forces you to articulate fuzzy thinking and get everyone aligned.
- **Strategic Classification** — three lenses:
  - *Domain:* how important is this context — **core**, **supporting**, or **generic**?
  - *Business model:* what role does it play — **revenue generator** (paid for directly), **engagement creator** (liked but not paid for), or **compliance enforcer** (protects the business)?
  - *Evolution:* how mature is the concept — **genesis** (new, unexplored), **custom build**, **product** (off-the-shelf with differentiation), or **commodity** (highly standardized)?
- **Domain Roles** — characterize the traits this context plays in the business model.
- **Inbound Communication** — collaborations *initiated by others*: the **messages** received, the **collaborators** who send them, the **relationship type**, organized into swimlanes.
- **Outbound Communication** — collaborations this context *initiates* toward others; same message types and notation.
- **Ubiquitous Language** — the key domain terms inside this context and what they mean.
- **Business Decisions** — the key business rules and policies this context owns.

### The three message types

DDD integration uses three kinds of message, and the canvas makes them explicit:

- **Command** — the sender tells the recipient to *do something*.
- **Domain Event** — a significant thing that *happened* inside one bounded context. Others may need to react, but there is **no obligation** on when or how they respond (unlike a command).
- **Query** — one context asks another for information.

### Information and services provided

The public interface of a context — what others may consume — breaks down into:

- **Queryable Information** — what other contexts can ask about.
- **Invokable Commands** — what other contexts can ask this one to do.
- **Published Events** — what this context publishes for others to subscribe to.
- **Reactive Jobs** — work this context starts internally, e.g., scheduled jobs, or starting a business process in response to another context's published event.

## Context mapping

Begin with the **core subdomains** — the parts of the domain with the most potential for business differentiation or strategic significance — and let the map grow from there. A useful way to classify each context is by **model complexity vs. business differentiation**: high-differentiation areas are **core**, low-differentiation but custom areas are **supporting**, and low-differentiation standard areas are **generic**.

### Context map patterns

When two contexts integrate, name the relationship. The common patterns:

- **Open Host Service** — a context publishes a defined, open protocol/API that any number of consumers integrate with.
- **Conformist** — the downstream context adopts the upstream's model as-is, with no translation (cheap, but it gives up its own model).
- **Anti-Corruption Layer (ACL)** — the downstream builds a translation layer to protect its own model from the upstream's. The default when you must integrate but want to stay clean.
- **Shared Kernel** — two contexts deliberately share a small common model or code; any change requires coordination between both teams.
- **Customer/Supplier** — an upstream **supplier** and a downstream **customer**, where the customer's needs are given weight in the supplier's planning.
- **Partnership** — two contexts (and teams) succeed or fail together and coordinate closely.
- **Published Language** — a well-documented shared language/format for integration (often paired with an Open Host Service).
- **Separate Ways** — the contexts do not integrate at all; each goes its own way.
- **Big Ball of Mud** — a messy area with no clear boundaries; recognize it, wall it off, and keep its mess from leaking into clean contexts.

### Team relationships

The map also captures how the *teams* relate, which shapes the technical relationship:

- **Mutually Dependent** — two contexts must be delivered together to work; a close, reciprocal link.
- **Free** — changes in one context do not affect the other; no organizational or technical link.
- **Upstream / Downstream (U/D)** — the upstream's actions influence the downstream, but not the reverse — and not only in code, but in schedule and responsiveness too.

## Putting it together: a modeling process

A practical order for combining the techniques (based on the ddd-crew Starter Modelling Process):

1. **Big Picture EventStorming** — explore the whole domain as a flow of events.
2. **Candidate Context Modelling** — group the events/aggregates into candidate bounded contexts.
3. **Domain Message Flow Modelling** — model how those candidate contexts talk to each other per scenario.
4. **Bounded Context Canvas** — design each candidate context in detail.
5. **Refined Context Exploration** — revisit and refine boundaries as understanding improves.

Treat it as a loop, not a one-way pipeline: each step can send you back to refine an earlier one.

---

**Sources:** EventStorming (Alberto Brandolini); the Bounded Context Canvas and the DDD Starter Modelling Process are from the ddd-crew (github.com/ddd-crew). Use them as the canonical references when you need more detail than this summary provides.
