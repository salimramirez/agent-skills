using System.Text;

namespace __RootNamespace__.Iam.Interfaces.Rest.Resources;

/// <summary>
///     The body of a sign-in request.
/// </summary>
/// <param name="Username">The username.</param>
/// <param name="Password">The password.</param>
public record SignInResource(string Username, string Password)
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
