
```javascript
const { DataTypes, Model } = require('sequelize');

class FilmActor extends Model {
  static init(sequelize) {
    return super.init({
      actorId: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        field: 'actor_id',
        allowNull: false
      },
      filmId: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        field: 'film_id',
        allowNull: false
      }
    }, {
      sequelize,
      tableName: 'film_actor',
      schema: 'sakila',
      timestamps: false
    });
  }

  static associate(models) {
    FilmActor.belongsTo(models.Actor, { foreignKey: 'actorId' });
    FilmActor.belongsTo(models.Film, { foreignKey: 'filmId' });
  }
}

module.exports = FilmActor;

const { DataTypes, Model } = require('sequelize');

class FilmCategory extends Model {
  static init(sequelize) {
    return super.init({
      filmId: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        field: 'film_id',
        allowNull: false
      },
      categoryId: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        field: 'category_id',
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
      tableName: 'film_category',
      schema: 'sakila',
      timestamps: false
    });
  }

  static associate(models) {
    FilmCategory.belongsTo(models.Film, { foreignKey: 'filmId' });
    FilmCategory.belongsTo(models.Category, { foreignKey: 'categoryId' });
  }
}

module.exports = FilmCategory;
```