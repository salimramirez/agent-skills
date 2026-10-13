using System.Text;

namespace __RootNamespace__.Iam.Interfaces.Rest.Resources;

/// <summary>
///     The body of a sign-up request.
/// </summary>
/// <param name="Username">The username.</param>
/// <param name="Password">The password, between 8 characters and 72 bytes.</param>
/// <param name="Roles">The role names (<c>ROLE_USER</c>, <c>ROLE_ADMIN</c>); none means <c>ROLE_USER</c>.</param>
public record SignUpResource(string Username, string Password, IReadOnlyCollection<string>? Roles)
{
    /// <summary>
    ///     Writes the members for <c>ToString()</c>, leaving the password out: a record prints every property,
    ///     and a log line that formats this one would otherwise print the password.
    /// </summary>
    /// <param name="builder">Where the members are written.</param>
    /// <returns><c>true</c>: there were members to write.</returns>
    protected virtual bool PrintMembers(StringBuilder builder)
    {
        builder.Append($"Username = {Username}");
        return true;
    }
}
