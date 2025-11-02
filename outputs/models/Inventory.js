
```javascript
const { DataTypes, Model } = require('sequelize');

// FilmCategory Model
class FilmCategory extends Model {
  static init(sequelize) {
    return super.init({
      filmId: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        field: 'film_id'
      },
      categoryId: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        field: 'category_id'
      },
      lastUpdate: {
        type: DataTypes.DATE,
        field: 'last_update',
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
    // Define associations here if needed
    // Example: belongs to Film and Category models
    FilmCategory.belongsTo(models.Film, { foreignKey: 'filmId' });
    FilmCategory.belongsTo(models.Category, { foreignKey: 'categoryId' });
  }
}

// FilmText Model
class FilmText extends Model {
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
        field: 'description',
        allowNull: true
      }
    }, {
      sequelize,
      tableName: 'film_text',
      schema: 'sakila',
      timestamps: false
    });
  }

  static associate(models) {
    // Define associations here if needed
    // Example: belongs to Film model
    FilmText.belongsTo(models.Film, { foreignKey: 'filmId' });
  }
}

module.exports = {
  FilmCategory,
  FilmText
};
```