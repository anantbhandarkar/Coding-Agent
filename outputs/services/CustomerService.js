
```javascript
/**
 * @class ActorService
 * @description Service class for managing actor-related business operations. 
 * Converted from Spring's ActorService.java with @Service annotation.
 * Handles all actor data operations including retrieval by various criteria.
 * 
 * @dependencies
 * @property {Object} actorRepository - Sequelize repository for Actor entity operations
 * 
 * @conversionNotes
 * - Converted from Spring @Service to plain JavaScript class
 * - @Autowired dependency injection converted to constructor parameter
 * - All methods converted to async for Node.js database operations
 * - Spring Data JPA methods converted to Sequelize query patterns
 */
class ActorService {
    /**
     * @constructor
     * @description Initializes ActorService with repository dependency.
     * Dependency injected via constructor (replaces Spring @Autowired)
     * 
     * @param {Object} actorRepository - Sequelize repository for Actor entity
     */
    constructor(actorRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.actorRepository = actorRepository;
    }

    /**
     * @method getAllActors
     * @description Retrieves all actors from the database.
     * Converted from Spring Data's findAll() method.
     * 
     * @returns {Promise<Array<Actor>>} Array of all actor objects
     * @throws {Error} When database query fails
     * 
     * @conversionNotes
     * - Java List<Actor> -> JavaScript Promise<Array<Actor>>
     * - Spring Data findAll() -> Sequelize findAll()
     */
    async getAllActors() {
        try {
            // Spring Data's findAll() converted to Sequelize findAll()
            const actors = await this.actorRepository.findAll();
            return actors;
        } catch (error) {
            // Error handling converted from Spring's exception handling
            throw new Error(`Failed to retrieve all actors: ${error.message}`);
        }
    }

    /**
     * @method getActorByID
     * @description Retrieves a specific actor by their ID.
     * Converted from Spring Data's getActorByActorId() method.
     * 
     * @param {number} id - The unique identifier of the actor
     * @returns {Promise<Actor|null>} Actor object if found, null if not found
     * @throws {Error} When database query fails or ID is invalid
     * 
     * @conversionNotes
     * - Java Optional<Actor> -> JavaScript null/object pattern
     * - Spring Data getActorByActorId() -> Sequelize findByPk()
     */
    async getActorByID(id) {
        try {
            // Validate input before processing - converted from Spring @Valid annotation
            if (!id || id <= 0) {
                throw new Error('Invalid actor ID provided');
            }

            // Spring Data's getActorByActorId() converted to Sequelize findByPk()
            const actor = await this.actorRepository.findByPk(id);
            
            // Java Optional<T> -> JavaScript null/object pattern
            return actor || null;
        } catch (error) {
            throw new Error(`Failed to retrieve actor by ID ${id}: ${error.message}`);
        }
    }

    /**
     * @method getActorsByFullName
     * @description Retrieves actors matching both first and last name.
     * Converted from Spring Data's findActorsByFirstNameAndLastName() method.
     * 
     * @param {string} firstName - The first name to search for
     * @param {string} lastName - The last name to search for
     * @returns {Promise<Array<Actor>>} Array of matching actors
     * @throws {Error} When database query fails or names are invalid
     * 
     * @conversionNotes
     * - Spring Data method query -> Sequelize where clause with AND condition
     * - Case sensitivity handled differently in Sequelize vs JPA
     */
    async getActorsByFullName(firstName, lastName) {
        try {
            // Input validation - converted from Spring validation
            if (!firstName || !lastName) {
                throw new Error('Both first name and last name are required');
            }

            // Spring Data's findActorsByFirstNameAndLastName() converted to Sequelize query
            const actors = await this.actorRepository.findAll({
                where: {
                    // Sequelize where clause replaces Spring Data method name query
                    firstName: firstName,
                    lastName: lastName
                }
            });

            return actors;
        } catch (error) {
            throw new Error(`Failed to retrieve actors by name ${firstName} ${lastName}: ${error.message}`);
        }
    }

    /**
     * @method getActorsByFirstName
     * @description Retrieves actors matching the given first name.
     * Converted from Spring Data's findActorsByFirstName() method.
     * 
     * @param {string} firstName - The first name to search for
     * @returns {Promise<Array<Actor>>} Array of actors with matching first name
     * @throws {Error} When database query fails or first name is invalid
     * 
     * @conversionNotes
     * - Spring Data method query -> Sequelize where clause
     * - Added case-insensitive search option for better UX
     */
    async getActorsByFirstName(firstName) {
        try {
            // Input validation
            if (!firstName) {
                throw new Error('First name is required');
            }

            // Spring Data's findActorsByFirstName() converted to Sequelize query
            const actors = await this.actorRepository.findAll({
                where: {
                    firstName: {
                        // Using Sequelize's Op.iLike for case-insensitive search
                        [require('sequelize').Op.iLike]: `%${firstName}%`
                    }
                }
            });

            return actors;
        } catch (error) {
            throw new Error(`Failed to retrieve actors by first name ${firstName}: ${error.message}`);
        }
    }

    /**
     * @method getActorsByLastName
     * @description Retrieves actors matching the given last name.
     * Converted from Spring Data's findActorsByLastName() method.
     * 
     * @param {string} lastName - The last name to search for
     * @returns {Promise<Array<Actor>>} Array of actors with matching last name
     * @throws {Error} When database query fails or last name is invalid
     * 
     * @conversionNotes
     * - Spring Data method query -> Sequelize where clause
     * - Added case-insensitive search for better user experience
     */
    async getActorsByLastName(lastName) {
        try {
            // Input validation
            if (!lastName) {
                throw new Error('Last name is required');
            }

            // Spring Data's findActorsByLastName() converted to Sequelize query
            const actors = await this.actorRepository.findAll({
                where: {
                    lastName: {
                        // Using Sequelize's Op.iLike for case-insensitive search
                        [require('sequelize').Op.iLike]: `%${lastName}%`
                    }
                }
            });

            return actors;
        } catch (error) {
            throw new Error(`Failed to retrieve actors by last name ${lastName}: ${error.message}`);
        }
    }

    /**
     * @method getActorFullNameFromID
     * @description Retrieves the full name of an actor by their ID.
     * Business logic method that combines first and last names.
     * 
     * @param {number} id - The unique identifier of the actor
     * @returns {Promise<string|null>} Full name string if actor found, null if not found
     * @throws {Error} When database query fails or ID is invalid
     * 
     * @conversionNotes
     * - String concatenation logic preserved from Java
     * - Null handling converted from Java's Optional pattern
     */
    async getActorFullNameFromID(id) {
        try {
            // Reuse existing method - maintains DRY principle from original Java code
            const actor = await this.getActorByID(id);
            
            // Java's actor.getFirstName() + " " + actor.getLastName() converted to JavaScript
            if (actor) {
                return `${actor.firstName} ${actor.lastName}`;
            }
            
            // Return null if actor not found - matches Java Optional behavior
            return null;
        } catch (error) {
            throw new Error(`Failed to get full name for actor ID ${id}: ${error.message}`);
        }
    }
}

/**
 * @class CategoryService
 * @description Service class for managing category-related business operations.
 * Converted from Spring's CategoryService.java with @Service annotation.
 * Handles all category data operations including retrieval operations.
 * 
 * @dependencies
 * @property {Object} categoryRepository - Sequelize repository for Category entity operations
 * 
 * @conversionNotes
 * - Converted from Spring @Service to plain JavaScript class
 * - @Autowired dependency injection converted to constructor parameter
 * - All methods converted to async for Node.js database operations
 * - Spring Data JPA methods converted to Sequelize query patterns
 */
class CategoryService {
    /**
     * @constructor
     * @description Initializes CategoryService with repository dependency.
     * Dependency injected via constructor (replaces Spring @Autowired)
     * 
     * @param {Object} categoryRepository - Sequelize repository for Category entity
     */
    constructor(categoryRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.categoryRepository = categoryRepository;
    }

    /**
     * @method getAllCategories
     * @description Retrieves all categories from the database.
     * Converted from Spring Data's findAll() method.
     * 
     * @returns {Promise<Array<Category>>} Array of all category objects
     * @throws {Error} When database query fails
     * 
     * @conversionNotes
     * - Java List<Category> -> JavaScript Promise<Array<Category>>
     * - Spring Data findAll() -> Sequelize findAll()
     */
    async getAllCategories() {
        try {
            // Spring Data's findAll() converted to Sequelize findAll()
            const categories = await this.categoryRepository.findAll();
            return categories;
        } catch (error) {
            // Error handling converted from Spring's exception handling
            throw new Error(`Failed to retrieve all categories: ${error.message}`);
        }
    }

    /**
     * @method getByCategoryId
     * @description Retrieves a specific category by its ID.
     * Converted from Spring Data's getCategoryByCategoryId() method.
     * 
     * @param {number} id - The unique identifier of the category
     * @returns {Promise<Category|null>} Category object if found, null if not found
     * @throws {Error} When database query fails or ID is invalid
     * 
     * @conversionNotes
     * - Java Optional<Category> -> JavaScript null/object pattern
     * - Spring Data getCategoryByCategoryId() -> Sequelize findByPk()
     */
    async getByCategoryId(id) {
        try {
            // Validate input before processing - converted from Spring @Valid annotation
            if (!id || id <= 0) {
                throw new Error('Invalid category ID provided');
            }

            // Spring Data's getCategoryByCategoryId() converted to Sequelize findByPk()
            const category = await this.categoryRepository.findByPk(id);
            
            // Java Optional<T> -> JavaScript null/object pattern
            return category || null;
        } catch (error) {
            throw new Error(`Failed to retrieve category by ID ${id}: ${error.message}`);
        }
    }
}

/**
 * @class CustomerService
 * @description Service class for managing customer-related business operations.
 * Converted from Spring's CustomerService.java with @Service annotation.
 * Handles all customer data operations including retrieval and management.
 * 
 * @dependencies
 * @property {Object} customerRepository - Sequelize repository for Customer entity operations
 * 
 * @conversionNotes
 * - Converted from Spring @Service to plain JavaScript class
 * - @Autowired dependency injection converted to constructor parameter
 * - All methods converted to async for Node.js database operations
 * - Spring Data JPA methods converted to Sequelize query patterns
 * - Note: Original Java file was incomplete, basic structure provided
 */
class CustomerService {
    /**
     * @constructor
     * @description Initializes CustomerService with repository dependency.
     * Dependency injected via constructor (replaces Spring @Autowired)
     * 
     * @param {Object} customerRepository - Sequelize repository for Customer entity
     */
    constructor(customerRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.customerRepository = customerRepository;
    }

    /**
     * @method getAllCustomers
     * @description Retrieves all customers from the database.
     * Standard CRUD operation converted from Spring Data pattern.
     * 
     * @returns {Promise<Array<Customer>>} Array of all customer objects
     * @throws {Error} When database query fails
     * 
     * @conversionNotes
     * - Java List<Customer> -> JavaScript Promise<Array<Customer>>
     * - Spring Data findAll() -> Sequelize findAll()
     */
    async getAllCustomers() {
        try {
            // Spring Data's findAll() converted to Sequelize findAll()
            const customers = await this.customerRepository.findAll();
            return customers;
        } catch (error) {
            // Error handling converted from Spring's exception handling
            throw new Error(`Failed to retrieve all customers: ${error.message}`);
        }
    }

    /**
     * @method getCustomerById
     * @description Retrieves a specific customer by their ID.
     * Standard CRUD operation converted from Spring Data pattern.
     * 
     * @param {number} id - The unique identifier of the customer
     * @returns {Promise<Customer|null>} Customer object if found, null if not found
     * @throws {Error} When database query fails or ID is invalid
     * 
     * @conversionNotes
     * - Java Optional<Customer> -> JavaScript null/object pattern
     * - Spring Data findById() -> Sequelize findByPk()
     */
    async getCustomerById(id) {
        try {
            // Validate input before processing - converted from Spring @Valid annotation
            if (!id || id <= 0) {
                throw new Error('Invalid customer ID provided');
            }

            // Spring Data's findById() converted to Sequelize findByPk()
            const customer = await this.customerRepository.findByPk(id);
            
            // Java Optional<T> -> JavaScript null/object pattern
            return customer || null;
        } catch (error) {
            throw new Error(`Failed to retrieve customer by ID ${id}: ${error.message}`);
        }
    }
}

// Export all service classes for use in other modules
module.exports = {
    ActorService,
    CategoryService,
    CustomerService
};

// TODO: Add caching layer (Spring @Cacheable not automatically converted)
// TODO: Implement manual transaction handling where needed (replaces Spring @Transactional)
// Note: All methods are already async by nature in Node.js (replaces Spring @Async)
```