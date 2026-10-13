using Microsoft.EntityFrameworkCore;
using MySql.Data.MySqlClient;

namespace __RootNamespace__.Shared.Infrastructure.Persistence.EntityFrameworkCore.Extensions;

/// <summary>
///     Reads what the database said when a save failed. The one place that knows which database it is.
/// </summary>
public static class DbUpdateExceptionExtensions
{
    // MySQL's ER_DUP_ENTRY. On PostgreSQL: Npgsql.PostgresException with SqlState "23505".
    private const int MySqlDuplicateEntry = 1062;

    /// <summary>
    ///     Gets whether the save failed because a unique index already holds the value.
    /// </summary>
    /// <param name="exception">The failure of the save.</param>
    /// <returns><c>true</c> for a duplicate value; <c>false</c> for any other failure.</returns>
    public static bool IsUniqueConstraintViolation(this DbUpdateException exception)
    {
        return exception.InnerException is MySqlException { Number: MySqlDuplicateEntry };
    }
}
