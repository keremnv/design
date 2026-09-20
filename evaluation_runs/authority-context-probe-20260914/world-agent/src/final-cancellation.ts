import { cancelSubscription } from "./retention";

export function FinalCancellation(): void {
  // cancellation_requires_prior → this function's call site,
  // which program_invokes cancelSubscription.
  cancelSubscription();
}
