import { Celesto } from "@celestoai/celesto";

async function main() {
  const celesto = new Celesto({ onEvent: (event) => console.log(event.type) });
  const sandbox = await celesto.sandboxes.create({ network: { mode: "off" } });

  try {
    await sandbox.files.write("/workspace/input.txt", "hello");
    const result = await sandbox.exec(
      ["sh", "-c", "tr a-z A-Z < /workspace/input.txt"],
      { timeoutMs: 30_000 },
    );
    console.log(result.stdout);
  } finally {
    await celesto.close();
  }
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
