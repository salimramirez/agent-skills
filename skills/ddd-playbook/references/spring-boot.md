# Implementing DDD in Spring Boot

Read this when writing the actual code for a DDD model in **Spring Boot / Java**. It assumes you already know *what* the building blocks are and their rules (see `SKILL.md` and `references/tactical-patterns.md`); here we cover *how to express them idiomatically* in Spring Boot.

No specific Spring Boot or Java version is assumed; the patterns here work on Spring Boot 3 and 4 with Java 17+ (including 21 and the 25 LTS). One caveat that does depend on the version: persistence annotations live in `jakarta.persistence.*` on Spring Boot 3 and 4 and `javax.persistence.*` on Spring Boot 2 — adjust imports accordingly. Examples use a fictional food-delivery domain, **QuickBite** (an `Order` in the Ordering context).

## Contents

- [Package structure: the four layers](#package-structure-the-four-layers)
- [The shared kernel](#the-shared-kernel)
- [Value objects](#value-objects)
- [Aggregate root and entities](#aggregate-root-and-entities)
- [Commands and queries](#commands-and-queries)
- [Command services and query services](#command-services-and-query-services)
- [Repositories](#repositories)
- [Domain events](#domain-events)
- [Anti-corruption layer](#anti-corruption-layer)
- [Interfaces (REST)](#interfaces-rest)
- [Domain exceptions and error handling](#domain-exceptions-and-error-handling)
- [Identity and persistence: choices and trade-offs](#identity-and-persistence-choices-and-trade-offs)

## Package structure: the four layers

Give each **bounded context** its own package, split into the four layers, with dependencies pointing inward toward `domain`. A common, consistent layout:

```
com.quickbite.ordering
├── interfaces                     // inbound adaptors — the outside drives the context
│   ├── rest
│   │   ├── controllers            // REST controllers
│   │   ├── resources              // request/response DTOs (records)
│   │   └── transform              // assemblers: resource <-> command / entity
│   └── acl                // facade this context exposes to other contexts
├── application                    // use-case orchestration (no business rules)
│   ├── acl                    // this context's facade implementation
│   └── internal
│       ├── commandservices    // command service implementations
│       ├── queryservices      // query service implementations
│       ├── eventhandlers      // react to domain events
│       └── outboundservices
│           └── acl            // talk to other contexts through their facades
├── domain                         // the domain model + its ports (depends on nothing)
│   ├── model
│   │   ├── aggregates
│   │   ├── entities
│   │   ├── valueobjects
│   │   ├── commands       // command types (domain)
│   │   ├── queries        // query types (domain)
│   │   └── events         // domain events
│   ├── services           // command/query service interfaces (ports)
│   └── exceptions         // domain-specific exceptions
└── infrastructure                 // outbound adaptors — the context reaches out
    └── persistence
        └── jpa
            └── repositories       // Spring Data repositories
```

**What each layer is** (dependencies always point inward, toward `domain`):

- **`interfaces` — inbound adaptors.** Where the outside world drives this context: REST controllers, message/event listeners, a CLI. They turn external input into application calls and shape the response back out. No business logic.
- **`application` — application services.** They orchestrate use cases (here split into command and query services): load aggregates, invoke their behavior, manage transactions and security. They coordinate but hold no business rules.
- **`domain` — the domain model.** Aggregates, entities, value objects, domain events, the service *interfaces* (ports), and domain exceptions. Every business rule lives here, and it depends on nothing outside itself.
- **`infrastructure` — outbound adaptors.** The technical pieces the context uses to reach external systems: the Spring Data repositories, message publishers, external API clients. They implement any ports the inner layers declare.

**Inbound vs. outbound adaptor** describes the direction of flow. An *inbound* adaptor brings a request *into* the context — e.g., a controller turning an HTTP call into a command. An *outbound* adaptor lets the context reach *out* to something external — e.g., a repository writing to the database, or an ACL service calling another context. The domain in the middle never knows about either: the inner layers declare **ports** (interfaces), and the adaptors implement them.

## The shared kernel

A `shared` package holds the small **shared kernel** every context reuses — base classes for the domain model, common REST resources, and cross-cutting technical configuration (a snake-case table-naming strategy, OpenAPI setup, database migrations). Keep it small and stable; it must never hold business rules — those belong to a bounded context.

When a project chooses the surrogate-id + auditing approach (a common alternative — see [Identity and persistence](#identity-and-persistence-choices-and-trade-offs)), a base class carries that decision. `AuditableAbstractAggregateRoot` is the base for **aggregate roots**: it extends Spring Data's `AbstractAggregateRoot` (so it can register domain events) and adds a generated surrogate id plus created/updated timestamps.

```java
// shared/domain/model/aggregates
@Getter
@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
public class AuditableAbstractAggregateRoot<T extends AbstractAggregateRoot<T>> extends AbstractAggregateRoot<T> {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @CreatedDate
    @Column(nullable = false, updatable = false)
    private Date createdAt;
    @LastModifiedDate
    @Column(nullable = false)
    private Date updatedAt;
}
```

A sibling `AuditableModel` gives the same surrogate id and timestamps to **entities inside an aggregate** that aren't the root (without the event-registration base). For the timestamps to populate, enable auditing with `@EnableJpaAuditing` on a configuration class.

The shared kernel is also the home for a generic response resource reused across contexts — for example a message returned after a delete:

```java
// shared/interfaces/rest/resources
public record MessageResource(String message) { }
```

## Value objects

Model value objects as **immutable** types. A Java `record` is the natural fit — immutable, with value equality for free. Validate in the compact constructor so invalid states cannot be built. Map them as JPA embeddables (`@Embeddable` on the type; `@Embedded` where used).

```java
public record Money(BigDecimal amount, Currency currency) {
    public Money {
        if (amount == null || currency == null) throw new IllegalArgumentException("money requires amount and currency");
        if (amount.signum() < 0) throw new IllegalArgumentException("amount cannot be negative");
    }
    public Money add(Money other) {
        if (!currency.equals(other.currency)) throw new IllegalArgumentException("cannot add different currencies");
        return new Money(amount.add(other.amount), currency);
    }
}
```

Use value objects for **typed identifiers** too, so a reference to another aggregate stays type-safe and meaningful:

```java
@Embeddable
public record CustomerId(Long value) {
    public CustomerId {
        if (value == null || value < 1) throw new IllegalArgumentException("invalid customer id");
    }
}
```

JPA needs a no-argument constructor to hydrate an embeddable, so give value objects a default constructor alongside the validating one — a record can declare its compact canonical constructor *and* a no-arg one that supplies a default:

```java
@Embeddable
public record EmailAddress(@Email String address) {
    public EmailAddress() { this(null); }   // required by JPA
}
```

A record fits most value objects, but use an `@Embeddable` **class** when the value object has to map a JPA association or collection — a record can't, because its components are final. A `LearningPath` that owns a `@OneToMany` list of items is such a case: a class with behavior, owned wholly by its aggregate and reached only through it.

## Aggregate root and entities

The aggregate root is a JPA `@Entity`. Give it real **behavior** (not just getters/setters), enforce invariants inside it, and **reference other aggregates by their typed id value object** — never map a `@ManyToOne` to another aggregate root. Extend Spring Data's `AbstractAggregateRoot` so the aggregate can register domain events (or a shared `AuditableAbstractAggregateRoot` that also adds a surrogate id and audit timestamps — see [The shared kernel](#the-shared-kernel)). A useful idiom is a constructor (or static factory) that builds the aggregate straight from a command.

```java
@Getter   // Lombok: generates getId(), getCustomerId(), getStatus(), getLines()
@Entity
public class Order extends AbstractAggregateRoot<Order> {

    @EmbeddedId
    private OrderId id;

    @Embedded
    private CustomerId customerId;        // another aggregate, referenced by typed id only

    @Enumerated(EnumType.STRING)
    private OrderStatus status;

    @ElementCollection
    private List<OrderLine> lines = new ArrayList<>();

    protected Order() { }                 // required by JPA

    public Order(PlaceOrderCommand command) {
        if (command.lines().isEmpty()) throw new IllegalArgumentException("an order needs at least one line");
        this.id = OrderId.newId();
        this.customerId = command.customerId();
        this.lines = new ArrayList<>(command.lines());
        this.status = OrderStatus.PLACED;
        registerEvent(new OrderPlaced(this, id, customerId));   // raise a domain event
    }

    public void cancel() {
        if (status == OrderStatus.SHIPPED) throw new IllegalStateException("a shipped order cannot be cancelled");
        status = OrderStatus.CANCELLED;
        registerEvent(new OrderCancelled(this, id));
    }

    public Money total() {
        return lines.stream().map(OrderLine::subtotal).reduce(Money.zero(), Money::add);
    }
}
```

Entities and value objects *inside* the aggregate (here `OrderLine`) are reached only through the root — that is what lets the root guarantee the aggregate's invariants. The Lombok `@Getter` exposes the fields for read access (the assemblers use them); all behavior stays in methods like `cancel()` and `total()`.

## Commands and queries

Make **commands** and **queries** first-class types in the domain, as records that validate their own input. A command expresses an intent to *change* state; a query expresses an intent to *read* it.

```java
public record PlaceOrderCommand(CustomerId customerId, List<OrderLine> lines) {
    public PlaceOrderCommand {
        if (customerId == null) throw new IllegalArgumentException("customerId is required");
    }
}
public record CancelOrderCommand(OrderId orderId) { }

public record GetOrderByIdQuery(OrderId orderId) { }
public record GetAllOrdersQuery() { }
```

## Command services and query services

Split the application layer along the command/query line (this is CQRS in practice — see `tactical-patterns.md`). Declare the **service interfaces in the domain** (`domain/services`) as ports, and **implement them in the application layer**.

A **command service** handles commands: it loads or creates an aggregate, invokes its behavior, persists it, and returns just an identifier. It holds **no business rules** — those live in the aggregate.

```java
// domain/services — the port
public interface OrderCommandService {
    OrderId handle(PlaceOrderCommand command);
    void handle(CancelOrderCommand command);
}

// application/internal/commandservices — the implementation
@Service
public class OrderCommandServiceImpl implements OrderCommandService {

    private final OrderRepository orders;

    public OrderCommandServiceImpl(OrderRepository orders) {
        this.orders = orders;
    }

    @Override
    @Transactional
    public OrderId handle(PlaceOrderCommand command) {
        var order = new Order(command);
        orders.save(order);              // registered domain events are published here
        return order.getId();
    }

    @Override
    @Transactional
    public void handle(CancelOrderCommand command) {
        var order = orders.findById(command.orderId())
                          .orElseThrow(() -> new IllegalArgumentException("order not found"));
        order.cancel();
        orders.save(order);
    }
}
```

A **query service** handles queries and returns entities for reading; keep it free of state changes. Like the command service, the interface is a domain port and the implementation reads through the repository.

```java
// domain/services — the port
public interface OrderQueryService {
    Optional<Order> handle(GetOrderByIdQuery query);
    List<Order> handle(GetAllOrdersQuery query);
}

// application/internal/queryservices — the implementation
@Service
public class OrderQueryServiceImpl implements OrderQueryService {

    private final OrderRepository orders;

    public OrderQueryServiceImpl(OrderRepository orders) {
        this.orders = orders;
    }

    @Override
    public Optional<Order> handle(GetOrderByIdQuery query) {
        return orders.findById(query.orderId());
    }

    @Override
    public List<Order> handle(GetAllOrdersQuery query) {
        return orders.findAll();
    }
}
```

## Repositories

Give each aggregate root a repository — collection-like access to whole aggregates by their root, one per aggregate root. The simplest and most common approach in Spring is to define a Spring Data repository **in `infrastructure`** and let command and query services depend on it directly:

```java
// infrastructure/persistence/jpa/repositories
@Repository
public interface OrderRepository extends JpaRepository<Order, OrderId> {
    Optional<Order> findByCustomerId(CustomerId customerId);   // finders named in the ubiquitous language
}
```

`JpaRepository` gives you `save`, `findById`, and the rest; add finders named in the domain's language, and keep them about whole aggregates (not arbitrary inner entities). The trade-off is that the application layer now depends on an infrastructure type.

> **Alternative — a domain port.** To keep the domain *and* the application free of any dependency on the persistence framework, declare a plain repository interface in the `domain` layer as a **port**, implemented in `infrastructure`:
>
> ```java
> // domain/repositories — no framework leakage
> public interface OrderRepository {
>     Optional<Order> findById(OrderId id);
>     Order save(Order order);
> }
>
> // infrastructure — Spring Data satisfies the port
> interface OrderJpaRepository extends JpaRepository<Order, OrderId>, OrderRepository { }
> ```
>
> This is the purer, hexagonal-style choice; the cost is a little more indirection. Prefer it when isolating the domain from infrastructure matters for the project.

## Domain events

Model each event as a class in the domain, named in the past tense, extending Spring's `ApplicationEvent`. Keep the payload `final` (an event is an immutable fact) and take the source that raised it as the first constructor argument:

```java
// domain/model/events
@Getter
public class OrderPlaced extends ApplicationEvent {
    private final OrderId orderId;
    private final CustomerId customerId;

    public OrderPlaced(Object source, OrderId orderId, CustomerId customerId) {
        super(source);                 // the aggregate that raised the event
        this.orderId = orderId;
        this.customerId = customerId;
    }
}
```

The aggregate raises it from inside its own behavior with `registerEvent`, passing itself as the source (as shown in `Order` above). Because the aggregate extends `AbstractAggregateRoot`, Spring Data **publishes the registered events automatically when the aggregate is saved**. Handle them in `application/internal/eventhandlers` — a `@Service` whose method reacts to the event and orchestrates the follow-up through the relevant services:

```java
// application/internal/eventhandlers
@Service
public class OrderPlacedHandler {
    @EventListener
    public void on(OrderPlaced event) {
        // react via the relevant services — notify kitchen, start dispatch, award points (event.getOrderId())
    }
}
```

`@EventListener` runs the handler synchronously, inside the same transaction that saved the aggregate — the simplest option. Switch to `@TransactionalEventListener` when the handler must run only **after** the transaction commits (e.g. sending an email or calling an external system that must not fire if the write rolls back). Spring can also publish a plain POJO as an event, so a record works too; extending `ApplicationEvent` keeps the event explicit and carries the source that raised it.

## Anti-corruption layer

When this context needs something from **another** bounded context, do not import its model. The provider context exposes a **facade interface** (in its `interfaces/acl`) and implements it in `application/acl`, returning only primitives or ids — never its own domain types. The consumer calls that facade through an **outbound ACL service** that translates the result into *its own* value objects. This is the strategic anti-corruption layer, realized in code.

```java
// Customer context exposes — customer/interfaces/acl
public interface CustomerContextFacade {
    Long fetchCustomerIdByEmail(String email);
}

// Customer context implements — customer/application/acl
@Service
public class CustomerContextFacadeImpl implements CustomerContextFacade {
    private final CustomerQueryService customerQueryService;
    public CustomerContextFacadeImpl(CustomerQueryService customerQueryService) {
        this.customerQueryService = customerQueryService;
    }
    @Override
    public Long fetchCustomerIdByEmail(String email) {
        return customerQueryService.handle(new GetCustomerByEmailQuery(email))
            .map(Customer::getId).orElse(0L);   // 0 signals "not found" across the boundary
    }
}

// Ordering context consumes — ordering/application/internal/outboundservices/acl
@Service
public class ExternalCustomerService {
    private final CustomerContextFacade customers;
    public ExternalCustomerService(CustomerContextFacade customers) { this.customers = customers; }

    public Optional<CustomerId> fetchCustomerByEmail(String email) {
        var id = customers.fetchCustomerIdByEmail(email);
        return id == 0L ? Optional.empty() : Optional.of(new CustomerId(id));  // translate to our VO
    }
}
```

## Interfaces (REST)

The interfaces layer is where the outside drives the context, and it has three parts:

- **`resources`** — the request and response DTOs (records); the public API contract, with no domain types.
- **`transform`** — small static assemblers, one per direction: a request resource → a command, and an entity → a response resource.
- the **controller** (in `interfaces/rest/controllers`) — a thin orchestrator that wires resources and assemblers to the command and query services.

**Resources** validate their input (request) and expose only what the API returns (response):

```java
// interfaces/rest/resources
public record PlaceOrderResource(Long customerId, List<OrderLineResource> lines) {
    public PlaceOrderResource {
        if (customerId == null) throw new IllegalArgumentException("customerId is required");
        if (lines == null || lines.isEmpty()) throw new IllegalArgumentException("at least one line is required");
    }
}
public record OrderLineResource(Long itemId, int quantity) { }

public record OrderResource(Long id, Long customerId, String status, BigDecimal total) { }
```

**Transformers** are static assemblers — one turns a request resource into a command (translating wire types into domain value objects), the other turns an entity into a response resource:

```java
// interfaces/rest/transform
public class PlaceOrderCommandFromResourceAssembler {
    public static PlaceOrderCommand toCommandFromResource(PlaceOrderResource resource) {
        var lines = resource.lines().stream()
            .map(line -> new OrderLine(new ItemId(line.itemId()), line.quantity()))
            .toList();
        return new PlaceOrderCommand(new CustomerId(resource.customerId()), lines);
    }
}

public class OrderResourceFromEntityAssembler {
    public static OrderResource toResourceFromEntity(Order order) {
        return new OrderResource(order.getId().value(), order.getCustomerId().value(),
                order.getStatus().name(), order.total().amount());
    }
}
```

**The controller** turns a request resource into a command, handles it, and — for a write — *queries* the result to build the response. It holds no business logic, and no domain types appear in its signatures.

```java
// interfaces/rest/controllers
@RestController
@RequestMapping("/api/v1/orders")
class OrdersController {
    private final OrderCommandService orderCommandService;
    private final OrderQueryService orderQueryService;

    OrdersController(OrderCommandService orderCommandService, OrderQueryService orderQueryService) {
        this.orderCommandService = orderCommandService;
        this.orderQueryService = orderQueryService;
    }

    @PostMapping
    ResponseEntity<OrderResource> placeOrder(@RequestBody PlaceOrderResource resource) {
        var command = PlaceOrderCommandFromResourceAssembler.toCommandFromResource(resource);
        var orderId = orderCommandService.handle(command);
        return orderQueryService.handle(new GetOrderByIdQuery(orderId))
            .map(order -> new ResponseEntity<>(OrderResourceFromEntityAssembler.toResourceFromEntity(order), HttpStatus.CREATED))
            .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/{orderId}")
    ResponseEntity<OrderResource> getOrderById(@PathVariable Long orderId) {
        return orderQueryService.handle(new GetOrderByIdQuery(new OrderId(orderId)))
            .map(order -> ResponseEntity.ok(OrderResourceFromEntityAssembler.toResourceFromEntity(order)))
            .orElseGet(() -> ResponseEntity.notFound().build());
    }
}
```

The flow runs end to end: **resource → (assembler) → command → command service → id → query service → entity → (assembler) → resource**. After a write the controller re-queries, so the response reflects the stored state.

## Domain exceptions and error handling

Express failures in the **ubiquitous language**, not as generic errors. Define domain-specific exceptions in `domain/exceptions`, thrown by the domain (or its services) when an invariant breaks or an aggregate is missing:

```java
// domain/exceptions
public class OrderNotFoundException extends RuntimeException {
    public OrderNotFoundException(OrderId id) {
        super("Order with id %s not found".formatted(id.value()));
    }
}
```

Keep these exceptions free of web/HTTP concerns — no status codes inside them. That preserves domain purity and lets the same exception surface over REST, messaging, or a CLI.

Translate them to transport responses at the edge, in **one place**: a `@RestControllerAdvice` in the interfaces layer maps each exception to a status code, so controllers stay clean.

```java
// interfaces/rest — one handler for the whole app
@RestControllerAdvice
class GlobalExceptionHandler {

    @ExceptionHandler(OrderNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    ErrorResponse handle(OrderNotFoundException ex) {
        return ErrorResponse.create(ex, HttpStatusCode.valueOf(404), ex.getMessage());
    }

    @ExceptionHandler(IllegalArgumentException.class)   // e.g. value-object validation failures
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    ErrorResponse handle(IllegalArgumentException ex) {
        return ErrorResponse.create(ex, HttpStatusCode.valueOf(400), ex.getMessage());
    }
}
```

This pairs a clear domain vocabulary for failures with a single, centralized place that decides how each failure looks to the outside.

## Identity and persistence: choices and trade-offs

Three honest choices, each with a primary recommendation and a common alternative:

- **Identity — typed id vs. surrogate base class.** *Primary:* a typed id value object (`OrderId` as `@EmbeddedId`) keeps identity a domain concept and type-safe. *Alternative (very common):* the shared `AuditableAbstractAggregateRoot` base class with a generated `Long` surrogate id and audit timestamps (see [The shared kernel](#the-shared-kernel)); even then, keep typed id value objects for *cross-aggregate references* (`CustomerId`, not bare `Long`).
- **Repository — infrastructure-only vs. domain port.** Covered above: the default here is a Spring Data repository in `infrastructure` that services use directly (simplest, and the common convention); declare a domain port instead when you want the persistence dependency kept out of the domain.
- **Domain purity — JPA in the domain.** Annotating domain entities with JPA (as shown) is idiomatic and fine for most projects; the cost is a soft dependency on the persistence framework. For maximum isolation, keep the domain as plain Java and map to a separate persistence model in `infrastructure`, at the cost of mapping boilerplate.

Whichever you pick, hold the non-negotiables: business rules and invariants stay in the domain model, and the domain never depends on `interfaces` or `application`.
