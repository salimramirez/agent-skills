package __base_package__.__context__.domain.model.commands;

/**
 * Command to create a __entity__
 * @param name the __entity__ name.
 *             Cannot be null or blank
 */
public record Create__Entity__Command(String name) {
    /**
     * Constructor
     * @param name the __entity__ name.
     *             Cannot be null or blank
     * @throws IllegalArgumentException if name is null or blank
     */
    public Create__Entity__Command {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("name cannot be null or blank");
        }
    }
}
