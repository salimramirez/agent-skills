package __base_package__.iam.application.internal.queryservices;

import __base_package__.iam.domain.model.aggregates.User;
import __base_package__.iam.domain.model.queries.GetAllUsersQuery;
import __base_package__.iam.domain.model.queries.GetUserByIdQuery;
import __base_package__.iam.domain.model.queries.GetUserByUsernameQuery;
import __base_package__.iam.domain.services.UserQueryService;
import __base_package__.iam.infrastructure.persistence.jpa.repositories.UserRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

/**
 * Implementation of {@link UserQueryService} interface.
 */
@Service
public class UserQueryServiceImpl implements UserQueryService {
    private final UserRepository userRepository;

    /**
     * Constructor.
     *
     * @param userRepository {@link UserRepository} instance.
     */
    public UserQueryServiceImpl(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public List<User> handle(GetAllUsersQuery query) {
        return userRepository.findAll();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Optional<User> handle(GetUserByIdQuery query) {
        return userRepository.findById(query.userId());
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Optional<User> handle(GetUserByUsernameQuery query) {
        return userRepository.findByUsername(query.username());
    }
}