namespace __RootNamespace__.Iam.Domain.Model.ValueObjects;

/// <summary>
///     What a user may do. Name the members in the ubiquitous language (<c>Customer</c>, <c>Courier</c>,
///     <c>RestaurantManager</c>); these two are placeholders.
/// </summary>
public enum Role
{
    /// <summary>
    ///     Any signed-up user. The role a sign-up gets when it asks for none.
    /// </summary>
    User,

    /// <summary>
    ///     A user who administers the platform.
    /// </summary>
    Admin
}
