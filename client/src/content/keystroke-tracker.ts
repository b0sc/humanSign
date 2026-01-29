/**
 * KeystrokeTracker - Captures keystroke events with high-precision timing.
 *
 * Uses performance.now() for sub-millisecond accuracy.
 * Buffers events and sends them to background worker in batches.
 */

import type { KeystrokeEvent, ExtensionMessage, ExtensionResponse, Session } from '../types';
import { now, throttle } from '../utils/timing';

// Configuration
const BATCH_SIZE = 100;
const FLUSH_INTERVAL_MS = 500;
const MIN_FLUSH_SIZE = 10;

class KeystrokeTracker {
    private events: KeystrokeEvent[] = [];
    private sessionId: string | null = null;
    private batchSequence = 0;
    private isTracking = false;
    private flushTimeoutId: ReturnType<typeof setTimeout> | null = null;
    private lastFlushTime = 0;

    /**
     * Start tracking keystrokes.
     */
    async start(): Promise<void> {
        if (this.isTracking) {
            return;
        }

        try {
            // Request session from background worker
            const response = await this.sendMessage<Session>({
                type: 'START_SESSION',
                payload: { domain: window.location.hostname },
            });

            if (response.success) {
                this.sessionId = response.data.id;
                this.isTracking = true;
                this.attachListeners();
                console.log('[HumanSign] Tracking started for session:', this.sessionId);
            } else {
                console.error('[HumanSign] Failed to start session:', response.error);
            }
        } catch (error) {
            console.error('[HumanSign] Error starting tracking:', error);
        }
    }

    /**
     * Stop tracking keystrokes.
     */
    async stop(): Promise<void> {
        if (!this.isTracking || !this.sessionId) {
            return;
        }

        this.detachListeners();
        await this.flush();

        try {
            await this.sendMessage({
                type: 'END_SESSION',
                payload: { session_id: this.sessionId },
            });
            console.log('[HumanSign] Session ended:', this.sessionId);
        } catch (error) {
            console.error('[HumanSign] Error ending session:', error);
        }

        this.reset();
    }

    /**
     * Request verification for current session.
     */
    async verify(): Promise<void> {
        if (!this.sessionId) {
            console.error('[HumanSign] No active session to verify');
            return;
        }

        try {
            const response = await this.sendMessage({
                type: 'VERIFY_SESSION',
                payload: { session_id: this.sessionId },
            });

            if (response.success) {
                console.log('[HumanSign] Verification result:', response.data);
            } else {
                console.error('[HumanSign] Verification failed:', response.error);
            }
        } catch (error) {
            console.error('[HumanSign] Error verifying session:', error);
        }
    }

    /**
     * Handle keydown event.
     */
    private handleKeyDown = (event: KeyboardEvent): void => {
        if (!this.isTracking) return;

        const keystrokeEvent: KeystrokeEvent = {
            event_type: 'keydown',
            key_code: event.keyCode,
            key_char: event.key.length === 1 ? event.key : null,
            client_timestamp: now(),
        };

        this.events.push(keystrokeEvent);
        this.scheduleFlush();
    };

    /**
     * Handle keyup event.
     */
    private handleKeyUp = (event: KeyboardEvent): void => {
        if (!this.isTracking) return;

        const keystrokeEvent: KeystrokeEvent = {
            event_type: 'keyup',
            key_code: event.keyCode,
            key_char: event.key.length === 1 ? event.key : null,
            client_timestamp: now(),
        };

        this.events.push(keystrokeEvent);
        this.scheduleFlush();
    };

    /**
     * Attach keyboard event listeners.
     */
    private attachListeners(): void {
        document.addEventListener('keydown', this.handleKeyDown, { capture: true });
        document.addEventListener('keyup', this.handleKeyUp, { capture: true });
    }

    /**
     * Detach keyboard event listeners.
     */
    private detachListeners(): void {
        document.removeEventListener('keydown', this.handleKeyDown, { capture: true });
        document.removeEventListener('keyup', this.handleKeyUp, { capture: true });
    }

    /**
     * Schedule a flush of buffered events.
     */
    private scheduleFlush(): void {
        // Immediate flush if buffer is full
        if (this.events.length >= BATCH_SIZE) {
            void this.flush();
            return;
        }

        // Throttled flush for smaller batches
        if (this.flushTimeoutId === null) {
            this.flushTimeoutId = setTimeout(() => {
                void this.flush();
                this.flushTimeoutId = null;
            }, FLUSH_INTERVAL_MS);
        }
    }

    /**
     * Flush buffered events to background worker.
     */
    private async flush(): Promise<void> {
        if (this.events.length < MIN_FLUSH_SIZE || !this.sessionId) {
            return;
        }

        const eventsToSend = this.events.slice(0, BATCH_SIZE);
        this.events = this.events.slice(BATCH_SIZE);

        try {
            await this.sendMessage({
                type: 'KEYSTROKE_BATCH',
                payload: {
                    session_id: this.sessionId,
                    events: eventsToSend,
                    batch_sequence: this.batchSequence++,
                },
            });
            this.lastFlushTime = now();
        } catch (error) {
            // Re-add events to buffer on failure
            this.events = [...eventsToSend, ...this.events];
            console.error('[HumanSign] Failed to flush events:', error);
        }
    }

    /**
     * Send message to background worker.
     */
    private sendMessage<T>(message: ExtensionMessage): Promise<ExtensionResponse<T>> {
        return new Promise((resolve) => {
            chrome.runtime.sendMessage(message, (response: ExtensionResponse<T>) => {
                resolve(response ?? { success: false, error: 'No response from background' });
            });
        });
    }

    /**
     * Reset tracker state.
     */
    private reset(): void {
        this.events = [];
        this.sessionId = null;
        this.batchSequence = 0;
        this.isTracking = false;
        if (this.flushTimeoutId) {
            clearTimeout(this.flushTimeoutId);
            this.flushTimeoutId = null;
        }
    }

    /**
     * Get current tracking status.
     */
    get status(): { isTracking: boolean; sessionId: string | null; bufferedEvents: number } {
        return {
            isTracking: this.isTracking,
            sessionId: this.sessionId,
            bufferedEvents: this.events.length,
        };
    }
}

// Export singleton instance
export const keystrokeTracker = new KeystrokeTracker();
