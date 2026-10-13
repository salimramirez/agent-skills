namespace __RootNamespace__.Shared.Domain.Model.Exceptions;

/// <summary>
///     An operation the aggregate refuses in its current state: placing an order that is not a draft,
///     cancelling one that was already delivered.
/// </summary>
/// <remarks>
///     Thrown by the methods of an aggregate. Answered with <c>409 Conflict</c>: the request was well formed,
///     and it conflicts with the state of the resource.
/// </remarks>
/// <param name="message">Which rule the operation would break.</param>
public sealed class BusinessRuleViolationException(string message) : DomainException(message);
