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

    // MySQL's ER_LOCK_DEADLOCK. On PostgreSQL: Npgsql.PostgresException with SqlState "40P01".
    private const int MySqlDeadlock = 1213;

    /// <summary>
    ///     Gets whether the save failed because a unique index already holds the value.
    /// </summary>
    /// <param name="exception">The failure of the save.</param>
    /// <returns><c>true</c> for a duplicate value; <c>false</c> for any other failure.</returns>
    public static bool IsUniqueConstraintViolation(this DbUpdateException exception)
    {
        return exception.InnerException is MySqlException { Number: MySqlDuplicateEntry };
    }

    /// <summary>
    ///     Gets whether the database rolled the save back because a concurrent save held a lock it needed. Two
    ///     saves that each add an entity to the same aggregate end this way on MySQL: inserting the entity locks
    ///     the root's row for the foreign key, and updating the root's version then waits on the other save.
    /// </summary>
    /// <param name="exception">The failure of the save.</param>
    /// <returns><c>true</c> for a deadlock; <c>false</c> for any other failure.</returns>
    public static bool IsDeadlock(this DbUpdateException exception)
    {
        return exception.InnerException is MySqlException { Number: MySqlDeadlock };
    }
}
