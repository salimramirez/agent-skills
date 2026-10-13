using __RootNamespace__.__Context__.Domain.Model.Commands;
using __RootNamespace__.Shared.Domain.Model.Aggregates;
using __RootNamespace__.Shared.Domain.Model.Exceptions;

namespace __RootNamespace__.__Context__.Domain.Model.Aggregates;

/// <summary>
///     __A_entity__ of the __Context__ bounded context.
/// </summary>
/// <remarks>
///     A placeholder with a single <see cref="Name" />: replace it with the real attributes and the methods that
///     guard them.
/// </remarks>
public class __Entity__ : AuditableAggregateRoot
{
    /// <summary>
    ///     The longest name __a_entity__ accepts.
    /// </summary>
    public const int NameMaxLength = 100;

    /// <summary>
    ///     Creates __a_entity__.
    /// </summary>
    /// <param name="name">The name.</param>
    /// <exception cref="InvalidValueException">The name is blank or too long.</exception>
    public __Entity__(string name)
    {
        Name = ValidName(name);
    }

    /// <summary>
    ///     Creates __a_entity__ from the command that asks for it.
    /// </summary>
    /// <param name="command">The __entity words__ to create.</param>
    public __Entity__(Create__Entity__Command command) : this(command.Name)
    {
    }

    // For Entity Framework Core, which sets the properties itself.
    private __Entity__()
    {
        Name = null!;
    }

    /// <summary>
    ///     Gets the name.
    /// </summary>
    public string Name { get; private set; }

    /// <summary>
    ///     Replaces the information of the __entity words__.
    /// </summary>
    /// <param name="name">The new name.</param>
    /// <exception cref="InvalidValueException">The name is blank or too long.</exception>
    public void UpdateInformation(string name)
    {
        Name = ValidName(name);
    }

    private static string ValidName(string name)
    {
        if (string.IsNullOrWhiteSpace(name)) throw new InvalidValueException("A name is required.");
        if (name.Trim().Length > NameMaxLength)
            throw new InvalidValueException($"A name has at most {NameMaxLength} characters.");
        return name.Trim();
    }
}
