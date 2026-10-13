using __RootNamespace__.Iam.Application.CommandServices;
using __RootNamespace__.Iam.Application.Internal.OutboundServices;
using __RootNamespace__.Iam.Domain.Model.Aggregates;
using __RootNamespace__.Iam.Domain.Model.Commands;
using __RootNamespace__.Iam.Domain.Repositories;
using __RootNamespace__.Shared.Application.Model;
using __RootNamespace__.Shared.Domain.Repositories;

namespace __RootNamespace__.Iam.Application.Internal.CommandServices;

/// <summary>
///     Signing up and signing in, through the hashing and token ports.
/// </summary>
/// <param name="userRepository">The users.</param>
/// <param name="unitOfWork">Commits the sign-up.</param>
/// <param name="hashingService">Hashes and checks passwords.</param>
/// <param name="tokenService">Issues bearer tokens.</param>
public class UserCommandService(
    IUserRepository userRepository,
    IUnitOfWork unitOfWork,
    IHashingService hashingService,
    ITokenService tokenService) : IUserCommandService
{
    private const string InvalidCredentials = "The username or the password is wrong.";

    // Checked when the username does not exist, so that answer takes as long as a wrong password does and
    // the response time does not tell which usernames exist. Static: hashing it per request would make the
    // unknown username the slow one instead.
    private static string? _decoyHash;

    /// <inheritdoc />
    public async Task<Result<User>> Handle(SignUpCommand command, CancellationToken cancellationToken)
    {
        var username = User.NormalizeUsername(command.Username);
        if (await userRepository.ExistsByUsernameAsync(username, cancellationToken))
            return Result<User>.Conflict($"The username '{username}' is taken.");

        var user = new User(username, hashingService.HashPassword(command.Password), command.Roles);
        await userRepository.AddAsync(user, cancellationToken);
        await unitOfWork.CompleteAsync(cancellationToken);
        return Result<User>.Success(user);
    }

    /// <inheritdoc />
    public async Task<Result<(User User, string Token)>> Handle(
        SignInCommand command, CancellationToken cancellationToken)
    {
        var usernameIsValid = !string.IsNullOrWhiteSpace(command.Username) &&
                              command.Username.Trim().Length <= User.UsernameMaxLength;
        var user = usernameIsValid
            ? await userRepository.FindByUsernameAsync(User.NormalizeUsername(command.Username), cancellationToken)
            : null;

        _decoyHash ??= hashingService.HashPassword("not the password of anyone");
        var passwordMatches = hashingService.VerifyPassword(command.Password, user?.PasswordHash ?? _decoyHash);
        if (user is null || !passwordMatches) return Result<(User, string)>.Unauthorized(InvalidCredentials);

        return Result<(User, string)>.Success((user, tokenService.GenerateToken(user)));
    }
}
