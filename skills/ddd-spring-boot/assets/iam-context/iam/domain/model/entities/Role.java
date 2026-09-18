package __base_package__.iam.domain.model.entities;

import __base_package__.iam.domain.model.valueobjects.Roles;
import jakarta.persistence.*;
import lombok.Getter;

import java.util.List;

/**
 * Role entity
 * @summary
 * This entity represents the role of a user in the system.
 * It is used to define the permissions of a user.
 */
@Getter
@Entity
public class Role {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Enumerated(EnumType.STRING)
    @Column(length = 20)
    private Roles name;

    public Role() {
        // Required by JPA
    }

    public Role(Roles name) {
        this.name = name;
    }

    /**
     * Get the name of the role as a string
     * @return the name of the role as a string
     */
    public String getStringName() {
        return name.name();
    }

    /**
     * Get the default role
     * @return the default role
     */
    public static Role getDefaultRole() {
        return new Role(Roles.ROLE_USER);
    }

    /**
     * Get the role from its name
     * @param name the name of the role
     * @return the role
     * @throws IllegalArgumentException if no role has that name
     */
    public static Role toRoleFromName(String name) {
        try {
            return new Role(Roles.valueOf(name));
        } catch (IllegalArgumentException e) {
            throw new IllegalArgumentException("Role %s does not exist".formatted(name));
        }
    }

    /**
     * Validate the role set
     * <p>
     *     This method validates the role set and returns the default role if the set is empty.
     * </p>
     * @param roles the role set
     * @return the role set
     */
    public static List<Role> validateRoleSet(List<Role> roles) {
        if (roles == null || roles.isEmpty()) {
            return List.of(getDefaultRole());
        }
        return roles;
    }

}