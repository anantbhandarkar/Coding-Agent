
```javascript
const { DataTypes, Model } = require('sequelize');

class FilmActor extends Model {
  static init(sequelize) {
    return super.init({
      actorId: {
        type: DataTypes.INTEGER,
        field: 'actor_id',
        primaryKey: true,
        allowNull: false
      },
      filmId: {
        type: DataTypes.INTEGER,
        field: 'film_id',
        primaryKey: true,
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
      modelName: 'FilmActor',
      tableName: 'film_actor',
      schema: 'sakila',
      timestamps: false
    });
  }

  static associate(models) {
    // Define associations here if needed
    // Example:
    // FilmActor.belongsTo(models.Actor, { foreignKey: 'actorId' });
    // FilmActor.belongsTo(models.Film, { foreignKey: 'filmId' });
  }
}

class FilmCategory extends Model {
  static init(sequelize) {
    return super.init({
      filmId: {
        type: DataTypes.INTEGER,
        field: 'film_id',
        primaryKey: true,
        allowNull: false
      },
      categoryId: {
        type: DataTypes.INTEGER,
        field: 'category_id',
        primaryKey: true,
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
      modelName: 'FilmCategory',
      tableName: 'film_category',
      schema: 'sakila',
      timestamps: false
    });
  }

  static associate(models) {
    // Define associations here if needed
    // Example:
    // FilmCategory.belongsTo(models.Film, { foreignKey: 'filmId' });
    // FilmCategory.belongsTo(models.Category, { foreignKey: 'categoryId' });
  }
}

module.exports = {
  FilmActor,
  FilmCategory
};
```