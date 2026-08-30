# Domain events

Raising domain events from an aggregate and handling them in the application layer.

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

The aggregate raises it from inside its own behavior with `registerEvent`, passing itself as the source (as shown in `Order` in `aggregates.md`). Because the aggregate extends `AbstractAggregateRoot`, Spring Data **publishes the registered events automatically when the aggregate is saved**. Handle them in `application/internal/eventhandlers` — a `@Service` whose method reacts to the event and orchestrates the follow-up through the relevant services:

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
