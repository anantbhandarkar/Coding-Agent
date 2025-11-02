
```javascript
const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  const Actor = sequelize.define('Actor', {
    actorId: {
      type: DataTypes.INTEGER,
      field: 'actor_id',
      primaryKey: true,
      autoIncrement: true
    },
    firstName: {
      type: DataTypes.STRING,
      field: 'first_name',
      allowNull: false
    },
    lastName: {
      type: DataTypes.STRING,
      field: 'last_name',
      allowNull: false
    },
    lastUpdate: {
      type: DataTypes.DATE,
      field: 'last_update',
      allowNull: false,
      defaultValue: DataTypes.NOW
    }
  }, {
    tableName: 'actor',
    timestamps: false
  });

  return Actor;
};

const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  const Category = sequelize.define('Category', {
    categoryId: {
      type: DataTypes.INTEGER,
      field: 'category_id',
      primaryKey: true,
      autoIncrement: true
    },
    name: {
      type: DataTypes.STRING,
      allowNull: false
    },
    lastUpdate: {
      type: DataTypes.DATE,
      field: 'last_update',
      allowNull: false,
      defaultValue: DataTypes.NOW
    }
  }, {
    tableName: 'category',
    timestamps: false
  });

  return Category;
};
```