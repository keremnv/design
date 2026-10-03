export class NotificationGateway {
  send(body: string): string { return body; }
}
export class SMTPClient {
  send(body: string): string { return body; }
}
export function notificationGatewaySend(body: string): string { return body; }
export function smtpClientSend(body: string): string { return body; }
export function sendReceipt(body: string): string {
  const marked = body;
  notificationGatewaySend(body);
  return notificationGatewaySend(marked);
}
export function sendInvoice(body: string): string {
  return notificationGatewaySend(body);
}
export function sendAmbiguous(body: string, channel: NotificationGateway | SMTPClient): string {
  return channel.send(body);
}
