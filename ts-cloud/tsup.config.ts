import { defineConfig } from "tsup";

export default defineConfig({
  entry: {
    index: "src/index.ts",
    "gatekeeper/index": "src/gatekeeper/index.ts",
    "computers/index": "src/computers/index.ts",
    "agents/index": "src/agents/index.ts",
  },
  format: ["esm", "cjs"],
  dts: true,
  sourcemap: true,
  clean: true,
  target: "es2020",
  platform: "node",
});
