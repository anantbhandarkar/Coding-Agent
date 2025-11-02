
```javascript
/**
 * ActorService - Handles all actor-related business operations
 * Converted from Java Spring Service class (com.sparta.engineering72.sakilaproject.services.ActorService)
 * Replaces Spring @Service annotation with Node.js module pattern
 * 
 * Dependencies:
 * - ActorRepository: Data access layer for actor operations (replaces Spring Data JPA repository)
 * 
 * @class ActorService
 * @description Provides business logic for managing actors in the Sakila database
 */
class ActorService {
    /**
     * Creates an instance of ActorService
     * Dependency injected via constructor (replaces Spring @Autowired)
     * 
     * @param {Object} actorRepository - Repository for actor data access operations
     * @description Initializes service with required repository dependency
     */
    constructor(actorRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.actorRepository = actorRepository;
    }

    /**
     * Retrieves all actors from the database
     * @description Fetches complete list of actors, converted from Spring's findAll()
     * @returns {Promise<Array<Actor>>} Array of all actor objects
     * @throws {Error} When database query fails
     */
    async getAllActors() {
        try {
            // Spring Data findAll() -> Sequelize findAll()
            return await this.actorRepository.findAll();
        } catch (error) {
            // Error handling converted from Spring's DataAccessException
            throw new Error(`Failed to retrieve all actors: ${error.message}`);
        }
    }

    /**
     * Retrieves an actor by their unique ID
     * @description Gets single actor by ID, converts Spring's Optional<Actor> to null/object pattern
     * @param {number} id - The unique identifier of the actor
     * @returns {Promise<Actor|null>} Actor object if found, null if not found
     * @throws {Error} When database query fails or ID is invalid
     */
    async getActorByID(id) {
        try {
            // Input validation - converted from Spring @Valid annotation
            if (!id || id <= 0) {
                throw new Error('Invalid actor ID provided');
            }
            
            // Spring Data getActorByActorId() -> Sequelize findByPk()
            const actor = await this.actorRepository.findByPk(id);
            return actor || null; // Java Optional<T> -> JavaScript null/object pattern
        } catch (error) {
            throw new Error(`Failed to retrieve actor by ID: ${error.message}`);
        }
    }

    /**
     * Retrieves actors by first and last name
     * @description Searches for actors matching both first and last name exactly
     * @param {string} firstName - The first name to search for
     * @param {string} lastName - The last name to search for
     * @returns {Promise<Array<Actor>>} Array of matching actors
     * @throws {Error} When database query fails or names are invalid
     */
    async getActorsByFullName(firstName, lastName) {
        try {
            // Validate input parameters
            if (!firstName || !lastName) {
                throw new Error('Both first name and last name are required');
            }
            
            // Spring Data findActorsByFirstNameAndLastName() -> Sequelize where clause
            return await this.actorRepository.findAll({
                where: {
                    first_name: firstName,
                    last_name: lastName
                }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve actors by full name: ${error.message}`);
        }
    }

    /**
     * Retrieves actors by first name
     * @description Searches for actors with matching first name
     * @param {string} firstName - The first name to search for
     * @returns {Promise<Array<Actor>>} Array of actors with matching first name
     * @throws {Error} When database query fails or first name is invalid
     */
    async getActorsByFirstName(firstName) {
        try {
            if (!firstName) {
                throw new Error('First name is required');
            }
            
            // Spring Data findActorsByFirstName() -> Sequelize where clause
            return await this.actorRepository.findAll({
                where: {
                    first_name: firstName
                }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve actors by first name: ${error.message}`);
        }
    }

    /**
     * Retrieves actors by last name
     * @description Searches for actors with matching last name
     * @param {string} lastName - The last name to search for
     * @returns {Promise<Array<Actor>>} Array of actors with matching last name
     * @throws {Error} When database query fails or last name is invalid
     */
    async getActorsByLastName(lastName) {
        try {
            if (!lastName) {
                throw new Error('Last name is required');
            }
            
            // Spring Data findActorsByLastName() -> Sequelize where clause
            return await this.actorRepository.findAll({
                where: {
                    last_name: lastName
                }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve actors by last name: ${error.message}`);
        }
    }

    /**
     * Gets the full name of an actor by their ID
     * @description Combines first and last name into a single string
     * @param {number} id - The unique identifier of the actor
     * @returns {Promise<string|null>} Full name string if actor found, null if not found
     * @throws {Error} When database query fails or ID is invalid
     */
    async getActorFullNameFromID(id) {
        try {
            // Reuse existing method for consistency
            const actor = await this.getActorByID(id);
            
            // Java null check -> JavaScript null check
            if (!actor) {
                return null;
            }
            
            // String concatenation - same logic as Java
            return `${actor.first_name} ${actor.last_name}`;
        } catch (error) {
            throw new Error(`Failed to get actor full name: ${error.message}`);
        }
    }
}

/**
 * CategoryService - Handles all category-related business operations
 * Converted from Java Spring Service class (com.sparta.engineering72.sakilaproject.services.CategoryService)
 * Replaces Spring @Service annotation with Node.js module pattern
 * 
 * Dependencies:
 * - CategoryRepository: Data access layer for category operations (replaces Spring Data JPA repository)
 * 
 * @class CategoryService
 * @description Provides business logic for managing categories in the Sakila database
 */
class CategoryService {
    /**
     * Creates an instance of CategoryService
     * Dependency injected via constructor (replaces Spring @Autowired)
     * 
     * @param {Object} categoryRepository - Repository for category data access operations
     * @description Initializes service with required repository dependency
     */
    constructor(categoryRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.categoryRepository = categoryRepository;
    }

    /**
     * Retrieves all categories from the database
     * @description Fetches complete list of categories, converted from Spring's findAll()
     * @returns {Promise<Array<Category>>} Array of all category objects
     * @throws {Error} When database query fails
     */
    async getAllCategories() {
        try {
            // Spring Data findAll() -> Sequelize findAll()
            return await this.categoryRepository.findAll();
        } catch (error) {
            // Error handling converted from Spring's DataAccessException
            throw new Error(`Failed to retrieve all categories: ${error.message}`);
        }
    }

    /**
     * Retrieves a category by its unique ID
     * @description Gets single category by ID, converts Spring's Optional<Category> to null/object pattern
     * @param {number} id - The unique identifier of the category
     * @returns {Promise<Category|null>} Category object if found, null if not found
     * @throws {Error} When database query fails or ID is invalid
     */
    async getByCategoryId(id) {
        try {
            // Input validation - converted from Spring @Valid annotation
            if (!id || id <= 0) {
                throw new Error('Invalid category ID provided');
            }
            
            // Spring Data getCategoryByCategoryId() -> Sequelize findByPk()
            const category = await this.categoryRepository.findByPk(id);
            return category || null; // Java Optional<T> -> JavaScript null/object pattern
        } catch (error) {
            throw new Error(`Failed to retrieve category by ID: ${error.message}`);
        }
    }
}

/**
 * CustomerService - Handles all customer-related business operations
 * Converted from Java Spring Service class (com.sparta.engineering72.sakilaproject.services.CustomerService)
 * Replaces Spring @Service annotation with Node.js module pattern
 * 
 * Dependencies:
 * - CustomerRepository: Data access layer for customer operations (replaces Spring Data JPA repository)
 * 
 * @class CustomerService
 * @description Provides business logic for managing customers in the Sakila database
 */
class CustomerService {
    /**
     * Creates an instance of CustomerService
     * Dependency injected via constructor (replaces Spring @Autowired)
     * 
     * @param {Object} customerRepository - Repository for customer data access operations
     * @description Initializes service with required repository dependency
     */
    constructor(customerRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.customerRepository = customerRepository;
    }

    /**
     * Retrieves all customers from the database
     * @description Fetches complete list of customers, converted from Spring's findAll()
     * @returns {Promise<Array<Customer>>} Array of all customer objects
     * @throws {Error} When database query fails
     */
    async getAllCustomers() {
        try {
            // Spring Data findAll() -> Sequelize findAll()
            return await this.customerRepository.findAll();
        } catch (error) {
            // Error handling converted from Spring's DataAccessException
            throw new Error(`Failed to retrieve all customers: ${error.message}`);
        }
    }

    /**
     * Retrieves customers by first name
     * @description Searches for customers with matching first name
     * @param {string} firstName - The first name to search for
     * @returns {Promise<Array<Customer>>} Array of customers with matching first name
     * @throws {Error} When database query fails or first name is invalid
     */
    async getCustomersByFirstName(firstName) {
        try {
            if (!firstName) {
                throw new Error('First name is required');
            }
            
            // Spring Data getCustomersByFirstName() -> Sequelize where clause
            return await this.customerRepository.findAll({
                where: {
                    first_name: firstName
                }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve customers by first name: ${error.message}`);
        }
    }

    /**
     * Retrieves customers by last name
     * @description Searches for customers with matching last name
     * @param {string} lastName - The last name to search for
     * @returns {Promise<Array<Customer>>} Array of customers with matching last name
     * @throws {Error} When database query fails or last name is invalid
     */
    async getCustomersByLastName(lastName) {
        try {
            if (!lastName) {
                throw new Error('Last name is required');
            }
            
            // Spring Data getCustomersByLastName() -> Sequelize where clause
            return await this.customerRepository.findAll({
                where: {
                    last_name: lastName
                }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve customers by last name: ${error.message}`);
        }
    }

    /**
     * Retrieves customers by full name
     * @description Searches for customers matching both first and last name exactly
     * @param {string} firstName - The first name to search for
     * @param {string} lastName - The last name to search for
     * @returns {Promise<Array<Customer>>} Array of matching customers
     * @throws {Error} When database query fails or names are invalid
     */
    async getCustomersByFullName(firstName, lastName) {
        try {
            // Validate input parameters
            if (!firstName || !lastName) {
                throw new Error('Both first name and last name are required');
            }
            
            // Spring Data getCustomersByFullName() -> Sequelize where clause
            return await this.customerRepository.findAll({
                where: {
                    first_name: firstName,
                    last_name: lastName
                }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve customers by full name: ${error.message}`);
        }
    }

    /**
     * Retrieves a customer by their unique ID
     * @description Gets single customer by ID, converts Spring's Optional<Customer> to null/object pattern
     * @param {number} id - The unique identifier of the customer
     * @returns {Promise<Customer|null>} Customer object if found, null if not found
     * @throws {Error} When database query fails or ID is invalid
     */
    async getCustomerByID(id) {
        try {
            // Input validation - converted from Spring @Valid annotation
            if (!id || id <= 0) {
                throw new Error('Invalid customer ID provided');
            }
            
            // Spring Data getCustomerByCustomerId() -> Sequelize findByPk()
            const customer = await this.customerRepository.findByPk(id);
            return customer || null; // Java Optional<T> -> JavaScript null/object pattern
        } catch (error) {
            throw new Error(`Failed to retrieve customer by ID: ${error.message}`);
        }
    }

    /**
     * Retrieves a customer by their email address
     * @description Gets single customer by email, email should be unique
     * @param {string} email - The email address to search for
     * @returns {Promise<Customer|null>} Customer object if found, null if not found
     * @throws {Error} When database query fails or email is invalid
     */
    async getCustomerByEmail(email) {
        try {
            if (!email) {
                throw new Error('Email is required');
            }
            
            // Validate email format
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                throw new Error('Invalid email format');
            }
            
            // Spring Data getCustomerByEmail() -> Sequelize findOne with where clause
            const customer = await this.customerRepository.findOne({
                where: {
                    email: email
                }
            });
            return customer || null; // Java Optional<T> -> JavaScript null/object pattern
        } catch (error) {
            throw new Error(`Failed to retrieve customer by email: ${error.message}`);
        }
    }

    /**
     * Saves a customer to the database
     * @description Creates or updates a customer record, converted from Spring's save()
     * @param {Customer} customer - The customer object to save
     * @returns {Promise<void>} Resolves when save operation completes
     * @throws {Error} When save operation fails or customer data is invalid
     */
    async save(customer) {
        try {
            // Validate customer object
            if (!customer) {
                throw new Error('Customer object is required');
            }
            
            // Manual transaction handling (replaces Spring @Transactional)
            // In a real implementation, you might use Sequelize transactions
            await this.customerRepository.save(customer);
        } catch (error) {
            throw new Error(`Failed to save customer: ${error.message}`);
        }
    }

    /**
     * Gets the total count of customers
     * @description Returns the number of customers in the database
     * @returns {Promise<number>} Total count of customers
     * @throws {Error} When database query fails
     */
    async getCustomerCount() {
        try {
            // Spring Data getCustomerCount() -> Sequelize count()
            return await this.customerRepository.count();
        } catch (error) {
            throw new Error(`Failed to get customer count: ${error.message}`);
        }
    }
}

/**
 * FilmService - Handles all film-related business operations
 * Converted from Java Spring Service class (com.sparta.engineering72.sakilaproject.services.FilmService)
 * Replaces Spring @Service annotation with Node.js module pattern
 * 
 * Dependencies:
 * - FilmRepository: Data access layer for film operations (replaces Spring Data JPA repository)
 * 
 * @class FilmService
 * @description Provides business logic for managing films in the Sakila database
 */
class FilmService {
    /**
     * Creates an instance of FilmService
     * Dependency injected via constructor (replaces Spring @Autowired)
     * 
     * @param {Object} filmRepository - Repository for film data access operations
     * @description Initializes service with required repository dependency
     */
    constructor(filmRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.filmRepository = filmRepository;
    }

    // TODO: Implement remaining film service methods based on original Java implementation
    // The original FilmService.java was cut off in the provided code
}

module.exports = {
    ActorService,
    CategoryService,
    CustomerService,
    FilmService
};
```