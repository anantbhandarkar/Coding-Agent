
```javascript
const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  const FilmActor = sequelize.define('FilmActor', {
    actor_id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      allowNull: false,
      field: 'actor_id'
    },
    film_id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      allowNull: false,
      field: 'film_id'
    },
    last_update: {
      type: DataTypes.DATE,
      allowNull: false,
      field: 'last_update'
    }
  }, {
    tableName: 'film_actor',
    schema: 'sakila',
    timestamps: false
  });

  return FilmActor;
};
```