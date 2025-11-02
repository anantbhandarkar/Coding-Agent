
```javascript
const { DataTypes, Model } = require('sequelize');

class Actor extends Model {
  static init(sequelize) {
    return super.init({
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
      sequelize,
      modelName: 'Actor',
      tableName: 'actor',
      timestamps: false
    });
  }

  static associate(models) {
    // Define associations here if needed
    // Example:
    // Actor.hasMany(models.FilmActor, { foreignKey: 'actorId' });
  }
}

module.exports = Actor;
```