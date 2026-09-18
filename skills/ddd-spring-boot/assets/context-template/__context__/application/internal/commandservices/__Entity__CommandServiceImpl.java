package __base_package__.__context__.application.internal.commandservices;

import __base_package__.__context__.domain.exceptions.__Entity__NotFoundException;
import __base_package__.__context__.domain.model.aggregates.__Entity__;
import __base_package__.__context__.domain.model.commands.Create__Entity__Command;
import __base_package__.__context__.domain.model.commands.Delete__Entity__Command;
import __base_package__.__context__.domain.model.commands.Update__Entity__Command;
import __base_package__.__context__.domain.services.__Entity__CommandService;
import __base_package__.__context__.infrastructure.persistence.jpa.repositories.__Entity__Repository;
import org.springframework.stereotype.Service;

import java.util.Optional;

/**
 * Implementation of the __Entity__CommandService interface.
 * <p>This class is responsible for handling the commands related to the __Entity__ aggregate. It requires a __Entity__Repository.</p>
 * @see __Entity__CommandService
 * @see __Entity__Repository
 */
@Service
public class __Entity__CommandServiceImpl implements __Entity__CommandService {
    private final __Entity__Repository __entity__Repository;

    /**
     * Constructor of the class.
     * @param __entity__Repository the repository to be used by the class.
     */
    public __Entity__CommandServiceImpl(__Entity__Repository __entity__Repository) {
        this.__entity__Repository = __entity__Repository;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Long handle(Create__Entity__Command command) {
        if (__entity__Repository.existsByName(command.name()))
            throw new IllegalArgumentException("__Entity__ with name %s already exists".formatted(command.name()));
        var __entity__ = new __Entity__(command);
        __entity__Repository.save(__entity__);
        return __entity__.getId();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Optional<__Entity__> handle(Update__Entity__Command command) {
        var __entity__ = __entity__Repository.findById(command.__entity__Id())
                .orElseThrow(() -> new __Entity__NotFoundException(command.__entity__Id()));
        if (__entity__Repository.existsByNameAndIdIsNot(command.name(), command.__entity__Id()))
            throw new IllegalArgumentException("__Entity__ with name %s already exists".formatted(command.name()));
        var updated__Entity__ = __entity__Repository.save(__entity__.updateInformation(command.name()));
        return Optional.of(updated__Entity__);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void handle(Delete__Entity__Command command) {
        if (!__entity__Repository.existsById(command.__entity__Id()))
            throw new __Entity__NotFoundException(command.__entity__Id());
        __entity__Repository.deleteById(command.__entity__Id());
    }
}
