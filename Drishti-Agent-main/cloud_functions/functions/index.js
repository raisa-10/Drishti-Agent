// cloud_functions/functions/index.js

const admin = require('firebase-admin');

// Initialize Firebase Admin SDK
admin.initializeApp();

// Export individual functions
exports.onAnomalyTrigger = require('./onAnomalyTrigger').onAnomalyTrigger;
exports.onNewIncident = require('./onNewIncident').onNewIncident;
exports.autoDispatch = require('./autoDispatch').autoDispatch;

// You can also add other shared constants or helper functions here if needed.