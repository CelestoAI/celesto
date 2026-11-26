import { readFile } from "node:fs/promises";
import { homedir } from "node:os";
import path from "node:path";

import { parse } from "dotenv";

import { DEFAULT_BASE_URL, type ClientConfig } from "./config";
import { CelestoError } from "./errors";

export const MISSING_CREDENTIALS_MESSAGE =
  "No Celesto credentials found. Run pip install celesto && celesto auth login, or export CELESTO_API_KEY.";

export interface CredentialResolutionOptions {
  /** Directory containing the local .env file. Defaults to process.cwd(). */
  cwd?: string;
  /** Environment variables to inspect. Defaults to process.env. */
  env?: NodeJS.ProcessEnv;
  /** Home directory containing the saved CLI login. Defaults to os.homedir(). */
  homeDir?: string;
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

type Credentials = { token: string; baseUrl?: string };

async function loadCliCredentials(home: string): Promise<Credentials | undefined> {
  try {
    const saved = JSON.parse(await readFile(path.join(home, ".celesto", "credentials"), "utf8"));
    const token = typeof saved?.api_key === "string" ? nonEmpty(saved.api_key) : undefined;
    if (!token) return undefined;
    const url = new URL(nonEmpty(typeof saved.base_url === "string" ? saved.base_url : undefined) ?? DEFAULT_BASE_URL);
    const local = url.protocol === "http:" && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
    if ((!local && url.protocol !== "https:") || url.username || url.password ||
      url.pathname !== "/" || url.search || url.hash) return undefined;
    return { token, baseUrl: url.origin };
  } catch {
    return undefined;
  }
}

async function resolveCredentials(options: CredentialResolutionOptions): Promise<Credentials | undefined> {
  const env = options.env ?? process.env;
  const environmentKey = nonEmpty(env.CELESTO_API_KEY);
  if (environmentKey) return { token: environmentKey };

  const dotEnvKey = await readDotEnvApiKey(
    options.cwd ?? process.cwd(),
    options.readDotEnv ?? ((filePath) => readFile(filePath, "utf8")),
  );
  if (dotEnvKey) return { token: dotEnvKey };

  if (options.loadSavedApiKey) {
    const token = await options.loadSavedApiKey();
    return token ? { token } : undefined;
  }
  return loadCliCredentials(options.homeDir ?? homedir());
}

/** Resolve a Celesto API key from local sources, in precedence order. */
export async function resolveCelestoApiKey(
  options: CredentialResolutionOptions = {},
): Promise<string | undefined> {
  return (await resolveCredentials(options))?.token;
}

/** Resolve an API key while preserving explicit SDK configuration. */
export async function resolveClientConfig(
  config: ClientConfig = {},
  options: CredentialResolutionOptions = {},
): Promise<ClientConfig> {
  if (nonEmpty(config.token) || nonEmpty(config.apiKey)) return config;

  const credentials = await resolveCredentials(options);
  if (!credentials) throw new CelestoError(MISSING_CREDENTIALS_MESSAGE);
  if (credentials.baseUrl && config.baseUrl !== undefined && new URL(config.baseUrl).origin !== credentials.baseUrl) {
    throw new CelestoError("Your saved Celesto key is for a different API URL. Run 'celesto auth login' for this URL or pass an API key explicitly.");
  }
  const baseUrl = config.baseUrl ?? credentials.baseUrl;
  return { ...config, token: credentials.token, ...(baseUrl === undefined ? {} : { baseUrl }) };
}
