namespace __RootNamespace__.Shared.Domain.Model.Exceptions;

/// <summary>
///     A value the domain cannot accept: a blank name, a negative amount, a malformed email address.
/// </summary>
/// <remarks>
///     Thrown by constructors of value objects, entities and aggregates. Answered with <c>400 Bad Request</c>.
/// </remarks>
/// <param name="message">What is wrong with the value.</param>
public sealed class InvalidValueException(string message) : DomainException(message);
