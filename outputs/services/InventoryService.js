
```javascript
/**
 * @class CategoryService
 * @description Service class for managing category-related business operations. 
 * Converted from Java Spring CategoryService with @Service annotation.
 * Handles all category data operations through the CategoryRepository.
 * 
 * @dependencies
 * @property {CategoryRepository} categoryRepository - Repository for category data access (replaces Spring @Autowired)
 */
class CategoryService {
    /**
     * @constructor
     * @description Initializes CategoryService with required dependencies.
     * Dependency injected via constructor (replaces Spring @Autowired)
     * @param {CategoryRepository} categoryRepository - Repository for category database operations
     */
    constructor(categoryRepository) {
        this.categoryRepository = categoryRepository;
    }

    /**
     * @method getAllCategories
     * @description Retrieves all categories from the database.
     * Converted from Spring's findAll() method to async/await pattern.
     * @returns {Promise<Array<Category>>} Array of all category objects
     * @throws {Error} When database query fails
     */
    async getAllCategories() {
        try {
            // Sequelize findAll() equivalent to Spring Data findAll()
            return await this.categoryRepository.findAll();
        } catch (error) {
            // Error handling converted from Spring's DataAccessException
            throw new Error(`Failed to retrieve all categories: ${error.message}`);
        }
    }

    /**
     * @method getByCategoryId
     * @description Retrieves a specific category by its ID.
     * Converted from Spring's getCategoryByCategoryId() method.
     * Java Optional<T> -> JavaScript null/object pattern
     * @param {number} id - The category ID to search for
     * @returns {Promise<Category|null>} Category object if found, null if not found
     * @throws {Error} When database query fails or invalid ID provided
     */
    async getByCategoryId(id) {
        try {
            // Input validation - converted from Spring @Valid annotation
            if (!id || typeof id !== 'number' || id <= 0) {
                throw new Error('Invalid category ID provided');
            }
            
            // Sequelize findByPk() equivalent to Spring Data custom query
            const category = await this.categoryRepository.findByPk(id);
            return category || null; // Explicit null return for consistency
        } catch (error) {
            throw new Error(`Failed to retrieve category by ID ${id}: ${error.message}`);
        }
    }
}

/**
 * @class CustomerService
 * @description Service class for managing customer-related business operations.
 * Converted from Java Spring CustomerService with @Service annotation.
 * Handles all customer data operations including CRUD and search functionality.
 * 
 * @dependencies
 * @property {CustomerRepository} customerRepository - Repository for customer data access (replaces Spring @Autowired)
 */
class CustomerService {
    /**
     * @constructor
     * @description Initializes CustomerService with required dependencies.
     * Dependency injected via constructor (replaces Spring @Autowired)
     * @param {CustomerRepository} customerRepository - Repository for customer database operations
     */
    constructor(customerRepository) {
        this.customerRepository = customerRepository;
    }

    /**
     * @method getAllCustomers
     * @description Retrieves all customers from the database.
     * Converted from Spring's findAll() method to async/await pattern.
     * @returns {Promise<Array<Customer>>} Array of all customer objects
     * @throws {Error} When database query fails
     */
    async getAllCustomers() {
        try {
            // Sequelize findAll() equivalent to Spring Data findAll()
            return await this.customerRepository.findAll();
        } catch (error) {
            throw new Error(`Failed to retrieve all customers: ${error.message}`);
        }
    }

    /**
     * @method getCustomersByFirstName
     * @description Retrieves customers filtered by first name.
     * Converted from Spring's getCustomersByFirstName() custom query method.
     * @param {string} firstName - The first name to filter by
     * @returns {Promise<Array<Customer>>} Array of matching customer objects
     * @throws {Error} When database query fails or invalid name provided
     */
    async getCustomersByFirstName(firstName) {
        try {
            // Input validation - converted from Spring @Valid annotation
            if (!firstName || typeof firstName !== 'string') {
                throw new Error('Invalid first name provided');
            }
            
            // Sequelize where clause equivalent to Spring Data custom query
            return await this.customerRepository.findAll({
                where: { firstName: { [require('sequelize').Op.like]: `%${firstName}%` } }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve customers by first name '${firstName}': ${error.message}`);
        }
    }

    /**
     * @method getCustomersByLastName
     * @description Retrieves customers filtered by last name.
     * Converted from Spring's getCustomersByLastName() custom query method.
     * @param {string} lastName - The last name to filter by
     * @returns {Promise<Array<Customer>>} Array of matching customer objects
     * @throws {Error} When database query fails or invalid name provided
     */
    async getCustomersByLastName(lastName) {
        try {
            // Input validation
            if (!lastName || typeof lastName !== 'string') {
                throw new Error('Invalid last name provided');
            }
            
            // Sequelize where clause for case-insensitive search
            return await this.customerRepository.findAll({
                where: { lastName: { [require('sequelize').Op.iLike]: `%${lastName}%` } }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve customers by last name '${lastName}': ${error.message}`);
        }
    }

    /**
     * @method getCustomersByFullName
     * @description Retrieves customers filtered by both first and last name.
     * Converted from Spring's getCustomersByFullName() custom query method.
     * @param {string} firstName - The first name to filter by
     * @param {string} lastName - The last name to filter by
     * @returns {Promise<Array<Customer>>} Array of matching customer objects
     * @throws {Error} When database query fails or invalid names provided
     */
    async getCustomersByFullName(firstName, lastName) {
        try {
            // Input validation for both parameters
            if (!firstName || typeof firstName !== 'string' || !lastName || typeof lastName !== 'string') {
                throw new Error('Invalid first name or last name provided');
            }
            
            // Sequelize multiple where conditions equivalent to Spring Data custom query
            return await this.customerRepository.findAll({
                where: {
                    firstName: { [require('sequelize').Op.iLike]: `%${firstName}%` },
                    lastName: { [require('sequelize').Op.iLike]: `%${lastName}%` }
                }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve customers by full name '${firstName} ${lastName}': ${error.message}`);
        }
    }

    /**
     * @method getCustomerByID
     * @description Retrieves a specific customer by their ID.
     * Converted from Spring's getCustomerByCustomerId() method.
     * Java Optional<T> -> JavaScript null/object pattern
     * @param {number} id - The customer ID to search for
     * @returns {Promise<Customer|null>} Customer object if found, null if not found
     * @throws {Error} When database query fails or invalid ID provided
     */
    async getCustomerByID(id) {
        try {
            // Input validation
            if (!id || typeof id !== 'number' || id <= 0) {
                throw new Error('Invalid customer ID provided');
            }
            
            // Sequelize findByPk() equivalent to Spring Data custom query
            const customer = await this.customerRepository.findByPk(id);
            return customer || null;
        } catch (error) {
            throw new Error(`Failed to retrieve customer by ID ${id}: ${error.message}`);
        }
    }

    /**
     * @method getCustomerByEmail
     * @description Retrieves a specific customer by their email address.
     * Converted from Spring's getCustomerByEmail() custom query method.
     * @param {string} email - The email address to search for
     * @returns {Promise<Customer|null>} Customer object if found, null if not found
     * @throws {Error} When database query fails or invalid email provided
     */
    async getCustomerByEmail(email) {
        try {
            // Email format validation
            if (!email || typeof email !== 'string' || !email.includes('@')) {
                throw new Error('Invalid email address provided');
            }
            
            // Sequelize findOne() with where clause equivalent to Spring Data custom query
            const customer = await this.customerRepository.findOne({
                where: { email: email.toLowerCase() } // Normalize email for case-insensitive search
            });
            return customer || null;
        } catch (error) {
            throw new Error(`Failed to retrieve customer by email '${email}': ${error.message}`);
        }
    }

    /**
     * @method save
     * @description Saves a customer to the database (create or update).
     * Converted from Spring's save() method.
     * Manual transaction handling (replaces Spring @Transactional)
     * @param {Customer} customer - The customer object to save
     * @returns {Promise<void>} Resolves when save operation completes
     * @throws {Error} When save operation fails or invalid customer data provided
     */
    async save(customer) {
        const transaction = await this.customerRepository.sequelize.transaction();
        try {
            // Input validation - converted from Spring @Valid annotation
            if (!customer || typeof customer !== 'object') {
                throw new Error('Invalid customer object provided');
            }
            
            // Sequelize save() equivalent to Spring Data save()
            await this.customerRepository.save(customer, { transaction });
            await transaction.commit();
        } catch (error) {
            await transaction.rollback();
            throw new Error(`Failed to save customer: ${error.message}`);
        }
    }

    /**
     * @method getCustomerCount
     * @description Retrieves the total count of customers in the database.
     * Converted from Spring's getCustomerCount() custom query method.
     * @returns {Promise<number>} Total number of customers
     * @throws {Error} When database query fails
     */
    async getCustomerCount() {
        try {
            // Sequelize count() equivalent to Spring Data custom count query
            return await this.customerRepository.count();
        } catch (error) {
            throw new Error(`Failed to retrieve customer count: ${error.message}`);
        }
    }
}

/**
 * @class FilmService
 * @description Service class for managing film-related business operations.
 * Converted from Java Spring FilmService with @Service annotation.
 * Handles all film data operations including CRUD, search, and availability checks.
 * 
 * @dependencies
 * @property {FilmRepository} filmRepository - Repository for film data access (replaces Spring @Autowired)
 */
class FilmService {
    /**
     * @constructor
     * @description Initializes FilmService with required dependencies.
     * Dependency injected via constructor (replaces Spring @Autowired)
     * @param {FilmRepository} filmRepository - Repository for film database operations
     */
    constructor(filmRepository) {
        this.filmRepository = filmRepository;
    }

    /**
     * @method getAllFilms
     * @description Retrieves all films from the database.
     * Converted from Spring's findAll() method to async/await pattern.
     * @returns {Promise<Array<Film>>} Array of all film objects
     * @throws {Error} When database query fails
     */
    async getAllFilms() {
        try {
            // Sequelize findAll() equivalent to Spring Data findAll()
            return await this.filmRepository.findAll();
        } catch (error) {
            throw new Error(`Failed to retrieve all films: ${error.message}`);
        }
    }

    /**
     * @method getFilmByID
     * @description Retrieves a specific film by its ID.
     * Converted from Spring's getFilmByFilmId() method.
     * Java Optional<T> -> JavaScript null/object pattern
     * @param {number} id - The film ID to search for
     * @returns {Promise<Film|null>} Film object if found, null if not found
     * @throws {Error} When database query fails or invalid ID provided
     */
    async getFilmByID(id) {
        try {
            // Input validation
            if (!id || typeof id !== 'number' || id <= 0) {
                throw new Error('Invalid film ID provided');
            }
            
            // Sequelize findByPk() equivalent to Spring Data custom query
            const film = await this.filmRepository.findByPk(id);
            return film || null;
        } catch (error) {
            throw new Error(`Failed to retrieve film by ID ${id}: ${error.message}`);
        }
    }

    /**
     * @method getFilmsByTitle
     * @description Retrieves films filtered by title.
     * Converted from Spring's findByTitle() custom query method.
     * @param {string} title - The title to filter by
     * @returns {Promise<Array<Film>>} Array of matching film objects
     * @throws {Error} When database query fails or invalid title provided
     */
    async getFilmsByTitle(title) {
        try {
            // Input validation
            if (!title || typeof title !== 'string') {
                throw new Error('Invalid film title provided');
            }
            
            // Sequelize where clause with case-insensitive search
            return await this.filmRepository.findAll({
                where: { title: { [require('sequelize').Op.iLike]: `%${title}%` } }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve films by title '${title}': ${error.message}`);
        }
    }

    /**
     * @method getAvailableFilms
     * @description Retrieves all films that are currently available for rental.
     * Converted from Spring's getAvailableFilms() custom query method.
     * Complex business logic - checks inventory availability
     * @returns {Promise<Array<Film>>} Array of available film objects
     * @throws {Error} When database query fails
     */
    async getAvailableFilms() {
        try {
            // Complex query - converted from Spring Data JPQL
            // This requires joining Film, Inventory, and Rental tables
            return await this.filmRepository.findAll({
                include: [{
                    model: require('./Inventory'),
                    as: 'inventories',
                    where: {
                        // Custom logic to check availability
                        '$inventories.rentals.returnDate$': { [require('sequelize').Op.not]: null }
                    }
                }],
                distinct: true
            });
        } catch (error) {
            throw new Error(`Failed to retrieve available films: ${error.message}`);
        }
    }

    /**
     * @method getAvailableFilmCount
     * @description Retrieves the count of available copies for a specific film.
     * Converted from Spring's getAvailableFilmCount() custom query method.
     * @param {number} id - The film ID to check availability for
     * @returns {Promise<number>} Number of available copies
     * @throws {Error} When database query fails or invalid ID provided
     */
    async getAvailableFilmCount(id) {
        try {
            // Input validation
            if (!id || typeof id !== 'number' || id <= 0) {
                throw new Error('Invalid film ID provided');
            }
            
            // Complex count query - converted from Spring Data custom query
            const film = await this.filmRepository.findByPk(id, {
                include: [{
                    model: require('./Inventory'),
                    as: 'inventories',
                    where: {
                        // Logic to count only non-rented copies
                        '$inventories.rentals.returnDate$': { [require('sequelize').Op.not]: null }
                    }
                }]
            });
            
            return film ? film.inventories.length : 0;
        } catch (error) {
            throw new Error(`Failed to retrieve available film count for ID ${id}: ${error.message}`);
        }
    }

    /**
     * @method getFilmsByCategory
     * @description Retrieves films filtered by category ID.
     * Converted from Spring's getAllFilmsByCategory() custom query method.
     * @param {number} id - The category ID to filter by
     * @returns {Promise<Array<Film>>} Array of films in the specified category
     * @throws {Error} When database query fails or invalid ID provided
     */
    async getFilmsByCategory(id) {
        try {
            // Input validation
            if (!id || typeof id !== 'number' || id <= 0) {
                throw new Error('Invalid category ID provided');
            }
            
            // Sequelize include with where clause equivalent to Spring Data join query
            return await this.filmRepository.findAll({
                include: [{
                    model: require('./Category'),
                    as: 'categories',
                    where: { categoryId: id }
                }]
            });
        } catch (error) {
            throw new Error(`Failed to retrieve films by category ID ${id}: ${error.message}`);
        }
    }

    /**
     * @method getFilmsByActor
     * @description Retrieves films filtered by actor ID.
     * Converted from Spring's getAllFilmsByActor() custom query method.
     * @param {number} id - The actor ID to filter by
     * @returns {Promise<Array<Film>>} Array of films featuring the specified actor
     * @throws {Error} When database query fails or invalid ID provided
     */
    async getFilmsByActor(id) {
        try {
            // Input validation
            if (!id || typeof id !== 'number' || id <= 0) {
                throw new Error('Invalid actor ID provided');
            }
            
            // Sequelize include with where clause for many-to-many relationship
            return await this.filmRepository.findAll({
                include: [{
                    model: require('./Actor'),
                    as: 'actors',
                    where: { actorId: id }
                }]
            });
        } catch (error) {
            throw new Error(`Failed to retrieve films by actor ID ${id}: ${error.message}`);
        }
    }

    /**
     * @method save
     * @description Saves a film to the database (create or update).
     * Converted from Spring's save() method.
     * Manual transaction handling (replaces Spring @Transactional)
     * @param {Film} film - The film object to save
     * @returns {Promise<void>} Resolves when save operation completes
     * @throws {Error} When save operation fails or invalid film data provided
     */
    async save(film) {
        const transaction = await this.filmRepository.sequelize.transaction();
        try {
            // Input validation
            if (!film || typeof film !== 'object') {
                throw new Error('Invalid film object provided');
            }
            
            // Sequelize save() with transaction equivalent to Spring Data save()
            await this.filmRepository.save(film, { transaction });
            await transaction.commit();
        } catch (error) {
            await transaction.rollback();
            throw new Error(`Failed to save film: ${error.message}`);
        }
    }

    /**
     * @method deleteFilmById
     * @description Deletes a film by its ID.
     * Converted from Spring's deleteById() method.
     * Manual transaction handling (replaces Spring @Transactional)
     * @param {number} id - The film ID to delete
     * @returns {Promise<void>} Resolves when delete operation completes
     * @throws {Error} When delete operation fails or invalid ID provided
     */
    async deleteFilmById(id) {
        const transaction = await this.filmRepository.sequelize.transaction();
        try {
            // Input validation
            if (!id || typeof id !== 'number' || id <= 0) {
                throw new Error('Invalid film ID provided');
            }
            
            // Check if film exists before deletion
            const film = await this.filmRepository.findByPk(id, { transaction });
            if (!film) {
                throw new Error(`Film with ID ${id} not found`);
            }
            
            // Sequelize destroy() with transaction equivalent to Spring Data deleteById()
            await this.filmRepository.destroy({
                where: { filmId: id },
                transaction
            });
            await transaction.commit();
        } catch (error) {
            await transaction.rollback();
            throw new Error(`Failed to delete film with ID ${id}: ${error.message}`);
        }
    }
}

// TODO: Add caching layer (Spring @Cacheable not automatically converted)
// TODO: Add rate limiting for API endpoints
// TODO: Implement proper logging system
// TODO: Add input sanitization for security

module.exports = {
    CategoryService,
    CustomerService,
    FilmService
};
```