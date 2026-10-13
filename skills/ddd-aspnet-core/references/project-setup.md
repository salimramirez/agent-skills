# Project setup

The `.csproj`, `Program.cs` piece by piece, settings and secrets, the database, the migration workflow — and the two swaps that were verified: PostgreSQL for MySQL, Scalar for Swagger UI.

## Creating the project

From a new, empty directory named like the root namespace, with the skill installed into it:

```bash
mkdir QuickBite.Platform && cd QuickBite.Platform
npx skills add salimramirez/agent-skills --skill ddd-aspnet-core
python3 .claude/skills/ddd-aspnet-core/scripts/install.py project --name "QuickBite Platform"
dotnet tool restore
dotnet build
```

`install.py project` writes `QuickBite.Platform.csproj`, `Program.cs`, the two settings files, the launch profile (on a random port between 5001 and 5299 — not 5000, which macOS keeps for the AirPlay Receiver: a request there is answered `403` by `AirTunes`, measured), the `dotnet-ef` tool manifest (`dotnet-tools.json`, at the root, which is where the .NET 10 SDK's `dotnet new tool-manifest` puts it), a `.gitignore`, and the shared kernel. The project builds and starts with no bounded context yet; add one with `new-context.py` and its migration (see `adding-a-resource.md`).

The skill lives under `.claude/skills/` inside the project, `.cs` assets included, and the build ignores it: the .NET SDK leaves out folders whose name starts with a dot (measured — the project built with no errors from the placeholders in the skill's templates).

For an existing project — say one made with `dotnet new webapi --use-controllers` — install only the kernel with `install.py shared-kernel`, add the packages it prints, and replace `Program.cs` with the skill's `assets/project/Program.cs`, keeping the namespace.

## The .csproj

```xml
<PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <RootNamespace>QuickBite.Platform</RootNamespace>
    <GenerateDocumentationFile>true</GenerateDocumentationFile>
    <UserSecretsId>…a GUID…</UserSecretsId>
</PropertyGroup>

<ItemGroup>
    <PackageReference Include="MySql.EntityFrameworkCore" Version="10.0.9"/>
    <PackageReference Include="Microsoft.EntityFrameworkCore.Design" Version="10.0.12"> … PrivateAssets all … </PackageReference>
    <PackageReference Include="Humanizer.Core" Version="3.0.10"/>
    <PackageReference Include="Swashbuckle.AspNetCore" Version="10.3.0"/>
</ItemGroup>
```

- **`MySql.EntityFrameworkCore`** is Oracle's provider. The community's `Pomelo.EntityFrameworkCore.MySql` has no release for EF Core 10, so on .NET 10 this is the MySQL provider there is.
- **`Microsoft.EntityFrameworkCore.Design`** is what `dotnet ef` needs to create migrations; `PrivateAssets` keeps it out of what the application ships.
- **`Humanizer.Core`** pluralizes the table names and writes the routes in kebab-case. The full `Humanizer` package adds dozens of languages the project does not use.
- **`Swashbuckle.AspNetCore` 10.3.0, not an older 10.x.** Earlier versions pull in a `Microsoft.OpenApi` with a known high-severity advisory (NU1903 on restore); 10.3.0 depends on the patched one.
- **`GenerateDocumentationFile`** makes the XML comments the API description, and a public member without one a warning — see `house-style.md`.
- **`UserSecretsId`** lets `dotnet user-secrets` keep the token secret out of the repository; `install.py` writes a new GUID for each project.

The IAM context adds two packages, `Microsoft.AspNetCore.Authentication.JwtBearer` and `BCrypt.Net-Next`; its installer prints the commands.

## Program.cs, piece by piece

The order of the pieces is not arbitrary; each one says why it is where it is.

```csharp
builder.Services.AddControllers(options =>
{
    options.Conventions.Add(new RouteTokenTransformerConvention(new KebabCaseParameterTransformer()));
    options.OutputFormatters.RemoveType<StringOutputFormatter>();
    options.OutputFormatters.OfType<SystemTextJsonOutputFormatter>().Single().SupportedMediaTypes.Remove("text/json");
}).AddJsonOptions(options =>
    // A missing value-type property (a price, a quantity) is a 400, not a silent 0
    options.JsonSerializerOptions.RespectRequiredConstructorParameters = true);
builder.Services.AddProblemDetails();
builder.Services.AddExceptionHandler<DomainExceptionHandler>();
```

Controllers answer at kebab-case routes (`MenuItemsController` → `/api/v1/menu-items`), in JSON only — the two formatter lines take `text/plain` and `text/json` out of the API description, where every response otherwise lists them. `RespectRequiredConstructorParameters` makes every constructor parameter of a request resource required: without it, a body with no `unitPrice` reached the domain as a price of `0` (measured) — see `rest.md`. `AddProblemDetails` and the kernel's exception handler make every failure an RFC 9457 body — see `exceptions.md`.

```csharp
builder.Services.AddCors(options => options.AddPolicy("AllowAllPolicy",
    policy => policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader()));
```

A frontend served from another port is another origin. Any origin is right for a class project and wrong for production, where the policy names the frontend's origin with `WithOrigins(...)`.

```csharp
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection")
                       ?? throw new InvalidOperationException("The connection string 'DefaultConnection' is not set.");
builder.Services.AddDbContext<AppDbContext>(options =>
{
    options.UseMySQL(connectionString).AddInterceptors(new AuditableEntityInterceptor());
    if (builder.Environment.IsDevelopment()) options.EnableSensitiveDataLogging().EnableDetailedErrors();
});
```

One database context for every bounded context, with the interceptor that sets the audit timestamps. Sensitive data logging shows parameter values in the logs, which is why it stays in development.

```csharp
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new OpenApiInfo { Title = "QuickBite Platform API", Version = "v1" });
    options.IncludeXmlComments(typeof(Program).Assembly);
    options.CustomSchemaIds(OpenApiSchemaIds.For);
    options.AddSecurityDefinition("bearerAuth", new OpenApiSecurityScheme
    {
        Type = SecuritySchemeType.Http, Scheme = "bearer", BearerFormat = "JWT",
        Description = "The token returned by sign-in."
    });
    options.AddSecurityRequirement(document => new OpenApiSecurityRequirement
    {
        [new OpenApiSecuritySchemeReference("bearerAuth", document)] = []
    });
});
```

The XML comments become the description of every operation and response. `CustomSchemaIds` names each schema after its context (`Ordering.MoneyResource`): with the default — the bare type name — a second context with a `MoneyResource` makes `swagger.json` a 500 (`Can't use schemaId "$MoneyResource" for type "$…". The same schemaId is already used for type "$…"`, measured). The security scheme is what puts the **Authorize** button in Swagger UI; the name in `AddSecurityDefinition` and the one in `OpenApiSecuritySchemeReference` must be the same string. With a mismatch the document's requirement comes out empty (`"security": [{}]`): the button still authorizes, no operation sends the header, and every protected call answers 401 (measured).

```csharp
builder.Services.AddScoped<IUnitOfWork, UnitOfWork>();
builder.Services.AddScoped<DomainEventDispatcher>();

// Bounded contexts: one line each, added by new-context.py and install.py iam-context
builder.Services.AddIamContext(builder.Configuration);
builder.Services.AddOrderingContext();
```

The shared kernel's two services, then one line per bounded context: each context registers its own repositories, services, handlers and facade in its `Add<Context>Context` method. In development the container checks every registration when the application starts: a service whose dependency nobody registered — a facade forgotten, say — stops the start-up with the name of what is missing (measured), instead of failing the first request that needs it.

```csharp
var app = builder.Build();

using (var scope = app.Services.CreateScope())
{
    scope.ServiceProvider.GetRequiredService<AppDbContext>().Database.Migrate();
}
```

Pending migrations are applied at start-up. `Migrate()` creates the database when it does not exist, and takes a lock first (`GET_LOCK` on MySQL — measured): EF Core's guard against two instances migrating at the same time.

```csharp
app.UseExceptionHandler();
app.UseStatusCodePages();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors("AllowAllPolicy");

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();
```

- **`UseExceptionHandler` first**, so it catches what everything after it throws.
- **`UseStatusCodePages`** gives a problem details body to the responses that would otherwise be empty: the 401 of a missing token, the 404 of a route that does not exist.
- **CORS before authentication**, so a browser's preflight is answered before anything asks it for a token.
- **`UseAuthentication` and `UseAuthorization` are there from the start.** Without an authentication scheme they do nothing (measured); with the IAM context they protect every endpoint. ASP.NET Core adds `UseAuthentication` by itself when it is missing (measured), but written out, its place in the pipeline is visible.
- **No `UseHttpsRedirection`.** The template has it; with the `https` profile it answers a frontend's plain-HTTP preflight with a 307 redirect, and browsers refuse to follow a redirect on a preflight (measured), so every call from the frontend fails. In production, TLS ends at the proxy or the platform in front of the application.

## Settings and secrets

| Setting | Development | Production |
| --- | --- | --- |
| `ConnectionStrings:DefaultConnection` | `appsettings.Development.json` | environment variable `ConnectionStrings__DefaultConnection` |
| `TokenSettings:Secret` (IAM) | `dotnet user-secrets set "TokenSettings:Secret" "…"` | environment variable `TokenSettings__Secret` |

`appsettings.json` holds neither: what is in it is committed and shipped. The application refuses to start without a connection string, and the IAM context refuses to start without a secret of at least 32 characters (see `iam.md`), so a missing setting is found at start-up, not at the first request.

A MySQL server for development, in Docker:

```bash
docker run -d --name quickbite-mysql -e MYSQL_ROOT_PASSWORD=your-password -p 3306:3306 mysql:8.0
```

The database named in the connection string does not need to exist; `Migrate()` creates it.

## The migration workflow

```bash
dotnet ef migrations add AddOrdering     # after every change to the model
dotnet run --launch-profile http         # applies it at start-up
dotnet ef migrations remove              # undo the last one, while it was not applied anywhere that matters
dotnet ef migrations has-pending-model-changes   # "No changes have been made to the model since the last migration."
```

Read every migration before running it: it is generated from the difference between the model and the last snapshot, and what it does to the data already there — a column dropped, a length narrowed — is visible only in it. EF Core does recognize a plain rename: renaming `DeliveryAddress` produced a `RenameColumn`, not a drop and an add (measured).

**Read the start-up log, too.** When the model changed and no migration was added, EF Core 10 logs it as an error — `fail: … The model for context 'AppDbContext' has pending changes. Add a new migration before updating the database.` — and **the application starts anyway** (measured); the first request that touches the new column fails with a 500. Without any migration at all, the database is created with nothing but the `__EFMigrationsHistory` table.

## Switching to PostgreSQL

Verified end to end against PostgreSQL 17, with the IAM context, a generated context and an aggregate with parts. Four edits and a new set of migrations; nothing in any bounded context changes.

1. The provider package:
   ```bash
   dotnet remove package MySql.EntityFrameworkCore
   dotnet add package Npgsql.EntityFrameworkCore.PostgreSQL --version 10.0.3
   ```
2. In `Program.cs`, `options.UseMySQL(connectionString)` becomes `options.UseNpgsql(connectionString)`.
3. The connection string: `Host=localhost;Port=5432;Database=quickbite_platform;Username=postgres;Password=…`.
4. The two lines of the kernel that know the database, in `Shared/Infrastructure/Persistence/EntityFrameworkCore/Extensions/DbUpdateExceptionExtensions.cs`:
   ```csharp
   using Npgsql;
   …
   return exception.InnerException is PostgresException { SqlState: PostgresErrorCodes.UniqueViolation };
   …
   return exception.InnerException is PostgresException { SqlState: PostgresErrorCodes.DeadlockDetected };
   ```
5. Delete `Migrations/` and create them again: `dotnet ef migrations add InitialCreate`. Migrations carry provider-specific annotations and column types; they do not move between providers.

What behaves differently afterwards, measured:

- **Text comparison is case-sensitive.** MySQL's default collation (`utf8mb4_0900_ai_ci`) ignores case and accents, so a unique name rejects `lomo SALTADO` once `Lomo saltado` exists; PostgreSQL accepts it. Where the domain must treat two spellings as one, it normalizes the value itself — `EmailAddress` and the IAM username lower-case what they store — and then both databases agree.
- **`DateTimeOffset` becomes `timestamp with time zone`**, kept to the microsecond.
- **The unique-index conflict still answers 409**: under concurrent requests for the same name, the ones that got past the service's check hit the index and came back as 409 through the changed line, none as 500.
- **Concurrent changes to one aggregate answer 409 without a deadlock.** Ten lines added to one order at once, and ten placements of it: 201s or a single 200, the rest 409, one notification to the kitchen — as on MySQL, where the lines race goes through a deadlock first (see `aggregates.md`).

## OpenAPI with Scalar instead of Swagger UI

The web API template no longer includes Swashbuckle (since .NET 9; the .NET 10 template was checked): it ships `Microsoft.AspNetCore.OpenApi`, which generates the document (OpenAPI 3.1) and has no user interface of its own. Scalar is the reference UI usually paired with it. Verified end to end, down to the bearer token in the requests Scalar builds; the controllers and their XML comments do not change.

1. The packages:
   ```bash
   dotnet remove package Swashbuckle.AspNetCore
   dotnet add package Microsoft.AspNetCore.OpenApi --version 10.0.12
   dotnet add package Scalar.AspNetCore --version 2.18.0
   ```
2. A document transformer in the kernel that declares the bearer token, `Shared/Infrastructure/Interfaces/AspNetCore/Configuration/BearerSecuritySchemeTransformer.cs`:
   ```csharp
   using Microsoft.AspNetCore.OpenApi;
   using Microsoft.OpenApi;

   public sealed class BearerSecuritySchemeTransformer : IOpenApiDocumentTransformer
   {
       public Task TransformAsync(
           OpenApiDocument document, OpenApiDocumentTransformerContext context, CancellationToken cancellationToken)
       {
           document.Components ??= new OpenApiComponents();
           document.Components.SecuritySchemes ??= new Dictionary<string, IOpenApiSecurityScheme>();
           document.Components.SecuritySchemes["bearerAuth"] = new OpenApiSecurityScheme
           {
               Type = SecuritySchemeType.Http, Scheme = "bearer", BearerFormat = "JWT",
               Description = "The token returned by sign-in."
           };
           document.Security ??= [];
           document.Security.Add(new OpenApiSecurityRequirement
           {
               [new OpenApiSecuritySchemeReference("bearerAuth", document)] = []
           });
           return Task.CompletedTask;
       }
   }
   ```
3. In `Program.cs`, the `AddSwaggerGen(...)` block becomes
   ```csharp
   builder.Services.AddOpenApi(options =>
   {
       options.AddDocumentTransformer<BearerSecuritySchemeTransformer>();
       // Name each schema after its context, as Swagger UI does: Ordering.MoneyResource
       options.CreateSchemaReferenceId = type =>
           OpenApiOptions.CreateDefaultSchemaReferenceId(type) is null ? null : OpenApiSchemaIds.For(type.Type);
   });
   ```
   and, in the pipeline, `UseSwagger()` and `UseSwaggerUI()` become
   ```csharp
   app.MapOpenApi().AllowAnonymous();
   app.MapScalarApiReference().AllowAnonymous();
   ```
   with `using Microsoft.AspNetCore.OpenApi;` and `using Scalar.AspNetCore;` in place of `using Microsoft.OpenApi;`.

**Keep `CreateSchemaReferenceId`.** Without it, two contexts' `MoneyResource` are not an error here: the document describes both with whichever schema came first, and the other context's operations are documented with the wrong fields (measured). The default function returns `null` for the types it writes inline (strings, numbers); the check keeps them inline.

**The `.AllowAnonymous()` is not optional once the IAM context is in.** Swagger UI is middleware and runs before authorization; the document and Scalar are endpoints, and the policy that protects every endpoint answers them with 401 (measured). The document is at `/openapi/v1.json`; the reference at `/scalar`, where the **Authentication** section takes the token and adds it to every request it builds (measured).
