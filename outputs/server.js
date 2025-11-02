const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
require('dotenv').config();

const app = express();

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
const mainRouter = require('./routes/maincontroller');
app.use('/api/main', mainRouter);
const categoryRouter = require('./routes/categorycontroller');
app.use('/api/category', categoryRouter);
const filmRouter = require('./routes/filmcontroller');
app.use('/api/film', filmRouter);
const customerRouter = require('./routes/customercontroller');
app.use('/api/customer', customerRouter);
const actorRouter = require('./routes/actorcontroller');
app.use('/api/actor', actorRouter);
const staffRouter = require('./routes/staffcontroller');
app.use('/api/staff', staffRouter);

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({
        success: false,
        error: err.message
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        success: false,
        error: 'Route not found'
    });
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
    console.log(`Server running on port ${{PORT}}`);
});

module.exports = app;