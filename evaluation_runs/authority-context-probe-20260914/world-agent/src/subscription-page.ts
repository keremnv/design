import { openRetentionFlow } from "./retention";

export function SubscriptionPage(): void {
  // enters_flow(CancellationEntryAction, RetentionFlow);
  // realized_by → this function's call site, which program_invokes openRetentionFlow.
  openRetentionFlow();
}
