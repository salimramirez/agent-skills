namespace __RootNamespace__.__Context__.Domain.Model.Commands;

/// <summary>
///     Replace the information of __a_entity__.
/// </summary>
/// <param name="__Entity__Id">The __entity words__ to update.</param>
/// <param name="Name">The new name.</param>
public record Update__Entity__Command(int __Entity__Id, string Name);
