// docs/ambiguous.md requires the primary checkout button to confirm the total
// before submitting, but does not uniquely identify submitPrimary vs
// submitSecondary (and there is no confirm-total helper to wire).
export function submitPrimary(): void {}
export function submitSecondary(): void {}
