using System.Text;
using __RootNamespace__.Iam.Domain.Model.ValueObjects;
using __RootNamespace__.Shared.Domain.Model.Exceptions;

namespace __RootNamespace__.Iam.Domain.Model.Commands;

/// <summary>
///     Sign up a new user.
/// </summary>
/// <remarks>
///     The password is checked here because no domain object ever holds it: only its hash reaches the
///     <c>User</c>. Its upper bound is the hashing algorithm's: bcrypt reads the first 72 bytes and ignores
///     the rest, so a longer password would also accept any other password with the same beginning.
/// </remarks>
/// <param name="Username">The username.</param>
/// <param name="Password">The password, between 8 characters and 72 bytes.</param>
/// <param name="Roles">The roles; none means <see cref="Role.User" />.</param>
public record SignUpCommand(string Username, string Password, IReadOnlyCollection<Role> Roles)
{
    /// <summary>
    ///     The shortest password accepted.
    /// </summary>
    public const int PasswordMinLength = 8;

    /// <summary>
    ///     The longest password accepted, in UTF-8 bytes.
    /// </summary>
    public const int PasswordMaxBytes = 72;

    /// <summary>
    ///     Gets the password.
    /// </summary>
    public string Password { get; } = Password.Length < PasswordMinLength
        ? throw new InvalidValueException($"A password has at least {PasswordMinLength} characters.")
        : Encoding.UTF8.GetByteCount(Password) > PasswordMaxBytes
            ? throw new InvalidValueException($"A password has at most {PasswordMaxBytes} bytes.")
            : Password;

    /// <summary>
    ///     Writes the members for <c>ToString()</c>, leaving the password out: a record prints every property,
    ///     and a log line that formats this one would otherwise print the password.
    /// </summary>
    /// <param name="builder">Where the members are written.</param>
    /// <returns><c>true</c>: there were members to write.</returns>
    protected virtual bool PrintMembers(StringBuilder builder)
    {
        builder.Append($"Username = {Username}, Roles = [{string.Join(", ", Roles)}]");
        return true;
    }
}
