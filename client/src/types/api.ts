/**
 * API client types.
 */

export interface ApiConfig {
    baseUrl: string;
    timeout: number;
}

export interface ApiError {
    status: number;
    message: string;
    detail?: string;
}

export interface HealthResponse {
    status: string;
    service: string;
}

export interface SessionCreateRequest {
    user_external_id: string;
    domain: string | null;
    metadata?: Record<string, unknown>;
}

export interface KeystrokeBatchResponse {
    session_id: string;
    events_processed: number;
    batch_sequence: number;
}
