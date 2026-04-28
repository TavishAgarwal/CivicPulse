/**
 * CivicPulse — Firebase Cloud Functions
 *
 * 1. onCSSUpdate  — Firestore trigger: auto-dispatch when CSS >= 76
 * 2. generateBrief — HTTPS callable: server-side Gemini proxy for crisis briefs
 *
 * Google Technologies: Cloud Functions, Firestore, FCM, Gemini API
 */

const { onDocumentWritten } = require("firebase-functions/v2/firestore");
const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");
const admin = require("firebase-admin");
const { GoogleGenerativeAI } = require("@google/generative-ai");

admin.initializeApp();
const db = admin.firestore();
const messaging = admin.messaging();

// Gemini API key stored as Firebase secret
const geminiApiKey = defineSecret("GEMINI_API_KEY");

/* ── CSS Thresholds (matching src/dispatch/thresholds.py) ─── */
const CSS_HIGH_THRESHOLD = 56;
const CSS_CRITICAL_THRESHOLD = 76;

/* ── Signal insight mappings ─────────────────────────────── */
const SIGNAL_INSIGHTS = {
  pharmacy: "Pharmacy supply disruptions detected",
  school: "School attendance drops indicate family distress",
  utility: "Utility complaint spikes suggest infrastructure issues",
  social: "Social media distress signals rising",
  foodbank: "Food bank demand has increased sharply",
  health: "Health facility strain detected",
};

/**
 * 1. onCSSUpdate — Firestore Trigger
 *
 * Fires when any ward document is written under cities/{cityId}/wards/{wardId}.
 * If CSS crosses the critical threshold (76+), auto-creates a dispatch.
 * If CSS is in high range (56-75), creates a suggestion for coordinator review.
 * Full audit logging for every decision.
 */
exports.onCSSUpdate = onDocumentWritten(
  {
    document: "cities/{cityId}/wards/{wardId}",
    region: "asia-south1",
  },
  async (event) => {
    const beforeData = event.data?.before?.data();
    const afterData = event.data?.after?.data();

    if (!afterData) return; // Document deleted

    const currentCSS = afterData.currentCSS || afterData.css || 0;
    const previousCSS = beforeData?.currentCSS || beforeData?.css || 0;
    const wardId = event.params.wardId;
    const cityId = event.params.cityId;
    const wardName = afterData.name || afterData.code || wardId;

    // Only act on threshold crossings (not repeated updates at same level)
    const crossedCritical = currentCSS >= CSS_CRITICAL_THRESHOLD && previousCSS < CSS_CRITICAL_THRESHOLD;
    const crossedHigh = currentCSS >= CSS_HIGH_THRESHOLD && previousCSS < CSS_HIGH_THRESHOLD;

    if (!crossedCritical && !crossedHigh) return;

    console.log(`[CivicPulse] CSS threshold crossed: ${wardName} ${previousCSS} → ${currentCSS}`);

    // Find best available volunteer
    const volunteersSnapshot = await db
      .collection("volunteers")
      .where("isAvailable", "==", true)
      .orderBy("fatigueScore", "asc")
      .limit(5)
      .get();

    if (volunteersSnapshot.empty) {
      console.log(`[CivicPulse] No available volunteers for ${wardName}`);
      return;
    }

    const topVolunteer = volunteersSnapshot.docs[0];
    const volData = topVolunteer.data();

    // Determine action based on threshold
    const isCritical = currentCSS >= CSS_CRITICAL_THRESHOLD;

    // Build top signal description
    const signals = afterData.signalBreakdown || {};
    const topSignal = Object.entries(signals)
      .sort(([, a], [, b]) => b - a)[0];
    const signalDesc = topSignal
      ? SIGNAL_INSIGHTS[topSignal[0]] || `${topSignal[0]} signal elevated`
      : "Multiple signals elevated";

    // Create dispatch document with full audit trail
    const dispatchData = {
      wardId: wardId,
      wardName: wardName,
      cityId: cityId,
      volunteerId: topVolunteer.id,
      volunteerName: volData.displayHandle || volData.handle || topVolunteer.id,
      cssAtDispatch: currentCSS,
      previousCSS: previousCSS,
      matchScore: 1 - (volData.fatigueScore || 0), // Simple proximity for auto-dispatch
      status: isCritical ? "active" : "suggested",
      reason: isCritical
        ? `Auto-dispatched: CSS ${currentCSS} exceeded critical threshold (${CSS_CRITICAL_THRESHOLD}). ${signalDesc}.`
        : `Suggested: CSS ${currentCSS} exceeded high threshold (${CSS_HIGH_THRESHOLD}). Awaiting coordinator approval. ${signalDesc}.`,
      dispatchedAt: admin.firestore.FieldValue.serverTimestamp(),
      createdBy: isCritical ? "cloud_function:auto_dispatch" : "cloud_function:suggestion",
      auditLog: [
        {
          action: isCritical ? "auto_dispatched" : "suggested",
          timestamp: new Date().toISOString(),
          by: "cloud_function:onCSSUpdate",
          details: {
            trigger: "css_threshold_crossed",
            previousCSS: previousCSS,
            currentCSS: currentCSS,
            threshold: isCritical ? CSS_CRITICAL_THRESHOLD : CSS_HIGH_THRESHOLD,
            volunteerSelected: topVolunteer.id,
            selectionReason: "lowest_fatigue_available",
          },
        },
      ],
    };

    await db.collection("dispatches").add(dispatchData);

    // Send FCM notification for critical dispatches
    if (isCritical) {
      try {
        await messaging.send({
          topic: "dispatch_alerts",
          notification: {
            title: `🚨 CivicPulse — ${wardName} CRITICAL`,
            body: `CSS ${currentCSS}/100. ${signalDesc}. Volunteer ${volData.displayHandle || volData.handle} dispatched.`,
          },
          data: {
            wardId: wardId,
            css: String(currentCSS),
            type: "auto_dispatch",
          },
          android: {
            priority: "high",
            notification: {
              channelId: "dispatch_alerts",
              priority: "max",
            },
          },
        });
        console.log(`[CivicPulse] FCM sent for ${wardName} auto-dispatch`);
      } catch (fcmError) {
        console.error(`[CivicPulse] FCM failed for ${wardName}:`, fcmError.message);
      }

      // Update volunteer fatigue
      await db.collection("volunteers").doc(topVolunteer.id).update({
        fatigueScore: admin.firestore.FieldValue.increment(0.15),
        lastDispatched: admin.firestore.FieldValue.serverTimestamp(),
      });
    }

    console.log(
      `[CivicPulse] ${isCritical ? "Auto-dispatched" : "Suggested"}: ` +
      `${volData.displayHandle || topVolunteer.id} → ${wardName} (CSS: ${currentCSS})`
    );
  }
);

/**
 * 2. generateBrief — HTTPS Callable Function
 *
 * Server-side Gemini proxy. Receives ward data, calls Gemini 2.0 Flash,
 * returns crisis brief text. Eliminates client-side API key exposure.
 */
exports.generateBrief = onCall(
  {
    region: "asia-south1",
    secrets: [geminiApiKey],
  },
  async (request) => {
    const { wardName, currentCSS, cssStatus, signalBreakdown } = request.data;

    if (!wardName || currentCSS === undefined) {
      throw new HttpsError("invalid-argument", "wardName and currentCSS are required");
    }

    const apiKey = geminiApiKey.value();
    if (!apiKey) {
      throw new HttpsError("failed-precondition", "Gemini API key not configured");
    }

    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

    const signalText = Object.entries(signalBreakdown || {})
      .map(([type, score]) => `${type}: ${(score * 100).toFixed(0)}%`)
      .join(", ");

    const prompt = `You are an AI analyst for CivicPulse, a community distress prediction platform used by NGO coordinators in India.

Given the following ward data, generate a concise 2-3 sentence crisis brief in plain English that:
1. Identifies the primary distress signals
2. Suggests what may be happening on the ground
3. Recommends what type of volunteer intervention would help most

Ward: ${wardName}
Community Stress Score (CSS): ${currentCSS}/100 (${cssStatus})
Signal Breakdown: ${signalText}

Be specific and actionable. Use simple language an NGO field worker would understand. Do NOT use markdown formatting.`;

    try {
      const result = await model.generateContent(prompt);
      const text = result.response.text().trim();
      return { brief: text, source: "gemini" };
    } catch (error) {
      console.error("[CivicPulse] Gemini API error:", error.message);
      throw new HttpsError("internal", "Failed to generate crisis brief");
    }
  }
);
