using System.ComponentModel.DataAnnotations;

namespace __RootNamespace__.Iam.Infrastructure.Tokens.Jwt.Configuration;

/// <summary>
///     How bearer tokens are signed and how long they last; bound from the <c>TokenSettings</c> section.
/// </summary>
public class TokenSettings
{
    /// <summary>
    ///     Gets or sets the key that signs the tokens: at least 32 characters, from user secrets or the
    ///     environment, never from a committed file.
    /// </summary>
    [Required]
    [MinLength(32)]
    public string Secret { get; set; } = string.Empty;

    /// <summary>
    ///     Gets or sets how many days a token is valid.
    /// </summary>
    [Range(1, 365)]
    public int ExpirationDays { get; set; } = 7;
}
