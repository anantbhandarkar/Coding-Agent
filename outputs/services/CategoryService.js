
```javascript
/**
 * Actor Service - Handles business logic for actor-related operations
 * Converted from Spring's ActorService.java
 * 
 * @class ActorService
 * @description Provides methods to manage actor data including retrieval by various criteria.
 *              Replaces Spring's @Service annotation with a plain JavaScript class.
 *              Dependencies are injected via constructor (replaces Spring @Autowired).
 */
class ActorService {
    /**
     * Creates an instance of ActorService.
     * @constructor
     * @param {Object} actorRepository - The data access object for actor operations
     * @description Constructor injection replaces Spring's @Autowired annotation.
     *              The repository handles all database interactions using Sequelize ORM.
     */
    constructor(actorRepository) {
        // Dependency injected via constructor (replaces Spring @Autowired)
        this.actorRepository = actorRepository;
    }

    /**
     * Retrieves all actors from the database
     * @method getAllActors
     * @description Fetches all actor records. Converted from Spring's findAll() method.
     *              Returns a promise that resolves to an array of Actor objects.
     * @returns {Promise<Array<Actor>>} Array of all actors in the database
     * @throws {Error} When database query fails
     * @example
     * const actors = await actorService.getAllActors();
     * console.log(actors); // [{id: 1, firstName: 'John', lastName: 'Doe'}, ...]
     */
    async getAllActors() {
        try {
            // Sequelize findAll() replaces Spring Data's findAll()
            // Java List<Actor> -> JavaScript Array (Promise<Array<Actor>>)
            const actors = await this.actorRepository.findAll();
            return actors;
        } catch (error) {
            // Error handling replaces Spring's DataAccessException
            throw new Error(`Failed to retrieve all actors: ${error.message}`);
        }
    }

    /**
     * Retrieves an actor by their unique ID
     * @method getActorByID
     * @description Fetches a single actor by their ID. Converted from Spring's getActorByActorId().
     *              Java Optional<T> pattern converted to JavaScript null/object pattern.
     * @param {number} id - The unique identifier of the actor
     * @returns {Promise<Actor|null>} The actor object if found, null otherwise
     * @throws {Error} When database query fails or ID is invalid
     * @example
     * const actor = await actorService.getActorByID(1);
     * if (actor) console.log(actor.firstName); // 'John'
     */
    async getActorByID(id) {
        try {
            // Input validation - replaces Spring's @Valid annotation
            if (!id || typeof id !== 'number' || id <= 0) {
                throw new Error('Invalid actor ID provided');
            }

            // Sequelize findByPk() replaces Spring Data's getActorByActorId()
            // Java Optional<Actor> -> JavaScript null/object pattern
            const actor = await this.actorRepository.findByPk(id);
            return actor || null; // Explicit null return for consistency
        } catch (error) {
            throw new Error(`Failed to retrieve actor by ID ${id}: ${error.message}`);
        }
    }

    /**
     * Retrieves actors by their full name (first and last name)
     * @method getActorsByFullName
     * @description Searches for actors matching both first and last name.
     *              Converted from Spring's findActorsByFirstNameAndLastName().
     * @param {string} firstName - The first name to search for
     * @param {string} lastName - The last name to search for
     * @returns {Promise<Array<Actor>>} Array of actors matching the full name
     * @throws {Error} When database query fails or parameters are invalid
     * @example
     * const actors = await actorService.getActorsByFullName('John', 'Doe');
     * console.log(actors.length); // Number of matching actors
     */
    async getActorsByFullName(firstName, lastName) {
        try {
            // Validate input parameters
            if (!firstName || !lastName || typeof firstName !== 'string' || typeof lastName !== 'string') {
                throw new Error('Both first name and last name must be provided as strings');
            }

            // Sequelize where clause replaces Spring Data's method name query
            // Case-insensitive search for better user experience
            const actors = await this.actorRepository.findAll({
                where: {
                    firstName: {
                        [require('sequelize').Op.iLike]: firstName // iLike for case-insensitive
                    },
                    lastName: {
                        [require('sequelize').Op.iLike]: lastName
                    }
                }
            });
            return actors;
        } catch (error) {
            throw new Error(`Failed to retrieve actors by name ${firstName} ${lastName}: ${error.message}`);
        }
    }

    /**
     * Retrieves actors by their first name
     * @method getActorsByFirstName
     * @description Searches for actors matching the given first name.
     *              Converted from Spring's findActorsByFirstName().
     * @param {string} firstName - The first name to search for
     * @returns {Promise<Array<Actor>>} Array of actors with the given first name
     * @throws {Error} When database query fails or parameter is invalid
     * @example
     * const actors = await actorService.getActorsByFirstName('John');
     * console.log(actors); // All actors named John
     */
    async getActorsByFirstName(firstName) {
        try {
            // Input validation
            if (!firstName || typeof firstName !== 'string') {
                throw new Error('First name must be provided as a string');
            }

            // Sequelize query replaces Spring Data's derived query
            const actors = await this.actorRepository.findAll({
                where: {
                    firstName: {
                        [require('sequelize').Op.iLike]: firstName // Case-insensitive search
                    }
                }
            });
            return actors;
        } catch (error) {
            throw new Error(`Failed to retrieve actors by first name ${firstName}: ${error.message}`);
        }
    }

    /**
     * Retrieves actors by their last name
     * @method getActorsByLastName
     * @description Searches for actors matching the given last name.
     *              Converted from Spring's findActorsByLastName().
     * @param {string} lastName - The last name to search for
     * @returns {Promise<Array<Actor>>} Array of actors with the given last name
     * @throws {Error} When database query fails or parameter is invalid
     * @example
     * const actors = await actorService.getActorsByLastName('Doe');
     * console.log(actors); // All actors with last name Doe
     */
    async getActorsByLastName(lastName) {
        try {
            // Input validation
            if (!lastName || typeof lastName !== 'string') {
                throw new Error('Last name must be provided as a string');
            }

            // Sequelize query replaces Spring Data's derived query
            const actors = await this.actorRepository.findAll({
                where: {
                    lastName: {
                        [require('sequelize').Op.iLike]: lastName // Case-insensitive search
                    }
                }
            });
            return actors;
        } catch (error) {
            throw new Error(`Failed to retrieve actors by last name ${lastName}: ${error.message}`);
        }
    }

    /**
     * Retrieves the full name of an actor by their ID
     * @method getActorFullNameFromID
     * @description Combines first and last name into a single string.
     *              Converted from Java's string concatenation method.
     * @param {number} id - The unique identifier of the actor
     * @returns {Promise<string|null>} The full name of the actor, or null if not found
     * @throws {Error} When database query fails or ID is invalid
     * @example
     * const fullName = await actorService.getActorFullNameFromID(1);
     * console.log(fullName); // 'John Doe'
     */
    async getActorFullNameFromID(id) {
        try {
            // Reuse existing method for consistency (DRY principle)
            const actor = await this.getActorByID(id);
            
            // Java's string concatenation -> JavaScript template literal
            // Returns null if actor not found (consistent with getActorByID)
            return actor ? `${actor.firstName} ${actor.lastName}` : null;
        } catch (error) {
            throw new Error(`Failed to get full name for actor ID ${id}: ${error.message}`);
        }
    }
}

// Export the class for use in other modules
// Replaces Spring's @Component scanning with explicit module export
module.exports = ActorService;

/**
 * Usage Example:
 * 
 * const ActorService = require('./ActorService');
 * const ActorRepository = require('../repositories/ActorRepository');
 * 
 * // Create service instance with dependency injection
 * const actorService = new ActorService(new ActorRepository());
 * 
 * // Use the service methods
 * async function example() {
 *     try {
 *         const allActors = await actorService.getAllActors();
 *         const actor = await actorService.getActorByID(1);
 *         const fullName = await actorService.getActorFullNameFromID(1);
 *         
 *         console.log('All actors:', allActors.length);
 *         console.log('Actor 1:', actor);
 *         console.log('Full name:', fullName);
 *     } catch (error) {
 *         console.error('Error:', error.message);
 *     }
 * }
 * 
 * // Note: This service is inherently async in Node.js (replaces Spring @Async)
 * // TODO: Add caching layer (Spring @Cacheable not automatically converted)
 * // TODO: Add transaction support for multi-operation methods (replaces Spring @Transactional)
 */
```