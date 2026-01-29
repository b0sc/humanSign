/**
 * Background service worker.
 *
 * Handles messages from content scripts and communicates with the API.
 */

import type { ExtensionMessage, ExtensionResponse } from '../types';
import {
    startSession,
    endSession,
    sendKeystrokeBatch,
    verifySession,
} from './api-client';

/**
 * Handle messages from content scripts.
 */
chrome.runtime.onMessage.addListener(
    (
        message: ExtensionMessage,
        _sender: chrome.runtime.MessageSender,
        sendResponse: (response: ExtensionResponse) => void
    ): boolean => {
        handleMessage(message)
            .then(sendResponse)
            .catch((error) => {
                console.error('[HumanSign Background] Error:', error);
                sendResponse({
                    success: false,
                    error: error instanceof Error ? error.message : 'Unknown error',
                });
            });

        // Return true to indicate async response
        return true;
    }
);

/**
 * Process incoming message.
 */
async function handleMessage(
    message: ExtensionMessage
): Promise<ExtensionResponse> {
    switch (message.type) {
        case 'START_SESSION': {
            const session = await startSession(message.payload.domain);
            return { success: true, data: session };
        }

        case 'END_SESSION': {
            const session = await endSession(message.payload.session_id);
            return { success: true, data: session };
        }

        case 'KEYSTROKE_BATCH': {
            const result = await sendKeystrokeBatch(message.payload);
            return { success: true, data: result };
        }

        case 'VERIFY_SESSION': {
            const result = await verifySession(message.payload.session_id);

            // Show badge based on result
            if (result.is_human) {
                await chrome.action.setBadgeText({ text: '✓' });
                await chrome.action.setBadgeBackgroundColor({ color: '#22c55e' });
            } else {
                await chrome.action.setBadgeText({ text: '?' });
                await chrome.action.setBadgeBackgroundColor({ color: '#f59e0b' });
            }

            return { success: true, data: result };
        }

        default:
            return { success: false, error: 'Unknown message type' };
    }
}

// Log when service worker starts
console.log('[HumanSign Background] Service worker started');
