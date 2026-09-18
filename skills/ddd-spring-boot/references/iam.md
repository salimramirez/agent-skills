# Identity and access: the IAM context

A complete bounded context for sign-up, sign-in and bearer-token authorization, shipped as code. Install it, read it, then bend it to the domain.

Security is not domain modeling, and this skill does not teach Spring Security. What it offers is one working, house-style answer to "who is calling?", so that a new platform starts protected instead of adding a filter chain the week before delivery. It is a recommendation with a working default for every decision — token format, hashing, what is public — and every one of them is yours to change.

## Install it

```bash
SKILL=.claude/skills/ddd-spring-boot
python3 "$SKILL/scripts/install.py" iam-context
```

Then the four edits it prints: the dependencies, the two properties, the public-path list, and the roles. The dependencies:

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
</dependency>
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-api</artifactId>
    <version>0.12.6</version>
</dependency>
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-impl</artifactId>
    <version>0.12.6</version>
    <scope>runtime</scope>
</dependency>
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-jackson</artifactId>
    <version>0.12.6</version>
    <scope>runtime</scope>
</dependency>
<dependency>
    <groupId>org.apache.commons</groupId>
    <artifactId>commons-lang3</artifactId>
</dependency>
```

And the properties — the secret from the environment outside development, and long enough for HMAC-SHA (32 bytes at least):

```properties
# JWT Configuration Properties
authorization.jwt.secret=${QUICKBITE_JWT_SECRET}
authorization.jwt.expiration.days=7
```

The moment it is in, every request outside `/api/v1/authentication/**` and the Swagger paths answers **401** without a valid `Authorization: Bearer …` header. Swagger UI's "Authorize" button (the `bearerAuth` scheme from the shared kernel) is how you try the rest from the browser.

## What it is, layer by layer

It is an ordinary bounded context — the same four layers, the same names — plus an infrastructure package for each technical concern:

```
iam/
├── domain/
│   ├── model/aggregates/User                 username, hashed password, a Set<Role>
│   ├── model/entities/Role                   an entity with a Roles name; seeded on startup
│   ├── model/valueobjects/Roles              enum: ROLE_USER, ROLE_ADMIN, ROLE_INSTRUCTOR
│   ├── model/commands/SignUpCommand, SignInCommand, SeedRolesCommand
│   ├── model/queries/GetUserByIdQuery, GetUserByUsernameQuery, GetAllUsersQuery, GetRoleByNameQuery, GetAllRolesQuery
│   ├── services/UserCommandService, UserQueryService, RoleCommandService, RoleQueryService
│   └── exceptions/InvalidCredentialsException
├── application/internal/
│   ├── commandservices/UserCommandServiceImpl, RoleCommandServiceImpl
│   ├── queryservices/UserQueryServiceImpl, RoleQueryServiceImpl
│   ├── eventhandlers/ApplicationReadyEventHandler       seeds the roles
│   └── outboundservices/hashing/HashingService, tokens/TokenService     the two ports
├── infrastructure/
│   ├── persistence/jpa/repositories/UserRepository, RoleRepository
│   ├── hashing/bcrypt/BCryptHashingService, services/HashingServiceImpl
│   ├── tokens/jwt/BearerTokenService, services/TokenServiceImpl
│   └── authorization/sfs/
│       ├── configuration/WebSecurityConfiguration        the SecurityFilterChain
│       ├── pipeline/BearerAuthorizationRequestFilter, UnauthorizedRequestHandlerEntryPoint
│       ├── model/UserDetailsImpl, UsernamePasswordAuthenticationTokenBuilder
│       └── services/UserDetailsServiceImpl
└── interfaces/rest/
    ├── AuthenticationController                /api/v1/authentication/sign-up, /sign-in
    ├── UsersController, RolesController        /api/v1/users, /api/v1/roles — read-only
    ├── IamExceptionHandler                     InvalidCredentialsException → 401
    ├── resources/SignUpResource, SignInResource, UserResource, AuthenticatedUserResource, RoleResource
    └── transform/ the assemblers
```

The part worth studying is the two **ports** in `application/internal/outboundservices`: `HashingService` (`encode`, `matches`) and `TokenService` (`generateToken`, `getUsernameFromToken`, `validateToken`). The command service depends on those interfaces only. Infrastructure supplies BCrypt and JWT behind them through marker interfaces (`BCryptHashingService extends HashingService, PasswordEncoder`) that let the security configuration inject the concrete capability without the application layer ever naming it. Swapping Argon2 for BCrypt, or opaque tokens for JWT, touches `infrastructure` alone. That is the same idea as the ACL, applied to a technical dependency instead of another context.

## The flow

1. `POST /api/v1/authentication/sign-up` with `{"username","password","roles":["ROLE_ADMIN"]}` → `SignUpCommand` → the service checks the username is free, resolves the roles (`Role.toRoleFromName`, default `ROLE_USER` when none are given), hashes the password, saves the `User` → **201** with `{id, username, roles}`. A taken username or an unknown role is an `IllegalArgumentException` → **400**.
2. `POST /api/v1/authentication/sign-in` with `{"username","password"}` → `SignInCommand` → the service finds the user and checks the hash; either failure is the same `InvalidCredentialsException` → **401**, so the response never says which one it was. Success is **200** with `{id, username, token}`.
3. Any other request: `BearerAuthorizationRequestFilter` reads the header, validates the token, loads the user and sets the `SecurityContext`; the filter chain then admits it. No header, or a bad one, → `UnauthorizedRequestHandlerEntryPoint` → **401**.

Roles are seeded by `ApplicationReadyEventHandler` on every start, through `SeedRolesCommand`; `existsByName` keeps it idempotent.

## What to adapt

- **`Roles`** — the three constants are placeholders. Name them in the ubiquitous language (`ROLE_CUSTOMER`, `ROLE_COURIER`, `ROLE_RESTAURANT_MANAGER`); keep the `ROLE_` prefix, which is what `hasRole("ADMIN")` expects. `Role.getDefaultRole()` says which one a sign-up gets when it names none.
- **`WebSecurityConfiguration.filterChain`** — the `permitAll` list is the public surface; CORS allows every origin, which is right for a class project and wrong for production. Both live in that one method. Keep the line that permits the `ERROR` dispatch: without it an unhandled exception on any endpoint comes back as a 401 instead of a 500, which sends you looking for a token problem that does not exist.
- **Authorization beyond authentication** — `@EnableMethodSecurity` is already on, so `@PreAuthorize("hasRole('ADMIN')")` on a controller method is all it takes to restrict it: 200 for an admin, 403 for any other signed-in user, 401 for no token. The asset restricts nothing by role on purpose; that is a domain decision.
- **The link to the domain** — a `User` is an *account*, not a person. `Customer`, `Courier` and the other people of the domain are aggregates in their own contexts, and they reference the account by id (`UserId`) or by username, exactly as Ordering references Customers. Do not add a customer's address to `User`.
- **What `User` carries** — a hashed password, a `Set<Role>` with `FetchType.EAGER` (the filter needs the authorities on every request), `@Column(unique = true)` on the username. No `@Setter`; the constructor and `addRole` are the only ways in.

## What it deliberately leaves out

Refresh tokens, password reset, email verification, OAuth2 and OpenID Connect. Each is a real feature with its own decisions; the asset is the floor they are built on, and adding any of them is ordinary work in this context — a command, a service method, an endpoint.
