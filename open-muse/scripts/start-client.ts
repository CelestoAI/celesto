import { pathToFileURL } from "node:url";
import { createServer } from "vite";

type FetchApi = (input: string) => Promise<Response>;
type Wait = (milliseconds: number) => Promise<void>;

export async function waitForOpenMuseApi(
  fetchApi: FetchApi = (input) => fetch(input),
  wait: Wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds)),
  timeoutMs = 30_000,
  now: () => number = Date.now,
): Promise<void> {
  const port = process.env.OPEN_MUSE_PORT ?? "4318";
  const healthUrl = `http://127.0.0.1:${port}/api/health`;
  const deadline = now() + timeoutMs;
  while (true) {
    try {
      const response = await fetchApi(healthUrl);
      if (response.ok) return;
    }
    catch { /* The API process is still starting. */ }
    if (now() >= deadline) throw new Error(`The OpenMuse API did not become ready within ${Math.ceil(timeoutMs / 1_000)} seconds; check the server log for the startup error.`);
    await wait(50);
  }
}

async function main(): Promise<void> {
  await waitForOpenMuseApi();
  const server = await createServer();
  await server.listen();
  server.printUrls();
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  void main().catch((error: unknown) => {
    const detail = error instanceof Error ? error.message : String(error);
    console.error(`OpenMuse client could not start: ${detail}`);
    process.exitCode = 1;
  });
}
