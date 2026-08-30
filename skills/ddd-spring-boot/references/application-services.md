# Commands, queries, and their services

Commands and queries as records, and the command and query services that execute them.

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

Split the application layer along the command/query line — this is CQRS in its light form: one model, one store. Declare the **service interfaces in the domain** (`domain/services`) as ports, and **implement them in the application layer**.

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
