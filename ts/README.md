# @celestoai/celesto

Run TypeScript agent code in a disposable computer on your own machine. No cloud account or API key is required.

This package is an alpha for Node.js 20.4 or newer on Linux x64 and Apple Silicon macOS. Install the Celesto runtime first; the SDK starts its private local bridge automatically.

```bash
pip install 'celesto[server]==0.1.3'
celesto setup
npm install https://github.com/CelestoAI/Celesto/releases/download/typescript-v0.1.0-preview.1/celestoai-celesto-0.1.0-preview.1.tgz
npm install --save-dev tsx
```

```ts
import { Celesto } from "@celestoai/celesto";

async function main() {
  const celesto = new Celesto({ runtimePath: "celesto" });
  const sandbox = await celesto.sandboxes.create({ network: { mode: "off" } });

  try {
    await sandbox.files.write("/workspace/input.txt", "hello");
    const result = await sandbox.exec(["cat", "/workspace/input.txt"]);
    console.log(result.stdout);
  } finally {
    await celesto.close();
  }
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
```

`celesto.sandboxes.create()` starts a minimal computer. The `sandboxes` name predates Celesto's current terminology.

The source checkout also includes `celesto.browsers.create(...)`, which starts a browser session: Chromium in its own computer, with commands, files, private Chromium automation, and an optional live view. A live session returns private `cdpUrl` and `viewerUrl` connections for Playwright and a web browser. Raw VNC `displayUrl` connections are unavailable. That API is planned for the next preview and is not included in `0.1.0-preview.1`; see the source repository's TypeScript guide and `examples/browser-computer.ts` for working examples.

See the TypeScript guide in the source repository for lifecycle, files, network policy, cancellation, diagnostics, and CI examples.
