export const NOT_AVAILABLE = "Not available in current evidence";

/**
 * Renders a species field honestly: null/undefined/empty-array become the
 * fixed "not available" copy rather than being hidden or blanked.
 */
export function fieldValue(value) {
  if (value === null || value === undefined) return NOT_AVAILABLE;
  if (Array.isArray(value)) return value.length ? value.join(", ") : NOT_AVAILABLE;
  return value;
}
