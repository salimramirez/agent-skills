# REST

Controllers, resources and assemblers, how a result becomes a response, and the API description that comes out of the XML comments.

## The controller

```csharp
/// <summary>
///     Registers, reads, updates and deletes customers.
/// </summary>
/// <param name="customerCommandService">The use cases that change customers.</param>
/// <param name="customerQueryService">The use cases that read customers.</param>
[ApiController]
[Route("api/v1/[controller]")]
public class CustomersController(
    ICustomerCommandService customerCommandService,
    ICustomerQueryService customerQueryService) : ControllerBase
{
    /// <summary>
    ///     Gets a customer.
    /// </summary>
    /// <param name="customerId">The identity of the customer.</param>
    /// <param name="cancellationToken">Cancels the request.</param>
    /// <response code="200">The customer.</response>
    /// <response code="404">There is no customer with that identity.</response>
    [HttpGet("{customerId:int}")]
    [ProducesResponseType<CustomerResource>(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetCustomerById(int customerId, CancellationToken cancellationToken)
    {
        var customer = await customerQueryService.Handle(new GetCustomerByIdQuery(customerId), cancellationToken);
        if (customer is null)
            return Problem(detail: $"Customer {customerId} was not found.", statusCode: StatusCodes.Status404NotFound);
        return Ok(CustomerResourceFromEntityAssembler.ToResourceFromEntity(customer));
    }

    /// <summary>
    ///     Registers a customer.
    /// </summary>
    /// <param name="resource">The customer's name and email address.</param>
    /// <param name="cancellationToken">Cancels the request.</param>
    /// <response code="201">The registered customer.</response>
    /// <response code="400">A value is missing or invalid.</response>
    /// <response code="409">A customer is already registered with that email address.</response>
    [HttpPost]
    [ProducesResponseType<CustomerResource>(StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> RegisterCustomer(
        RegisterCustomerResource resource, CancellationToken cancellationToken)
    {
        var command = RegisterCustomerCommandFromResourceAssembler.ToCommandFromResource(resource);
        var result = await customerCommandService.Handle(command, cancellationToken);
        return result.ToActionResult(this, customer => CreatedAtAction(
            nameof(GetCustomerById),
            new { customerId = customer.Id },
            CustomerResourceFromEntityAssembler.ToResourceFromEntity(customer)));
    }
}
```

- **Plural, at `api/v1/[controller]`.** The kebab-case convention turns `CustomersController` into `/api/v1/customers` and `MenuItemsController` into `/api/v1/menu-items`, and writes the `Location` of a created resource the same way.
- **A route parameter is named after what it identifies** — `{customerId:int}`, never `{id}` — and constrained to its type, so `/customers/abc` is a 404 and never reaches the action.
- **Thin.** An action builds a command or a query, calls one service, and answers. It never calls a repository, never checks a rule, never decides a status code from anything but the result.
- **A command's result goes through `ToActionResult`**, which runs the success lambda or answers the failure with problem details and the status of its kind. A query's `null` is answered by the action itself with `Problem(...)` and 404.
- **No `[Produces("application/json")]`.** It looks harmless and forces every response the controller writes into `application/json` — including the problem details, which then leave as `application/json` while the exception handler's leave as `application/problem+json` (measured). Without it, successes are `application/json` and every failure, whoever writes it, is `application/problem+json`. `Program.cs` removes the `text/plain` and `text/json` formatters instead, which is what keeps the API description to JSON.

## Resources and assemblers

A resource is a record of primitives — the shape of the JSON, nothing more:

```csharp
public record RegisterCustomerResource(string FirstName, string LastName, string Email);
public record CustomerResource(int Id, string FirstName, string LastName, string FullName, string Email);
```

- **Requests are named after what they do** (`RegisterCustomerResource`, `AddOrderLineResource`); the response after what it is (`CustomerResource`).
- **A response flattens the value objects** a client needs (`FirstName`, `Email`) and **carries other aggregates as identities** (`CustomerId` on an order), never as nested objects.
- **No domain type appears in a resource or in an action's signature.** A controller that returns an `Order` lets the JSON serializer decide what the API looks like and ties the API to every rename in the domain.

An assembler is a static class with one static method, one per direction:

```csharp
public static class RegisterCustomerCommandFromResourceAssembler
{
    public static RegisterCustomerCommand ToCommandFromResource(RegisterCustomerResource resource)
    {
        return new RegisterCustomerCommand(resource.FirstName, resource.LastName, resource.Email);
    }
}

public static class CustomerResourceFromEntityAssembler
{
    public static CustomerResource ToResourceFromEntity(Customer entity)
    {
        return new CustomerResource(
            entity.Id, entity.Name.FirstName, entity.Name.LastName, entity.Name.FullName, entity.Email.Address);
    }
}
```

`<Target>From<Source>Assembler.To<Target>From<Source>(...)` — the name says the direction. An assembler that needs the route as well as the body takes both: `UpdateCustomerCommandFromResourceAssembler.ToCommandFromResource(customerId, resource)`. No null checks: `[ApiController]` never passes a null body to an action.

## What the framework checks before the action runs

With `[ApiController]` and nullable reference types on, a request whose body is missing a non-nullable property is answered with 400 before the action runs:

```json
{"type":"https://tools.ietf.org/html/rfc9110#section-15.5.1","title":"One or more validation errors occurred.",
 "status":400,"errors":{"Email":["The Email field is required."],"LastName":["The LastName field is required."]}}
```

That is all it checks, and it is enough: an empty string *is* present, so `{"firstName": ""}` passes the framework and reaches the domain, where `PersonName` refuses it with a 400 that says why (measured, both). The rules live in one place, the domain; the resource does not repeat them with `[Required]`, `[MaxLength]` or `[EmailAddress]`.

## Status codes

| Answer | When |
| --- | --- |
| `200 OK` with the resource | a read; an update; a transition |
| `201 Created` with the resource and `Location` | a creation; a part added to an aggregate (`Location` is the aggregate's) |
| `204 No Content` | a deletion |
| `400 Bad Request` | a malformed body; a value the domain refuses; a reference to something that does not exist |
| `401 Unauthorized` | no valid bearer token (with the IAM context) |
| `403 Forbidden` | a valid token without the role the endpoint requires |
| `404 Not Found` | the resource in the URL does not exist |
| `409 Conflict` | a rule of the aggregate's state; a value that must be unique and is not |
| `500` | a bug — logged, answered without details |

Every 4xx and 5xx body is problem details (RFC 9457) — see `exceptions.md`. A list that is empty is a 200 with `[]`, never a 404.

## The API description

Swagger UI is built from the XML comments and the attributes, with nothing else to maintain:

- the `<summary>` of an action is its summary;
- each `<response code>` is the description of that status;
- each `[ProducesResponseType<T>(…)]` declares the status and the schema of its body. A 4xx declared without a type is documented as `ProblemDetails`.

Declare every status an action can answer, with both: the attribute for the schema, the comment for the sentence. The JSON is camelCase (`firstName`); `decimal` amounts are numbers, exact on the way in and on the way out.

CORS, the bearer token in Swagger UI and the switch to Scalar are in `project-setup.md`.
