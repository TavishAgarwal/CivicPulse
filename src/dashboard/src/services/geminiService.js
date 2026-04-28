/**
 * CivicPulse — Gemini AI Service
 *
 * Three-tier crisis brief generation:
 *   1. Cloud Function (server-side Gemini proxy — no API key exposure)
 *   2. Client-side Gemini API (fallback if Cloud Function unavailable)
 *   3. Intelligent local generation (offline-capable fallback)
 */
import { GoogleGenerativeAI } from '@google/generative-ai';
import { getFunctions, httpsCallable } from 'firebase/functions';
import app from '../firebase/config';

const GEMINI_API_KEY = import.meta.env.VITE_GEMINI_API_KEY;

let genAI = null;
let model = null;

function getModel() {
  if (!model && GEMINI_API_KEY) {
    genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
    model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });
  }
  return model;
}

/* ─── Signal intelligence mappings ─────────────────────── */
const SIGNAL_INSIGHTS = {
  pharmacy: {
    high: 'Pharmacy supply disruptions indicate potential health access crisis — communities may be stockpiling medications or facing shortages.',
    medium: 'Moderate pharmacy activity fluctuations suggest emerging health concerns in the area.',
    action: 'Deploy medical/logistics volunteers to assess supply chain bottlenecks and set up temporary distribution.',
  },
  school: {
    high: 'School attendance drops signal family-level distress — economic hardship or safety concerns may be keeping children home.',
    medium: 'Slight attendance irregularities hint at localized disruptions affecting families.',
    action: 'Send counseling and teaching volunteers for door-to-door welfare checks and community support.',
  },
  utility: {
    high: 'Utility complaint spikes point to infrastructure breakdown — water, power, or sanitation systems may be failing.',
    medium: 'Elevated utility complaints indicate infrastructure strain that could escalate.',
    action: 'Coordinate with municipal teams and deploy logistics volunteers for immediate infrastructure assessment.',
  },
  social: {
    high: 'Social media distress signals are surging — community sentiment is deteriorating rapidly, indicating a potential crisis event.',
    medium: 'Rising social media chatter suggests growing community unrest or concern.',
    action: 'Deploy counseling volunteers and community liaisons for ground-truth assessment.',
  },
  foodbank: {
    high: 'Food bank demand has spiked sharply — food insecurity is likely worsening, with families struggling to meet basic nutrition needs.',
    medium: 'Increased food bank activity suggests a growing number of families facing food access challenges.',
    action: 'Prioritize logistics and general support volunteers for emergency food distribution coordination.',
  },
  health: {
    high: 'Health facility strain detected — clinics may be overwhelmed with patient volume, indicating a public health concern.',
    medium: 'Health service utilization is above normal, suggesting emerging health issues in the community.',
    action: 'Deploy medical volunteers to support clinic overflow and conduct community health screenings.',
  },
};

/**
 * Generate a local crisis brief without API call.
 */
function generateLocalBrief(wardData) {
  const { name, currentCSS, cssStatus, signalBreakdown = {} } = wardData;

  // Find top 2 signals
  const sorted = Object.entries(signalBreakdown)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 2);

  if (sorted.length === 0) {
    return `Ward ${name} shows a CSS of ${currentCSS}/100 (${cssStatus}). Insufficient signal data for detailed analysis — recommend deploying a general assessment team for on-ground evaluation.`;
  }

  const [topSignal, topScore] = sorted[0];
  const topLevel = topScore >= 0.6 ? 'high' : 'medium';
  const topInsight = SIGNAL_INSIGHTS[topSignal]?.[topLevel] || `${topSignal} signal activity is elevated.`;
  const topAction = SIGNAL_INSIGHTS[topSignal]?.action || 'Deploy general support volunteers.';

  let brief = '';

  if (cssStatus === 'critical') {
    brief = `⚠️ CRITICAL: Ward ${name} is at CSS ${currentCSS}/100 — immediate intervention required. ${topInsight} ${topAction}`;
  } else if (cssStatus === 'high') {
    brief = `Ward ${name} is at CSS ${currentCSS}/100 (High alert). ${topInsight} ${topAction}`;
  } else if (cssStatus === 'elevated') {
    brief = `Ward ${name} is showing early stress signals at CSS ${currentCSS}/100. ${topInsight} Monitor closely and prepare volunteer teams for potential deployment.`;
  } else {
    brief = `Ward ${name} is currently stable at CSS ${currentCSS}/100. ${topInsight} No immediate intervention needed, but continue monitoring.`;
  }

  // Add secondary signal if available
  if (sorted.length > 1) {
    const [secSignal, secScore] = sorted[1];
    const secLevel = secScore >= 0.6 ? 'high' : 'medium';
    const secInsight = SIGNAL_INSIGHTS[secSignal]?.[secLevel] || '';
    if (secInsight) {
      brief += ` Additionally, ${secInsight.charAt(0).toLowerCase() + secInsight.slice(1)}`;
    }
  }

  return brief;
}

/**
 * Generate a human-readable crisis brief for a ward.
 * Three-tier fallback: Cloud Function → client-side Gemini → local analysis
 * @param {Object} wardData — { name, currentCSS, signalBreakdown, cssStatus }
 * @returns {Promise<string>} — 2-3 sentence crisis narrative
 */
export async function generateCrisisBrief(wardData) {
  // Tier 1: Try Cloud Function (server-side Gemini — no API key exposure)
  try {
    const functions = getFunctions(app, 'asia-south1');
    const generateBrief = httpsCallable(functions, 'generateBrief');
    const result = await generateBrief({
      wardName: wardData.name,
      currentCSS: wardData.currentCSS,
      cssStatus: wardData.cssStatus,
      signalBreakdown: wardData.signalBreakdown,
    });
    if (result.data?.brief) {
      console.log('[CivicPulse] Crisis brief generated via Cloud Function');
      return result.data.brief;
    }
  } catch (cfError) {
    console.warn('Cloud Function unavailable, trying client-side Gemini:', cfError.message);
  }

  // Tier 2: Try client-side Gemini API
  const gemini = getModel();
  if (gemini) {
    const signalText = Object.entries(wardData.signalBreakdown || {})
      .map(([type, score]) => `${type}: ${(score * 100).toFixed(0)}%`)
      .join(', ');

    const prompt = `You are an AI analyst for CivicPulse, a community distress prediction platform used by NGO coordinators in India.

Given the following ward data, generate a concise 2-3 sentence crisis brief in plain English that:
1. Identifies the primary distress signals
2. Suggests what may be happening on the ground
3. Recommends what type of volunteer intervention would help most

Ward: ${wardData.name}
Community Stress Score (CSS): ${wardData.currentCSS}/100 (${wardData.cssStatus})
Signal Breakdown: ${signalText}

Be specific and actionable. Use simple language an NGO field worker would understand. Do NOT use markdown formatting.`;

    try {
      const result = await gemini.generateContent(prompt);
      const response = result.response;
      console.log('[CivicPulse] Crisis brief generated via client-side Gemini');
      return response.text().trim();
    } catch (error) {
      console.warn('Gemini API unavailable, using local analysis:', error.message);
    }
  }

  // Tier 3: Fallback to local generation (always works, even offline)
  console.log('[CivicPulse] Crisis brief generated via local fallback');
  return generateLocalBrief(wardData);
}

/**
 * Generate a dispatch message for a volunteer.
 * @param {Object} params — { wardName, cssScore, skills, volunteerName }
 * @returns {Promise<string>} — Personalized dispatch notification
 */
export async function generateDispatchMessage(params) {
  const gemini = getModel();

  if (gemini) {
    const prompt = `Write a short, urgent but compassionate volunteer dispatch notification (3-4 sentences max) for:
- Volunteer: ${params.volunteerName}
- Ward: ${params.wardName}
- Stress Level: ${params.cssScore}/100
- Skills needed: ${(params.skills || []).join(', ') || 'general support'}

Start with a 🚨 emoji. Be direct and action-oriented. Include a call to respond.`;

    try {
      const result = await gemini.generateContent(prompt);
      return result.response.text().trim();
    } catch (error) {
      console.warn('Gemini dispatch message unavailable, using fallback:', error.message);
    }
  }

  // Fallback
  const severity = params.cssScore >= 76 ? 'CRITICAL' : params.cssScore >= 56 ? 'HIGH' : 'ELEVATED';
  const skillText = (params.skills || []).join(', ') || 'general support';
  return `🚨 CivicPulse Dispatch Alert — ${severity}\n\nHi ${params.volunteerName}, Ward ${params.wardName} urgently needs your help. The Community Stress Score has reached ${params.cssScore}/100. Your skills in ${skillText} are a strong match for the current situation. Please confirm your availability to deploy within the next hour.`;
}
