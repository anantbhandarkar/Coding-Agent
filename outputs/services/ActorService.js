
```javascript
/**
 * @class SecurityConfigService
 * @description Security configuration service that handles authentication, authorization, and route protection.
 * Converted from Spring's WebSecurityConfig class which extended WebSecurityConfigurerAdapter.
 * This service replaces Spring Security annotations with Node.js/Express middleware patterns.
 * 
 * Dependencies:
 * - CustomerService: Handles customer data operations
 * - StaffService: Handles staff data operations
 * - SuccessHandler: Handles post-authentication success logic
 * - bcrypt: Password hashing library (replaces Spring's BCryptPasswordEncoder)
 * - passport: Authentication middleware (replaces Spring Security's authentication provider)
 * - passport-local: Local authentication strategy
 * 
 * @author Converted from Java Spring Security configuration
 * @version 1.0.0
 */

const bcrypt = require('bcrypt');
const passport = require('passport');
const LocalStrategy = require('passport-local').Strategy;
const CustomerService = require('../services/CustomerService');
const StaffService = require('../services/StaffService');
const SuccessHandler = require('../handlers/SuccessHandler');

class SecurityConfigService {
    /**
     * @constructor
     * @description Initializes the security configuration service with required dependencies.
     * Dependency injection via constructor (replaces Spring @Autowired).
     * @param {CustomerService} customerService - Service for customer operations
     * @param {StaffService} staffService - Service for staff operations
     * @param {SuccessHandler} successHandler - Handler for successful authentication
     */
    constructor(customerService, staffService, successHandler) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.customerService = customerService;
        this.staffService = staffService;
        this.successHandler = successHandler;
        
        // Initialize passport configuration
        this.initializePassport();
    }

    /**
     * @method initializePassport
     * @description Configures Passport.js authentication strategy.
     * Replaces Spring's DaoAuthenticationProvider and UserDetailsService configuration.
     * @returns {void}
     * @throws {Error} If passport configuration fails
     */
    initializePassport() {
        try {
            // Configure local strategy for username/password authentication
            // Replaces Spring's DaoAuthenticationProvider configuration
            passport.use(new LocalStrategy(
                {
                    usernameField: 'username',
                    passwordField: 'password'
                },
                async (username, password, done) => {
                    try {
                        // First try to authenticate as customer
                        let user = await this.customerService.findByUsername(username);
                        let role = 'USER';
                        
                        // If not found as customer, try staff
                        if (!user) {
                            user = await this.staffService.findByUsername(username);
                            role = 'ADMIN';
                        }
                        
                        // User not found in either service
                        if (!user) {
                            return done(null, false, { message: 'Invalid credentials' });
                        }
                        
                        // Verify password using bcrypt (replaces Spring's PasswordEncoder)
                        const isValidPassword = await bcrypt.compare(password, user.password);
                        if (!isValidPassword) {
                            return done(null, false, { message: 'Invalid credentials' });
                        }
                        
                        // Attach role to user object for authorization
                        user.role = role;
                        return done(null, user);
                    } catch (error) {
                        return done(error);
                    }
                }
            ));

            // Serialize user for session (replaces Spring's session management)
            passport.serializeUser((user, done) => {
                done(null, { id: user.id, role: user.role });
            });

            // Deserialize user from session (replaces Spring's session management)
            passport.deserializeUser(async (serializedUser, done) => {
                try {
                    let user;
                    if (serializedUser.role === 'USER') {
                        user = await this.customerService.findById(serializedUser.id);
                    } else {
                        user = await this.staffService.findById(serializedUser.id);
                    }
                    if (user) {
                        user.role = serializedUser.role;
                    }
                    done(null, user);
                } catch (error) {
                    done(error);
                }
            });
        } catch (error) {
            throw new Error(`Failed to initialize passport: ${error.message}`);
        }
    }

    /**
     * @method configureRoutes
     * @description Configures route security middleware for Express application.
     * Replaces Spring's configure(HttpSecurity http) method.
     * @param {Express} app - Express application instance
     * @returns {void}
     * @throws {Error} If route configuration fails
     */
    configureRoutes(app) {
        try {
            // Initialize passport middleware
            app.use(passport.initialize());
            app.use(passport.session());

            // Public routes that don't require authentication
            // Replaces Spring's .permitAll() antMatchers
            const publicRoutes = [
                '/',
                '/images/*',
                '/home',
                '/webjars/*',
                '/css/*',
                '/films/*',
                '/actors/*',
                '/categories/*'
            ];

            // Apply public route middleware
            publicRoutes.forEach(route => {
                app.use(route, (req, res, next) => {
                    // No authentication required for these routes
                    next();
                });
            });

            // Customer routes - require USER role
            // Replaces Spring's .antMatchers("/customer").hasRole("USER")
            app.use('/customer', this.authenticateMiddleware('USER'));

            // Owner routes - require ADMIN role
            // Replaces Spring's .antMatchers("/owner").hasRole("ADMIN")
            app.use('/owner', this.authenticateMiddleware('ADMIN'));

            // Configure login route
            // Replaces Spring's .formLogin().loginPage("/login").permitAll()
            app.post('/login', 
                passport.authenticate('local', {
                    failureRedirect: '/login?error=true',
                    failureFlash: true
                }),
                this.successHandler.handleSuccess // Custom success handler
            );

            // Configure logout route
            // Replaces Spring's .logout()
            app.post('/logout', (req, res) => {
                req.logout((err) => {
                    if (err) {
                        return res.redirect('/error');
                    }
                    res.redirect('/');
                });
            });

            // Handle access denied
            // Replaces Spring's .exceptionHandling().accessDeniedPage("/error")
            app.use((err, req, res, next) => {
                if (err.code === 'ACCESS_DENIED') {
                    res.redirect('/error');
                } else {
                    next(err);
                }
            });

        } catch (error) {
            throw new Error(`Failed to configure routes: ${error.message}`);
        }
    }

    /**
     * @method authenticateMiddleware
     * @description Creates authentication middleware for specific roles.
     * Replaces Spring's role-based access control.
     * @param {string} requiredRole - The role required to access the route ('USER' or 'ADMIN')
     * @returns {Function} Express middleware function
     * @throws {Error} If role validation fails
     */
    authenticateMiddleware(requiredRole) {
        return (req, res, next) => {
            // Check if user is authenticated
            if (!req.isAuthenticated()) {
                return res.redirect('/login');
            }

            // Check if user has required role
            if (req.user && req.user.role === requiredRole) {
                return next();
            }

            // User doesn't have required role
            const error = new Error('Access denied');
            error.code = 'ACCESS_DENIED';
            throw error;
        };
    }

    /**
     * @method hashPassword
     * @description Hashes a password using bcrypt.
     * Replaces Spring's PasswordEncoder bean.
     * @param {string} password - Plain text password to hash
     * @returns {Promise<string>} Hashed password
     * @throws {Error} If password hashing fails
     */
    async hashPassword(password) {
        try {
            // Generate salt and hash password (replaces Spring's BCryptPasswordEncoder)
            const saltRounds = 10; // Default strength, similar to Spring's default
            const hashedPassword = await bcrypt.hash(password, saltRounds);
            return hashedPassword;
        } catch (error) {
            throw new Error(`Failed to hash password: ${error.message}`);
        }
    }

    /**
     * @method verifyPassword
     * @description Verifies a plain text password against a hashed password.
     * Replaces Spring's password verification in authentication provider.
     * @param {string} plainPassword - Plain text password to verify
     * @param {string} hashedPassword - Hashed password to verify against
     * @returns {Promise<boolean>} True if password matches, false otherwise
     * @throws {Error} If password verification fails
     */
    async verifyPassword(plainPassword, hashedPassword) {
        try {
            // Compare plain password with hash (replaces Spring's PasswordEncoder.matches)
            const isMatch = await bcrypt.compare(plainPassword, hashedPassword);
            return isMatch;
        } catch (error) {
            throw new Error(`Failed to verify password: ${error.message}`);
        }
    }

    /**
     * @method getPassport
     * @description Returns the configured Passport instance.
     * Replaces Spring's authentication provider bean.
     * @returns {Passport} Configured Passport instance
     */
    getPassport() {
        return passport;
    }
}

module.exports = SecurityConfigService;

// TODO: Add caching layer (Spring @Cacheable not automatically converted)
// TODO: Implement rate limiting for login attempts
// TODO: Add CSRF protection (Spring Security's default CSRF protection)
// TODO: Configure session store for production (Redis/MongoDB)
// TODO: Add password strength validation
// TODO: Implement account lockout after failed attempts
```