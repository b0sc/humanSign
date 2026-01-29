/**
 * Content script entry point.
 *
 * Initializes keystroke tracking on page load.
 */

import { keystrokeTracker } from './keystroke-tracker';

// Auto-start tracking when focusing on text inputs
function initializeTracking(): void {
    // Track focus on text inputs
    document.addEventListener('focusin', (event) => {
        const target = event.target as HTMLElement;

        if (isTextInput(target)) {
            void keystrokeTracker.start();
        }
    });

    // Stop tracking when leaving text inputs
    document.addEventListener('focusout', (event) => {
        const target = event.target as HTMLElement;
        const relatedTarget = event.relatedTarget as HTMLElement | null;

        if (isTextInput(target) && !isTextInput(relatedTarget)) {
            // Delay stop to allow form submission verification
            setTimeout(() => {
                void keystrokeTracker.stop();
            }, 1000);
        }
    });

    // Verify on form submission
    document.addEventListener('submit', () => {
        void keystrokeTracker.verify();
    });

    console.log('[HumanSign] Content script initialized');
}

/**
 * Check if an element is a text input.
 */
function isTextInput(element: HTMLElement | null): boolean {
    if (!element) return false;

    const tagName = element.tagName.toLowerCase();

    if (tagName === 'textarea') return true;

    if (tagName === 'input') {
        const type = (element as HTMLInputElement).type.toLowerCase();
        return ['text', 'email', 'password', 'search', 'url', 'tel'].includes(type);
    }

    // Contenteditable elements
    if (element.isContentEditable) return true;

    return false;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTracking);
} else {
    initializeTracking();
}
