// cloud_functions/functions/onNewIncident.js

const functions = require('firebase-functions');
const admin = require('firebase-admin');
// const { GoogleAuth } = require('google-auth-library'); // For calling Vertex AI APIs
// const { TextServiceClient } = require('@google-cloud/language').v1; // Example for NLP
// const { ImageAnnotatorClient } = require('@google-cloud/vision'); // Example for Vision API

// Initialize Firebase Admin SDK (will be initialized by index.js if exported)
// If running standalone for testing, uncomment: admin.initializeApp();

const db = admin.firestore();

/**
 * Pub/Sub Cloud Function triggered when a new anomaly incident is reported.
 * This function will orchestrate deeper analysis using Vertex AI Vision and Gemini.
 *
 * @param {object} message The Pub/Sub message.
 * @param {object} context The context of the event.
 */
exports.onNewIncident = functions
    .runWith({
        timeoutSeconds: 300,
        memory: '512MB'
    })
    .pubsub.topic('anomaly-triggers').onPublish(async (message, context) => {
    const startTime = Date.now();
    const incidentData = message.json;
    const incidentId = incidentData.incidentId;
    const videoUrl = incidentData.videoUrl;
    const anomalyType = incidentData.anomalyType;
    const deviceId = incidentData.deviceId;
    const location = incidentData.location;

    console.log(`Received new incident ${incidentId} for deeper analysis. Type: ${anomalyType}, Video: ${videoUrl}`);

    try {
        // --- Step 1: Perform Deeper Video Analysis (Vertex AI Vision) ---
        // In a real scenario, you would call Vertex AI Vision here.
        // For hackathon, we'll simulate this or use a simple placeholder.
        console.log(`[Deeper Analysis] Simulating Vertex AI Vision analysis for video: ${videoUrl}`);
        // Example: If you were to call Vertex AI Vision:
        // const visionClient = new ImageAnnotatorClient();
        // const [result] = await visionClient.annotateImage({
        //     image: { source: { imageUri: videoUrl } },
        //     features: [{ type: 'LABEL_DETECTION' }, { type: 'SAFE_SEARCH_DETECTION' }],
        // });
        // const visionInsights = result.labelAnnotations.map(label => label.description);

        const visionInsights = [`Detailed analysis of ${anomalyType} confirmed.`, 'Crowd movement patterns analyzed.'];
        await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate delay

        // --- Step 2: Generate Situational Summary / Plan (Gemini) ---
        // This would involve calling your Python backend service (gemini_agent.py)
        // or directly calling the Gemini API from here.
        console.log(`[Gemini Agent] Requesting situational summary for incident ${incidentId}...`);
        
        // For hackathon, directly call Gemini API (requires API key or proper auth)
        // Or, better for hackathon, you could have your Python backend expose an HTTP endpoint
        // that this Cloud Function calls to delegate to Gemini.
        const prompt = `An incident of type "${anomalyType}" was detected by device ${deviceId} at location ${JSON.stringify(location)}.
        Video analysis insights: ${visionInsights.join(', ')}.
        Please provide a concise situational summary and recommend immediate actions.`;

        let chatHistory = [];
        chatHistory.push({ role: "user", parts: [{ text: prompt }] });
        const payload = { contents: chatHistory };
        const apiKey = ""; // Canvas will provide this at runtime. DO NOT HARDCODE.
        const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`;

        // Make the API call to Gemini
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        
        let geminiSummary = "AI agent is analyzing...";
        if (result.candidates && result.candidates.length > 0 &&
            result.candidates[0].content && result.candidates[0].content.parts &&
            result.candidates[0].content.parts.length > 0) {
            geminiSummary = result.candidates[0].content.parts[0].text;
        } else {
            console.warn('Gemini response structure unexpected or empty:', result);
            geminiSummary = "AI analysis inconclusive or response format error.";
        }
        
        console.log(`[Gemini Agent] Summary: ${geminiSummary.substring(0, 100)}...`);


        // --- Step 3: Update Firestore with Analysis Results ---
        const processingTime = Date.now() - startTime;
        await db.collection('incidents').doc(incidentId).update({
            status: 'analyzed',
            visionInsights: visionInsights,
            geminiSummary: geminiSummary,
            processingTimeMs: processingTime,
            analyzedAt: admin.firestore.FieldValue.serverTimestamp()
        });
        console.log(`Incident ${incidentId} updated with analysis results. Processing time: ${processingTime}ms`);

    } catch (error) {
        console.error(`Error processing incident ${incidentId} for deeper analysis:`, error);
        // Update incident status to 'failed_analysis' or similar
        await db.collection('incidents').doc(incidentId).update({
            status: 'analysis_failed',
            errorMessage: error.message,
            analyzedAt: admin.firestore.FieldValue.serverTimestamp()
        });
    }
});