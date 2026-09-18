package __base_package__.iam.infrastructure.hashing.bcrypt;

import __base_package__.iam.application.internal.outboundservices.hashing.HashingService;
import org.springframework.security.crypto.password.PasswordEncoder;

/**
 * BCryptHashingService
 * @summary
 * This interface is a marker interface for the BCrypt hashing service.
 * It extends the {@link HashingService} and {@link PasswordEncoder} interfaces.
 * Infrastructure implements it once, in HashingServiceImpl, and the configuration injects it by this type.
 */
public interface BCryptHashingService extends HashingService, PasswordEncoder {
}