
```javascript
/**
 * @class UserDetailsService
 * @description Node.js service class equivalent to Spring's UserDetailsService.
 * Handles user authentication, authorization, and user data retrieval.
 * Converted from Spring's UserDetailsServiceImpl and related security components.
 * 
 * Dependencies:
 * - {Sequelize} sequelize - Database ORM instance (replaces Spring Data JPA)
 * - {Object} models - Sequelize models (replaces JPA entities)
 * - {Object} bcrypt - Password hashing library (replaces Spring Security password encoding)
 * - {Object} jwt - JSON Web Token library (replaces Spring Security token management)
 * 
 * @author Converted from Spring Boot application
 * @version 1.0.0
 */
class UserDetailsService {
    /**
     * @constructor
     * @description Initializes the UserDetailsService with required dependencies.
     * Dependency injection via constructor (replaces Spring @Autowired).
     * 
     * @param {Sequelize} sequelize - Database ORM instance
     * @param {Object} models - Sequelize models including User, Staff, Customer
     * @param {Object} bcrypt - Password hashing library
     * @param {Object} jwt - JWT library for token management
     */
    constructor(sequelize, models, bcrypt, jwt) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.sequelize = sequelize;
        this.models = models;
        this.bcrypt = bcrypt;
        this.jwt = jwt;
        
        // Initialize default redirect strategy (replaces Spring's DefaultRedirectStrategy)
        this.redirectStrategy = {
            sendRedirect: (req, res, url) => {
                res.redirect(url);
            }
        };
    }

    /**
     * @method loadUserByUsername
     * @description Loads user details by username for authentication.
     * Converted from Spring's loadUserByUsername method.
     * 
     * @param {string} username - The username to search for
     * @returns {Promise<Object|null>} User object with authorities or null if not found
     * @throws {Error} When database query fails
     * 
     * @example
     * const user = await userDetailsService.loadUserByUsername('john_doe');
     * if (user) {
     *   console.log('User found:', user.username);
     * }
     */
    async loadUserByUsername(username) {
        try {
            // Manual transaction handling (replaces Spring @Transactional)
            const transaction = await this.sequelize.transaction();
            
            try {
                // First check staff table (equivalent to Spring's StaffRepository query)
                // @Query(value = "SELECT * FROM staff s WHERE s.username = :username", nativeQuery = true)
                const staff = await this.models.Staff.findOne({
                    where: { username: username },
                    transaction: transaction
                });

                if (staff) {
                    // Convert Spring's GrantedAuthority to JavaScript role array
                    const authorities = ['ROLE_ADMIN', 'ROLE_STAFF'];
                    
                    await transaction.commit();
                    
                    // Return user details object (equivalent to Spring's UserDetails)
                    return {
                        id: staff.staff_id,
                        username: staff.username,
                        password: staff.password,
                        authorities: authorities,
                        isActive: staff.active,
                        userType: 'staff'
                    };
                }

                // Check customer table if not found in staff
                const customer = await this.models.Customer.findOne({
                    where: { 
                        // Assuming email is used as username for customers
                        email: username 
                    },
                    transaction: transaction
                });

                if (customer) {
                    const authorities = ['ROLE_USER'];
                    
                    await transaction.commit();
                    
                    return {
                        id: customer.customer_id,
                        username: customer.email,
                        password: customer.password,
                        authorities: authorities,
                        isActive: customer.active,
                        userType: 'customer'
                    };
                }

                await transaction.commit();
                return null; // Java Optional<T> -> JavaScript null/object pattern
                
            } catch (error) {
                await transaction.rollback();
                throw error;
            }
        } catch (error) {
            // Error handling strategy: wrap database errors
            throw new Error(`Failed to load user by username: ${error.message}`);
        }
    }

    /**
     * @method authenticateUser
     * @description Authenticates a user with username and password.
     * Combines Spring Security authentication flow with password verification.
     * 
     * @param {string} username - User's username or email
     * @param {string} password - User's plain text password
     * @returns {Promise<Object|null>} Authentication result with token or null
     * @throws {Error} When authentication fails due to invalid credentials
     * 
     * @example
     * const authResult = await userDetailsService.authenticateUser('admin', 'password123');
     * if (authResult) {
     *   console.log('Token:', authResult.token);
     * }
     */
    async authenticateUser(username, password) {
        try {
            // Validate input before processing - converted from Spring @Valid annotation
            if (!username || !password) {
                throw new Error('Username and password are required');
            }

            // Load user details (equivalent to Spring's AuthenticationManager)
            const userDetails = await this.loadUserByUsername(username);
            
            if (!userDetails) {
                // Equivalent to BadCredentialsException in Spring
                throw new Error('Invalid username or password');
            }

            // Verify password (replaces Spring's PasswordEncoder)
            const isPasswordValid = await this.bcrypt.compare(password, userDetails.password);
            
            if (!isPasswordValid) {
                throw new Error('Invalid username or password');
            }

            if (!userDetails.isActive) {
                // Equivalent to DisabledException in Spring
                throw new Error('Account is disabled');
            }

            // Generate JWT token (replaces Spring Security's token creation)
            const token = this.jwt.sign(
                { 
                    id: userDetails.id,
                    username: userDetails.username,
                    authorities: userDetails.authorities,
                    userType: userDetails.userType
                },
                process.env.JWT_SECRET || 'default-secret',
                { expiresIn: '24h' }
            );

            return {
                token: token,
                user: {
                    id: userDetails.id,
                    username: userDetails.username,
                    authorities: userDetails.authorities,
                    userType: userDetails.userType
                }
            };

        } catch (error) {
            // Log authentication failures (equivalent to Spring's authentication event logging)
            console.error(`Authentication failed for user ${username}:`, error.message);
            throw error;
        }
    }

    /**
     * @method handleAuthenticationSuccess
     * @description Handles successful authentication and redirects based on user role.
     * Converted from Spring's SuccessHandler.onAuthenticationSuccess method.
     * 
     * @param {Object} req - Express request object
     * @param {Object} res - Express response object
     * @param {Object} authentication - Authentication object with user details
     * @returns {Promise<void>}
     * @throws {Error} When redirect fails or user role is invalid
     * 
     * @example
     * await userDetailsService.handleAuthenticationSuccess(req, res, {
     *   authorities: [{ authority: 'ROLE_USER' }]
     * });
     */
    async handleAuthenticationSuccess(req, res, authentication) {
        try {
            // Extract authorities from authentication object
            const authorities = authentication.authorities || [];
            
            // Check user role and redirect accordingly (converted from Spring's SuccessHandler logic)
            if (authorities.includes('ROLE_USER')) {
                // Redirect customer users
                await this.redirectStrategy.sendRedirect(req, res, '/customer');
            } else if (authorities.includes('ROLE_ADMIN') || authorities.includes('ROLE_STAFF')) {
                // Redirect admin/staff users
                await this.redirectStrategy.sendRedirect(req, res, '/owner');
            } else {
                // Handle unknown role (equivalent to IllegalStateException in Java)
                throw new Error('Unknown user role');
            }
        } catch (error) {
            // Error handling for redirect failures
            console.error('Authentication success handler error:', error);
            res.status(500).json({ error: 'Authentication succeeded but redirect failed' });
        }
    }

    /**
     * @method handleAccessDenied
     * @description Handles access denied scenarios.
     * Converted from Spring's FailureHandler.handle method.
     * 
     * @param {Object} req - Express request object
     * @param {Object} res - Express response object
     * @param {Error} accessDeniedException - Access denied exception
     * @returns {Promise<void>}
     * 
     * @example
     * await userDetailsService.handleAccessDenied(req, res, new Error('Access denied'));
     */
    async handleAccessDenied(req, res, accessDeniedException) {
        try {
            // Log access denied attempt (security audit)
            console.warn(`Access denied for user ${req.user?.username}: ${accessDeniedException.message}`);
            
            // Redirect to error page (equivalent to Spring's AccessDeniedHandler)
            // request.getContextPath() -> Express doesn't have context path, using root
            res.redirect('/error');
        } catch (error) {
            console.error('Access denied handler error:', error);
            res.status(500).json({ error: 'Access denied handling failed' });
        }
    }

    /**
     * @method validateToken
     * @description Validates JWT token and returns user details.
     * Replaces Spring Security's token validation filter.
     * 
     * @param {string} token - JWT token to validate
     * @returns {Promise<Object|null>} Decoded token payload or null if invalid
     * @throws {Error} When token is malformed or expired
     * 
     * @example
     * const user = await userDetailsService.validateToken('Bearer eyJhbGciOi...');
     * if (user) {
     *   console.log('Valid user:', user.username);
     * }
     */
    async validateToken(token) {
        try {
            // Remove 'Bearer ' prefix if present
            const tokenString = token.startsWith('Bearer ') ? token.slice(7) : token;
            
            // Verify token (equivalent to Spring Security's token validation)
            const decoded = this.jwt.verify(tokenString, process.env.JWT_SECRET || 'default-secret');
            
            return decoded;
        } catch (error) {
            // Handle token validation errors
            if (error.name === 'TokenExpiredError') {
                throw new Error('Token has expired');
            } else if (error.name === 'JsonWebTokenError') {
                throw new Error('Invalid token');
            }
            throw error;
        }
    }

    /**
     * @method hasAuthority
     * @description Checks if user has specific authority/role.
     * Utility method replacing Spring Security's @PreAuthorize annotations.
     * 
     * @param {Object} user - User object with authorities
     * @param {string} authority - Authority to check for
     * @returns {boolean} True if user has the authority
     * 
     * @example
     * if (userDetailsService.hasAuthority(user, 'ROLE_ADMIN')) {
     *   // Admin-only logic
     * }
     */
    hasAuthority(user, authority) {
        // Check if user exists and has authorities array
        if (!user || !user.authorities || !Array.isArray(user.authorities)) {
            return false;
        }
        
        // Check for specific authority (equivalent to Spring's hasAuthority())
        return user.authorities.includes(authority);
    }

    /**
     * @method refreshToken
     * @description Refreshes an existing JWT token.
     * Additional security feature not present in original Spring code.
     * 
     * @param {string} token - Existing JWT token
     * @returns {Promise<string>} New JWT token
     * @throws {Error} When token is invalid or refresh fails
     * 
     * @example
     * const newToken = await userDetailsService.refreshToken(oldToken);
     */
    async refreshToken(token) {
        try {
            // Validate existing token
            const decoded = await this.validateToken(token);
            
            // Generate new token with same payload
            const newToken = this.jwt.sign(
                {
                    id: decoded.id,
                    username: decoded.username,
                    authorities: decoded.authorities,
                    userType: decoded.userType
                },
                process.env.JWT_SECRET || 'default-secret',
                { expiresIn: '24h' }
            );
            
            return newToken;
        } catch (error) {
            throw new Error(`Token refresh failed: ${error.message}`);
        }
    }
}

module.exports = UserDetailsService;

// TODO: Add caching layer (Spring @Cacheable not automatically converted)
// TODO: Implement rate limiting for authentication attempts
// TODO: Add password strength validation
// TODO: Implement account lockout after failed attempts
```