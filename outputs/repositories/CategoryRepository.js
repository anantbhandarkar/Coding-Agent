const Category = require('../models/Category');
const { Op } = require('sequelize');

class CategoryRepository {
    /**
     * Find entity by ID
     * @description Retrieves an entity by its primary key
     * @param {number} id - Entity ID
     * @returns {Promise<Object|null>} Entity object or null if not found
     */
    async findById(id) {
        return await Category.findByPk(id);
    }

    /**
     * Find all entities
     * @description Retrieves all entities from the database
     * @returns {Promise<Array>} Array of entity objects
     */
    async findAll() {
        return await Category.findAll();
    }

    /**
     * Save entity (create or update)
     * @description Creates a new entity or updates existing one based on ID presence
     * @param {Object} entity - Entity object to save
     * @returns {Promise<Object>} Saved entity object
     */
    async save(entity) {
        if (entity.id) {
            return await Category.update(entity, {
                where: {id: entity.id}
            });
        } else {
            return await Category.create(entity);
        }
    }

    /**
     * Delete entity by ID
     * @description Deletes an entity by its primary key
     * @param {number} id - Entity ID to delete
     * @returns {Promise<number>} Number of deleted rows
     */
    async deleteById(id) {
        return await Category.destroy({
            where: {id}
        });
    }
}

module.exports = new CategoryRepository();