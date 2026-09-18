package __base_package__.__context__.domain.model.commands;

/**
 * Command to delete a __entity__
 * @param __entity__Id the __entity__ id.
 *                     Cannot be null or less than 1
 */
public record Delete__Entity__Command(Long __entity__Id) {
    /**
     * Constructor
     * @param __entity__Id the __entity__ id.
     *                     Cannot be null or less than 1
     * @throws IllegalArgumentException if __entity__Id is null or less than 1
     */
    public Delete__Entity__Command {
        if (__entity__Id == null || __entity__Id <= 0) {
            throw new IllegalArgumentException("__entity__Id cannot be null or less than 1");
        }
    }
}
