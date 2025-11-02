
```javascript
const { DataTypes, Model } = require('sequelize');

class Actor extends Model {
  static init(sequelize) {
    return super.init({
      actorId: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
        field: 'actor_id'
      },
      firstName: {
        type: DataTypes.STRING,
        allowNull: false,
        field: 'first_name'
      },
      lastName: {
        type: DataTypes.STRING,
        allowNull: false,
        field: 'last_name'
      },
      lastUpdate: {
        type: DataTypes.DATE,
        allowNull: false,
        defaultValue: DataTypes.NOW,
        field: 'last_update'
      }
    }, {
      sequelize,
      modelName: 'Actor',
      tableName: 'actor',
      timestamps: false
    });
  }

  static associate(models) {
    // Many-to-many relationship with Film through film_actor
    Actor.belongsToMany(models.Film, {
      through: 'film_actor',
      foreignKey: 'actor_id',
      otherKey: 'film_id',
      as: 'films'
    });
  }
}

module.exports = Actor;
```