# Commands, queries, and their services

Commands and queries as records in the domain, the service interfaces that accept them, and the implementations that execute them.

## Commands and queries are records that validate themselves

A command is an intent to change state; a query is an intent to read it. Both are records in `domain/model`, and both reject bad input in the compact constructor, so a service never has to:

```java
public record CreateOrderCommand(String customerEmail, Currency currency) {
    public CreateOrderCommand {
        if (customerEmail == null || customerEmail.isBlank()) {
            throw new IllegalArgumentException("customerEmail cannot be null or blank");
        }
        if (currency == null) {
            throw new IllegalArgumentException("currency cannot be null");
        }
    }
}

public record PlaceOrderCommand(Long orderId) {
    public PlaceOrderCommand {
        if (orderId == null || orderId <= 0) {
            throw new IllegalArgumentException("orderId cannot be null or less than 1");
        }
    }
}

public record GetOrderByIdQuery(Long orderId) {
    public GetOrderByIdQuery {
        if (orderId == null || orderId <= 0) {
            throw new IllegalArgumentException("orderId cannot be null or less than 1");
        }
    }
}

public record GetAllOrdersQuery() {
}
```

Carry value objects where the domain has them — `AddLineToOrderCommand(Long orderId, MenuItemId menuItemId, int quantity, Money unitPrice)`, `GetAllOrdersByCustomerIdQuery(CustomerId customerId)` — and the aggregate's own `Long` id where the command names the aggregate it acts on. The assembler at the edge is what turns wire primitives into those value objects; by the time a command exists, its contents are already valid.

`GetAllOrdersQuery()` has no components and still exists, so that "all orders" is a thing with a name that the query service can be asked for.

## The service interfaces are ports, and they live in the domain

`domain/services` declares what the context can be asked to do. Every method is called `handle` and is overloaded on the command or query type — the type *is* the operation name:

```java
public interface OrderCommandService {
    Long handle(CreateOrderCommand command);
    Long handle(AddLineToOrderCommand command);
    Long handle(PlaceOrderCommand command);
    Long handle(CancelOrderCommand command);
}

public interface OrderQueryService {
    Optional<Order> handle(GetOrderByIdQuery query);
    Optional<Order> handle(GetOrderByCodeQuery query);
    List<Order> handle(GetAllOrdersQuery query);
    List<Order> handle(GetAllOrdersByCustomerIdQuery query);
}
```

Return types follow a small table, so a controller knows what to expect without reading the implementation:

| Command | Returns |
| --- | --- |
| create | `Long` — the new id; the controller re-queries with it |
| update of plain attributes | `Optional<Order>` — the saved aggregate |
| delete | `void` |
| a state transition (place, cancel, confirm) | `Long` — the id of the aggregate it acted on |
| a query for one | `Optional<Order>` |
| a query for many | `List<Order>` — empty, never `null` |
| an existence check | `boolean` |

## The command service implementation

In `application/internal/commandservices`, a `@Service` with the repository and whatever outbound services it needs, injected through the constructor. Each `handle` does the same four things: check what only the whole collection can know, load or create the aggregate, ask it to act, save it.

```java
@Service
public class OrderCommandServiceImpl implements OrderCommandService {
    private final OrderRepository orderRepository;
    private final ExternalCustomerService externalCustomerService;

    public OrderCommandServiceImpl(OrderRepository orderRepository, ExternalCustomerService externalCustomerService) {
        this.orderRepository = orderRepository;
        this.externalCustomerService = externalCustomerService;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Long handle(CreateOrderCommand command) {
        var customerId = externalCustomerService.fetchCustomerByEmail(command.customerEmail())
                .orElseThrow(() -> new CustomerNotFoundException(command.customerEmail()));
        var order = new Order(customerId, command);
        orderRepository.save(order);
        return order.getId();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Long handle(PlaceOrderCommand command) {
        return orderRepository.findById(command.orderId()).map(order -> {
            order.place();
            orderRepository.save(order);
            return order.getId();
        }).orElseThrow(() -> new OrderNotFoundException(command.orderId()));
    }
}
```

Three things to notice:

- **The rule is in the aggregate.** The service calls `order.place()`; it does not check the status first. If it did, the same rule would exist twice and drift.
- **Uniqueness is the service's job**, because only the repository can see the whole collection: `if (orderRepository.existsByCode(command.code())) throw new IllegalArgumentException("Order with code %s already exists".formatted(…))`. On an update, the check excludes the aggregate itself — `existsByNameAndIdIsNot(command.name(), command.id())`.
- **`findById(...).map(...).orElseThrow(...)` is one expression, and the `map` returns the id.** The value of the chain *is* the method's return value; nothing is returned after it.

The generated context template shows the create / update / delete trio with the `Optional<Entity>` update and the `void` delete; this reference shows the transitions. Both follow the table above.

### On `@Transactional`

Every Spring Data `save` runs in its own transaction, and `@EventListener` handlers run inside it (see `domain-events.md`), so a `handle` that loads one aggregate, changes it and saves it once needs nothing more — the methods above have no `@Transactional`, and that is the house default. Add `@Transactional` to a `handle` when it saves **two** things that must stand or fall together — two aggregates, or an aggregate and an outbox row. Even then, prefer to let a domain event carry the second change, so each aggregate keeps its own transaction.

## The query service implementation

In `application/internal/queryservices`, the same shape, and every method is one line that delegates to the repository:

```java
@Service
public class OrderQueryServiceImpl implements OrderQueryService {
    private final OrderRepository orderRepository;

    public OrderQueryServiceImpl(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Optional<Order> handle(GetOrderByIdQuery query) {
        return orderRepository.findById(query.orderId());
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public List<Order> handle(GetAllOrdersByCustomerIdQuery query) {
        return orderRepository.findAllByCustomerId(query.customerId());
    }
}
```

A query service returns aggregates, not resources: the assembler in `interfaces` shapes them for the wire. It also never changes anything. If a "query" needs to write, it is a command with a bad name.
