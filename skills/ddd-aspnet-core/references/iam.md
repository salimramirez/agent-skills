# Identity and access: the IAM context

A complete bounded context for sign-up, sign-in and bearer-token authentication, shipped as code. Install it, read it, then bend it to the domain.

Security is not domain modeling, and this skill does not teach it. What it offers is one working, house-style answer to "who is calling?", so that a new platform starts protected instead of adding authentication the week before delivery. Every decision in it — token format, hashing algorithm, what is public — is a default, and every one is yours to change.

## Install it

```bash
python3 "$SKILL/scripts/install.py" iam-context
```

It needs the shared kernel (the installer refuses without it) and prints four edits:

```bash
dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer --version 10.0.12
dotnet add package BCrypt.Net-Next --version 4.2.1
```

```csharp
using QuickBite.Platform.Iam.Infrastructure.DependencyInjection;
builder.Services.AddIamContext(builder.Configuration);       // in Program.cs, under "// Bounded contexts"
```

```bash
dotnet user-secrets set "TokenSettings:Secret" "<a long random string>"
dotnet ef migrations add AddIam
```

The moment it is in, **every endpoint needs a bearer token** except sign-up and sign-in. A request without one, or with one that does not validate, is answered **401** with `WWW-Authenticate: Bearer` and a problem details body. Swagger UI's **Authorize** button is how you try the rest from the browser.

## What it is, layer by layer

```
Iam/
├── Domain/
│   ├── Model/Aggregates/         User — username, password hash, roles (never empty)
│   ├── Model/ValueObjects/       Role (User, Admin), RoleNames (ROLE_USER, ROLE_ADMIN)
│   ├── Model/Commands/           SignUpCommand, SignInCommand
│   ├── Model/Queries/            GetUserByIdQuery, GetAllUsersQuery, GetUserByUsernameQuery
│   └── Repositories/             IUserRepository
├── Application/
│   ├── CommandServices/          IUserCommandService — sign-up, sign-in
│   ├── QueryServices/            IUserQueryService
│   ├── Acl/                      IamContextFacade
│   └── Internal/
│       ├── CommandServices/      UserCommandService
│       ├── QueryServices/        UserQueryService
│       └── OutboundServices/     IHashingService, ITokenService — the two ports
├── Infrastructure/
│   ├── Hashing/BCrypt/Services/  HashingService
│   ├── Tokens/Jwt/               Configuration/TokenSettings, Services/TokenService
│   ├── Persistence/EntityFrameworkCore/   UserConfiguration, UserRepository
│   └── DependencyInjection/      IamContextExtensions — services, JwtBearer, the fallback policy
└── Interfaces/
    ├── Acl/                      IIamContextFacade
    └── Rest/                     AuthenticationController (public), UsersController, RolesController
```

The part worth studying is the two **ports** in `Application/Internal/OutboundServices`: `IHashingService` (`HashPassword`, `VerifyPassword`) and `ITokenService` (`GenerateToken`). `UserCommandService` depends on those abstractions only; bcrypt and JWT are adapters in `Infrastructure`, chosen in `AddIamContext`. Switching to Argon2, or to opaque tokens stored in a table, touches those two places and no use case. It is the anti-corruption idea applied to a technical dependency instead of another context.

## The contract

| Request | Success | Failures |
| --- | --- | --- |
| `POST /api/v1/authentication/sign-up` `{"username", "password", "roles": ["ROLE_ADMIN"]}` | **201** `{id, username, roles}` | 400 a blank or long username, a password under 8 characters or over 72 bytes, an unknown role; 409 the username is taken |
| `POST /api/v1/authentication/sign-in` `{"username", "password"}` | **200** `{id, username, token}` | **401**, the same body for an unknown username and a wrong password |
| `GET /api/v1/users`, `/api/v1/users/{userId}` | 200 — never the hash | 401 without a token; 404 |
| `GET /api/v1/roles` | 200 `["ROLE_USER", "ROLE_ADMIN"]` | 401 without a token |

`roles` is optional: a sign-up that names none gets `ROLE_USER`. Usernames are stored trimmed and in lower case, so `Ana` signs in as `ana` and a second `ANA` is a conflict, on every database.

## How a request is authenticated

`AddIamContext` registers ASP.NET Core's own JWT bearer authentication and makes every endpoint require it:

```csharp
services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme).AddJwtBearer();
services.AddOptions<JwtBearerOptions>(JwtBearerDefaults.AuthenticationScheme)
    .Configure<IOptions<TokenSettings>>((options, tokenSettings) =>
    {
        // Keep the claim names the token carries (sub, unique_name, role) instead of long URIs: the two
        // claim types below name them, and with the mapping on, no user has a name or a role.
        options.MapInboundClaims = false;
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(tokenSettings.Value.Secret)),
            ValidateIssuer = false,
            ValidateAudience = false,
            NameClaimType = "unique_name",
            RoleClaimType = "role"
        };
    });

// Every endpoint needs a signed-in user unless it says [AllowAnonymous].
services.AddAuthorizationBuilder()
    .SetFallbackPolicy(new AuthorizationPolicyBuilder().RequireAuthenticatedUser().Build());
```

- **The fallback policy protects by default.** A new controller is protected the moment it exists; `AuthenticationController` carries `[AllowAnonymous]` — the attribute from `Microsoft.AspNetCore.Authorization`, the real one — and is the only public surface. With the policy in place, a route that does not exist answers 401 to a caller without a token and 404 to one with it (measured).
- **The token is HS256** (`SecurityAlgorithms.HmacSha256`), with `sub` (the user's id), `unique_name` and one `role` claim per role. Measured, the header reads `{"alg": "HS256", "typ": "JWT"}`. `SecurityAlgorithms.HmacSha256Signature` looks like the same thing and is not: it writes the XML-DSIG URI `http://www.w3.org/2001/04/xmldsig-more#hmac-sha256` as the algorithm, which .NET accepts and the JWT standard does not register: PyJWT, for one, rejects such a token with `InvalidAlgorithmError` (measured).
- **`MapInboundClaims = false` and the two claim types go together.** By default the handler renames `sub`, `unique_name` and `role` to long `http://schemas…` URIs before the application sees them; the validation parameters then name claims that are no longer there, and — measured with that one line flipped — `User.Identity.Name` was `null` and `User.IsInRole("ROLE_ADMIN")` was `false` for an admin's token, so every `[Authorize(Roles = …)]` would refuse everyone.
- **Swagger UI is not under the policy**: it is middleware, not an endpoint, and stays reachable without a token. With Scalar instead, the document and the reference *are* endpoints and need `.AllowAnonymous()` — see `project-setup.md`.

## Authorization by role

Authentication answers "who is calling?". Which roles may do what is a domain decision, and the asset restricts nothing by role on purpose. When an endpoint needs one:

```csharp
[HttpGet]
[Authorize(Roles = RoleNames.Admin)]
public IActionResult GetAllRoles()
```

Measured: a token with `ROLE_USER` is answered **403** with a problem details body, a token with `ROLE_ADMIN` 200, no token 401. `RoleNames` holds the names as constants because an attribute argument must be one.

## The decisions inside, and why

- **The secret is at least 32 characters and never in a committed file.** `TokenSettings` is validated with data annotations at start-up (`ValidateOnStart`): without a secret, or with a short one, the application does not start, and the message names the setting (measured both). In development it comes from `dotnet user-secrets`, in production from `TokenSettings__Secret` in the environment.
- **bcrypt, at the library's default work factor.** About 0.4 seconds per hash and per check on a laptop (measured), which is the point: it makes guessing slow.
- **A password has between 8 characters and 72 bytes.** bcrypt reads the first 72 bytes and ignores the rest: two passwords that share their first 72 characters verify against each other (measured). `SignUpCommand` refuses a longer password instead of accepting one whose end does not matter. It counts bytes, not characters: `ñ` is two.
- **Sign-in takes as long for an unknown username as for a wrong password.** Without care it would not: the unknown username returns before hashing anything, and the response time says which usernames exist. The service checks the password against a decoy hash when there is no user, computed once per process (computing it per request would make the unknown username the slow one). Measured after the fix: about 385 ms and 400 ms for the two cases.
- **The roles are stored in one column, as names separated by commas**, through an explicit converter: the MySQL provider has no support for collections of primitives — see `persistence.md`.
- **No password reaches a log.** `SignUpCommand`, `SignInCommand` and their resources override `PrintMembers`, so the `ToString()` of a record leaves the password out (measured).

## What to adapt

- **`Role`** — `User` and `Admin` are placeholders. Name the roles in the ubiquitous language (`Customer`, `Courier`, `RestaurantManager`), and their wire names in `RoleNames`; the `ROLE_` prefix keeps the API compatible with the other backends of this collection.
- **Who may become an admin.** The public sign-up grants whatever roles it is sent: an anonymous `{"roles": ["ROLE_ADMIN"]}` is answered 201 with `ROLE_ADMIN` (measured). That is the contract the other backends of this collection share, and convenient in class, where one person tests both sides. Before anything real, close it: sign-up ignores `roles` and gives `ROLE_USER`, and roles are granted by an endpoint that itself requires `[Authorize(Roles = RoleNames.Admin)]`, with the first admin seeded at start-up.
- **The public surface** — today, sign-up and sign-in. Anything else that must be public carries `[AllowAnonymous]`.
- **The lifetime of a token** — `TokenSettings:ExpirationDays`, seven by default.
- **A user deleted while holding a token.** JWT bearer validates the signature and the expiry; it does not ask whether the user still exists, so a deleted user's token keeps working until it expires (measured). If that matters, ask the IAM context on every request — one query each — in `AddIamContext`:

```csharp
options.Events = new JwtBearerEvents
{
    OnTokenValidated = async context =>
    {
        var subject = context.Principal?.FindFirst(JwtRegisteredClaimNames.Sub)?.Value;
        var users = context.HttpContext.RequestServices.GetRequiredService<IUserQueryService>();
        if (!int.TryParse(subject, out var userId) ||
            await users.Handle(new GetUserByIdQuery(userId), context.HttpContext.RequestAborted) is null)
            context.Fail("The user of this token no longer exists.");
    }
};
```

  Measured: with it, the deleted user's token is answered 401 `invalid_token`.
- **Issuer and audience** are not validated: the application that signs the tokens is the only one that reads them. When another service starts accepting them, set both in `TokenValidationParameters` and in the token.
- **CORS** — see `project-setup.md`: any origin is right for a class project, wrong for production.
