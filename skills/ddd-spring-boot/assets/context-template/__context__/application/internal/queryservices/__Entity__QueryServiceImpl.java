package __base_package__.__context__.application.internal.queryservices;

import __base_package__.__context__.domain.model.aggregates.__Entity__;
import __base_package__.__context__.domain.model.queries.GetAll__Entities__Query;
import __base_package__.__context__.domain.model.queries.Get__Entity__ByIdQuery;
import __base_package__.__context__.domain.services.__Entity__QueryService;
import __base_package__.__context__.infrastructure.persistence.jpa.repositories.__Entity__Repository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

/**
 * Implementation of the __Entity__QueryService interface.
 * @see __Entity__QueryService
 * @see __Entity__Repository
 */
@Service
public class __Entity__QueryServiceImpl implements __Entity__QueryService {
    private final __Entity__Repository __entity__Repository;

    /**
     * Constructor of the class.
     * @param __entity__Repository the repository to be used by the class.
     */
    public __Entity__QueryServiceImpl(__Entity__Repository __entity__Repository) {
        this.__entity__Repository = __entity__Repository;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Optional<__Entity__> handle(Get__Entity__ByIdQuery query) {
        return __entity__Repository.findById(query.__entity__Id());
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public List<__Entity__> handle(GetAll__Entities__Query query) {
        return __entity__Repository.findAll();
    }
}
