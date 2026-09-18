# Domain events

Raising an event from the aggregate, publishing it on save, and reacting in the application layer.

## The event

A class in `domain/model/events`, named for what happened, extending Spring's `ApplicationEvent`. The payload is `final` — an event is a fact, and facts do not change — and holds ids and value objects, never the aggregate:

```java
@Getter
public class OrderPlacedEvent extends ApplicationEvent {
    private final Long orderId;
    private final CustomerId customerId;

    public OrderPlacedEvent(Object source, Long orderId, CustomerId customerId) {
        super(source);
        this.orderId = orderId;
        this.customerId = customerId;
    }
}
```

`source` is the aggregate that raised it, which is what `ApplicationEvent` asks for; the handler does not read it — it reads the ids and queries what it needs.

## Raising it

The aggregate registers the event inside the method that makes it true, through `addDomainEvent` from the base class:

```java
    public void place() {
        if (!isDraft()) throw new IllegalStateException("Only a draft order can be placed");
        if (lines.isEmpty()) throw new IllegalStateException("An order needs at least one line to be placed");
        this.status = OrderStatus.PLACED;
        this.addDomainEvent(new OrderPlacedEvent(this, this.getId(), this.customerId));
    }
```

Nothing is published yet. `AbstractAggregateRoot` keeps the registered events, and Spring Data publishes them **when the aggregate is saved** — `orderRepository.save(order)` in the command service is the moment the handlers run. An event registered on an aggregate that is never saved is never published, which is exactly right: what did not get persisted did not happen.

Register the event *after* the state change, and pass `this.getId()` only on an aggregate that already has one. A creation event registered from the constructor would carry a `null` id, because the id is assigned by the insert. If a "created" event is needed, the command service publishes it after `save` has returned, through an injected `ApplicationEventPublisher` — `applicationEventPublisher.publishEvent(new OrderCreatedEvent(this, order.getId()))` — which is the one case where an event is not registered on the aggregate.

## Handling it

A `@Service` in `application/internal/eventhandlers`, with one method named `on`:

```java
@Service
public class OrderPlacedEventHandler {
    private static final Logger LOGGER = LoggerFactory.getLogger(OrderPlacedEventHandler.class);

    @EventListener
    public void on(OrderPlacedEvent event) {
        LOGGER.info("Order {} placed by customer {}", event.getOrderId(), event.getCustomerId().customerId());
    }
}
```

The handler orchestrates the follow-up through services — it builds a command and hands it to a command service, the same way a controller would — and holds no rule of its own. A handler that updates a second aggregate (the customer's order count, say) is the house way of keeping two aggregates consistent: each is saved in its own transaction, and the event is the link.

`@EventListener` runs **synchronously, on the same thread, inside the transaction of the `save` that published it** — so when the handler throws, the save rolls back with it, and when it is slow, the request is slow. That is the simple, predictable default. Use `@TransactionalEventListener` instead when the reaction must happen only if the save committed and must not undo it — sending an email, calling another system; it fires after the commit. Do not make handlers `@Async` until a measured problem asks for it.

## Events the framework raises

The same `@EventListener` shape serves Spring's own events. Seeding reference data on startup is the recurring case:

```java
@Service
public class ApplicationReadyEventHandler {
    private final RoleCommandService roleCommandService;
    private static final Logger LOGGER = LoggerFactory.getLogger(ApplicationReadyEventHandler.class);

    public ApplicationReadyEventHandler(RoleCommandService roleCommandService) {
        this.roleCommandService = roleCommandService;
    }

    @EventListener
    public void on(ApplicationReadyEvent event) {
        var applicationName = event.getApplicationContext().getId();
        LOGGER.info("Starting to verify if roles seeding is needed for {} at {}", applicationName, currentTimestamp());
        var seedRolesCommand = new SeedRolesCommand();
        roleCommandService.handle(seedRolesCommand);
        LOGGER.info("Roles seeding verification finished for {} at {}", applicationName, currentTimestamp());
    }

    private Timestamp currentTimestamp() {
        return new Timestamp(System.currentTimeMillis());
    }
}
```

Even here the handler does not touch a repository: it issues a command, and `RoleCommandServiceImpl` decides what seeding means (`existsByName` before each `save`, so a restart adds nothing twice).
