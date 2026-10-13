using __RootNamespace__.Iam.Application.Internal.OutboundServices;
using BCryptNet = BCrypt.Net.BCrypt;

namespace __RootNamespace__.Iam.Infrastructure.Hashing.BCrypt.Services;

/// <summary>
///     Hashes passwords with bcrypt, at the library's default work factor.
/// </summary>
public class HashingService : IHashingService
{
    /// <inheritdoc />
    public string HashPassword(string password)
    {
        return BCryptNet.HashPassword(password);
    }

    /// <inheritdoc />
    public bool VerifyPassword(string password, string passwordHash)
    {
        return BCryptNet.Verify(password, passwordHash);
    }
}
