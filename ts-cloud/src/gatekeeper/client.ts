import { buildRequestContext, ClientConfig, RequestOverrides } from "../core/config";
import { request } from "../core/http";
import {
  GatekeeperAccessRules,
  GatekeeperAccessRulesParams,
  GatekeeperConnectRequest,
  GatekeeperConnectResponse,
  GatekeeperConnection,
  GatekeeperDriveFile,
  GatekeeperDriveListParams,
  GatekeeperDriveListResponse,
  GatekeeperListConnectionsParams,
  GatekeeperListConnectionsResponse,
  GatekeeperRevokeParams,
  GatekeeperRevokeResponse,
} from "./types";

interface GatekeeperConnectRequestWire {
  subject: string;
  provider: string;
  project_name: string;
  redirect_uri?: string;
}

interface GatekeeperConnectResponseWire {
  status: string;
  oauth_url?: string | null;
  connection_id?: string | null;
}

interface GatekeeperConnectionWire {
  id: string;
  subject: string;
  provider: string;
  project_id: string;
  account_email?: string | null;
  scopes?: string[];
  status: string;
  created_at: string;
  updated_at: string;
  last_used_at?: string | null;
  access_rules?: {
    allowed_folders?: string[];
    allowed_files?: string[];
    version?: string;
  } | null;
}

interface GatekeeperListConnectionsResponseWire {
  data: GatekeeperConnectionWire[];
  total: number;
}

interface GatekeeperDriveFileWire {
  id: string;
  name?: string | null;
  mime_type?: string | null;
  size?: number | null;
  modified_time?: string | null;
  created_time?: string | null;
  web_view_link?: string | null;
  icon_link?: string | null;
  thumbnail_link?: string | null;
  parents?: string[] | null;
  drive_id?: string | null;
  shared?: boolean | null;
  owned_by_me?: boolean | null;
}

interface GatekeeperDriveListResponseWire {
  files: GatekeeperDriveFileWire[];
  next_page_token?: string | null;
}

interface GatekeeperAccessRulesResponseWire {
  version: string;
  allowed_folders: string[];
  allowed_files: string[];
  unrestricted: boolean;
}

const toConnectRequest = (payload: GatekeeperConnectRequest): GatekeeperConnectRequestWire => ({
  subject: payload.subject,
  provider: payload.provider ?? "google_drive",
  project_name: payload.projectName,
  redirect_uri: payload.redirectUri,
});

const toConnectResponse = (payload: GatekeeperConnectResponseWire): GatekeeperConnectResponse => ({
  status: payload.status,
  oauthUrl: payload.oauth_url ?? undefined,
  connectionId: payload.connection_id ?? undefined,
});

const toConnection = (payload: GatekeeperConnectionWire): GatekeeperConnection => ({
  id: payload.id,
  subject: payload.subject,
  provider: payload.provider,
  projectId: payload.project_id,
  accountEmail: payload.account_email ?? null,
  scopes: payload.scopes ?? [],
  status: payload.status,
  createdAt: payload.created_at,
  updatedAt: payload.updated_at,
  lastUsedAt: payload.last_used_at ?? null,
  accessRules: payload.access_rules
    ? {
        version: payload.access_rules.version ?? "1",
        allowedFolders: payload.access_rules.allowed_folders ?? [],
        allowedFiles: payload.access_rules.allowed_files ?? [],
        unrestricted: false,
      }
    : null,
});

const toAccessRules = (payload: GatekeeperAccessRulesResponseWire): GatekeeperAccessRules => ({
  version: payload.version,
  allowedFolders: payload.allowed_folders ?? [],
  allowedFiles: payload.allowed_files ?? [],
  unrestricted: payload.unrestricted,
});

const toDriveFile = (payload: GatekeeperDriveFileWire): GatekeeperDriveFile => ({
  id: payload.id,
  name: payload.name ?? null,
  mimeType: payload.mime_type ?? null,
  size: payload.size ?? null,
  modifiedTime: payload.modified_time ?? null,
  createdTime: payload.created_time ?? null,
  webViewLink: payload.web_view_link ?? null,
  iconLink: payload.icon_link ?? null,
  thumbnailLink: payload.thumbnail_link ?? null,
  parents: payload.parents ?? null,
  driveId: payload.drive_id ?? null,
  shared: payload.shared ?? null,
  ownedByMe: payload.owned_by_me ?? null,
});

const gatekeeperPath = (path: string): string => `/v1/gatekeeper${path}`;

const pickOverrides = (options?: RequestOverrides): RequestOverrides => ({
  headers: options?.headers,
  signal: options?.signal,
});

export class GatekeeperClient {
  private readonly config: ClientConfig;

  constructor(config: ClientConfig) {
    this.config = config;
  }

  async connect(payload: GatekeeperConnectRequest, options?: RequestOverrides): Promise<GatekeeperConnectResponse> {
    const ctx = buildRequestContext(this.config);
    const data = await request<GatekeeperConnectResponseWire>(ctx, {
      method: "POST",
      path: gatekeeperPath("/connect"),
      body: toConnectRequest(payload),
      ...pickOverrides(options),
    });
    return toConnectResponse(data);
  }

  async listConnections(params: GatekeeperListConnectionsParams, options?: RequestOverrides): Promise<GatekeeperListConnectionsResponse> {
    const ctx = buildRequestContext(this.config);
    const data = await request<GatekeeperListConnectionsResponseWire>(ctx, {
      method: "GET",
      path: gatekeeperPath("/connections"),
      query: {
        project_name: params.projectName,
        status_filter: params.statusFilter,
      },
      ...pickOverrides(options),
    });

    return {
      total: data.total,
      data: data.data.map(toConnection),
    };
  }

  async getConnection(connectionId: string, options?: RequestOverrides): Promise<GatekeeperConnection> {
    const ctx = buildRequestContext(this.config);
    const data = await request<GatekeeperConnectionWire>(ctx, {
      method: "GET",
      path: gatekeeperPath(`/connections/${connectionId}`),
      ...pickOverrides(options),
    });
    return toConnection(data);
  }

  async revokeConnection(params: GatekeeperRevokeParams, options?: RequestOverrides): Promise<GatekeeperRevokeResponse> {
    const ctx = buildRequestContext(this.config);
    return request<GatekeeperRevokeResponse>(ctx, {
      method: "DELETE",
      path: gatekeeperPath("/connections"),
      query: {
        subject: params.subject,
        project_name: params.projectName,
        provider: params.provider,
      },
      ...pickOverrides(options),
    });
  }

  async listDriveFiles(params: GatekeeperDriveListParams, options?: RequestOverrides): Promise<GatekeeperDriveListResponse> {
    const ctx = buildRequestContext(this.config);
    const data = await request<GatekeeperDriveListResponseWire>(ctx, {
      method: "GET",
      path: gatekeeperPath("/connectors/drive/files"),
      query: {
        project_name: params.projectName,
        subject: params.subject,
        page_size: params.pageSize,
        page_token: params.pageToken,
        folder_id: params.folderId,
        query: params.query,
        include_folders: params.includeFolders,
        order_by: params.orderBy,
      },
      ...pickOverrides(options),
    });

    return {
      files: data.files.map(toDriveFile),
      nextPageToken: data.next_page_token ?? null,
    };
  }

  async getAccessRules(connectionId: string, options?: RequestOverrides): Promise<GatekeeperAccessRules> {
    const ctx = buildRequestContext(this.config);
    const data = await request<GatekeeperAccessRulesResponseWire>(ctx, {
      method: "GET",
      path: gatekeeperPath(`/connections/${connectionId}/access-rules`),
      ...pickOverrides(options),
    });
    return toAccessRules(data);
  }

  async updateAccessRules(params: GatekeeperAccessRulesParams, options?: RequestOverrides): Promise<GatekeeperAccessRules> {
    const ctx = buildRequestContext(this.config);
    const data = await request<GatekeeperAccessRulesResponseWire>(ctx, {
      method: "PUT",
      path: gatekeeperPath("/connections/access-rules"),
      query: {
        subject: params.subject,
        project_name: params.projectName,
        provider: params.provider,
      },
      body: {
        allowed_folders: params.accessRules.allowedFolders ?? [],
        allowed_files: params.accessRules.allowedFiles ?? [],
      },
      ...pickOverrides(options),
    });
    return toAccessRules(data);
  }

  async clearAccessRules(connectionId: string, options?: RequestOverrides): Promise<GatekeeperAccessRules> {
    const ctx = buildRequestContext(this.config);
    const data = await request<GatekeeperAccessRulesResponseWire>(ctx, {
      method: "DELETE",
      path: gatekeeperPath(`/connections/${connectionId}/access-rules`),
      ...pickOverrides(options),
    });
    return toAccessRules(data);
  }
}
