# State transitions and nested resources

Endpoints for what is not CRUD: placing, cancelling, adding a part to a whole, filtering a collection.

## A transition is a `POST` to a plural noun

`place()` is not an update of the `status` field; it is something that happens to an order. The URL says so — a plural noun under the aggregate, naming what the transition produces — and the route calls the use case:

```python
@router.post("/{order_id}/placements", responses=error_responses(404, 409))
async def place_order(order_id: int, service: OrderServiceDep) -> OrderResponse:
    """Send a draft order to the restaurant."""
    return OrderResponse.from_entity(await service.place_order(order_id))


@router.post("/{order_id}/cancellations", responses=error_responses(404, 409))
async def cancel_order(order_id: int, request: CancelOrderRequest, service: OrderServiceDep) -> OrderResponse:
    """Cancel a placed order."""
    return OrderResponse.from_entity(await service.cancel_order(order_id, request.reason))
```

- **`placements`, `cancellations`, `confirmations`, `rejections`.** `POST /orders/1/place` would work too; it just stops being a resource, and the next transition gets named differently.
- **A transition with data takes a body** (`CancelOrderRequest` carries the reason); one without takes none.
- **It answers 200 with the resource after the change.** The client sees the new status, the recomputed total, whatever the transition touched, without a second request. A transition that produces something with its own identity — a refund, an invoice — answers 201 with *that* instead.
- **The two failures never reach the route.** A missing order is `OrderNotFoundError` → 404; an order the transition does not apply to is the `ConflictError` the aggregate raises → 409. Both are documented in `responses=` and handled once, in the shared handler.

Never `PATCH /orders/1` with `{"status": "PLACED"}`. That makes the status a field a client can set, and the rules of `place()` — not empty, only from a draft, raise the event — either get skipped or get reimplemented in the route.

## A part of the aggregate is a nested resource

Lines belong to an order, so they are addressed under it, in the same router:

```python
@router.post("/{order_id}/lines", status_code=status.HTTP_201_CREATED, responses=error_responses(400, 404, 409))
async def add_order_line(order_id: int, request: AddOrderLineRequest, service: OrderServiceDep) -> OrderResponse:
    """Add a dish to a draft order."""
    order = await service.add_line(order_id, request.dish_name, request.quantity, request.unit_price)
    return OrderResponse.from_entity(order)
```

- **It answers 201 with the whole aggregate**, not the line: the line is part of the order, and adding it changed the order's total. A client that shows the order needs the order.
- **The service goes through the root**: it loads the order, calls `order.add_line(...)`, saves the order. There is no `OrderLineRepository` and no route that writes a line directly.
- **The path is `/{order_id}/lines`**, plural, under the root. Changing or removing one line is `PUT` / `DELETE /{order_id}/lines/{line_id}`, again through a method of `Order` (`order.remove_line(line_id)`), which checks the status first.

When a context's router grows large, split the nested routes into their own `APIRouter` in the same module (`lines_router = APIRouter(prefix="/api/v1/orders/{order_id}/lines", tags=["Orders"])`) and include both in `main.py`. The tag stays the root's: in `/docs`, lines are part of orders.

## Filtering a collection

Filters are optional query parameters on the list route, typed with the domain's types where one exists:

```python
@router.get("")
async def get_all_orders(
    service: OrderServiceDep, customer_id: int | None = None, status: OrderStatus | None = None
) -> list[OrderResponse]:
    """List orders, optionally for one customer or in one status."""
    orders = await service.get_all_orders(customer_id=customer_id, status=status)
    return [OrderResponse.from_entity(order) for order in orders]
```

`GET /api/v1/orders?customer_id=1&status=PLACED`. FastAPI validates `status` against the enum — `?status=NOPE` is a 422 listing the allowed values — and documents it. The service turns the primitives into value objects and passes them to one repository finder with optional filters; a combination of filters is never a new endpoint.

A filter that returns nothing is `200 []`, never 404: the collection exists, it is just empty.

## Actions that return nothing

Rare, and usually a sign the action produces something worth returning. When it genuinely does not — "resend the confirmation email" — answer 202 or 200 with `MessageResponse` from the kernel:

```python
@router.post("/{order_id}/confirmation-emails", status_code=status.HTTP_202_ACCEPTED)
async def resend_confirmation(order_id: int, service: OrderServiceDep) -> MessageResponse:
    """Send the order confirmation again."""
    await service.resend_confirmation(order_id)
    return MessageResponse(message=f"Confirmation for order {order_id} queued")
```
