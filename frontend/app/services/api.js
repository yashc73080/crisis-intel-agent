/**
 * CrisisNet API Service Layer
 * Communicates with the FastAPI backend at localhost:8000
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    };

    try {
        const response = await fetch(url, config);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `API error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

/**
 * Query assessed events from the backend
 * POST /api/events/query
 * 
 * @param {string} statusFilter - Filter events by status (default: "ASSESSED")
 * @param {number} limit - Maximum number of events to return (default: 50)
 * @returns {Promise<Array>} Array of event objects
 */
export async function queryEvents(statusFilter = 'ASSESSED', limit = 50) {
    return apiRequest('/api/events/query', {
        method: 'POST',
        body: JSON.stringify({
            status_filter: statusFilter,
            limit: limit,
        }),
    });
}

/**
 * Get high-risk events
 * GET /api/events/high_risk
 * 
 * @param {number} minRiskScore - Minimum risk score threshold (default: 70)
 * @param {number} limit - Maximum number of events (default: 50)
 * @returns {Promise<Array>} Array of high-risk event objects
 */
export async function getHighRiskEvents(minRiskScore = 70, limit = 50) {
    const params = new URLSearchParams({
        min_risk_score: minRiskScore.toString(),
        limit: limit.toString(),
    });

    return apiRequest(`/api/events/high_risk?${params}`, {
        method: 'GET',
    });
}

/**
 * Check location safety - comprehensive analysis
 * POST /api/safety/check
 * 
 * @param {number} latitude - User's latitude
 * @param {number} longitude - User's longitude
 * @param {number} radiusKm - Check radius in kilometers (default: 25)
 * @returns {Promise<Object>} Safety analysis with overall_status, recommendation, threats, hospitals
 */
export async function checkLocationSafety(latitude, longitude, radiusKm = 25) {
    return apiRequest('/api/safety/check', {
        method: 'POST',
        body: JSON.stringify({
            user_location: [latitude, longitude],
            check_radius_km: radiusKm,
        }),
    });
}

/**
 * Compute evacuation routes
 * POST /api/routes/compute
 * 
 * @param {Array<number>} origin - [latitude, longitude] origin point
 * @param {Array<number>} destination - [latitude, longitude] destination point
 * @param {boolean} avoidThreats - Whether to avoid threats in routing (default: true)
 * @param {string} travelMode - Travel mode: "DRIVE", "WALK", etc. (default: "DRIVE")
 * @returns {Promise<Object>} Route options with recommended_route_index
 */
export async function computeRoutes(origin, destination, avoidThreats = true, travelMode = 'DRIVE') {
    return apiRequest('/api/routes/compute', {
        method: 'POST',
        body: JSON.stringify({
            origin: origin,
            destination: destination,
            travel_mode: travelMode,
            avoid_threats: avoidThreats,
            alternatives: true,
        }),
    });
}

/**
 * Health check endpoint
 * GET /health
 * 
 * @returns {Promise<Object>} Health status
 */
export async function healthCheck() {
    return apiRequest('/health', {
        method: 'GET',
    });
}

// Named exports are preferred - use individual imports like:
// import { checkLocationSafety, queryEvents } from './services/api';
