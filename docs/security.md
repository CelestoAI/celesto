# Secure local access

Celesto runs programs inside disposable computers. Control links and keys still grant access to those computers, so keep them with the application that owns the session.

## Open the dashboard

Run `celesto ui` and open its private link. The link signs your browser in; opening the address without that link does not grant access. Restarting the dashboard changes its generated access token.

Set `CELESTO_DASHBOARD_TOKEN` to a long random value if you need a stable token. You must set it before binding the dashboard to an address other than localhost. Browser requests must come from the dashboard's own origin. An API client can send `Authorization: Bearer <token>`.

The local API server also requires a token. `celesto server start` prints a generated token for localhost use, or reads `CELESTO_SERVER_TOKEN`. Set that variable before listening on another address. The TypeScript SDK supplies its own token when it starts the private server. Applications embedding `create_app()` can supply `auth_token` or read the generated value from `app.state.auth_token`.

## Connect to a browser or desktop

Use the complete connection URL returned by Celesto. Browser and display URLs contain a random capability: possession of that URL grants control of that endpoint. Do not publish them, include them in analytics, or give them to a model as page content. Request a read-only display connection when control is unnecessary.

Raw, unauthenticated VNC connections are disabled. Use the browser viewer or the WebSocket URL returned by `Computer.display()`. Browser automation continues to use Playwright or CDP with the returned URL. Older browser images with an unrecognized launcher are rejected; rebuild them before retrying.

Existing running sessions do not acquire these protections automatically. Stop and recreate them after upgrading. Attaching to a saved session with an older unprotected URL clears its saved links and asks you to recreate it. On Linux and macOS, CLI inventory files and SQLite journals are private to their owning account; shared writable inventory folders and linked database files are refused.

## Verify SSH identity

SSH rejects unknown or changed server keys before sending credentials. Updated managed Linux images publish their public host key through their local boot console; Celesto uses that trusted channel to identify the guest. Custom, Windows, or older images need a trusted `known_hosts` entry. Set `CELESTO_SSH_KNOWN_HOSTS` to a file provisioned through a trusted console or image-building process. Do not populate it from an unverified network scan.

Collected SSH command output is limited to 8 MiB. Use streaming output or write a large result to a file when needed. Streaming commands retain their execution deadline even while output arrives continuously.

## Limit browsing to public websites

Use `internet_settings={"mode": "public"}` with QEMU's default slirp network on Linux or macOS. This permits HTTP and HTTPS through a destination-checking proxy while blocking direct outbound connections. Private, loopback, link-local and other non-public destinations are rejected, including destinations discovered through DNS.

Chromium receives the proxy configuration automatically. Other applications must explicitly use the proxy at `http://10.0.2.100:3128`. This mode does not support shared folders, extra configured port forwards, or snapshot creation or restore. OpenMuse selects it for local browsing and rejects cloud browsing until the cloud provider offers the same guarantee. See [networking](guides/networking.md).

## Import images and files

Imported QCOW2 disks must be standalone: external backing files and external data files are rejected. Celesto's own managed overlays remain an internal implementation detail.

`celesto image load` limits aggregate extraction work to 64 GiB by default and reserves 1 GiB of the available free space when calculating that budget. Set `CELESTO_IMAGE_LOAD_MAX_BYTES` to a positive integer to choose a different limit. Compressed data is checked while it expands. Sparse tar entries are rejected. Guest tar downloads have separate limits of 10,000 entries, 256 MiB per file and 1 GiB in total.

## Administrator setup

The setup script removes the previous unrestricted passwordless grants for networking commands and the image-building helper. Networking operations that require administrator rights need an appropriately privileged invocation. Image building uses Docker when the privileged helper is unavailable. Run `celesto setup` after upgrading to replace the old policy.

## Release requirements

Source fixes do not update existing images or installed native extensions. Before releasing these changes, build and smoke-test both guest architectures and the supported images, publish the guest-agent and image assets, then update the image tag, rootfs checksums and the separate guest-agent checksums in the SDK. Verify source-checkout and installed-wheel paths before tagging the package. The repository's [release checklist](../AGENTS.md#release-checklist) governs that sequence.
