using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Authorization;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;
using __RootNamespace__.Iam.Application.Acl;
using __RootNamespace__.Iam.Application.CommandServices;
using __RootNamespace__.Iam.Application.Internal.CommandServices;
using __RootNamespace__.Iam.Application.Internal.OutboundServices;
using __RootNamespace__.Iam.Application.Internal.QueryServices;
using __RootNamespace__.Iam.Application.QueryServices;
using __RootNamespace__.Iam.Domain.Repositories;
using __RootNamespace__.Iam.Infrastructure.Hashing.BCrypt.Services;
using __RootNamespace__.Iam.Infrastructure.Persistence.EntityFrameworkCore.Repositories;
using __RootNamespace__.Iam.Infrastructure.Tokens.Jwt.Configuration;
using __RootNamespace__.Iam.Infrastructure.Tokens.Jwt.Services;
using __RootNamespace__.Iam.Interfaces.Acl;

namespace __RootNamespace__.Iam.Infrastructure.DependencyInjection;

/// <summary>
///     Registers the IAM bounded context, and with it bearer-token authentication for the whole platform.
/// </summary>
public static class IamContextExtensions
{
    /// <summary>
    ///     Adds the IAM services, validates the token settings at start-up, and makes every endpoint require
    ///     a valid bearer token unless it is marked <c>[AllowAnonymous]</c>.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="configuration">The configuration holding the <c>TokenSettings</c> section.</param>
    /// <returns>The same service collection.</returns>
    public static IServiceCollection AddIamContext(this IServiceCollection services, IConfiguration configuration)
    {
        services.AddOptions<TokenSettings>()
            .Bind(configuration.GetSection(nameof(TokenSettings)))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddScoped<IUserRepository, UserRepository>();
        services.AddScoped<IUserCommandService, UserCommandService>();
        services.AddScoped<IUserQueryService, UserQueryService>();
        services.AddScoped<IHashingService, HashingService>();
        services.AddScoped<ITokenService, TokenService>();
        services.AddScoped<IIamContextFacade, IamContextFacade>();

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

        return services;
    }
}
