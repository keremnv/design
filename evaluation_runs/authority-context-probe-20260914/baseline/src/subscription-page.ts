import { openRetentionFlow } from "./retention";

export function SubscriptionPage(): void {
  // docs/subscriptions.md: initial "Cancel subscription" action enters the retention flow.
  openRetentionFlow();
}
