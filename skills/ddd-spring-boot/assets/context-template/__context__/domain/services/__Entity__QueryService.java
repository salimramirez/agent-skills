package __base_package__.__context__.domain.services;

import __base_package__.__context__.domain.model.aggregates.__Entity__;
import __base_package__.__context__.domain.model.queries.GetAll__Entities__Query;
import __base_package__.__context__.domain.model.queries.Get__Entity__ByIdQuery;

import java.util.List;
import java.util.Optional;

/**
 * __Entity__QueryService
 * Service that handles __entity__ queries
 */
public interface __Entity__QueryService {
    /**
     * Handle a get __entity__ by id query
     * @param query The get __entity__ by id query containing the __entity__ id
     * @return The __entity__, if it exists
     * @see Get__Entity__ByIdQuery
     */
    Optional<__Entity__> handle(Get__Entity__ByIdQuery query);

    /**
     * Handle a get all __entities__ query
     * @param query The get all __entities__ query
     * @return The list of __entities__
     * @see GetAll__Entities__Query
     */
    List<__Entity__> handle(GetAll__Entities__Query query);
}
