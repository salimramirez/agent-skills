package __base_package__.__context__.interfaces.rest.resources;

/**
 * Create __entity words__ resource.
 */
public record Create__Entity__Resource(String name) {
    /**
     * Validates the resource.
     * @throws IllegalArgumentException if the name is null or blank.
     */
    public Create__Entity__Resource {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("Name is required");
        }
    }
}
