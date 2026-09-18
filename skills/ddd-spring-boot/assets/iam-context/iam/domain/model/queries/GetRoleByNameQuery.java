package __base_package__.iam.domain.model.queries;

import __base_package__.iam.domain.model.valueobjects.Roles;

/**
 * Get role by name query
 * @summary
 * This class represents the query to get a role by its name.
 * @param name the name of the role
 * @see __base_package__.iam.domain.model.valueobjects.Roles
 */
public record GetRoleByNameQuery(Roles name) {
}