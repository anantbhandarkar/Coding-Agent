const Customer = require('../models/Customer');
const { Op } = require('sequelize');

class CustomerRepository {
    /**
     * Find entity by ID
     * @description Retrieves an entity by its primary key
     * @param {number} id - Entity ID
     * @returns {Promise<Object|null>} Entity object or null if not found
     */
    async findById(id) {
        return await Customer.findByPk(id);
    }

    /**
     * Find all entities
     * @description Retrieves all entities from the database
     * @returns {Promise<Array>} Array of entity objects
     */
    async findAll() {
        return await Customer.findAll();
    }

    /**
     * Save entity (create or update)
     * @description Creates a new entity or updates existing one based on ID presence
     * @param {Object} entity - Entity object to save
     * @returns {Promise<Object>} Saved entity object
     */
    async save(entity) {
        if (entity.id) {
            return await Customer.update(entity, {
                where: {id: entity.id}
            });
        } else {
            return await Customer.create(entity);
        }
    }

    /**
     * Delete entity by ID
     * @description Deletes an entity by its primary key
     * @param {number} id - Entity ID to delete
     * @returns {Promise<number>} Number of deleted rows
     */
    async deleteById(id) {
        return await Customer.destroy({
            where: {id}
        });
    }
}

module.exports = new CustomerRepository();