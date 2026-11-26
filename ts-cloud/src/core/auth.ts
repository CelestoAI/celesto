import { execFile as execFileCallback } from "node:child_process";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

import { parse } from "dotenv";

import type { ClientConfig } from "./config";
import { CelestoError } from "./errors";

const execFile = promisify(execFileCallback);

export const MISSING_CREDENTIALS_MESSAGE =
  "No Celesto credentials found. Run pip install celesto && celesto auth login, or export CELESTO_API_KEY.";

export interface CredentialResolutionOptions {
  /** Directory containing the local .env file. Defaults to process.cwd(). */
  cwd?: string;
  /** Environment variables to inspect. Defaults to process.env. */
  env?: NodeJS.ProcessEnv;
  /** Test or host override for reading .env. */
  readDotEnv?: (filePath: string) => Promise<string>;
  /** Test or host override for loading credentials saved by the Celesto CLI. */
  loadSavedApiKey?: () => Promise<string | undefined>;
}

function nonEmpty(value: string | undefined): string | undefined {
  const trimmed = value?.trim();
  return trimmed ? trimmed : undefined;
}

async function readDotEnvApiKey(
  cwd: string,
  readDotEnv: (filePath: string) => Promise<string>,
): Promise<string | undefined> {
  try {
    const contents = await readDotEnv(path.join(cwd, ".env"));
    return nonEmpty(parse(contents).CELESTO_API_KEY);
  } catch {
    return undefined;
  }
}

async function loadCliApiKey(): Promise<string | undefined> {
  try {
    const { stdout } = await execFile("celesto", ["auth", "token"], {
      encoding: "utf8",
      timeout: 5_000,
      maxBuffer: 64 * 1024,
    });
    return nonEmpty(stdout);
  } catch {
    return undefined;
  }
}

/** Resolve a Celesto API key from local sources, in precedence order. */
export async function resolveCelestoApiKey(
  options: CredentialResolutionOptions = {},
): Promise<string | undefined> {
  const env = options.env ?? process.env;
  const environmentKey = nonEmpty(env.CELESTO_API_KEY);
  if (environmentKey) return environmentKey;

  const dotEnvKey = await readDotEnvApiKey(
    options.cwd ?? process.cwd(),
    options.readDotEnv ?? ((filePath) => readFile(filePath, "utf8")),
  );
  if (dotEnvKey) return dotEnvKey;

  return (options.loadSavedApiKey ?? loadCliApiKey)();
}

/** Resolve an API key while preserving explicit SDK configuration. */
export async function resolveClientConfig(
  config: ClientConfig = {},
  options: CredentialResolutionOptions = {},
): Promise<ClientConfig> {
  if (nonEmpty(config.token) || nonEmpty(config.apiKey)) return config;

  const apiKey = await resolveCelestoApiKey(options);
  if (!apiKey) throw new CelestoError(MISSING_CREDENTIALS_MESSAGE);
  return { ...config, token: apiKey };
}
