# Implementing DDD in Spring Boot

Read this when writing the actual code for a DDD model in **Spring Boot / Java**. It assumes you already know *what* the building blocks are and their rules (see `SKILL.md` and `references/tactical-patterns.md`); here we cover *how to express them idiomatically* in Spring Boot.

No specific Spring Boot or Java version is assumed. One caveat that does depend on the version: persistence annotations live in `jakarta.persistence.*` on Spring Boot 3+ and `javax.persistence.*` on Spring Boot 2 — adjust imports accordingly. Examples use a fictional food-delivery domain, **QuickBite** (an `Order` in the Ordering context).

## Contents

- [Package structure: the four layers](#package-structure-the-four-layers)
- [Value objects](#value-objects)
- [Entities and the aggregate root](#entities-and-the-aggregate-root)
- [Repositories](#repositories)
- [Domain events](#domain-events)
- [Application services](#application-services)
- [Domain services](#domain-services)
- [Interfaces (REST)](#interfaces-rest)
- [Keeping the domain pure: the JPA trade-off](#keeping-the-domain-pure-the-jpa-trade-off)

## Package structure: the four layers

Give each **bounded context** its own package, split into the four layers. Dependencies point inward toward `domain`.

```
com.quickbite.ordering
├── interfaces        // REST controllers, request/response DTOs, mappers — the outside edge
├── application       // application services (use cases), @Transactional orchestration, command/result DTOs
├── domain            // aggregates, entities, value objects, domain events, domain services, repository interfaces
└── infrastructure    // repository implementations, messaging, external clients — the technical edge
```

The `domain` package holds the business model and **declares** the interfaces it needs (e.g. repositories); `infrastructure` implements them. Keep framework and persistence concerns out of `domain` as far as practical (see the last section).

## Value objects

Model value objects as **immutable** types. A Java `record` is the natural fit — it is immutable and gives you value equality for free. Put validation in the compact constructor so invalid states cannot be built.

```java
public record Money(BigDecimal amount, Currency currency) {
    public Money {
        Objects.requireNonNull(amount);
        Objects.requireNonNull(currency);
        if (amount.signum() < 0) throw new IllegalArgumentException("amount cannot be negative");
    }

    public Money add(Money other) {
        if (!currency.equals(other.currency))
            throw new IllegalArgumentException("cannot add different currencies");
        return new Money(amount.add(other.amount), currency);
    }
}
```

To persist a value object as part of an aggregate, map it as a JPA embeddable (`@Embeddable` on the type, `@Embedded` where it is used). Recent Hibernate versions can embed records directly; on older ones, use a small immutable class with the same shape. Either way the type stays defined by its values, not by an identity.

## Entities and the aggregate root

The aggregate root is a JPA `@Entity`. Give it a **typed identifier** (itself a value object), put real **behavior** on it (not just getters/setters), enforce invariants inside it, and **reference other aggregates by their id** — never map a `@ManyToOne` to another aggregate root.

Use named static factory methods for creation, and extend Spring Data's `AbstractAggregateRoot` so the aggregate can register domain events.

```java
@Entity
@Table(name = "orders")
public class Order extends AbstractAggregateRoot<Order> {

    @EmbeddedId
    private OrderId id;

    @Embedded
    private CustomerId customerId;          // another aggregate, referenced by id only

    @Enumerated(EnumType.STRING)
    private OrderStatus status;

    @ElementCollection
    @CollectionTable(name = "order_lines", joinColumns = @JoinColumn(name = "order_id"))
    private List<OrderLine> lines = new ArrayList<>();

    protected Order() { }                   // required by JPA, not for application use

    public static Order place(OrderId id, CustomerId customerId, List<OrderLine> lines) {
        if (lines.isEmpty()) throw new IllegalArgumentException("an order needs at least one line");
        Order order = new Order();
        order.id = id;
        order.customerId = customerId;
        order.lines = new ArrayList<>(lines);
        order.status = OrderStatus.PLACED;
        order.registerEvent(new OrderPlaced(id, customerId));   // raise a domain event
        return order;
    }

    public void cancel() {
        if (status == OrderStatus.SHIPPED)
            throw new IllegalStateException("a shipped order cannot be cancelled");
        status = OrderStatus.CANCELLED;
        registerEvent(new OrderCancelled(id));
    }

    public Money total() {
        return lines.stream()
                    .map(OrderLine::subtotal)
                    .reduce(Money.zero(), Money::add);
    }

    public OrderId id() { return id; }
}
```

Entities and value objects *inside* the aggregate (here `OrderLine`) are reached only through the root — outside code never modifies them directly. This is what lets the root guarantee the aggregate's invariants.

## Repositories

Declare the repository **interface in the domain layer**, in the ubiquitous language and dealing in whole aggregates by their root — one repository per aggregate root.

```java
// domain layer — no framework leakage
public interface OrderRepository {
    Optional<Order> findById(OrderId id);
    Order save(Order order);
}
```

Implement it in `infrastructure` with Spring Data. The pragmatic idiom is a Spring Data interface that satisfies the domain contract:

```java
// infrastructure layer
interface OrderJpaRepository extends JpaRepository<Order, OrderId>, OrderRepository { }
```

`JpaRepository` already provides matching `findById` and `save`, so Spring Data wires the implementation for you. (If you prefer to keep even the Spring Data type out of the domain, keep `OrderRepository` plain and add a thin adapter in `infrastructure` that delegates to a `JpaRepository`.)

## Domain events

Define each event as an immutable record in the domain, named in the past tense:

```java
public record OrderPlaced(OrderId orderId, CustomerId customerId) { }
```

Because `Order` extends `AbstractAggregateRoot` and calls `registerEvent(...)`, Spring Data **publishes the registered events automatically when the aggregate is saved** through its repository. Handle them with `@TransactionalEventListener` so a handler runs after the transaction commits — the basis for keeping other aggregates eventually consistent:

```java
@Component
class OrderPlacedHandler {

    @TransactionalEventListener
    void on(OrderPlaced event) {
        // e.g. notify the kitchen, award loyalty points, start dispatch — each decoupled
    }
}
```

## Application services

An application service orchestrates one **use case**: it loads aggregates, invokes their behavior, and manages the transaction — but holds **no business rules** itself. Annotate it `@Service` and `@Transactional`, take a command, return a small result.

```java
@Service
public class PlaceOrderService {

    private final OrderRepository orders;

    public PlaceOrderService(OrderRepository orders) {
        this.orders = orders;
    }

    @Transactional
    public OrderId handle(PlaceOrderCommand command) {
        Order order = Order.place(OrderId.newId(), command.customerId(), command.lines());
        orders.save(order);            // registered domain events are published here
        return order.id();
    }
}
```

The command (`PlaceOrderCommand`) and result are plain DTOs of the application layer; keep domain objects from leaking out to callers.

## Domain services

When logic genuinely spans aggregates or has no natural home on one, use a **stateless** domain service. Keep it in the `domain` layer and free of orchestration; it expresses a business rule, not a use case.

```java
// domain layer — stateless, no persistence, no transactions
public class DeliveryFeePolicy {
    public Money feeFor(DeliveryDistance distance, Money orderTotal) {
        // pure business calculation over the values it is given
    }
}
```

Reach for this sparingly — most behavior belongs *on* an entity or value object. A drift toward many services holding the logic is how an anemic model creeps back in.

## Interfaces (REST)

The controller is a thin edge: it accepts a request DTO, turns it into a command, calls the application service, and maps the result back out. No business logic, and no domain types in the API contract.

```java
@RestController
@RequestMapping("/orders")
class OrderController {

    private final PlaceOrderService placeOrder;

    OrderController(PlaceOrderService placeOrder) {
        this.placeOrder = placeOrder;
    }

    @PostMapping
    ResponseEntity<Void> place(@RequestBody PlaceOrderRequest request) {
        OrderId id = placeOrder.handle(request.toCommand());
        return ResponseEntity.created(URI.create("/orders/" + id.value())).build();
    }
}
```

## Keeping the domain pure: the JPA trade-off

There is a real tension: the cleanest DDD keeps the domain free of any framework, but the examples above put JPA annotations directly on the domain `Order`. Two honest options:

- **Pragmatic (shown here):** annotate the domain entities with JPA. Far less code, idiomatic in Spring, and fine for most projects — the rules and behavior still live in the model. The cost is a soft dependency on the persistence framework.
- **Pure:** keep the domain as plain Java and add a **separate persistence model** in `infrastructure` (JPA entities that mirror the aggregate), mapping between them in the repository implementation. Maximum isolation, at the cost of mapping boilerplate.

Choose by project size and how strict your isolation needs are. Whichever you pick, hold the non-negotiables: business rules and invariants stay in the domain model, and the domain never depends on `interfaces` or `application`.
