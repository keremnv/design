import { cancelSubscription } from "./retention";

export function FinalCancellation(): void {
  // docs/subscriptions.md: cancellation only after confirmation on the final screen.
  cancelSubscription();
}
