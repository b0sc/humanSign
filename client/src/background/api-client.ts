/**
 * API client for communicating with HumanSign backend.
 */

import type {
    Session,
    KeystrokeBatch,
    VerificationResult,
    SessionCreateRequest,
    KeystrokeBatchResponse,
} from '../types';

const API_BASE_URL = 'http://localhost:8000/api/v1';
const TIMEOUT_MS = 10000;

/**
 * Make an API request with timeout.
 */
async function apiRequest<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return await response.json();
    } finally {
        clearTimeout(timeoutId);
    }
}

/**
 * Start a new session.
 */
export async function startSession(domain: string): Promise<Session> {
    const userId = await getUserId();

    const request: SessionCreateRequest = {
        user_external_id: userId,
        domain,
    };

    return apiRequest<Session>('/sessions/start', {
        method: 'POST',
        body: JSON.stringify(request),
    });
}

/**
 * End a session.
 */
export async function endSession(sessionId: string): Promise<Session> {
    return apiRequest<Session>(`/sessions/${sessionId}/end`, {
        method: 'POST',
        body: JSON.stringify({}),
    });
}

/**
 * Send keystroke batch.
 */
export async function sendKeystrokeBatch(
    batch: KeystrokeBatch
): Promise<KeystrokeBatchResponse> {
    return apiRequest<KeystrokeBatchResponse>('/keystrokes/batch', {
        method: 'POST',
        body: JSON.stringify(batch),
    });
}

/**
 * Verify a session.
 */
export async function verifySession(
    sessionId: string
): Promise<VerificationResult> {
    return apiRequest<VerificationResult>('/verify', {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId }),
    });
}

/**
 * Get or create persistent user ID.
 */
async function getUserId(): Promise<string> {
    const result = await chrome.storage.local.get('userId');

    if (result.userId) {
        return result.userId;
    }

    // Generate new user ID
    const userId = crypto.randomUUID();
    await chrome.storage.local.set({ userId });
    return userId;
}
