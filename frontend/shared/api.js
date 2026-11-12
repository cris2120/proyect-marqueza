const loginUrl = new URL("../inicio_sesion/inicio_sesion.html?motivo=servidor_desconectado", document.currentScript.src);
const expiredSessionUrl = new URL("../inicio_sesion/inicio_sesion.html?motivo=sesion_requerida", document.currentScript.src);

class MarquezaApi {
    static get baseUrl() {
        const hostname = window.location.hostname;
        const isDevTunnel = hostname.endsWith(".devtunnels.ms");
        const isLocal = hostname === "localhost" || hostname === "127.0.0.1";
        const apiHost = isDevTunnel
            ? `${window.location.protocol}//${hostname.replace(/-(5500|5000)(?=\.)/, "-5000")}`
            : isLocal
                ? `${window.location.protocol}//${hostname}:5000`
                : window.location.origin;
        const localApiUrl = `${apiHost}/api`;
        return (window.MARQUEZA_API_BASE_URL || localApiUrl).replace(/\/+$/, "");
    }

    static async request(path, options = {}) {
        const suppressSessionRedirect = options.suppressSessionRedirect === true;
        const requestOptions = { ...options };
        delete requestOptions.suppressSessionRedirect;
        const sessionToken = this.sessionToken();
        let response;
        try {
            response = await fetch(`${this.baseUrl}${path}`, {
                ...requestOptions,
                headers: {
                    ...(options.body ? { "Content-Type": "application/json" } : {}),
                    ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}),
                    ...options.headers
                }
            });
        } catch {
            let session = null;
            try {
                session = JSON.parse(localStorage.getItem("marqueza_usuario_sesion") || "null");
            } catch {
                session = null;
            }
            const hasActiveSession = session?.id && sessionStorage.getItem("marqueza_sesion_activa") === String(session.id);
            const isLoginPage = window.location.pathname.endsWith("/inicio_sesion/inicio_sesion.html");
            if (hasActiveSession && !isLoginPage && !suppressSessionRedirect) {
                localStorage.removeItem("marqueza_usuario_sesion");
                sessionStorage.removeItem("marqueza_sesion_activa");
                window.location.replace(loginUrl);
            }
            throw new Error("No se pudo conectar con la API. Comprueba que el backend esté iniciado.");
        }

        const text = await response.text();
        let payload = null;
        if (text) {
            try {
                payload = JSON.parse(text);
            } catch {
                payload = { message: text };
            }
        }
        if (!response.ok) {
            const message = payload?.mensaje || payload?.message || `Error HTTP ${response.status}`;
            if (
                response.status === 401
                && sessionToken
                && (!path.startsWith("/auth/") || path === "/auth/heartbeat")
            ) {
                localStorage.removeItem("marqueza_usuario_sesion");
                sessionStorage.removeItem("marqueza_sesion_activa");
                window.location.replace(expiredSessionUrl);
            }
            const error = new Error(message);
            error.code = payload?.code;
            error.status = response.status;
            error.usuarioId = payload?.usuario_id;
            throw error;
        }
        return payload;
    }

    static sessionToken() {
        const storedSession = localStorage.getItem("marqueza_usuario_sesion");
        if (!storedSession) return null;

        let session;
        try {
            session = JSON.parse(storedSession);
        } catch (error) {
            console.error("No fue posible leer la sesión almacenada.", error);
            throw new Error("No fue posible leer la sesión almacenada. Cierra sesión y vuelve a ingresar.");
        }
        return typeof session?.token === "string" && session.token ? session.token : null;
    }

    static list(resource) {
        return this.request(`/${resource}/`);
    }

    static create(resource, record) {
        return this.request(`/${resource}/`, { method: "POST", body: JSON.stringify(record) });
    }

    static update(resource, id, record) {
        return this.request(`/${resource}/${encodeURIComponent(id)}`, {
            method: "PUT",
            body: JSON.stringify(record)
        });
    }

    static remove(resource, id) {
        return this.request(`/${resource}/${encodeURIComponent(id)}`, { method: "DELETE" });
    }

    static async load(resource, storageKey = `marqueza_${resource}`) {
        const pendingKey = `${storageKey}_pendientes_migracion`;
        let pending = this.cached(pendingKey);
        if (localStorage.getItem(pendingKey) === null) {
            pending = this.cached(storageKey)
                .filter(record => record.id === undefined || record.id === null)
                .map((record, index) => ({ ...record, __localKey: `${Date.now()}-${index}` }));
            if (pending.length) localStorage.setItem(pendingKey, JSON.stringify(pending));
        }
        const records = await this.list(resource);
        if (!Array.isArray(records)) throw new Error(`La respuesta de ${resource} no es una lista válida.`);
        const combined = [...records, ...pending];
        localStorage.setItem(storageKey, JSON.stringify(combined));
        return combined;
    }

    static consumeLegacy(storageKey, localKey) {
        if (!localKey) return;
        const pendingKey = `${storageKey}_pendientes_migracion`;
        const pending = this.cached(pendingKey).filter(record => record.__localKey !== localKey);
        localStorage.setItem(pendingKey, JSON.stringify(pending));
        localStorage.setItem(storageKey, JSON.stringify(this.cached(storageKey).filter(record => record.__localKey !== localKey)));
    }

    static cached(storageKey) {
        try {
            const records = JSON.parse(localStorage.getItem(storageKey) || "[]");
            return Array.isArray(records) ? records : [];
        } catch {
            return [];
        }
    }

    static notifyError(error, title = "No se pudo completar la operación") {
        const message = error instanceof Error ? error.message : String(error);
        if (window.Swal) {
            return window.Swal.fire({ icon: "error", title, text: message });
        }
        window.alert(`${title}: ${message}`);
        return Promise.resolve();
    }
}

window.MarquezaApi = MarquezaApi;

let sessionHeartbeatInProgress = false;

async function sendSessionHeartbeat() {
    if (window.location.pathname.endsWith("/inicio_sesion/inicio_sesion.html")) return;

    let session;
    try {
        session = JSON.parse(localStorage.getItem("marqueza_usuario_sesion") || "null");
    } catch (error) {
        console.error("No fue posible leer la sesión activa.", error);
        return;
    }

    if (
        !session?.id
        || sessionStorage.getItem("marqueza_sesion_activa") !== String(session.id)
        || sessionHeartbeatInProgress
    ) return;

    sessionHeartbeatInProgress = true;
    try {
        await MarquezaApi.request("/auth/heartbeat", {
            method: "POST",
            suppressSessionRedirect: true
        });
    } catch (error) {
        console.warn("No se pudo actualizar la actividad de la sesión.", error);
    } finally {
        sessionHeartbeatInProgress = false;
    }
}

void sendSessionHeartbeat();
window.setInterval(sendSessionHeartbeat, 20000);
document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") void sendSessionHeartbeat();
});

const sessionConflictRequestKey = "marqueza_solicitud_cierre_sesion";
const sessionConflictResponsePrefix = "marqueza_respuesta_cierre_sesion_";
const handledSessionConflictRequests = new Set();

function respondToSessionConflict(request) {
    if (!request?.id || handledSessionConflictRequests.has(request.id)) return;
    if (Date.now() - request.createdAt > 60000) return;

    let session;
    try {
        session = JSON.parse(localStorage.getItem("marqueza_usuario_sesion") || "null");
    } catch (error) {
        console.error("No fue posible leer la sesión activa.", error);
        return;
    }

    if (
        !session?.id
        || String(session.id) !== String(request.usuarioId)
        || sessionStorage.getItem("marqueza_sesion_activa") !== String(session.id)
    ) return;

    handledSessionConflictRequests.add(request.id);
    const confirmLogout = window.Swal
        ? window.Swal.fire({
            icon: "warning",
            title: "Usuario activo en otra pestaña",
            text: "Se intentó iniciar sesión con tu usuario. ¿Quieres cerrar esta sesión para permitir el acceso en la otra pestaña?",
            showCancelButton: true,
            confirmButtonText: "Sí, cerrar sesión",
            cancelButtonText: "No, mantener sesión"
        }).then(result => result.isConfirmed)
        : Promise.resolve(window.confirm(
            "Se intentó iniciar sesión con tu usuario en otra pestaña. ¿Quieres cerrar esta sesión?"
        ));

    confirmLogout.then(async shouldLogout => {
        if (!shouldLogout) {
            localStorage.setItem(`${sessionConflictResponsePrefix}${request.id}`, JSON.stringify({ approved: false }));
            return;
        }

        try {
            await MarquezaApi.request("/auth/logout", { method: "POST" });
            window.MarquezaAudit?.log({
                action: "Cierre de sesión",
                module: "Acceso",
                detail: "La sesión se cerró desde otra pestaña a petición del usuario."
            });
            localStorage.removeItem("marqueza_usuario_sesion");
            sessionStorage.removeItem("marqueza_sesion_activa");
            localStorage.setItem(`${sessionConflictResponsePrefix}${request.id}`, JSON.stringify({ approved: true }));
            const logoutUrl = new URL("../inicio_sesion/inicio_sesion.html", document.currentScript?.src || window.location.href);
            window.location.replace(logoutUrl);
        } catch (error) {
            await MarquezaApi.notifyError(error, "No se pudo cerrar la sesión activa");
            localStorage.setItem(`${sessionConflictResponsePrefix}${request.id}`, JSON.stringify({ approved: false }));
        }
    });
}

window.addEventListener("storage", event => {
    if (event.key !== sessionConflictRequestKey || !event.newValue) return;
    try {
        respondToSessionConflict(JSON.parse(event.newValue));
    } catch (error) {
        console.error("No fue posible procesar la solicitud de cierre de sesión.", error);
    }
});

void window.MarquezaAudit?.syncPending?.();
