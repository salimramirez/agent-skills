using Microsoft.AspNetCore.Mvc.ApplicationModels;
using Microsoft.AspNetCore.Mvc.Formatters;
using Microsoft.EntityFrameworkCore;
using Microsoft.OpenApi;
using __RootNamespace__.Shared.Domain.Repositories;
using __RootNamespace__.Shared.Infrastructure.Events;
using __RootNamespace__.Shared.Infrastructure.Interfaces.AspNetCore.Configuration;
using __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Configuration;
using __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Interceptors;
using __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Repositories;
using __RootNamespace__.Shared.Infrastructure.Pipeline.ExceptionHandlers;

var builder = WebApplication.CreateBuilder(args);

// REST: controllers at kebab-case routes, JSON only, failures as problem details (RFC 9457)
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

// Any origin may call the API: right for a class project, wrong for production
builder.Services.AddCors(options => options.AddPolicy("AllowAllPolicy",
    policy => policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader()));

// Persistence: one database context for every bounded context
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection")
                       ?? throw new InvalidOperationException("The connection string 'DefaultConnection' is not set.");
builder.Services.AddDbContext<AppDbContext>(options =>
{
    options.UseMySQL(connectionString).AddInterceptors(new AuditableEntityInterceptor());
    if (builder.Environment.IsDevelopment()) options.EnableSensitiveDataLogging().EnableDetailedErrors();
});

// API description and Swagger UI, with the bearer token
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new OpenApiInfo { Title = "__Title__ API", Version = "v1" });
    options.IncludeXmlComments(typeof(Program).Assembly);
    options.CustomSchemaIds(OpenApiSchemaIds.For);
    options.AddSecurityDefinition("bearerAuth", new OpenApiSecurityScheme
    {
        Type = SecuritySchemeType.Http,
        Scheme = "bearer",
        BearerFormat = "JWT",
        Description = "The token returned by sign-in."
    });
    options.AddSecurityRequirement(document => new OpenApiSecurityRequirement
    {
        [new OpenApiSecuritySchemeReference("bearerAuth", document)] = []
    });
});

// Shared kernel
builder.Services.AddScoped<IUnitOfWork, UnitOfWork>();
builder.Services.AddScoped<DomainEventDispatcher>();

// Bounded contexts: one line each, added by new-context.py and install.py iam-context

var app = builder.Build();

// Apply pending migrations; creates the database when it does not exist
using (var scope = app.Services.CreateScope())
{
    scope.ServiceProvider.GetRequiredService<AppDbContext>().Database.Migrate();
}

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

app.Run();
