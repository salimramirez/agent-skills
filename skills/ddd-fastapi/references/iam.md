# Identity and access: the IAM context

A complete bounded context for sign-up, sign-in and bearer-token authentication, shipped as code. Install it, read it, then bend it to the domain.

Security is not domain modeling, and this skill does not teach it. What it offers is one working, house-style answer to "who is calling?", so that a new platform starts protected instead of adding authentication the week before delivery. It is a recommendation with a working default for every decision — token format, hashing algorithm, what is public — and every one of them is yours to change.

## Install it

```bash
SKILL=.claude/skills/ddd-fastapi
python3 "$SKILL/scripts/install.py" iam-context
```

It needs the shared kernel (the installer refuses without it) and prints five edits. The dependencies:

```bash
uv add pyjwt "pwdlib[argon2]"
```

With pip, add both to `[project] dependencies` in `pyproject.toml` and run `pip install . --group dev` again.

The settings, in `.env` — the secret from the environment outside development, and at least 32 characters, which `JwtSettings` enforces at start-up:

```bash
JWT_SECRET=<a long random string>
JWT_EXPIRATION_DAYS=7
```

The wiring in `main.py`, the model import in `alembic/env.py` and a migration — `project-setup.md` shows the resulting `main.py`.

The moment it is in, every router included with `dependencies=authenticated` answers **401** with `WWW-Authenticate: Bearer` when the `Authorization: Bearer …` header is missing or invalid. The **Authorize** button in `/docs` (the `bearerAuth` scheme) is how you try the rest from the browser.

## What it is, layer by layer

An ordinary bounded context — the same four layers, the same module names — plus two ports for the technical concerns:

```
iam/
├── domain/
│   ├── entities.py              User — username, password hash, roles (never empty)
│   ├── value_objects.py         Role — StrEnum: USER = "ROLE_USER", ADMIN = "ROLE_ADMIN"
│   ├── exceptions.py            InvalidCredentialsError, UsernameTakenError, UserNotFoundError
│   └── repositories.py          UserRepository
├── application/
│   ├── outbound_services.py     HashingService, TokenService — the two ports
│   └── services.py              UserApplicationService — sign_up, sign_in, get_user_by_token, …
├── infrastructure/
│   ├── models.py                UserModel, UserRoleModel — users, user_roles
│   ├── repositories.py          SqlAlchemyUserRepository
│   ├── hashing.py               Argon2HashingService — pwdlib, off the event loop
│   └── tokens.py                JwtTokenService, JwtSettings — PyJWT, HS256
└── interfaces/
    ├── routes.py                authentication_router (public), users_router, roles_router
    ├── schemas.py               SignUpRequest, SignInRequest, UserResponse, AuthenticatedUserResponse
    ├── dependencies.py          get_current_user, CurrentUserDep, require_roles, CurrentUser
    └── exception_handlers.py    InvalidCredentialsError → 401
```

The part worth studying is the two **ports** in `application/outbound_services.py`: `HashingService` (`hash`, `verify`) and `TokenService` (`generate_token`, `get_username_from_token`). `UserApplicationService` depends on those abstractions only. Argon2 and JWT are supplied by `infrastructure` and chosen in `interfaces/dependencies.py`; switching to bcrypt, or to opaque tokens stored in a table, touches those two places and no use case. That is the same idea as the anti-corruption layer, applied to a technical dependency instead of another context.

## The flow

1. `POST /api/v1/authentication/sign-up` with `{"username", "password", "roles": ["ROLE_ADMIN"]}` → the service checks the username is free (`UsernameTakenError` → **409**), resolves the role names (`Role.from_name`, an unknown one is a `DomainError` → **400**), hashes the password and saves the `User` → **201** with `{id, username, roles}`. No roles means the default one, `ROLE_USER`.
2. `POST /api/v1/authentication/sign-in` with `{"username", "password"}` → the service loads the user and verifies the hash; an unknown username and a wrong password raise the **same** `InvalidCredentialsError` → **401**, so the response never says which one it was. Success is **200** with `{id, username, token}`.
3. Any protected request: `get_current_user` reads the bearer token through `HTTPBearer`, asks the service for the user it names, and returns a `CurrentUser`. No header → 401 `Not authenticated`; a malformed, foreign-signed or expired token, or one whose user no longer exists → 401 `Invalid or expired token`.

The token is an HS256 JWT whose `sub` is the username, with `iat` and `exp`; decoding requires both `sub` and `exp`. The request and response shapes match the sign-up and sign-in of the Spring Boot IAM in `ddd-spring-boot`, so a frontend written against one works against the other.

## What other contexts use

Four names from `iam.interfaces.dependencies`, and nothing else from IAM — `CurrentUser`, and three dependencies built on it:

```python
@dataclass(frozen=True, slots=True)
class CurrentUser:
    id: int
    username: str
    roles: frozenset[str]
```

- **`get_current_user`**, as a router dependency in `main.py`, protects every route of the router.
- **`CurrentUserDep`**, as a route parameter, when the route needs to know who is calling — to link what it creates to the calling account, for example:

  ```python
  @router.post("/me", status_code=status.HTTP_201_CREATED)
  async def register_me(request: RegisterMeRequest, user: CurrentUserDep, service: CustomerServiceDep) -> CustomerResponse:
      customer = await service.register_customer(request.full_name, request.email, account_id=user.id)
      return CustomerResponse.from_entity(customer)
  ```

  This assumes `Customer` gained an `account_id` attribute and `register_customer` a parameter for it — the asset's `Customer` has neither. The account id is stored as the customer's own reference to the account; it is never mistaken for the customer's id.

- **`require_roles(*roles)`**, which builds a dependency that answers **403** unless the account holds one of the roles:

  ```python
  @router.delete(
      "/{customer_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles(Role.ADMIN))]
  )
  ```

`CurrentUser` is deliberately not the `User` aggregate: other contexts get the id to refer to the account, the username to show, and the role names to check — never the password hash, and never a type whose change would ripple through them.

## What to adapt

- **`Role`** — `USER` and `ADMIN` are placeholders. Name the roles in the ubiquitous language (`CUSTOMER`, `COURIER`, `RESTAURANT_MANAGER`), keeping the `ROLE_` prefix in the values if a frontend already expects it. `Role.default()` says which one a sign-up gets when it names none. Roles are a closed set in code, stored per user in `user_roles`; there is no roles table to seed.
- **Who may sign up with which role** — the asset lets a sign-up request any role, which is right for a class project and wrong for production. Restrict it in `sign_up` (only `Role.default()` from the public route; an admin-only route to grant others through `user.grant(role)`).
- **What is public** — only `authentication_router` is included without `dependencies=authenticated`. Anything else public (a health check, a menu that anyone can read) is a router included without it.
- **The link to the domain** — a `User` is an *account*, not a person. `Customer`, `Courier` and the other people of the domain are aggregates in their own contexts, and they reference the account by id (`CurrentUser.id` stored as `account_id`), exactly as Ordering references Customers. Do not add a customer's address to `User`.
- **CORS** — a browser frontend on another origin needs `app.add_middleware(CORSMiddleware, allow_origins=[...], allow_headers=["Authorization", "Content-Type"], ...)` in `main.py`, with the frontend's origin listed explicitly.

## What it deliberately leaves out

Refresh tokens, logout and token revocation, password reset, email verification, rate limiting of sign-in, OAuth2 and OpenID Connect. Each is a real feature with its own decisions; the asset is the floor they are built on, and adding any of them is ordinary work in this context — a method on the service, a route, perhaps a table.

The sign-in route takes JSON, not the OAuth2 password form (`OAuth2PasswordRequestForm`) that FastAPI's tutorial uses. That keeps the contract identical to the Spring Boot IAM and to what the frontend skills send. The cost is that `/docs` cannot sign in by itself: call sign-in once from "Try it out", copy the token, and paste it into **Authorize**.
