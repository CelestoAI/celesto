const VIEWER_RECONNECT_DELAYS_MS = [250, 1_000, 3_000] as const;

export function viewerReconnectDelay(attempt: number): number | undefined {
  return attempt > 0 ? VIEWER_RECONNECT_DELAYS_MS[attempt - 1] : 0;
}
