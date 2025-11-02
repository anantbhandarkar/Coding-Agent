
```javascript
const { Model, DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  class FilmActor extends Model {
    static associate(models) {
      // associations can be defined here
      FilmActor.belongsTo(models.Actor, { foreignKey: 'actorId' });
      FilmActor.belongsTo(models.Film, { foreignKey: 'filmId' });
    }
  }

  FilmActor.init(
    {
      actorId: {
        type: DataTypes.INTEGER,
        allowNull: false,
        primaryKey: true,
        field: 'actor_id'
      },
      filmId: {
        type: DataTypes.INTEGER,
        allowNull: false,
        primaryKey: true,
        field: 'film_id'
      },
      lastUpdate: {
        type: DataTypes.DATE,
        allowNull: false,
        field: 'last_update',
        defaultValue: DataTypes.NOW
      }
    },
    {
      sequelize,
      modelName: 'FilmActor',
      tableName: 'film_actor',
      schema: 'sakila',
      timestamps: false
    }
  );

  return FilmActor;
};
```