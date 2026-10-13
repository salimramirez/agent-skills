using System.Security.Claims;
using System.Text;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.JsonWebTokens;
using Microsoft.IdentityModel.Tokens;
using __RootNamespace__.Iam.Application.Internal.OutboundServices;
using __RootNamespace__.Iam.Domain.Model.Aggregates;
using __RootNamespace__.Iam.Domain.Model.ValueObjects;
using __RootNamespace__.Iam.Infrastructure.Tokens.Jwt.Configuration;

namespace __RootNamespace__.Iam.Infrastructure.Tokens.Jwt.Services;

/// <summary>
///     Issues JSON Web Tokens signed with HMAC-SHA256 (<c>HS256</c>), carrying the user's identity, username
///     and roles.
/// </summary>
/// <param name="tokenSettings">The signing key and the lifetime.</param>
public class TokenService(IOptions<TokenSettings> tokenSettings) : ITokenService
{
    /// <inheritdoc />
    public string GenerateToken(User user)
    {
        var settings = tokenSettings.Value;
        var claims = new List<Claim>
        {
            new(JwtRegisteredClaimNames.Sub, user.Id.ToString()),
            new(JwtRegisteredClaimNames.UniqueName, user.Username)
        };
        claims.AddRange(user.Roles.Select(role => new Claim("role", role.ToName())));

        var descriptor = new SecurityTokenDescriptor
        {
            Subject = new ClaimsIdentity(claims),
            Expires = DateTime.UtcNow.AddDays(settings.ExpirationDays),
            SigningCredentials = new SigningCredentials(
                new SymmetricSecurityKey(Encoding.UTF8.GetBytes(settings.Secret)), SecurityAlgorithms.HmacSha256)
        };
        return new JsonWebTokenHandler().CreateToken(descriptor);
    }
}
