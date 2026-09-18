package __base_package__.__context__.interfaces.rest.resources;

/**
 * Update __entity__ resource.
 */
public record Update__Entity__Resource(String name) {
    /**
     * Validates the resource.
     * @throws IllegalArgumentException if the name is null or blank.
     */
    public Update__Entity__Resource {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("Name is required");
        }
    }
}
