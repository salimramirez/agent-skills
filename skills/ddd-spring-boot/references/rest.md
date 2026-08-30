# Interfaces (REST)

The inbound REST adaptor: resources, assemblers, and controllers.

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
