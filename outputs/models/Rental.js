
```javascript
const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  const FilmText = sequelize.define('FilmText', {
    filmId: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      field: 'film_id'
    },
    title: {
      type: DataTypes.STRING,
      field: 'title'
    },
    description: {
      type: DataTypes.TEXT,
      field: 'description'
    }
  }, {
    tableName: 'film_text',
    schema: 'sakila',
    timestamps: false
  });

  return FilmText;
};

const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  const Inventory = sequelize.define('Inventory', {
    inventoryId: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
      field: 'inventory_id'
    },
    filmId: {
      type: DataTypes.INTEGER,
      field: 'film_id',
      allowNull: false
    },
    lastUpdate: {
      type: DataTypes.DATE,
      field: 'last_update',
      allowNull: false,
      defaultValue: DataTypes.NOW
    }
  }, {
    tableName: 'inventory',
    timestamps: false
  });

  Inventory.associate = (models) => {
    Inventory.belongsTo(models.Film, {
      foreignKey: 'filmId',
      as: 'film'
    });
  };

  return Inventory;
};

const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  const Rental = sequelize.define('Rental', {
    rentalId: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
      field: 'rental_id'
    },
    rentalDate: {
      type: DataTypes.DATE,
      field: 'rental_date',
      allowNull: false
    },
    inventoryId: {
      type: DataTypes.INTEGER,
      field: 'inventory_id',
      allowNull: false
    },
    customerId: {
      type: DataTypes.INTEGER,
      field: 'customer_id',
      allowNull: false
    },
    returnDate: {
      type: DataTypes.DATE,
      field: 'return_date'
    },
    staffId: {
      type: DataTypes.INTEGER,
      field: 'staff_id',
      allowNull: false
    },
    lastUpdate: {
      type: DataTypes.DATE,
      field: 'last_update',
      allowNull: false,
      defaultValue: DataTypes.NOW
    }
  }, {
    tableName: 'rental',
    timestamps: false
  });

  Rental.associate = (models) => {
    Rental.belongsTo(models.Inventory, {
      foreignKey: 'inventoryId',
      as: 'inventory'
    });
    Rental.belongsTo(models.Customer, {
      foreignKey: 'customerId',
      as: 'customer'
    });
    Rental.belongsTo(models.Staff, {
      foreignKey: 'staffId',
      as: 'staff'
    });
  };

  return Rental;
};
```