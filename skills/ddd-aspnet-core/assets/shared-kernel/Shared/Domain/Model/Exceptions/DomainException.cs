namespace __RootNamespace__.Shared.Domain.Model.Exceptions;

/// <summary>
///     Base class of the exceptions the domain throws when it refuses something.
/// </summary>
/// <remarks>
///     The domain throws only subclasses of this type, never <see cref="ArgumentException" /> or
///     <see cref="InvalidOperationException" />: the framework throws those for programming errors, and
///     mapping them to a 4xx would report a bug as the client's fault.
/// </remarks>
/// <param name="message">What was refused and why, in the ubiquitous language.</param>
public abstract class DomainException(string message) : Exception(message);
