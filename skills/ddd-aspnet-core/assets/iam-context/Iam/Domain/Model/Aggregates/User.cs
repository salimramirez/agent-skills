using __RootNamespace__.Iam.Domain.Model.ValueObjects;
using __RootNamespace__.Shared.Domain.Model.Aggregates;
using __RootNamespace__.Shared.Domain.Model.Exceptions;

namespace __RootNamespace__.Iam.Domain.Model.Aggregates;

/// <summary>
///     Someone who can sign in: a username, the hash of a password, and the roles that say what they may do.
/// </summary>
public class User : AuditableAggregateRoot
{
    /// <summary>
    ///     The longest username accepted.
    /// </summary>
    public const int UsernameMaxLength = 50;

    private readonly List<Role> _roles = [];

    /// <summary>
    ///     Creates a user.
    /// </summary>
    /// <param name="username">The username; trimmed and lowered.</param>
    /// <param name="passwordHash">The hash of the password, never the password.</param>
    /// <param name="roles">The roles; <see cref="Role.User" /> when there are none.</param>
    /// <exception cref="InvalidValueException">The username is blank or too long.</exception>
    public User(string username, string passwordHash, IEnumerable<Role> roles)
    {
        Username = NormalizeUsername(username);
        PasswordHash = passwordHash;
        _roles.AddRange(roles.Distinct());
        if (_roles.Count == 0) _roles.Add(Role.User);
    }

    // For Entity Framework Core, which sets the properties itself.
    private User()
    {
        Username = null!;
        PasswordHash = null!;
    }

    /// <summary>
    ///     Gets the username, in lower case.
    /// </summary>
    public string Username { get; private set; }

    /// <summary>
    ///     Gets the hash of the password.
    /// </summary>
    public string PasswordHash { get; private set; }

    /// <summary>
    ///     Gets the roles; never empty.
    /// </summary>
    public IReadOnlyCollection<Role> Roles => _roles.AsReadOnly();

    /// <summary>
    ///     Writes a username the way it is stored, so sign-up and sign-in compare the same thing.
    /// </summary>
    /// <param name="username">The username as it was typed.</param>
    /// <returns>The username trimmed and in lower case.</returns>
    /// <exception cref="InvalidValueException">The username is blank or too long.</exception>
    public static string NormalizeUsername(string username)
    {
        if (string.IsNullOrWhiteSpace(username)) throw new InvalidValueException("A username is required.");
        var normalized = username.Trim().ToLowerInvariant();
        if (normalized.Length > UsernameMaxLength)
            throw new InvalidValueException($"A username has at most {UsernameMaxLength} characters.");
        return normalized;
    }
}
