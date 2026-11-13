import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig } from "tsup";

const packageRoot = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm"],
  dts: true,
  noExternal: ["dotenv"],
  esbuildOptions(options) {
    options.alias = {
      ...options.alias,
      dotenv: path.resolve(packageRoot, "node_modules/dotenv/lib/main.js"),
    };
  },
});
