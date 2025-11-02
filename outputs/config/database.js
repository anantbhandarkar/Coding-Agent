const { Sequelize } = require('sequelize');
require('dotenv').config();

const sequelize = new Sequelize(
    process.env.DB_NAME || 'sakila',
    process.env.DB_USER || 'root',
    process.env.DB_PASSWORD || 'Lozinka123',
    {
        host: process.env.DB_HOST || '${MYSQL_HOST',
        port: process.env.DB_PORT || 3306,
        dialect: 'mysql',
        logging: process.env.NODE_ENV === 'development' ? console.log : false,
    }
);

module.exports = sequelize;
