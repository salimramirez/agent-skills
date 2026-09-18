package __base_package__.__context__.interfaces.rest.transform;

import __base_package__.__context__.domain.model.aggregates.__Entity__;
import __base_package__.__context__.interfaces.rest.resources.__Entity__Resource;

/**
 * Assembler to convert a __Entity__ entity to a __Entity__Resource.
 */
public class __Entity__ResourceFromEntityAssembler {
    /**
     * Converts a __Entity__ entity to a __Entity__Resource.
     *
     * @param entity The {@link __Entity__} entity to convert.
     * @return The {@link __Entity__Resource} resource that results from the conversion.
     */
    public static __Entity__Resource toResourceFromEntity(__Entity__ entity) {
        return new __Entity__Resource(entity.getId(), entity.getName());
    }
}
