package __base_package__.iam.infrastructure.authorization.sfs.model;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;

/**
 * This class is used to build the UsernamePasswordAuthenticationToken object
 * that is used to authenticate the user.
 */
public class UsernamePasswordAuthenticationTokenBuilder {

    /**
     * This method is responsible for building the UsernamePasswordAuthenticationToken object.
     * @param principal The user details.
     * @param request The HTTP request.
     * @return The UsernamePasswordAuthenticationToken object.
     * @see UsernamePasswordAuthenticationToken
     * @see UserDetails
     */
    public static UsernamePasswordAuthenticationToken build(UserDetails principal, HttpServletRequest request) {
        var usernamePasswordAuthenticationToken = new UsernamePasswordAuthenticationToken(principal, null, principal.getAuthorities());
        usernamePasswordAuthenticationToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
        return usernamePasswordAuthenticationToken;
    }
}