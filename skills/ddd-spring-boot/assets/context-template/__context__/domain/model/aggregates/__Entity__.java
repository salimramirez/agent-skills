package __base_package__.__context__.domain.model.aggregates;

import __base_package__.__context__.domain.model.commands.Create__Entity__Command;
import __base_package__.shared.domain.model.aggregates.AuditableAbstractAggregateRoot;
import jakarta.persistence.Entity;
import lombok.Getter;

/**
 * __Entity__ aggregate root
 * @summary
 * This aggregate root represents __a_entity__. The generated version carries a single
 * {@code name}; replace it with the real attributes, in the language the domain experts use,
 * and put the rules that protect them in methods here.
 * @since 1.0
 */
@Getter
@Entity
public class __Entity__ extends AuditableAbstractAggregateRoot<__Entity__> {
    private String name;

    /**
     * Default constructor
     */
    public __Entity__() {
        // Required by JPA
    }

    /**
     * Create __a_entity__ with information from the command
     * @param command The command to create the __entity words__
     * @see Create__Entity__Command
     */
    public __Entity__(Create__Entity__Command command) {
        this.name = command.name();
    }

    /**
     * Update the information of the __entity words__
     * @param name The new name
     * @return The updated __entity words__
     */
    public __Entity__ updateInformation(String name) {
        this.name = name;
        return this;
    }
}
