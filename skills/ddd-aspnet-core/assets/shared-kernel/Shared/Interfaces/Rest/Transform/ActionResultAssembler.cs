using Microsoft.AspNetCore.Mvc;
using __RootNamespace__.Shared.Application.Model;

namespace __RootNamespace__.Shared.Interfaces.Rest.Transform;

/// <summary>
///     Turns the result of a command into the response: the success the controller describes, or a
///     problem details body (RFC 9457) with the status code of the failure.
/// </summary>
public static class ActionResultAssembler
{
    /// <summary>
    ///     Answers a result that carries a value.
    /// </summary>
    /// <param name="result">The result of the command.</param>
    /// <param name="controller">The controller answering the request.</param>
    /// <param name="onSuccess">Builds the response from the value.</param>
    /// <typeparam name="T">The type of the value.</typeparam>
    /// <returns>The response.</returns>
    public static IActionResult ToActionResult<T>(
        this Result<T> result, ControllerBase controller, Func<T, IActionResult> onSuccess)
    {
        return result.IsSuccess ? onSuccess(result.Value) : ToProblem(result.Error!, controller);
    }

    /// <summary>
    ///     Answers a result that carries no value.
    /// </summary>
    /// <param name="result">The result of the command.</param>
    /// <param name="controller">The controller answering the request.</param>
    /// <param name="onSuccess">Builds the response.</param>
    /// <returns>The response.</returns>
    public static IActionResult ToActionResult(
        this Result result, ControllerBase controller, Func<IActionResult> onSuccess)
    {
        return result.IsSuccess ? onSuccess() : ToProblem(result.Error!, controller);
    }

    private static IActionResult ToProblem(Error error, ControllerBase controller)
    {
        return controller.Problem(detail: error.Message, statusCode: error.Kind.ToStatusCode());
    }
}
