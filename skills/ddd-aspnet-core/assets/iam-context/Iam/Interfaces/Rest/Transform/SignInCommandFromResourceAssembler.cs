using __RootNamespace__.Iam.Domain.Model.Commands;
using __RootNamespace__.Iam.Interfaces.Rest.Resources;

namespace __RootNamespace__.Iam.Interfaces.Rest.Transform;

/// <summary>
///     Builds a <see cref="SignInCommand" /> from the body of the request.
/// </summary>
public static class SignInCommandFromResourceAssembler
{
    /// <summary>
    ///     Builds the command.
    /// </summary>
    /// <param name="resource">The body of the request.</param>
    /// <returns>The command.</returns>
    public static SignInCommand ToCommandFromResource(SignInResource resource)
    {
        return new SignInCommand(resource.Username, resource.Password);
    }
}
