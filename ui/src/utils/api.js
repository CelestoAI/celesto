/**
 * Where the dashboard's API lives.
 *
 * Served from the dashboard itself, the API is on the same origin and a
 * relative path is enough. During development Vite proxies /api and /login
 * to the local dashboard server, preserving the browser origin. API overrides
 * must still point to this same origin before the capability can be sent.
 */
export function getApiBaseUrl() {
    const envBase = import.meta.env.VITE_API_BASE_URL
    if (envBase) {
        return String(envBase).replace(/\/$/, '')
    }

    return ''
}

/** Absolute URL for an API path such as `/api/command`. */
export function apiUrl(path) {
    return `${getApiBaseUrl()}${path}`
}

// Browser storage includes the port in its origin; cookies do not. Keep the
// capability here so visiting another local server cannot send it there.
function dashboardToken() {
    return window.sessionStorage.getItem('celesto-dashboard-token')
}

function requireDashboardUrl(value, websocket = false) {
    const { protocol, hostname, port } = window.location
    const origin = new URL(`${protocol}//${hostname}${port ? `:${port}` : ''}`).origin
    const url = new URL(value, origin)
    if (websocket) {
        if (!['ws:', 'wss:'].includes(url.protocol)) throw new Error('Invalid dashboard stream.')
        url.protocol = url.protocol === 'wss:' ? 'https:' : 'http:'
    }
    if (url.origin !== origin || !url.pathname.startsWith('/api/') || url.username || url.password) {
        throw new Error("Open the private link printed by 'celesto ui' to use this dashboard.")
    }
}

export function apiFetch(url, options = {}) {
    requireDashboardUrl(url)
    const headers = new Headers(options.headers)
    const token = dashboardToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
    return fetch(url, { ...options, headers, credentials: 'omit', redirect: 'error' })
}

export function createApiSocket(url) {
    requireDashboardUrl(url, true)
    const token = dashboardToken()
    return new WebSocket(url, token ? ['celesto-dashboard-v1', `celesto-auth.${token}`] : [])
}
