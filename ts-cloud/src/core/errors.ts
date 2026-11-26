/** Base error for all Celesto SDK errors. */
export class CelestoError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CelestoError";
  }
}

/** Thrown when an API request returns a non-2xx HTTP status. */
export class CelestoApiError extends CelestoError {
  readonly status: number;
  readonly data: unknown;
  readonly requestId?: string;
  /** Response headers, for the ones that carry meaning — such as Retry-After. */
  readonly headers?: Headers;

  constructor(
    message: string,
    status: number,
    data: unknown,
    requestId?: string,
    headers?: Headers,
  ) {
    super(message);
    this.name = "CelestoApiError";
    this.status = status;
    this.data = data;
    this.requestId = requestId;
    this.headers = headers;
  }
}

/** Thrown when fetch() itself fails — DNS, network, timeout, abort. */
export class CelestoNetworkError extends CelestoError {
  readonly cause?: Error;

  constructor(message: string, cause?: Error) {
    super(message);
    this.name = "CelestoNetworkError";
    this.cause = cause;
  }
}
