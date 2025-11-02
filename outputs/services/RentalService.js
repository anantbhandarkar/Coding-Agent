
```javascript
/**
 * Customer Service - Handles all customer-related business operations
 * Converted from Spring @Service annotation to Node.js class
 * Original Java class: com.sparta.engineering72.sakilaproject.services.CustomerService
 * 
 * Dependencies:
 * - CustomerRepository: Handles database operations for Customer entities
 *   (Converted from Spring Data JPA Repository to Sequelize DAO)
 */
class CustomerService {
    /**
     * Constructor - Dependency injection replaces Spring @Autowired
     * @param {Object} customerRepository - Repository for customer database operations
     */
    constructor(customerRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.customerRepository = customerRepository;
    }

    /**
     * Retrieves all customers from the database
     * @description Returns a list of all customers in the system
     * @returns {Promise<Array<Customer>>} Array of customer objects
     * @throws {Error} When database query fails
     */
    async getAllCustomers() {
        try {
            // Converted from Spring Data findAll() to Sequelize findAll()
            return await this.customerRepository.findAll();
        } catch (error) {
            throw new Error(`Failed to retrieve all customers: ${error.message}`);
        }
    }

    /**
     * Retrieves customers by first name
     * @description Finds all customers matching the given first name
     * @param {string} firstName - The first name to search for
     * @returns {Promise<Array<Customer>>} Array of matching customers
     * @throws {Error} When database query fails or firstName is invalid
     */
    async getCustomersByFirstName(firstName) {
        // Input validation - converted from Spring @Valid annotation
        if (!firstName || typeof firstName !== 'string') {
            throw new Error('First name must be a non-empty string');
        }

        try {
            // Converted from Spring Data method query to Sequelize where clause
            return await this.customerRepository.findAll({
                where: { firstName }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve customers by first name: ${error.message}`);
        }
    }

    /**
     * Retrieves customers by last name
     * @description Finds all customers matching the given last name
     * @param {string} lastName - The last name to search for
     * @returns {Promise<Array<Customer>>} Array of matching customers
     * @throws {Error} When database query fails or lastName is invalid
     */
    async getCustomersByLastName(lastName) {
        // Input validation - converted from Spring @Valid annotation
        if (!lastName || typeof lastName !== 'string') {
            throw new Error('Last name must be a non-empty string');
        }

        try {
            // Converted from Spring Data method query to Sequelize where clause
            return await this.customerRepository.findAll({
                where: { lastName }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve customers by last name: ${error.message}`);
        }
    }

    /**
     * Retrieves customers by full name
     * @description Finds all customers matching both first and last name
     * @param {string} firstName - The first name to search for
     * @param {string} lastName - The last name to search for
     * @returns {Promise<Array<Customer>>} Array of matching customers
     * @throws {Error} When database query fails or parameters are invalid
     */
    async getCustomersByFullName(firstName, lastName) {
        // Input validation - converted from Spring @Valid annotation
        if (!firstName || typeof firstName !== 'string' || !lastName || typeof lastName !== 'string') {
            throw new Error('First name and last name must be non-empty strings');
        }

        try {
            // Converted from Spring Data method query to Sequelize where clause with multiple conditions
            return await this.customerRepository.findAll({
                where: { 
                    firstName,
                    lastName
                }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve customers by full name: ${error.message}`);
        }
    }

    /**
     * Retrieves a customer by ID
     * @description Finds a customer by their unique ID
     * @param {number} id - The customer ID to search for
     * @returns {Promise<Customer|null>} Customer object or null if not found
     * @throws {Error} When database query fails or id is invalid
     */
    async getCustomerByID(id) {
        // Input validation - converted from Spring @Valid annotation
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Customer ID must be a positive number');
        }

        try {
            // Java Optional<T> -> JavaScript null/object pattern
            const customer = await this.customerRepository.findByPk(id);
            return customer || null;
        } catch (error) {
            throw new Error(`Failed to retrieve customer by ID: ${error.message}`);
        }
    }

    /**
     * Retrieves a customer by email
     * @description Finds a customer by their email address
     * @param {string} email - The email address to search for
     * @returns {Promise<Customer|null>} Customer object or null if not found
     * @throws {Error} When database query fails or email is invalid
     */
    async getCustomerByEmail(email) {
        // Input validation - converted from Spring @Valid annotation
        if (!email || typeof email !== 'string' || !email.includes('@')) {
            throw new Error('Email must be a valid email address');
        }

        try {
            // Java Optional<T> -> JavaScript null/object pattern
            const customer = await this.customerRepository.findOne({
                where: { email }
            });
            return customer || null;
        } catch (error) {
            throw new Error(`Failed to retrieve customer by email: ${error.message}`);
        }
    }

    /**
     * Saves a customer to the database
     * @description Creates or updates a customer record
     * @param {Object} customer - The customer object to save
     * @returns {Promise<void>} Resolves when save is complete
     * @throws {Error} When save operation fails or customer is invalid
     */
    async save(customer) {
        // Input validation - converted from Spring @Valid annotation
        if (!customer || typeof customer !== 'object') {
            throw new Error('Customer must be a valid object');
        }

        try {
            // Converted from Spring Data save() to Sequelize save()
            await this.customerRepository.save(customer);
        } catch (error) {
            throw new Error(`Failed to save customer: ${error.message}`);
        }
    }

    /**
     * Gets the total count of customers
     * @description Returns the total number of customers in the database
     * @returns {Promise<number>} Total customer count
     * @throws {Error} When database query fails
     */
    async getCustomerCount() {
        try {
            // Converted from Spring Data count() to Sequelize count()
            return await this.customerRepository.count();
        } catch (error) {
            throw new Error(`Failed to get customer count: ${error.message}`);
        }
    }
}

/**
 * Film Service - Handles all film-related business operations
 * Converted from Spring @Service annotation to Node.js class
 * Original Java class: com.sparta.engineering72.sakilaproject.services.FilmService
 * 
 * Dependencies:
 * - FilmRepository: Handles database operations for Film entities
 *   (Converted from Spring Data JPA Repository to Sequelize DAO)
 */
class FilmService {
    /**
     * Constructor - Dependency injection replaces Spring @Autowired
     * @param {Object} filmRepository - Repository for film database operations
     */
    constructor(filmRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.filmRepository = filmRepository;
    }

    /**
     * Retrieves all films from the database
     * @description Returns a list of all films in the system
     * @returns {Promise<Array<Film>>} Array of film objects
     * @throws {Error} When database query fails
     */
    async getAllFilms() {
        try {
            // Converted from Spring Data findAll() to Sequelize findAll()
            return await this.filmRepository.findAll();
        } catch (error) {
            throw new Error(`Failed to retrieve all films: ${error.message}`);
        }
    }

    /**
     * Retrieves a film by ID
     * @description Finds a film by its unique ID
     * @param {number} id - The film ID to search for
     * @returns {Promise<Film|null>} Film object or null if not found
     * @throws {Error} When database query fails or id is invalid
     */
    async getFilmByID(id) {
        // Input validation - converted from Spring @Valid annotation
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Film ID must be a positive number');
        }

        try {
            // Java Optional<T> -> JavaScript null/object pattern
            const film = await this.filmRepository.findByPk(id);
            return film || null;
        } catch (error) {
            throw new Error(`Failed to retrieve film by ID: ${error.message}`);
        }
    }

    /**
     * Retrieves films by title
     * @description Finds all films matching the given title
     * @param {string} title - The title to search for
     * @returns {Promise<Array<Film>>} Array of matching films
     * @throws {Error} When database query fails or title is invalid
     */
    async getFilmsByTitle(title) {
        // Input validation - converted from Spring @Valid annotation
        if (!title || typeof title !== 'string') {
            throw new Error('Title must be a non-empty string');
        }

        try {
            // Converted from Spring Data findByTitle() to Sequelize where clause with LIKE
            return await this.filmRepository.findAll({
                where: { 
                    title: {
                        [require('sequelize').Op.like]: `%${title}%`
                    }
                }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve films by title: ${error.message}`);
        }
    }

    /**
     * Retrieves all available films
     * @description Returns films that are currently available for rental
     * @returns {Promise<Array<Film>>} Array of available films
     * @throws {Error} When database query fails
     */
    async getAvailableFilms() {
        try {
            // Complex query converted from Spring Data custom query to Sequelize include
            return await this.filmRepository.findAll({
                where: {
                    // Business logic: films with available inventory
                    '$inventories.rental.return_date$': {
                        [require('sequelize').Op.not]: null
                    }
                },
                include: [{
                    model: require('./inventory').Inventory,
                    include: [{
                        model: require('./rental').Rental
                    }]
                }]
            });
        } catch (error) {
            throw new Error(`Failed to retrieve available films: ${error.message}`);
        }
    }

    /**
     * Gets the count of available copies for a film
     * @description Returns the number of available rental copies for a specific film
     * @param {number} id - The film ID
     * @returns {Promise<number>} Number of available copies
     * @throws {Error} When database query fails or id is invalid
     */
    async getAvailableFilmCount(id) {
        // Input validation - converted from Spring @Valid annotation
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Film ID must be a positive number');
        }

        try {
            // Complex count query converted from Spring Data to Sequelize
            const film = await this.filmRepository.findByPk(id, {
                include: [{
                    model: require('./inventory').Inventory,
                    where: {
                        // Business logic: count only non-rented inventory
                        '$rentals.return_date$': {
                            [require('sequelize').Op.not]: null
                        }
                    },
                    required: false
                }]
            });
            
            return film ? film.inventories.length : 0;
        } catch (error) {
            throw new Error(`Failed to get available film count: ${error.message}`);
        }
    }

    /**
     * Retrieves films by category
     * @description Finds all films in a specific category
     * @param {number} id - The category ID
     * @returns {Promise<Array<Film>>} Array of films in the category
     * @throws {Error} When database query fails or id is invalid
     */
    async getFilmsByCategory(id) {
        // Input validation - converted from Spring @Valid annotation
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Category ID must be a positive number');
        }

        try {
            // Many-to-many query converted from Spring Data to Sequelize through join table
            return await this.filmRepository.findAll({
                include: [{
                    model: require('./category').Category,
                    where: { categoryId: id }
                }]
            });
        } catch (error) {
            throw new Error(`Failed to retrieve films by category: ${error.message}`);
        }
    }

    /**
     * Retrieves films by actor
     * @description Finds all films featuring a specific actor
     * @param {number} id - The actor ID
     * @returns {Promise<Array<Film>>} Array of films featuring the actor
     * @throws {Error} When database query fails or id is invalid
     */
    async getFilmsByActor(id) {
        // Input validation - converted from Spring @Valid annotation
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Actor ID must be a positive number');
        }

        try {
            // Many-to-many query converted from Spring Data to Sequelize through join table
            return await this.filmRepository.findAll({
                include: [{
                    model: require('./actor').Actor,
                    where: { actorId: id }
                }]
            });
        } catch (error) {
            throw new Error(`Failed to retrieve films by actor: ${error.message}`);
        }
    }

    /**
     * Saves a film to the database
     * @description Creates or updates a film record
     * @param {Object} film - The film object to save
     * @returns {Promise<void>} Resolves when save is complete
     * @throws {Error} When save operation fails or film is invalid
     */
    async save(film) {
        // Input validation - converted from Spring @Valid annotation
        if (!film || typeof film !== 'object') {
            throw new Error('Film must be a valid object');
        }

        try {
            // Converted from Spring Data save() to Sequelize save()
            await this.filmRepository.save(film);
        } catch (error) {
            throw new Error(`Failed to save film: ${error.message}`);
        }
    }

    /**
     * Deletes a film by ID
     * @description Removes a film record from the database
     * @param {number} id - The film ID to delete
     * @returns {Promise<void>} Resolves when deletion is complete
     * @throws {Error} When deletion fails or id is invalid
     */
    async deleteFilmById(id) {
        // Input validation - converted from Spring @Valid annotation
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Film ID must be a positive number');
        }

        try {
            // Manual transaction handling (replaces Spring @Transactional)
            const transaction = await this.filmRepository.sequelize.transaction();
            
            try {
                // First delete related records (business logic preservation)
                await this.filmRepository.destroy({
                    where: { filmId: id },
                    transaction
                });
                
                await transaction.commit();
            } catch (error) {
                await transaction.rollback();
                throw error;
            }
        } catch (error) {
            throw new Error(`Failed to delete film: ${error.message}`);
        }
    }
}

/**
 * Inventory Service - Handles all inventory-related business operations
 * Converted from Spring @Service annotation to Node.js class
 * Original Java class: com.sparta.engineering72.sakilaproject.services.InventoryService
 * 
 * Dependencies:
 * - InventoryRepository: Handles database operations for Inventory entities
 *   (Converted from Spring Data JPA Repository to Sequelize DAO)
 */
class InventoryService {
    /**
     * Constructor - Dependency injection replaces Spring @Autowired
     * @param {Object} inventoryRepository - Repository for inventory database operations
     */
    constructor(inventoryRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.inventoryRepository = inventoryRepository;
    }

    /**
     * Retrieves all inventory items
     * @description Returns a list of all inventory items in the system
     * @returns {Promise<Array<Inventory>>} Array of inventory objects
     * @throws {Error} When database query fails
     */
    async getAllInventory() {
        try {
            // Converted from Spring Data findAll() to Sequelize findAll()
            return await this.inventoryRepository.findAll();
        } catch (error) {
            throw new Error(`Failed to retrieve all inventory: ${error.message}`);
        }
    }

    /**
     * Retrieves an inventory item by ID
     * @description Finds an inventory item by its unique ID
     * @param {number} id - The inventory ID to search for
     * @returns {Promise<Inventory|null>} Inventory object or null if not found
     * @throws {Error} When database query fails or id is invalid
     */
    async getInventoriesById(id) {
        // Input validation - converted from Spring @Valid annotation
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Inventory ID must be a positive number');
        }

        try {
            // Java Optional<T> -> JavaScript null/object pattern
            const inventory = await this.inventoryRepository.findByPk(id);
            return inventory || null;
        } catch (error) {
            throw new Error(`Failed to retrieve inventory by ID: ${error.message}`);
        }
    }

    /**
     * Deletes an inventory item by ID
     * @description Removes an inventory item from the database with transaction safety
     * @param {number} id - The inventory ID to delete
     * @returns {Promise<void>} Resolves when deletion is complete
     * @throws {Error} When deletion fails or id is invalid
     */
    async deleteInventoryItemById(id) {
        // Input validation - converted from Spring @Valid annotation
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Inventory ID must be a positive number');
        }

        try {
            // Manual transaction handling (replaces Spring @Transactional)
            const transaction = await this.inventoryRepository.sequelize.transaction();
            
            try {
                // Business logic: Check if inventory is currently rented
                const inventory = await this.inventoryRepository.findByPk(id, {
                    include: [{
                        model: require('./rental').Rental,
                        where: {
                            return_date: null
                        },
                        required: false
                    }],
                    transaction
                });

                if (inventory && inventory.rentals && inventory.rentals.length > 0) {
                    throw new Error('Cannot delete inventory item that is currently rented');
                }

                // Delete the inventory item
                await this.inventoryRepository.destroy({
                    where: { inventoryId: id },
                    transaction
                });

                await transaction.commit();
            } catch (error) {
                await transaction.rollback();
                throw error;
            }
        } catch (error) {
            throw new Error(`Failed to delete inventory item: ${error.message}`);
        }
    }

    /**
     * Gets the total count of inventory items
     * @description Returns the total number of inventory items in the database
     * @returns {Promise<number>} Total inventory count
     * @throws {Error} When database query fails
     */
    async getInventoryCount() {
        try {
            // Converted from Spring Data count() to Sequelize count()
            return await this.inventoryRepository.count();
        } catch (error) {
            throw new Error(`Failed to get inventory count: ${error.message}`);
        }
    }
}

/**
 * Rental Service - Handles all rental-related business operations
 * Converted from Spring @Service annotation to Node.js class
 * Original Java class: com.sparta.engineering72.sakilaproject.services.RentalService
 * 
 * Dependencies:
 * - RentalRepository: Handles database operations for Rental entities
 *   (Converted from Spring Data JPA Repository to Sequelize DAO)
 */
class RentalService {
    /**
     * Constructor - Dependency injection replaces Spring @Autowired
     * @param {Object} rentalRepository - Repository for rental database operations
     */
    constructor(rentalRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.rentalRepository = rentalRepository;
    }

    /**
     * Retrieves all rentals from the database
     * @description Returns a list of all rental records
     * @returns {Promise<Array<Rental>>} Array of rental objects
     * @throws {Error} When database query fails
     */
    async getAllRentals() {
        try {
            // Converted from Spring Data findAll() to Sequelize findAll()
            return await this.rentalRepository.findAll();
        } catch (error) {
            throw new Error(`Failed to retrieve all rentals: ${error.message}`);
        }
    }

    /**
     * Retrieves rentals by customer ID
     * @description Finds all rentals for a specific customer
     * @param {number} customerId - The customer ID to search for
     * @returns {Promise<Array<Rental>>} Array of rental objects
     * @throws {Error} When database query fails or customerId is invalid
     */
    async getRentalsByCustomerId(customerId) {
        // Input validation - converted from Spring @Valid annotation
        if (!customerId || typeof customerId !== 'number' || customerId <= 0) {
            throw new Error('Customer ID must be a positive number');
        }

        try {
            // Converted from Spring Data method query to Sequelize where clause
            return await this.rentalRepository.findAll({
                where: { customerId }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve rentals by customer ID: ${error.message}`);
        }
    }

    /**
     * Retrieves active rentals (not returned)
     * @description Returns all currently active rentals
     * @returns {Promise<Array<Rental>>} Array of active rental objects
     * @throws {Error} When database query fails
     */
    async getActiveRentals() {
        try {
            // Business logic: Find rentals where return_date is null
            return await this.rentalRepository.findAll({
                where: {
                    returnDate: null
                }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve active rentals: ${error.message}`);
        }
    }

    /**
     * Creates a new rental record
     * @description Rents a film to a customer with transaction safety
     * @param {number} inventoryId - The inventory item to rent
     * @param {number} customerId - The customer renting the item
     * @param {Date} rentalDate - The date of the rental
     * @returns {Promise<Rental>} The created rental record
     * @throws {Error} When rental creation fails or parameters are invalid
     */
    async createRental(inventoryId, customerId, rentalDate = new Date()) {
        // Input validation - converted from Spring @Valid annotation
        if (!inventoryId || typeof inventoryId !== 'number' || inventoryId <= 0) {
            throw new Error('Inventory ID must be a positive number');
        }
        if (!customerId || typeof customerId !== 'number' || customerId <= 0) {
            throw new Error('Customer ID must be a positive number');
        }

        try {
            // Manual transaction handling (replaces Spring @Transactional)
            const transaction = await this.rentalRepository.sequelize.transaction();
            
            try {
                // Business logic: Check if inventory is available
                const inventory = await require('./inventory').InventoryRepository.findByPk(inventoryId, {
                    include: [{
                        model: this.rentalRepository,
                        where: {
                            returnDate: null
                        },
                        required: false
                    }],
                    transaction
                });

                if (!inventory) {
                    throw new Error('Inventory item not found');
                }

                if (inventory.rentals && inventory.rentals.length > 0) {
                    throw new Error('Inventory item is already rented');
                }

                // Create the rental record
                const rental = await this.rentalRepository.create({
                    inventoryId,
                    customerId,
                    rentalDate,
                    returnDate: null
                }, { transaction });

                await transaction.commit();
                return rental;
            } catch (error) {
                await transaction.rollback();
                throw error;
            }
        } catch (error) {
            throw new Error(`Failed to create rental: ${error.message}`);
        }
    }

    /**
     *