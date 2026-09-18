# REST: resources, assemblers, controllers

The inbound adaptor: what crosses the wire, how it becomes a command, and how an aggregate becomes a response.

The `interfaces/rest` package of a context has three parts, and the flow through them is always the same:

**resource → assembler → command → command service → id → query service → aggregate → assembler → resource**

## Resources are records of primitives

A request resource validates its own presence rules in the compact constructor; a response resource is a plain record. Neither mentions a domain type:

```java
public record CreateOrderResource(String customerEmail, String currency) {
    public CreateOrderResource {
        if (customerEmail == null || customerEmail.isBlank()) {
            throw new IllegalArgumentException("Customer email is required");
        }
        if (currency == null || currency.isBlank()) {
            throw new IllegalArgumentException("Currency is required");
        }
    }
}

public record OrderResource(Long id, String code, Long customerId, String status, String currency,
                            BigDecimal total, List<OrderLineResource> lines) {
}
```

When Jackson builds a `CreateOrderResource` from the body and the constructor throws, the `IllegalArgumentException` reaches the shared `GlobalExceptionHandler` — Spring looks through the causes of the deserialization failure — and the client gets a 400 with `"detail": "Customer email is required"`. No `@Valid` needed. Bean Validation (`@Valid @RequestBody`, `@NotBlank` on the components) is the other way to get the same 400 and is fine when the messages must be localized; do not mix the two on one resource.

## Assemblers are static, one per direction

```java
public class CreateOrderCommandFromResourceAssembler {
    public static CreateOrderCommand toCommandFromResource(CreateOrderResource resource) {
        return new CreateOrderCommand(resource.customerEmail(), Currency.getInstance(resource.currency()));
    }
}

public class OrderResourceFromEntityAssembler {
    public static OrderResource toResourceFromEntity(Order entity) {
        var lines = entity.getLines().stream()
                .map(OrderLineResourceFromEntityAssembler::toResourceFromEntity)
                .toList();
        return new OrderResource(entity.getId(), entity.getCode().code(), entity.getCustomerId().customerId(),
                entity.getStatus().name().toLowerCase(), entity.getCurrency().getCurrencyCode(),
                entity.total().amount(), lines);
    }
}
```

The resource-to-command assembler is where wire primitives become value objects (`Currency.getInstance`, `new MenuItemId(...)`, `new Money(...)`); the entity-to-resource assembler is where value objects become primitives again. Nothing else does either conversion. When the command needs something the body does not carry — the id from the path, the order's currency to price a line — the assembler takes it as an extra argument: `toCommandFromResource(orderId, currency, resource)`.

## The controller

```java
@RestController
@RequestMapping(value = "/api/v1/orders", produces = APPLICATION_JSON_VALUE)
@Tag(name = "Orders", description = "Available Order Endpoints")
public class OrdersController {
    private final OrderCommandService orderCommandService;
    private final OrderQueryService orderQueryService;

    public OrdersController(OrderCommandService orderCommandService, OrderQueryService orderQueryService) {
        this.orderCommandService = orderCommandService;
        this.orderQueryService = orderQueryService;
    }

    @PostMapping
    @Operation(summary = "Create a draft order", description = "Create a draft order for a customer, priced in one currency")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "201", description = "Order created"),
            @ApiResponse(responseCode = "400", description = "Invalid input"),
            @ApiResponse(responseCode = "404", description = "Customer not found")})
    public ResponseEntity<OrderResource> createOrder(@RequestBody CreateOrderResource resource) {
        var createOrderCommand = CreateOrderCommandFromResourceAssembler.toCommandFromResource(resource);
        var orderId = orderCommandService.handle(createOrderCommand);
        if (orderId == null || orderId == 0L) return ResponseEntity.badRequest().build();
        var getOrderByIdQuery = new GetOrderByIdQuery(orderId);
        var order = orderQueryService.handle(getOrderByIdQuery);
        if (order.isEmpty()) return ResponseEntity.notFound().build();
        var orderEntity = order.get();
        var orderResource = OrderResourceFromEntityAssembler.toResourceFromEntity(orderEntity);
        return new ResponseEntity<>(orderResource, HttpStatus.CREATED);
    }

    @GetMapping("/{orderId}")
    @Operation(summary = "Get order by id", description = "Get order by id")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Order found"),
            @ApiResponse(responseCode = "404", description = "Order not found")})
    public ResponseEntity<OrderResource> getOrderById(@PathVariable Long orderId) {
        var getOrderByIdQuery = new GetOrderByIdQuery(orderId);
        var order = orderQueryService.handle(getOrderByIdQuery);
        if (order.isEmpty()) return ResponseEntity.notFound().build();
        var orderEntity = order.get();
        var orderResource = OrderResourceFromEntityAssembler.toResourceFromEntity(orderEntity);
        return ResponseEntity.ok(orderResource);
    }

    @GetMapping
    @Operation(summary = "Get all orders", description = "Get all orders, or only those of a customer")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Orders found")})
    public ResponseEntity<List<OrderResource>> getAllOrders(
            @Parameter(description = "Customer id to filter by") @RequestParam(required = false) Long customerId) {
        var orders = customerId == null
                ? orderQueryService.handle(new GetAllOrdersQuery())
                : orderQueryService.handle(new GetAllOrdersByCustomerIdQuery(new CustomerId(customerId)));
        var orderResources = orders.stream()
                .map(OrderResourceFromEntityAssembler::toResourceFromEntity)
                .toList();
        return ResponseEntity.ok(orderResources);
    }
}
```

The rules the controller follows:

- **A write re-queries.** `createOrder` gets an id back and asks the query service for the aggregate, so the response is what was stored — not what the controller thinks it sent. It also keeps the command service's return type an id, not a resource.
- **`Optional` is unwrapped in two lines**: `if (order.isEmpty()) return ResponseEntity.notFound().build();` then `var orderEntity = order.get();`. The `.map(...).orElseGet(...)` chain is shorter and reads worse once there are three steps.
- **Status codes**: 201 with the body for a create, 200 for a read and an update, 404 when a read finds nothing, and **200 with `[]`** when a collection is empty — an empty list is a successful answer, not a missing resource. 400 and 409 never appear in a controller: they come from the exception advice.
- **Filtering is a query parameter on the collection**, `GET /api/v1/orders?customerId=1`, dispatched to the matching query. A parameter that is not a filter but a different resource gets its own path instead.
- **The controller holds no logic and no repository.** It names the two services in its constructor and nothing else.

Update and delete follow the same shape — `@PutMapping("/{orderId}")` returning the updated resource, `@DeleteMapping("/{orderId}")` returning a `MessageResource` — and the generated context template writes both. Transitions and nested resources are in `state-transitions.md`.
