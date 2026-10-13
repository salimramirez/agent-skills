using __RootNamespace__.Iam.Domain.Model.Commands;
using __RootNamespace__.Iam.Domain.Model.ValueObjects;
using __RootNamespace__.Iam.Interfaces.Rest.Resources;

namespace __RootNamespace__.Iam.Interfaces.Rest.Transform;

/// <summary>
///     Builds a <see cref="SignUpCommand" /> from the body of the request.
/// </summary>
public static class SignUpCommandFromResourceAssembler
{
    /// <summary>
    ///     Builds the command, turning each role name into a role.
    /// </summary>
    /// <param name="resource">The body of the request.</param>
    /// <returns>The command.</returns>
    public static SignUpCommand ToCommandFromResource(SignUpResource resource)
    {
        var roles = (resource.Roles ?? []).Select(RoleNames.ToRole).ToList();
        return new SignUpCommand(resource.Username, resource.Password, roles);
    }
}
