# REST

Routers, request and response schemas, the dependency that wires a service, and the OpenAPI description FastAPI builds from them.

## The router of a context

`interfaces/routes.py` holds one `APIRouter` per aggregate root, plural, under `/api/v1/`, tagged with the plural in title case:

```python
router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])


@router.post("", status_code=status.HTTP_201_CREATED, responses=error_responses(400, 409))
async def create_customer(request: CreateCustomerRequest, service: CustomerServiceDep) -> CustomerResponse:
    """Register a customer."""
    customer = await service.register_customer(request.full_name, request.email)
    return CustomerResponse.from_entity(customer)


@router.get("")
async def get_all_customers(service: CustomerServiceDep) -> list[CustomerResponse]:
    """List every customer."""
    return [CustomerResponse.from_entity(customer) for customer in await service.get_all_customers()]


@router.get("/{customer_id}", responses=error_responses(404))
async def get_customer_by_id(customer_id: int, service: CustomerServiceDep) -> CustomerResponse:
    """Get one customer."""
    return CustomerResponse.from_entity(await service.get_customer_by_id(customer_id))


@router.put("/{customer_id}", responses=error_responses(400, 404, 409))
async def update_customer(
    customer_id: int, request: UpdateCustomerRequest, service: CustomerServiceDep
) -> CustomerResponse:
    """Replace a customer's name and email."""
    customer = await service.update_customer(customer_id, request.full_name, request.email)
    return CustomerResponse.from_entity(customer)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404))
async def delete_customer(customer_id: int, service: CustomerServiceDep) -> None:
    """Remove a customer."""
    await service.delete_customer(customer_id)
```

A route does three things and nothing else: take the validated input, call **one** method of the application service, build **one** response. It has no `try`/`except` — a domain exception travels to the exception handler (`exceptions.md`) — and no `if`.

| Operation | Method and path | Status | Body |
| --- | --- | --- | --- |
| create | `POST /api/v1/customers` | 201 | the created resource |
| list | `GET /api/v1/customers` | 200 | a list, `[]` when empty |
| read | `GET /api/v1/customers/{customer_id}` | 200 | the resource |
| replace | `PUT /api/v1/customers/{customer_id}` | 200 | the resource after the change |
| remove | `DELETE /api/v1/customers/{customer_id}` | 204 | none |
| transition | `POST /api/v1/orders/{order_id}/placements` | 200 | the resource after the change — see `state-transitions.md` |

Path parameters are named `<aggregate>_id`, never `id`: a nested route has two ids, and `order_id` in a function signature reads better than a shadowed builtin.

## The return annotation is the response model

`-> CustomerResponse` is enough: FastAPI uses the return annotation as the response model, validates what the function returns against it, filters out any field the schema does not declare, and documents it. Do not repeat it in `response_model=`. The one case for `response_model=` is when the function returns something else on purpose — never here.

## Schemas

`interfaces/schemas.py` holds the Pydantic models of the context's HTTP contract.

```python
class CreateCustomerRequest(BaseModel):
    """Body of ``POST /api/v1/customers``."""

    full_name: str = Field(min_length=1, max_length=120, examples=["Ana Torres"])
    email: str = Field(max_length=254, examples=["ana@quickbite.dev"])


class CustomerResponse(BaseModel):
    """A customer as the API returns it."""

    id: int
    full_name: str
    email: str

    @classmethod
    def from_entity(cls, customer: Customer) -> "CustomerResponse":
        """Build the response from the aggregate."""
        assert customer.id is not None
        return cls(id=customer.id, full_name=customer.full_name, email=customer.email.value)
```

- **`<Action><Thing>Request`** for a body, **`<Thing>Response`** for what goes out. One request schema per use case, even when two look alike today (`CreateCustomerRequest`, `UpdateCustomerRequest`): they change for different reasons.
- **A request checks shape, not rules.** Presence, type, length that matches the column, an `examples` value for the docs. Whether a value is *acceptable* — a valid email, a positive quantity, a known role — is the domain's call, raised as a `DomainError` (400). Repeating the rule in a `@field_validator` means two places to change and, sooner or later, two different answers. A missing or mistyped field is FastAPI's **422**, with the field's location; a value the domain rejects is a **400** with the domain's message.
- **`from_entity` is the only way out of the domain.** An explicit classmethod, not `model_validate(entity, from_attributes=True)`: the mapping is visible, a value object becomes its primitive (`customer.email.value`), and a rename in the entity breaks here, under `mypy`, rather than in a client.
- **Never return an entity, never accept one.** A route typed `-> Customer` does not even load: FastAPI raises `FastAPIError: Invalid args for response field!` when the module is imported.
- **Field names are snake_case**, like Python. A client that wants camelCase gets it by mapping on its side, or by `model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)` on a shared base schema — a decision for the whole API at once, not per schema.
- **Money goes out as `Decimal`**, which serializes as a string (`"32.50"`), and **dates as `datetime`**, which Pydantic serializes as ISO 8601 with its offset — `"2025-06-04T23:23:00Z"` for UTC. Never format a date by hand: `datetime.isoformat() + "Z"` on an aware datetime yields `"…+00:00Z"`, which is not a valid timestamp. And never store a naive datetime — Pydantic serializes it with no offset at all, and the client has to guess the zone.

## Wiring: one dependency per service

`interfaces/dependencies.py` builds the application service for a request and exposes it as an `Annotated` alias:

```python
def get_order_service(session: SessionDep) -> OrderApplicationService:
    """Build the application service on the request's session."""
    return OrderApplicationService(
        SqlAlchemyOrderRepository(session),
        ExternalCustomerService(CustomersContextFacade(session)),
        session,
        event_bus,
    )


OrderServiceDep = Annotated[OrderApplicationService, Depends(get_order_service)]
```

- **It is the one place where ports meet adapters.** The service knows `OrderRepository`; only this function knows `SqlAlchemyOrderRepository`. Replacing an adapter — or giving a test an in-memory one with `app.dependency_overrides[get_order_service] = …` — touches nothing else.
- **Every collaborator shares the request's session**, so everything the use case reads and writes is one transaction.
- **The alias keeps signatures short**: `service: OrderServiceDep`. FastAPI caches dependencies within a request, so `get_session` runs once even when several dependencies ask for it.

## Protecting routers

Authentication is added where routers are included, in `main.py`, not route by route:

```python
authenticated = [Depends(get_current_user)]
unauthenticated = error_responses(401)

app.include_router(authentication_router)
app.include_router(customers_router, dependencies=authenticated, responses=unauthenticated)
app.include_router(ordering_router, dependencies=authenticated, responses=unauthenticated)
```

A route that needs to know *who* is calling asks for `CurrentUserDep` as a parameter; FastAPI resolves `get_current_user` once for the request either way. A route restricted to some roles adds `dependencies=[Depends(require_roles(Role.ADMIN))]` on its decorator. See `iam.md`.

## The OpenAPI description

FastAPI builds it from the code; the house style makes the code say enough:

- **`tags=["Customers"]`** on the router groups the operations in `/docs`.
- **The route's docstring becomes the operation description**, so it is one sentence for the API client.
- **`responses=error_responses(404, 409)`** documents each error status with the `ErrorResponse` schema (`{"detail": "..."}`). FastAPI adds 422 on its own to every route that takes input. Name only the statuses the service can actually raise — the `Raises:` section of the service method is the list.
- **The operation id is the function name** (`generate_unique_id_function` in `main.py`), so a client generated from `/openapi.json` gets methods named after `create_customer` and `place_order` — not after `create_customer_api_v1_customers_post`, which is FastAPI's default. Route function names must be unique across the application; `<verb>_<aggregate>` naming makes them so.
- **The bearer scheme is named `bearerAuth`**, and every protected operation carries it, so the **Authorize** button in `/docs` works for the whole API.
- **`Field(examples=[...])`** fills the "Try it out" body with something that passes.
