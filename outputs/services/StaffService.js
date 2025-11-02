
```javascript
/**
 * FilmService - Handles all film-related business operations
 * Converted from Java Spring Service class with @Service annotation
 * Manages film data operations including CRUD, search, and availability checks
 * 
 * @class FilmService
 * @description Service layer for film management operations. Replaces Spring's @Service annotation
 * with a plain JavaScript class. Dependencies are injected via constructor (replaces Spring @Autowired).
 */
class FilmService {
    /**
     * Creates an instance of FilmService.
     * @param {Object} filmRepository - The film data access object (replaces Spring FilmRepository)
     * @description Constructor injection pattern (replaces Spring @Autowired)
     */
    constructor(filmRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.filmRepository = filmRepository;
    }

    /**
     * Retrieves all films from the database
     * @description Gets all film records. Converted from Spring Data findAll() method.
     * @returns {Promise<Array<Film>>} Array of all film objects
     * @throws {Error} When database query fails
     */
    async getAllFilms() {
        try {
            // Sequelize findAll() equivalent to Spring Data findAll()
            return await this.filmRepository.findAll();
        } catch (error) {
            // Error handling converted from Spring's exception propagation
            throw new Error(`Failed to retrieve all films: ${error.message}`);
        }
    }

    /**
     * Retrieves a film by its ID
     * @description Gets a specific film by ID. Converted from Spring Data getFilmByFilmId().
     * Java Optional<T> pattern converted to JavaScript null/object pattern.
     * @param {number} id - The film ID to search for
     * @returns {Promise<Film|null>} The film object if found, null otherwise
     * @throws {Error} When database query fails or ID is invalid
     */
    async getFilmByID(id) {
        // Input validation - converted from Spring @Valid annotation
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Invalid film ID provided');
        }

        try {
            // Sequelize findByPk() equivalent to Spring Data getFilmByFilmId()
            const film = await this.filmRepository.findByPk(id);
            // Java Optional<T> -> JavaScript null/object pattern
            return film || null;
        } catch (error) {
            throw new Error(`Failed to retrieve film with ID ${id}: ${error.message}`);
        }
    }

    /**
     * Retrieves films by title
     * @description Searches for films matching the given title. Converted from Spring Data findByTitle().
     * @param {string} title - The title to search for (case-insensitive)
     * @returns {Promise<Array<Film>>} Array of films matching the title
     * @throws {Error} When database query fails or title is invalid
     */
    async getFilmsByTitle(title) {
        if (!title || typeof title !== 'string') {
            throw new Error('Invalid title provided');
        }

        try {
            // Sequelize query with WHERE clause - converted from Spring Data method name query
            return await this.filmRepository.findAll({
                where: {
                    title: {
                        // Case-insensitive search - common requirement converted from Java
                        [require('sequelize').Op.iLike]: `%${title}%`
                    }
                }
            });
        } catch (error) {
            throw new Error(`Failed to retrieve films by title "${title}": ${error.message}`);
        }
    }

    /**
     * Retrieves all available films
     * @description Gets films that are currently available for rental. Converted from custom repository method.
     * @returns {Promise<Array<Film>>} Array of available films
     * @throws {Error} When database query fails
     */
    async getAvailableFilms() {
        try {
            // Custom query converted from Spring Data @Query annotation
            return await this.filmRepository.getAvailableFilms();
        } catch (error) {
            throw new Error(`Failed to retrieve available films: ${error.message}`);
        }
    }

    /**
     * Gets the count of available copies for a specific film
     * @description Returns the number of available rental copies for a film. Converted from repository method.
     * @param {number} id - The film ID
     * @returns {Promise<number>} Number of available copies
     * @throws {Error} When database query fails or ID is invalid
     */
    async getAvailableFilmCount(id) {
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Invalid film ID provided');
        }

        try {
            // Custom repository method call - converted from Spring Data
            return await this.filmRepository.getAvailableFilmCount(id);
        } catch (error) {
            throw new Error(`Failed to get available film count for ID ${id}: ${error.message}`);
        }
    }

    /**
     * Retrieves films by category
     * @description Gets all films belonging to a specific category. Converted from repository method.
     * @param {number} id - The category ID
     * @returns {Promise<Array<Film>>} Array of films in the category
     * @throws {Error} When database query fails or ID is invalid
     */
    async getFilmsByCategory(id) {
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Invalid category ID provided');
        }

        try {
            // Custom repository method with JOIN - converted from Spring Data
            return await this.filmRepository.getAllFilmsByCategory(id);
        } catch (error) {
            throw new Error(`Failed to retrieve films by category ${id}: ${error.message}`);
        }
    }

    /**
     * Retrieves films by actor
     * @description Gets all films featuring a specific actor. Converted from repository method.
     * @param {number} id - The actor ID
     * @returns {Promise<Array<Film>>} Array of films featuring the actor
     * @throws {Error} When database query fails or ID is invalid
     */
    async getFilmsByActor(id) {
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Invalid actor ID provided');
        }

        try {
            // Custom repository method with JOIN - converted from Spring Data
            return await this.filmRepository.getAllFilmsByActor(id);
        } catch (error) {
            throw new Error(`Failed to retrieve films by actor ${id}: ${error.message}`);
        }
    }

    /**
     * Saves a film to the database
     * @description Creates or updates a film record. Converted from Spring Data save().
     * @param {Object} film - The film object to save
     * @returns {Promise<Film>} The saved film object
     * @throws {Error} When save operation fails or film data is invalid
     */
    async save(film) {
        if (!film || typeof film !== 'object') {
            throw new Error('Invalid film object provided');
        }

        try {
            // Sequelize save() equivalent to Spring Data save()
            return await this.filmRepository.save(film);
        } catch (error) {
            throw new Error(`Failed to save film: ${error.message}`);
        }
    }

    /**
     * Deletes a film by ID
     * @description Removes a film record from the database. Converted from Spring Data deleteById().
     * @param {number} id - The ID of the film to delete
     * @returns {Promise<void>} Resolves when deletion is complete
     * @throws {Error} When deletion fails or ID is invalid
     */
    async deleteFilmById(id) {
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Invalid film ID provided');
        }

        try {
            // Sequelize destroy() equivalent to Spring Data deleteById()
            await this.filmRepository.destroy({
                where: { film_id: id }
            });
        } catch (error) {
            throw new Error(`Failed to delete film with ID ${id}: ${error.message}`);
        }
    }
}

/**
 * InventoryService - Manages inventory-related operations
 * Converted from Java Spring Service class with @Service annotation
 * Handles inventory tracking and management
 * 
 * @class InventoryService
 * @description Service layer for inventory management. Replaces Spring's @Service annotation.
 * Dependencies injected via constructor (replaces Spring @Autowired).
 */
class InventoryService {
    /**
     * Creates an instance of InventoryService.
     * @param {Object} inventoryRepository - The inventory data access object
     * @description Constructor injection pattern (replaces Spring @Autowired)
     */
    constructor(inventoryRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.inventoryRepository = inventoryRepository;
    }

    /**
     * Retrieves all inventory items
     * @description Gets all inventory records. Converted from Spring Data findAll().
     * @returns {Promise<Array<Inventory>>} Array of all inventory items
     * @throws {Error} When database query fails
     */
    async getAllInventory() {
        try {
            // Sequelize findAll() equivalent to Spring Data findAll()
            return await this.inventoryRepository.findAll();
        } catch (error) {
            throw new Error(`Failed to retrieve all inventory: ${error.message}`);
        }
    }

    /**
     * Retrieves inventory by ID
     * @description Gets a specific inventory item by ID. Converted from repository method.
     * @param {number} id - The inventory ID
     * @returns {Promise<Inventory|null>} The inventory object if found, null otherwise
     * @throws {Error} When database query fails or ID is invalid
     */
    async getInventoriesById(id) {
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Invalid inventory ID provided');
        }

        try {
            // Sequelize findByPk() equivalent to repository method
            const inventory = await this.inventoryRepository.findByPk(id);
            // Java Optional<T> -> JavaScript null/object pattern
            return inventory || null;
        } catch (error) {
            throw new Error(`Failed to retrieve inventory with ID ${id}: ${error.message}`);
        }
    }

    /**
     * Deletes an inventory item by ID
     * @description Removes an inventory record. Converted from @Transactional method.
     * Manual transaction handling (replaces Spring @Transactional).
     * @param {number} id - The inventory ID to delete
     * @returns {Promise<void>} Resolves when deletion is complete
     * @throws {Error} When deletion fails or ID is invalid
     */
    async deleteInventoryItemById(id) {
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Invalid inventory ID provided');
        }

        // Manual transaction handling (replaces Spring @Transactional)
        const transaction = await this.inventoryRepository.sequelize.transaction();
        
        try {
            // Sequelize destroy() within transaction
            await this.inventoryRepository.destroy({
                where: { inventory_id: id },
                transaction
            });
            
            // Commit transaction if successful
            await transaction.commit();
        } catch (error) {
            // Rollback on error
            await transaction.rollback();
            throw new Error(`Failed to delete inventory item with ID ${id}: ${error.message}`);
        }
    }

    /**
     * Gets total inventory count
     * @description Returns the total number of inventory items. Converted from repository method.
     * @returns {Promise<number>} Total count of inventory items
     * @throws {Error} When database query fails
     */
    async getInventoryCount() {
        try {
            // Custom repository method - converted from Spring Data
            return await this.inventoryRepository.getInventoryCount();
        } catch (error) {
            throw new Error(`Failed to get inventory count: ${error.message}`);
        }
    }
}

/**
 * RentalService - Manages rental operations
 * Converted from Java Spring Service class with @Service annotation
 * Handles film rental transactions and tracking
 * 
 * @class RentalService
 * @description Service layer for rental management. Replaces Spring's @Service annotation.
 * Dependencies injected via constructor (replaces Spring @Autowired).
 */
class RentalService {
    /**
     * Creates an instance of RentalService.
     * @param {Object} rentalRepository - The rental data access object
     * @description Constructor injection pattern (replaces Spring @Autowired)
     */
    constructor(rentalRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.rentalRepository = rentalRepository;
    }

    /**
     * Retrieves rentals by customer ID
     * @description Gets all rentals for a specific customer. Converted from repository method.
     * @param {number} id - The customer ID
     * @returns {Promise<Array<Rental>>} Array of rental records for the customer
     * @throws {Error} When database query fails or ID is invalid
     */
    async getRentalsByCustomer(id) {
        if (!id || typeof id !== 'number' || id <= 0) {
            throw new Error('Invalid customer ID provided');
        }

        try {
            // Custom repository method - converted from Spring Data
            return await this.rentalRepository.getRentalByCustomerId(id);
        } catch (error) {
            throw new Error(`Failed to retrieve rentals for customer ${id}: ${error.message}`);
        }
    }

    /**
     * Adds a new rental record
     * @description Creates a new rental transaction. Converted from Java method with Timestamp handling.
     * Java LocalDateTime.now() converted to JavaScript Date.now().
     * @param {number} inventoryId - The inventory ID being rented
     * @param {number} customerId - The customer ID renting the item
     * @param {Date} returnDate - The expected return date
     * @returns {Promise<Rental>} The created rental record
     * @throws {Error} When rental creation fails or parameters are invalid
     */
    async addRental(inventoryId, customerId, returnDate) {
        // Input validation - converted from Spring @Valid annotation
        if (!inventoryId || typeof inventoryId !== 'number' || inventoryId <= 0) {
            throw new Error('Invalid inventory ID provided');
        }
        if (!customerId || typeof customerId !== 'number' || customerId <= 0) {
            throw new Error('Invalid customer ID provided');
        }
        if (!returnDate || !(returnDate instanceof Date)) {
            throw new Error('Invalid return date provided');
        }

        try {
            // Java LocalDateTime.now() -> JavaScript new Date()
            const rentalDate = new Date();
            
            // Create rental object - converted from Java entity creation
            const rental = {
                inventory_id: inventoryId,
                customer_id: customerId,
                rental_date: rentalDate,
                // Java Timestamp.valueOf() -> JavaScript Date
                last_update: rentalDate,
                return_date: returnDate,
                staff_id: 1 // Default value as in original Java code
            };

            // Sequelize create() equivalent to Spring Data save()
            return await this.rentalRepository.create(rental);
        } catch (error) {
            throw new Error(`Failed to add rental: ${error.message}`);
        }
    }
}

module.exports = {
    FilmService,
    InventoryService,
    RentalService
    // TODO: Add StaffService when complete (Spring @Service not automatically converted)
};
```