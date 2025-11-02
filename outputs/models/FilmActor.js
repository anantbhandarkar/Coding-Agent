
```javascript
const { DataTypes, Model } = require('sequelize');

class Film extends Model {
  static init(sequelize) {
    return super.init({
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
        type: DataTypes.STRING,
        field: 'description'
      },
      releaseYear: {
        type: DataTypes.INTEGER,
        field: 'release_year'
      },
      rentalDuration: {
        type: DataTypes.INTEGER,
        field: 'rental_duration'
      },
      rentalRate: {
        type: DataTypes.DECIMAL(4, 2),
        field: 'rental_rate'
      },
      length: {
        type: DataTypes.INTEGER,
        field: 'length'
      },
      replacementCost: {
        type: DataTypes.DECIMAL(5, 2),
        field: 'replacement_cost'
      },
      rating: {
        type: DataTypes.STRING,
        field: 'rating'
      },
      specialFeatures: {
        type: DataTypes.STRING,
        field: 'special_features'
      },
      lastUpdate: {
        type: DataTypes.DATE,
        field: 'last_update'
      }
    }, {
      sequelize,
      modelName: 'Film',
      tableName: 'film',
      timestamps: false
    });
  }

  static associate(models) {
    // Define associations here if needed
    // Example:
    // Film.belongsToMany(models.Actor, { through: models.FilmActor, foreignKey: 'filmId' });
  }
}

module.exports = Film;
```