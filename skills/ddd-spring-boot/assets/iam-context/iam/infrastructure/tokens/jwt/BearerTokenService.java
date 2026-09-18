package __base_package__.iam.infrastructure.tokens.jwt;

import __base_package__.iam.application.internal.outboundservices.tokens.TokenService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.security.core.Authentication;

/**
 * This interface is a marker interface for the JWT token service.
 * It extends the {@link TokenService} interface.
 * Infrastructure implements it once, in TokenServiceImpl, and the security pipeline injects it by this type.
 */
public interface BearerTokenService extends TokenService {

    /**
     * This method is responsible for extracting the JWT token from the HTTP request.
     * @param request the HTTP request
     * @return String the JWT token
     */
    String getBearerTokenFrom(HttpServletRequest request);

    /**
     * This method is responsible for generating a JWT token from an authentication object.
     * @param authentication the authentication object
     * @return String the JWT token
     * @see Authentication
     */
    String generateToken(Authentication authentication);
}