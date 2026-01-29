/**
 * Timing utilities using high-precision performance.now()
 */

/**
 * Get current timestamp using performance.now() for sub-millisecond precision.
 * This is more accurate than Date.now() for measuring intervals.
 */
export function now(): number {
    return performance.now();
}

/**
 * Calculate elapsed time since a given timestamp.
 */
export function elapsed(since: number): number {
    return performance.now() - since;
}

/**
 * Check if a duration has passed since a given timestamp.
 */
export function hasPassed(since: number, duration: number): boolean {
    return elapsed(since) >= duration;
}

/**
 * Debounce a function call.
 */
export function debounce<T extends (...args: unknown[]) => void>(
    fn: T,
    delay: number
): (...args: Parameters<T>) => void {
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    return (...args: Parameters<T>) => {
        if (timeoutId) {
            clearTimeout(timeoutId);
        }
        timeoutId = setTimeout(() => {
            fn(...args);
            timeoutId = null;
        }, delay);
    };
}

/**
 * Throttle a function call.
 */
export function throttle<T extends (...args: unknown[]) => void>(
    fn: T,
    limit: number
): (...args: Parameters<T>) => void {
    let lastRun = 0;

    return (...args: Parameters<T>) => {
        const currentTime = now();
        if (currentTime - lastRun >= limit) {
            fn(...args);
            lastRun = currentTime;
        }
    };
}
