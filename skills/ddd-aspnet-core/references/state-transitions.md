# State transitions and nested resources

Endpoints for what is not CRUD: placing, cancelling, adding a part to a whole, filtering a collection.

## A transition is a `POST` to a plural noun

`Place()` is not an update of the `Status` property; it is something that happens to an order. The URL says so — a plural noun under the aggregate, naming what the transition produces — and the action calls the use case:

```csharp
/// <summary>
///     Sends a draft order to the restaurant.
/// </summary>
/// <param name="orderId">The identity of the order.</param>
/// <param name="cancellationToken">Cancels the request.</param>
/// <response code="200">The placed order.</response>
/// <response code="404">There is no order with that identity.</response>
/// <response code="409">The order is not a draft, or has no lines.</response>
[HttpPost("{orderId:int}/placements")]
[ProducesResponseType<OrderResource>(StatusCodes.Status200OK)]
[ProducesResponseType(StatusCodes.Status404NotFound)]
[ProducesResponseType(StatusCodes.Status409Conflict)]
public async Task<IActionResult> PlaceOrder(int orderId, CancellationToken cancellationToken)
{
    var result = await orderCommandService.Handle(new PlaceOrderCommand(orderId), cancellationToken);
    return result.ToActionResult(this, order => Ok(OrderResourceFromEntityAssembler.ToResourceFromEntity(order)));
}
```

- **`placements`, `cancellations`, `confirmations`, `rejections`.** `POST /orders/1/place` would work too; it just stops being a resource, and the next transition gets named differently.
- **A transition with data takes a body** (a reason for the cancellation, a time for the delivery); one without takes none.
- **It answers 200 with the resource after the change.** The client sees the new status, the recomputed total, whatever the transition touched, without a second request. A transition that produces something with its own identity — a refund, an invoice — answers 201 with *that* instead.
- **The two failures never reach the action.** A missing order is the service's `NotFound` → 404; an order the transition does not apply to is the `BusinessRuleViolationException` the aggregate throws → 409, answered by the exception handler.

Measured, on one order: placing it with no lines → 409 "Cannot place an order without lines."; with a line → 200 and `"status": "Placed"`; placing it again → 409 "Cannot place an order that is Placed."; adding a line to it → 409; cancelling it → 200 and `"status": "Cancelled"`.

Never `PUT /orders/1` with `{"status": "Placed"}`, nor a `PATCH` of the status. That makes the status a field a client can set, and the rules of `Place()` — only from a draft, not empty, record the event — either get skipped or get reimplemented in the controller.

## A part of the aggregate is a nested resource

Lines belong to an order, so they are addressed under it, in the same controller:

```csharp
[HttpPost("{orderId:int}/lines")]
[ProducesResponseType<OrderResource>(StatusCodes.Status201Created)]
[ProducesResponseType(StatusCodes.Status400BadRequest)]
[ProducesResponseType(StatusCodes.Status404NotFound)]
[ProducesResponseType(StatusCodes.Status409Conflict)]
public async Task<IActionResult> AddOrderLine(
    int orderId, AddOrderLineResource resource, CancellationToken cancellationToken)
{
    var command = AddOrderLineCommandFromResourceAssembler.ToCommandFromResource(orderId, resource);
    var result = await orderCommandService.Handle(command, cancellationToken);
    return result.ToActionResult(this, order => CreatedAtAction(
        nameof(GetOrderById),
        new { orderId = order.Id },
        OrderResourceFromEntityAssembler.ToResourceFromEntity(order)));
}

[HttpDelete("{orderId:int}/lines/{orderLineId:int}")]
[ProducesResponseType<OrderResource>(StatusCodes.Status200OK)]
[ProducesResponseType(StatusCodes.Status404NotFound)]
[ProducesResponseType(StatusCodes.Status409Conflict)]
public async Task<IActionResult> RemoveOrderLine(int orderId, int orderLineId, CancellationToken cancellationToken)
{
    var result = await orderCommandService.Handle(
        new RemoveOrderLineCommand(orderId, orderLineId), cancellationToken);
    return result.ToActionResult(this, order => Ok(OrderResourceFromEntityAssembler.ToResourceFromEntity(order)));
}
```

- **Adding a part answers 201 with the whole order**, and the `Location` of the order: the line has no address of its own to fetch, and the client wants the new total anyway.
- **Removing a part answers 200 with the order**, not 204: the order changed, and the response shows how.
- **The command carries both identities** (`RemoveOrderLineCommand(int OrderId, int OrderLineId)`), and the service answers 404 for either one missing — a line that is not in this order is not found, even if a line with that number exists in another order:

```csharp
var order = await orderRepository.FindByIdAsync(command.OrderId, cancellationToken);
if (order is null) return Result<Order>.NotFound($"Order {command.OrderId} was not found.");
if (!order.HasLine(command.OrderLineId))
    return Result<Order>.NotFound($"Order {command.OrderId} has no line {command.OrderLineId}.");

order.RemoveLine(command.OrderLineId);
```

`HasLine` is a question the aggregate answers; the service asks it instead of searching `order.Lines` itself.

A part that is a separate aggregate — reviews of a restaurant, deliveries of an order — is not nested this way. It has its own controller and its own repository, and the relationship is a filter on its collection.

## Filtering a collection is a query parameter

The orders of one customer are the collection of orders, filtered — not a new resource:

```csharp
[HttpGet]
[ProducesResponseType<IEnumerable<OrderResource>>(StatusCodes.Status200OK)]
[ProducesResponseType(StatusCodes.Status400BadRequest)]
public async Task<IActionResult> GetOrders([FromQuery] int? customerId, CancellationToken cancellationToken)
{
    var orders = customerId is null
        ? await orderQueryService.Handle(new GetAllOrdersQuery(), cancellationToken)
        : await orderQueryService.Handle(
            new GetOrdersByCustomerIdQuery(new CustomerId(customerId.Value)), cancellationToken);
    return Ok(orders.Select(OrderResourceFromEntityAssembler.ToResourceFromEntity));
}
```

`GET /api/v1/orders?customerId=3` lists that customer's orders; `GET /api/v1/orders` lists them all. The controller builds the query's value object from the parameter, so `?customerId=-4` is refused by `CustomerId` — a 400 that says "-4 is not a customer identity." (measured) — and never reaches the repository. One query per filter, each a sentence: `GetOrdersByCustomerIdQuery`, `GetOrdersByStatusQuery`.
