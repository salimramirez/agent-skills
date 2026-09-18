package __base_package__.__context__.infrastructure.persistence.jpa.repositories;

import __base_package__.__context__.domain.model.aggregates.__Entity__;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/**
 * __Entity__Repository
 * <p>This interface is used to interact with the database and perform CRUD and business command and query supporting operations on the __Entity__ aggregate.</p>
 */
@Repository
public interface __Entity__Repository extends JpaRepository<__Entity__, Long> {
    /**
     * This method is used to check if __a_entity__ exists by its name.
     * @param name The name of the __entity words__.
     * @return A boolean indicating if the __entity words__ exists.
     */
    boolean existsByName(String name);

    /**
     * This method is used to check if __a_entity__ exists by its name and a different id.
     * @param name The name of the __entity words__.
     * @param id The id of the __entity words__.
     * @return A boolean indicating if __a_entity__ exists with the same name but a different id.
     */
    boolean existsByNameAndIdIsNot(String name, Long id);
}
