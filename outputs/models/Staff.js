const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Staff = sequelize.define('Staff', {
    customer: {
        type: DataTypes.STRING,
    },
    film: {
        type: DataTypes.STRING,
    },
    rental: {
        type: DataTypes.STRING,
    },
    rentalId: {
        type: DataTypes.STRING,
    },
    rentalDate: {
        type: DataTypes.DATE,
    },
    inventoryId: {
        type: DataTypes.STRING,
    },
    customerId: {
        type: DataTypes.STRING,
    },
    returnDate: {
        type: DataTypes.DATE,
    },
    lastUpdate: {
        type: DataTypes.DATE,
    },
    staffId: {
        type: DataTypes.STRING,
    },
}, {
    tableName: "order",
    timestamps: true,
});

module.exports = Staff;