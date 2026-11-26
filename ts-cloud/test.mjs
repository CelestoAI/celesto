// test.mjs (Node 18+)
// Manual smoke test — run locally with CELESTO_API_KEY set, not in CI.
import { GatekeeperClient } from "@celestoai/sdk/gatekeeper";

const token = process.env.CELESTO_API_KEY;
if (!token) {
  throw new Error("CELESTO_API_KEY must be set to run the smoke test");
}

const client = new GatekeeperClient({ token });
const res = await client.listConnections({ projectName: "Default" });
console.log(res);
