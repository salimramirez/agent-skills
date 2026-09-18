package __base_package__.__context__.domain.exceptions;

/**
 * Exception thrown when __a_entity__ is not found.
 * @summary
 * This exception is thrown when a command names __a_entity__ that does not exist.
 * @see RuntimeException
 */
public class __Entity__NotFoundException extends RuntimeException {
    /**
     * Constructor for the exception.
     * @param __entity__Id The id of the __entity words__ that was not found.
     */
    public __Entity__NotFoundException(Long __entity__Id) {
        super("__Entity__ with id %s not found".formatted(__entity__Id));
    }
}
