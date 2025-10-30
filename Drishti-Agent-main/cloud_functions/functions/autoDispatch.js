// cloud_functions/functions/autoDispatch.js

const functions = require('firebase-functions');
const admin = require('firebase-admin');
// const { Client } = require('@googlemaps/google-maps-services-js'); // For Google Maps Directions API
// const mapsClient = new Client({}); // Initialize Google Maps Client

// Initialize Firebase Admin SDK (will be initialized by index.js if exported)
// If running standalone for testing, uncomment: admin.initializeApp();

const db = admin.firestore();

/**
 * Cloud Function to automatically dispatch units if an incident is not
 * acknowledged or resolved within a certain timeframe, or based on severity.
 *
 * This function could be triggered by:
 * 1. A Pub/Sub message from a Cloud Scheduler job (e.g., every 5 minutes).
 * 2. A Firestore document update (e.g., if incident status changes to 'unacknowledged').
 *
 * For this hackathon demo, let's assume it's triggered by a Pub/Sub message
 * that contains an incidentId to check.
 *
 * @param {object} message The Pub/Sub message.
 * @param {object} context The context of the event.
 */
exports.autoDispatch = functions.pubsub.topic('dispatch-triggers').onPublish(async (message, context) => {
    const payload = message.json;
    const incidentId = payload.incidentId;

    if (!incidentId) {
        console.log("No incidentId provided in dispatch trigger. Skipping.");
        return null;
    }

    console.log(`Attempting auto-dispatch for incident: ${incidentId}`);

    try {
        const incidentRef = db.collection('incidents').doc(incidentId);
        const incidentDoc = await incidentRef.get();

        if (!incidentDoc.exists) {
            console.log(`Incident ${incidentId} not found.`);
            return null;
        }

        const incidentData = incidentDoc.data();

        // Check if incident already dispatched or resolved
        if (incidentData.status === 'dispatched' || incidentData.status === 'resolved') {
            console.log(`Incident ${incidentId} already ${incidentData.status}. No auto-dispatch needed.`);
            return null;
        }

        // --- Logic to find nearest available unit ---
        const respondersSnapshot = await db.collection('responders').where('status', '==', 'available').limit(1).get();
        if (respondersSnapshot.empty) {
            console.log("No available responders found for dispatch.");
            await incidentRef.update({
                status: 'pending_dispatch',
                dispatchAttemptedAt: admin.firestore.FieldValue.serverTimestamp(),
                dispatchMessage: 'No available responders.'
            });
            return null;
        }

        const responderDoc = respondersSnapshot.docs[0];
        const responderData = responderDoc.data();
        const responderId = responderDoc.id;

        console.log(`Found available responder: ${responderId}`);

        // --- Simulate Google Maps API for Routing ---
        // In a real scenario, you'd use Google Maps Directions API here:
        // const origin = `${responderData.location.latitude},${responderData.location.longitude}`;
        // const destination = `${incidentData.location.latitude},${incidentData.location.longitude}`;
        // const directionsResponse = await mapsClient.directions({
        //     params: {
        //         origin: origin,
        //         destination: destination,
        //         key: functions.config().googlemaps.api_key, // Get API key from Firebase config
        //     },
        //     timeout: 1000, // milliseconds
        // });
        // const route = directionsResponse.data.routes[0];
        // const duration = route.legs[0].duration.text; // e.g., "5 minutes"

        const simulatedRouteDuration = "5 minutes (simulated)";
        const simulatedRouteDetails = "Simulated fastest route via Main Street.";

        // --- Dispatch Notification (Firebase Cloud Messaging - FCM) ---
        // Send a push notification to the responder's device
        if (responderData.fcmToken) {
            const message = {
                notification: {
                    title: `New Incident: ${incidentData.anomalyType}`,
                    body: `Proceed to location: ${incidentData.location.latitude}, ${incidentData.location.longitude}. Estimated travel: ${simulatedRouteDuration}.`
                },
                data: {
                    incidentId: incidentId,
                    anomalyType: incidentData.anomalyType,
                    videoUrl: incidentData.videoUrl,
                    routeDetails: simulatedRouteDetails,
                    responderId: responderId
                },
                token: responderData.fcmToken
            };

            await admin.messaging().send(message);
            console.log(`FCM notification sent to responder ${responderId}`);
        } else {
            console.warn(`Responder ${responderId} does not have an FCM token.`);
        }

        // --- Update Firestore Status ---
        await incidentRef.update({
            status: 'dispatched',
            dispatchedTo: responderId,
            routeDuration: simulatedRouteDuration,
            dispatchedAt: admin.firestore.FieldValue.serverTimestamp()
        });
        await db.collection('responders').doc(responderId).update({
            status: 'en_route',
            currentIncidentId: incidentId
        });

        console.log(`Incident ${incidentId} auto-dispatched to responder ${responderId}.`);
        return null;

    } catch (error) {
        console.error(`Error during auto-dispatch for incident ${incidentId}:`, error);
        // Optionally update incident status to indicate dispatch failure
        await db.collection('incidents').doc(incidentId).update({
            status: 'dispatch_failed',
            dispatchErrorMessage: error.message,
            dispatchAttemptedAt: admin.firestore.FieldValue.serverTimestamp()
        });
        return null;
    }
});