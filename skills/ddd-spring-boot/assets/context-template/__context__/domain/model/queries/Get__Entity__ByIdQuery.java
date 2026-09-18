package __base_package__.__context__.domain.model.queries;

/**
 * Query to get __a_entity__ by id.
 * @param __entity__Id the __entity words__ id.
 *                     Cannot be null or less than 1
 */
public record Get__Entity__ByIdQuery(Long __entity__Id) {
    /**
     * Constructor
     * @param __entity__Id the __entity words__ id.
     *                     Cannot be null or less than 1
     * @throws IllegalArgumentException if __entity__Id is null or less than 1
     */
    public Get__Entity__ByIdQuery {
        if (__entity__Id == null || __entity__Id <= 0) {
            throw new IllegalArgumentException("__entity__Id cannot be null or less than 1");
        }
    }
}
