import { Celesto } from "@celestoai/celesto";

async function main() {
  const celesto = new Celesto();

  try {
    const computer = await celesto.browsers.create({ mode: "live" });
    await computer.files.write("/workspace/task.txt", "visit example.com");
    console.log({
      sandboxId: computer.sandboxId,
      cdpUrl: computer.cdpUrl,
      viewerUrl: computer.viewerUrl,
      displayUrl: computer.displayUrl,
    });
  } finally {
    await celesto.close();
  }
}

main().catch((error) => {
  const detail = error instanceof Error ? error.message : "Browser computer failed.";
  console.error(`${detail} Run 'npx tsx examples/browser-computer.ts' to retry.`);
  process.exitCode = 1;
});
