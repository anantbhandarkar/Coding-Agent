const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Film = sequelize.define('Film', {
    categoryId: {
        type: DataTypes.STRING,
    },
    name: {
        type: DataTypes.STRING,
    },
    lastUpdate: {
        type: DataTypes.DATE,
    },
    customerId: {
        type: DataTypes.STRING,
    },
    firstName: {
        type: DataTypes.STRING,
    },
    lastName: {
        type: DataTypes.STRING,
    },
    email: {
        type: DataTypes.STRING,
    },
    active: {
        type: DataTypes.STRING,
    },
    createDate: {
        type: DataTypes.DATE,
    },
    lastUpdate: {
        type: DataTypes.DATE,
    },
}, {
    tableName: "category",
    timestamps: true,
});

module.exports = Film;