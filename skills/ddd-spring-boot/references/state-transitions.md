# State transitions and nested resources

Endpoints for the operations that are not CRUD: placing, cancelling, confirming, adding a part to a whole.

## A transition is a POST to a sub-resource

`place()` is not an update of the `status` field; it is a thing that happens to an order. The URL says so — a plural noun under the aggregate, in the past tense of the event it causes — and the response is a `MessageResource`, because there is no new resource to return:

```java
    @PostMapping("/{orderId}/placements")
    @Operation(summary = "Place order", description = "Place a draft order")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Order placed"),
            @ApiResponse(responseCode = "404", description = "Order not found"),
            @ApiResponse(responseCode = "409", description = "Order cannot be placed in its current state")})
    public ResponseEntity<MessageResource> placeOrder(@PathVariable Long orderId) {
        var placeOrderCommand = new PlaceOrderCommand(orderId);
        var placedOrderId = orderCommandService.handle(placeOrderCommand);
        return ResponseEntity.ok(new MessageResource("Order %s placed".formatted(placedOrderId)));
    }

    @PostMapping("/{orderId}/cancellations")
    public ResponseEntity<MessageResource> cancelOrder(@PathVariable Long orderId) {
        var cancelOrderCommand = new CancelOrderCommand(orderId);
        var cancelledOrderId = orderCommandService.handle(cancelOrderCommand);
        return ResponseEntity.ok(new MessageResource("Order %s cancelled".formatted(cancelledOrderId)));
    }
}
```

There is no assembler because there is no body: the command is built from the path variable. The command service returns the id it acted on, and the two failure cases never reach this method — `OrderNotFoundException` becomes a 404 in the context's advice, and the `IllegalStateException` the aggregate throws for an order that is not a draft becomes a 409 in the shared one.

`placements`, `cancellations`, `confirmations`, `rejections`: the noun is what the transition produces. `POST /orders/1/cancel` would work too; it just stops being a resource.

## A part of the aggregate is a nested resource

Lines belong to an order, so they are addressed under it, in their own controller that shares the parent's `@Tag`:

```java
@RestController
@RequestMapping(value = "/api/v1/orders/{orderId}/lines", produces = APPLICATION_JSON_VALUE)
@Tag(name = "Orders")
public class OrderLinesController {
    private final OrderCommandService orderCommandService;
    private final OrderQueryService orderQueryService;

    public OrderLinesController(OrderCommandService orderCommandService, OrderQueryService orderQueryService) {
        this.orderCommandService = orderCommandService;
        this.orderQueryService = orderQueryService;
    }

    @PostMapping
    @Operation(summary = "Add a line to a draft order")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "201", description = "Line added"),
            @ApiResponse(responseCode = "404", description = "Order not found"),
            @ApiResponse(responseCode = "409", description = "Order is no longer a draft")})
    public ResponseEntity<OrderResource> addLineToOrder(@PathVariable Long orderId, @RequestBody AddLineToOrderResource resource) {
        var order = orderQueryService.handle(new GetOrderByIdQuery(orderId));
        if (order.isEmpty()) return ResponseEntity.notFound().build();
        var addLineToOrderCommand = AddLineToOrderCommandFromResourceAssembler.toCommandFromResource(orderId, order.get().getCurrency(), resource);
        orderCommandService.handle(addLineToOrderCommand);
        var updatedOrder = orderQueryService.handle(new GetOrderByIdQuery(orderId));
        if (updatedOrder.isEmpty()) return ResponseEntity.notFound().build();
        var orderResource = OrderResourceFromEntityAssembler.toResourceFromEntity(updatedOrder.get());
        return new ResponseEntity<>(orderResource, HttpStatus.CREATED);
    }
}
```

Two things worth copying from it:

- **The nested controller talks to the parent's services.** There is no `OrderLineCommandService` and no `OrderLineRepository`: a line is added *through* the order, because the order is what decides whether it may be (`Lines can only be added to a draft order`). The aggregate is the transaction boundary and the nested URL respects it.
- **The response is the whole aggregate**, freshly queried, with the new line in it and the total recomputed. The client learns what actually changed, and the assembler is the same one every other endpoint uses.

The same shape serves a nested read — `GET /api/v1/customers/{customerId}/orders` in a `CustomerOrdersController` that dispatches `GetAllOrdersByCustomerIdQuery` — when the parent path is the natural way to ask for the collection, and the query parameter on `/orders` is the alternative when it is only a filter.

## Consulting by parameters

When a collection endpoint answers different questions depending on which parameters arrive, dispatch on the parameter set and keep each answer a private method, so the public one stays a table of contents. Declare the parameters for the documentation, since a `Map` hides them from it:

```java
    @GetMapping
    @Parameters({
            @Parameter(name = "customerId", description = "Customer id", required = true),
            @Parameter(name = "status", description = "Order status")})
    public ResponseEntity<?> getOrdersWithParameters(
            @Parameter(name = "params", hidden = true) @RequestParam Map<String, String> params) {
        if (params.containsKey("customerId") && params.containsKey("status")) {
            return getAllOrdersByCustomerIdAndStatus(params.get("customerId"), params.get("status"));
        } else if (params.containsKey("customerId")) {
            return getAllOrdersByCustomerId(params.get("customerId"));
        } else {
            return ResponseEntity.badRequest().build();
        }
    }
```

Reach for this when there are three or more combinations; with one optional filter, a plain `@RequestParam(required = false)` as in `rest.md` is clearer.
