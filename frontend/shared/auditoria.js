(function () {
    const STORAGE_KEY = "marqueza_bitacora";
    const PENDING_KEY = "marqueza_bitacora_pendientes";
    const SESSION_TAB_PREFIX = "marqueza_sesion_pestana_activa_";
    const TAB_ID_KEY = "marqueza_id_pestana";
    const SESSION_TRANSFER_REQUEST_PREFIX = "marqueza_solicitud_cierre_sesion_";
    const SESSION_TRANSFER_RESPONSE_PREFIX = "marqueza_respuesta_cierre_sesion_";
    const SESSION_HEARTBEAT_MS = 5000;
    const SESSION_TIMEOUT_MS = 30000;
    const MAX_EVENTS = 500;
    let syncTask = null;
    let sessionHeartbeat = null;
    let sessionTransferPromptOpen = false;
    let tabId;
    const approvedTransfers = new Map();

    function getTabId() {
        if (tabId) return tabId;
        tabId = sessionStorage.getItem(TAB_ID_KEY);
        if (!tabId) {
            tabId = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
            sessionStorage.setItem(TAB_ID_KEY, tabId);
        }
        return tabId;
    }

    function sessionTabKey(sessionId) {
        return `${SESSION_TAB_PREFIX}${encodeURIComponent(String(sessionId))}`;
    }

    function readSessionTab(sessionId) {
        try {
            const activeTab = JSON.parse(localStorage.getItem(sessionTabKey(sessionId)) || "null");
            return activeTab && typeof activeTab === "object" ? activeTab : null;
        } catch {
            return null;
        }
    }

    function isSessionTabActive(activeTab, now = Date.now()) {
        return Boolean(activeTab?.tabId && now - Number(activeTab.updatedAt) < SESSION_TIMEOUT_MS);
    }

    function normalizeIdentifier(value) {
        return String(value || "").trim().toLocaleLowerCase("es");
    }

    function writeSessionTab(sessionId, identifiers = []) {
        const normalizedSessionId = String(sessionId);
        localStorage.setItem(sessionTabKey(normalizedSessionId), JSON.stringify({
            tabId: getTabId(),
            sessionId: normalizedSessionId,
            identifiers: [...new Set(identifiers.map(normalizeIdentifier).filter(Boolean))],
            updatedAt: Date.now()
        }));
    }

    function startSessionHeartbeat(session) {
        clearInterval(sessionHeartbeat);
        const sessionId = session?.id ?? session;
        const identifiers = typeof session === "object"
            ? [session.nombre, session.correo]
            : [];
        writeSessionTab(sessionId, identifiers);
        sessionHeartbeat = setInterval(() => {
            const activeTab = readSessionTab(sessionId);
            if (activeTab?.tabId !== getTabId()) {
                clearInterval(sessionHeartbeat);
                sessionHeartbeat = null;
                return;
            }
            writeSessionTab(sessionId, identifiers);
        }, SESSION_HEARTBEAT_MS);
    }

    function isActiveInAnotherTab(sessionId) {
        const activeTab = readSessionTab(sessionId);
        return isSessionTabActive(activeTab) && activeTab.tabId !== getTabId();
    }

    function showActiveElsewhereAlert() {
        const message = "El usuario está activo en otra pestaña. Cierra la sesión allí antes de volver a ingresar.";
        if (window.Swal) {
            void window.Swal.fire({ icon: "warning", title: "Sesión activa", text: message });
        } else {
            window.alert(message);
        }
    }

    function redirectToLoginForActiveSession() {
        const loginUrl = new URL("../inicio_sesion/inicio_sesion.html?motivo=usuario_activo_otra_pestana", window.location.href);
        window.location.replace(loginUrl);
    }

    function releaseSession({ sessionId = getSession()?.id } = {}) {
        if (sessionId === undefined || sessionId === null) {
            clearInterval(sessionHeartbeat);
            sessionHeartbeat = null;
            return;
        }
        const activeTab = readSessionTab(sessionId);
        if (activeTab?.tabId === getTabId()) {
            localStorage.removeItem(sessionTabKey(sessionId));
        }
        clearInterval(sessionHeartbeat);
        sessionHeartbeat = null;
    }

    function transferResponseKey(requestId) {
        return `${SESSION_TRANSFER_RESPONSE_PREFIX}${requestId}`;
    }

    function respondToSessionTransfer(requestId, approved, approvalId = null) {
        localStorage.setItem(transferResponseKey(requestId), JSON.stringify({ requestId, approved, approvalId }));
    }

    async function confirmSessionTransfer() {
        const message = "Estás intentando ingresar desde otra pestaña. ¿Quieres cerrar sesión? Solo se cerrará si la contraseña es válida.";
        if (!window.Swal) return window.confirm(message);
        const result = await window.Swal.fire({
            icon: "warning",
            title: "Ingreso desde otra pestaña",
            text: message,
            showCancelButton: true,
            confirmButtonText: "Sí, cerrar sesión",
            cancelButtonText: "No, mantener sesión",
            reverseButtons: true
        });
        return result.isConfirmed;
    }

    function findSessionByIdentifier(identifier) {
        const normalizedIdentifier = normalizeIdentifier(identifier);
        if (!normalizedIdentifier) return null;
        for (let index = 0; index < localStorage.length; index += 1) {
            const key = localStorage.key(index);
            if (!key?.startsWith(SESSION_TAB_PREFIX)) continue;
            try {
                const activeTab = JSON.parse(localStorage.getItem(key) || "null");
                if (isSessionTabActive(activeTab) && activeTab.identifiers?.includes(normalizedIdentifier)) {
                    return activeTab;
                }
            } catch (error) {
                console.error("No se pudo leer una sesión activa de otra pestaña.", error);
            }
        }
        return null;
    }

    async function preflightSession(identifier) {
        const activeTab = findSessionByIdentifier(identifier);
        if (!activeTab || activeTab.tabId === getTabId()) return null;
        const response = await requestSessionTransfer(activeTab.sessionId, "prepare");
        return response.approved
            ? { sessionId: String(activeTab.sessionId), approvalId: response.approvalId }
            : { denied: true };
    }

    async function closeSessionForTransfer(requestId, sessionId) {
        const requestKey = `${SESSION_TRANSFER_REQUEST_PREFIX}${requestId}`;
        if (!localStorage.getItem(requestKey)) {
            respondToSessionTransfer(requestId, false);
            return;
        }
        const currentSessionTab = readSessionTab(sessionId);
        const currentSession = getSession();
        if (currentSessionTab?.tabId !== getTabId() || currentSessionTab.sessionId !== String(currentSession?.id) || currentSessionTab.sessionId !== String(sessionId)) {
            respondToSessionTransfer(requestId, false);
            return;
        }
        if (window.MarquezaApi?.sessionToken()) {
            await window.MarquezaApi.request("/auth/logout", { method: "POST" });
        }
        releaseSession({ sessionId });
        sessionStorage.removeItem("marqueza_usuario_sesion");
        sessionStorage.removeItem("marqueza_sesion_activa");
        respondToSessionTransfer(requestId, true);
        window.location.replace("../inicio_sesion/inicio_sesion.html");
    }

    async function handleSessionTransferRequest(requestId) {
        const requestKey = `${SESSION_TRANSFER_REQUEST_PREFIX}${requestId}`;
        let request;
        try {
            request = JSON.parse(localStorage.getItem(requestKey) || "null");
        } catch (error) {
            console.error("No se pudo leer la solicitud de cierre de sesión.", error);
            return;
        }
        if (!request?.sessionId) return;
        const activeTab = readSessionTab(request.sessionId);
        const session = getSession();
        if (activeTab?.tabId !== getTabId()) return;
        if (!hasActiveSession() || activeTab.sessionId !== String(session?.id) || activeTab.sessionId !== String(request.sessionId)) {
            respondToSessionTransfer(requestId, false);
            return;
        }
        if (sessionTransferPromptOpen) {
            respondToSessionTransfer(requestId, false);
            return;
        }

        if (request.action === "commit") {
            const approval = approvedTransfers.get(request.approvalId);
            if (!approval || approval.sessionId !== String(request.sessionId) || approval.expiresAt < Date.now()) {
                respondToSessionTransfer(requestId, false);
                return;
            }
            approvedTransfers.delete(request.approvalId);
            try {
                await closeSessionForTransfer(requestId, request.sessionId);
            } catch (error) {
                await window.MarquezaApi?.notifyError(error, "No se pudo cerrar la sesión");
                respondToSessionTransfer(requestId, false);
            }
            return;
        }

        sessionTransferPromptOpen = true;
        try {
            if (!await confirmSessionTransfer()) {
                respondToSessionTransfer(requestId, false);
                return;
            }
            if (!localStorage.getItem(requestKey)) {
                respondToSessionTransfer(requestId, false);
                return;
            }
            const confirmedSessionTab = readSessionTab(request.sessionId);
            const confirmedSession = getSession();
            if (confirmedSessionTab?.tabId !== getTabId() || confirmedSessionTab.sessionId !== String(confirmedSession?.id)) {
                respondToSessionTransfer(requestId, false);
                return;
            }
            if (request.action === "prepare") {
                const approval = { sessionId: String(request.sessionId), expiresAt: Date.now() + SESSION_TIMEOUT_MS * 2 };
                approvedTransfers.set(requestId, approval);
                setTimeout(() => approvedTransfers.delete(requestId), SESSION_TIMEOUT_MS * 2);
                respondToSessionTransfer(requestId, true, requestId);
            } else {
                await closeSessionForTransfer(requestId, request.sessionId);
            }
        } catch (error) {
            await window.MarquezaApi?.notifyError(error, "No se pudo cerrar la sesión");
            respondToSessionTransfer(requestId, false);
        } finally {
            sessionTransferPromptOpen = false;
        }
    }

    function requestSessionTransfer(sessionId, action = "confirm", approvalId = null) {
        const requestId = `${getTabId()}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const requestKey = `${SESSION_TRANSFER_REQUEST_PREFIX}${requestId}`;
        const responseKey = transferResponseKey(requestId);
        return new Promise((resolve) => {
            const timeout = setTimeout(() => finish({ approved: false }), SESSION_TIMEOUT_MS * 2);
            const onPageHide = () => finish({ approved: false });
            const onStorage = (event) => {
                if (event.key !== responseKey || !event.newValue) return;
                let response;
                try {
                    response = JSON.parse(event.newValue);
                } catch (error) {
                    console.error("No se pudo leer la respuesta de cierre de sesión.", error);
                    return;
                }
                if (response?.requestId === requestId) finish(response);
            };
            const finish = (response) => {
                clearTimeout(timeout);
                window.removeEventListener("storage", onStorage);
                window.removeEventListener("pagehide", onPageHide);
                localStorage.removeItem(requestKey);
                localStorage.removeItem(responseKey);
                resolve(response);
            };
            window.addEventListener("storage", onStorage);
            window.addEventListener("pagehide", onPageHide);
            localStorage.setItem(requestKey, JSON.stringify({ requestId, sessionId: String(sessionId), action, approvalId, createdAt: Date.now() }));
        });
    }

    function getSession() {
        try {
            let session = JSON.parse(sessionStorage.getItem("marqueza_usuario_sesion") || "null");
            if (!session) {
                const legacySession = JSON.parse(localStorage.getItem("marqueza_usuario_sesion") || "null");
                if (legacySession?.id && sessionStorage.getItem("marqueza_sesion_activa") === String(legacySession.id)) {
                    session = legacySession;
                    sessionStorage.setItem("marqueza_usuario_sesion", JSON.stringify(session));
                }
            }
            return session && typeof session === "object" ? session : null;
        } catch {
            return null;
        }
    }

    function hasActiveSession() {
        const session = getSession();
        if (!session?.id) return false;
        try {
            return sessionStorage.getItem("marqueza_sesion_activa") === String(session.id);
        } catch {
            return false;
        }
    }

    function isPublicAccessPage() {
        const path = decodeURIComponent(window.location.pathname);
        return /\/(?:inicio_sesion\/inicio_sesion|olvido_contrasena\/(?:recuperar|restablecer))\.html$/.test(path);
    }

    function read() {
        try {
            const events = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
            return Array.isArray(events) ? events : [];
        } catch {
            return [];
        }
    }

    function saveLocal(events) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(events.slice(0, MAX_EVENTS)));
        } catch (error) {
            console.error("No fue posible guardar el evento de auditoría.", error);
        }
    }

    function readPending() {
        try {
            const pending = JSON.parse(localStorage.getItem(PENDING_KEY) || "[]");
            return Array.isArray(pending) ? pending : [];
        } catch (error) {
            console.error("No fue posible leer la cola de auditoría pendiente.", error);
            return [];
        }
    }

    async function syncPending() {
        const api = window.MarquezaApi;
        if (!api) return;
        try {
            if (!api.sessionToken()) return;
        } catch (error) {
            console.error("No se pudo validar la sesión para sincronizar la bitácora.", error);
            return;
        }
        if (syncTask) return syncTask;

        syncTask = (async () => {
            try {
                if (localStorage.getItem(PENDING_KEY) === null) {
                    localStorage.setItem(PENDING_KEY, JSON.stringify(read()));
                }

                let pending = readPending();
                while (pending.length) {
                    const batch = pending.slice(0, 10);
                    const settled = await Promise.allSettled(batch.map((event) =>
                        api.request("/bitacora-auditoria/", {
                            method: "POST",
                            body: JSON.stringify(event),
                            suppressSessionRedirect: true
                        })
                    ));
                    const completedIds = new Set(
                        settled.flatMap((result, index) => {
                            if (result.status === "fulfilled") return [batch[index].id];
                            console.warn("No se pudo sincronizar un evento de auditoría.", result.reason);
                            return [];
                        })
                    );
                    pending = readPending().filter((event) => !completedIds.has(event.id));
                    localStorage.setItem(PENDING_KEY, JSON.stringify(pending));
                    if (!completedIds.size) break;
                }
            } catch (error) {
                console.warn("La bitácora central no está disponible; los eventos quedan pendientes.", error);
            }
        })().finally(() => {
            syncTask = null;
        });
        return syncTask;
    }

    function normalizeEvent(event) {
        return {
            id: String(event.uuid || event.id || `${event.timestamp}-${event.action}`),
            timestamp: event.timestamp || event.fecha_hora || "",
            actor: event.actor || "Sin identificar",
            email: event.email || event.correo || "",
            role: event.role || event.rol || "",
            action: event.action || event.accion || "Actividad",
            module: event.module || event.modulo || "Sistema",
            entity: event.entity || event.entidad || "",
            detail: event.detail || event.detalle || "",
            outcome: event.outcome || event.resultado || "success"
        };
    }

    function mergeEvents(...eventLists) {
        const uniqueEvents = new Map();
        eventLists.flat().forEach((rawEvent) => {
            const event = normalizeEvent(rawEvent);
            const key = event.id || [event.timestamp, event.actor, event.action, event.module].join("|");
            uniqueEvents.set(key, event);
        });
        return [...uniqueEvents.values()].sort((first, second) =>
            new Date(second.timestamp).getTime() - new Date(first.timestamp).getTime()
        );
    }

    async function loadAll() {
        const localEvents = read();
        if (!window.MarquezaApi?.sessionToken()) return localEvents.map(normalizeEvent);

        await syncPending();
        const serverEvents = await window.MarquezaApi.request("/bitacora-auditoria/", {
            suppressSessionRedirect: true
        });
        if (!Array.isArray(serverEvents)) {
            throw new Error("La respuesta de la bitácora central no es válida.");
        }
        const events = mergeEvents(serverEvents, read());
        saveLocal(events);
        return events;
    }

    function log({ action, module = "Sistema", entity = "", detail = "", outcome = "success", actor, email, role }) {
        const session = getSession();
        const event = {
            id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            timestamp: new Date().toISOString(),
            actor: actor || session?.nombre || "Sin identificar",
            email: email ?? session?.correo ?? "",
            role: role ?? session?.rol ?? "",
            action,
            module,
            entity,
            detail,
            outcome
        };

        try {
            saveLocal([event, ...read()]);
            const pending = readPending();
            localStorage.setItem(PENDING_KEY, JSON.stringify([event, ...pending]));
        } catch (error) {
            console.error("No fue posible guardar el evento de auditoría.", error);
        }
        window.dispatchEvent(new CustomEvent("marqueza:audit", { detail: event }));
        void syncPending();
        return event;
    }

    function entityName(record) {
        if (!record || typeof record !== "object") return "Registro";
        const value = record.nombre || record.empresa || record.cliente || record.producto || record.codigo || record.documento || record.correo;
        return String(value || "Registro").slice(0, 120);
    }

    function recordChange(action, module, record) {
        const labels = { create: "Registro creado", update: "Registro actualizado", delete: "Registro eliminado" };
        const entity = entityName(record);
        return log({ action: labels[action] || action, module: moduleLabel(module), entity, detail: `${labels[action] || action}: ${entity}` });
    }

    function moduleLabel(module) {
        return String(module || "Sistema").replace(/^marqueza_/, "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
    }

    function guardPage() {
        if (isPublicAccessPage()) return;
        if (hasActiveSession()) {
            const session = getSession();
            if (isActiveInAnotherTab(session.id)) {
                sessionStorage.removeItem("marqueza_usuario_sesion");
                sessionStorage.removeItem("marqueza_sesion_activa");
                redirectToLoginForActiveSession();
                return;
            }
            startSessionHeartbeat(session);
            return;
        }
        const path = `${window.location.pathname}${window.location.search}`;
        log({ action: "Acceso denegado", module: "Acceso", entity: "Sesión requerida", detail: `Intento de acceso sin sesión a ${path}`, outcome: "denied" });
        window.location.replace("../inicio_sesion/inicio_sesion.html?motivo=sesion_requerida");
    }

    window.MarquezaAudit = {
        log,
        read,
        loadAll,
        recordChange,
        guardPage,
        syncPending,
        preflightSession,
        reserveSession: async (sessionId, transferApproval = null) => {
            const normalizedSessionId = String(sessionId);
            const reserve = () => {
                const activeTab = readSessionTab(normalizedSessionId);
                if (isSessionTabActive(activeTab) && activeTab.tabId !== getTabId()) return false;
                writeSessionTab(normalizedSessionId);
                return true;
            };
            const tryReserve = () => navigator.locks?.request
                ? navigator.locks.request(`marqueza-session-reservation-${encodeURIComponent(normalizedSessionId)}`, reserve)
                : Promise.resolve(reserve());
            if (await tryReserve()) return true;

            const activeTab = readSessionTab(normalizedSessionId);
            if (!isSessionTabActive(activeTab) || activeTab.tabId === getTabId()) return tryReserve();
            const response = transferApproval?.sessionId === normalizedSessionId
                ? await requestSessionTransfer(normalizedSessionId, "commit", transferApproval.approvalId)
                : await requestSessionTransfer(normalizedSessionId);
            if (!response.approved) return false;
            return tryReserve();
        },
        activateSession: (session) => {
            const sessionId = session?.id ?? session;
            const activeTab = readSessionTab(sessionId);
            if (activeTab?.tabId !== getTabId()) return false;
            sessionStorage.setItem("marqueza_sesion_activa", String(sessionId));
            startSessionHeartbeat(session);
            return true;
        },
        releaseSession,
        showActiveElsewhereAlert
    };
    window.addEventListener("storage", (event) => {
        if (!event.key?.startsWith(SESSION_TAB_PREFIX) || !hasActiveSession()) return;
        const session = getSession();
        if (event.key !== sessionTabKey(session.id) || !isActiveInAnotherTab(session.id)) return;
        sessionStorage.removeItem("marqueza_usuario_sesion");
        sessionStorage.removeItem("marqueza_sesion_activa");
        clearInterval(sessionHeartbeat);
        sessionHeartbeat = null;
        redirectToLoginForActiveSession();
    });
    window.addEventListener("storage", (event) => {
        if (!event.key?.startsWith(SESSION_TRANSFER_REQUEST_PREFIX) || !event.newValue) return;
        try {
            const request = JSON.parse(event.newValue);
            if (request?.requestId && request?.sessionId && event.key === `${SESSION_TRANSFER_REQUEST_PREFIX}${request.requestId}`) {
                void handleSessionTransferRequest(request.requestId);
            }
        } catch (error) {
            console.error("No se pudo leer la solicitud de cierre de sesión.", error);
        }
    });
    window.addEventListener("error", (event) => {
        const page = window.location.pathname.split("/").filter(Boolean).at(-2) || "Aplicación";
        log({ action: "Error de aplicación", module: moduleLabel(page), detail: String(event.message || "Error JavaScript").slice(0, 300), outcome: "error" });
    });
    window.addEventListener("unhandledrejection", (event) => {
        const reason = event.reason;
        const message = reason instanceof Error ? reason.message : String(reason || "Promesa rechazada");
        const page = window.location.pathname.split("/").filter(Boolean).at(-2) || "Aplicación";
        log({ action: "Error de aplicación", module: moduleLabel(page), detail: message.slice(0, 300), outcome: "error" });
    });
    guardPage();
})();