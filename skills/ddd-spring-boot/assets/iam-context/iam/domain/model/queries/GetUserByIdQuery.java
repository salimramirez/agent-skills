package __base_package__.iam.domain.model.queries;

/**
 * Get user by id query
 * <p>
 *     This class represents the query to get a user by its id.
 * </p>
 * @param userId the id of the user
 */
public record GetUserByIdQuery(Long userId) {
}