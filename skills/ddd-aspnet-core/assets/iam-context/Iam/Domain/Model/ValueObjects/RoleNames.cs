using __RootNamespace__.Shared.Domain.Model.Exceptions;

namespace __RootNamespace__.Iam.Domain.Model.ValueObjects;

/// <summary>
///     The names a <see cref="Role" /> goes by outside the domain: in requests, responses and token claims.
/// </summary>
/// <remarks>
///     The constants are what <c>[Authorize(Roles = RoleNames.Admin)]</c> takes.
/// </remarks>
public static class RoleNames
{
    /// <summary>
    ///     The name of <see cref="Role.User" />.
    /// </summary>
    public const string User = "ROLE_USER";

    /// <summary>
    ///     The name of <see cref="Role.Admin" />.
    /// </summary>
    public const string Admin = "ROLE_ADMIN";

    /// <summary>
    ///     Gets the name of a role.
    /// </summary>
    /// <param name="role">The role.</param>
    /// <returns>Its name.</returns>
    public static string ToName(this Role role)
    {
        return role switch
        {
            Role.User => User,
            Role.Admin => Admin,
            _ => throw new ArgumentOutOfRangeException(nameof(role), role, "A role without a name.")
        };
    }

    /// <summary>
    ///     Gets the role a name stands for.
    /// </summary>
    /// <param name="name">The name, as a client sent it.</param>
    /// <returns>The role.</returns>
    /// <exception cref="InvalidValueException">No role has that name.</exception>
    public static Role ToRole(string name)
    {
        return name switch
        {
            User => Role.User,
            Admin => Role.Admin,
            _ => throw new InvalidValueException($"'{name}' is not a role.")
        };
    }
}
