export interface GatekeeperConnectRequest {
  subject: string;
  /** Defaults to "google_drive". */
  provider?: string;
  projectName: string;
  redirectUri?: string;
}

export interface GatekeeperConnectResponse {
  status: "redirect" | "connected" | string;
  oauthUrl?: string;
  connectionId?: string;
}

export interface GatekeeperConnection {
  id: string;
  subject: string;
  provider: string;
  projectId: string;
  accountEmail?: string | null;
  scopes: string[];
  status: string;
  createdAt: string;
  updatedAt: string;
  lastUsedAt?: string | null;
  accessRules?: GatekeeperAccessRules | null;
}

export interface GatekeeperListConnectionsResponse {
  data: GatekeeperConnection[];
  total: number;
}

export interface GatekeeperDriveFile {
  id: string;
  name?: string | null;
  mimeType?: string | null;
  size?: number | null;
  modifiedTime?: string | null;
  createdTime?: string | null;
  webViewLink?: string | null;
  iconLink?: string | null;
  thumbnailLink?: string | null;
  parents?: string[] | null;
  driveId?: string | null;
  shared?: boolean | null;
  ownedByMe?: boolean | null;
}

export interface GatekeeperDriveListResponse {
  files: GatekeeperDriveFile[];
  nextPageToken?: string | null;
}

export interface GatekeeperAccessRules {
  version: string;
  allowedFolders: string[];
  allowedFiles: string[];
  unrestricted: boolean;
}

export interface GatekeeperAccessRulesUpdate {
  allowedFolders?: string[];
  allowedFiles?: string[];
}

export interface GatekeeperRevokeResponse {
  status: string;
  id: string;
}

export interface GatekeeperListConnectionsParams {
  projectName: string;
  statusFilter?: string;
}

export interface GatekeeperDriveListParams {
  projectName: string;
  subject: string;
  pageSize?: number;
  pageToken?: string;
  folderId?: string;
  query?: string;
  includeFolders?: boolean;
  orderBy?: string;
}

export interface GatekeeperRevokeParams {
  subject: string;
  projectName: string;
  provider?: string;
}

export interface GatekeeperAccessRulesParams {
  subject: string;
  projectName: string;
  provider?: string;
  accessRules: GatekeeperAccessRulesUpdate;
}
