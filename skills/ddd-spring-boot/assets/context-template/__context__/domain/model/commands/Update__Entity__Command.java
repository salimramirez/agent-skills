package __base_package__.__context__.domain.model.commands;

/**
 * Command to update __a_entity__
 * @param __entity__Id the __entity words__ id.
 *                     Cannot be null or less than 1
 * @param name the __entity words__ name.
 *             Cannot be null or blank
 */
public record Update__Entity__Command(Long __entity__Id, String name) {
    /**
     * Constructor
     * @param __entity__Id the __entity words__ id.
     *                     Cannot be null or less than 1
     * @param name the __entity words__ name.
     *             Cannot be null or blank
     * @throws IllegalArgumentException if __entity__Id is null or less than 1
     * @throws IllegalArgumentException if name is null or blank
     */
    public Update__Entity__Command {
        if (__entity__Id == null || __entity__Id <= 0) {
            throw new IllegalArgumentException("__entity__Id cannot be null or less than 1");
        }
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("name cannot be null or blank");
        }
    }
}
