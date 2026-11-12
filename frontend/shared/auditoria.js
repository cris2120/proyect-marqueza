(function () {
    const STORAGE_KEY = "marqueza_bitacora";
    const PENDING_KEY = "marqueza_bitacora_pendientes";
    const MAX_EVENTS = 500;
    let syncTask = null;

    function getSession() {
        try {
            let storedSession = sessionStorage.getItem("marqueza_usuario_sesion");
            if (!storedSession) {
                const legacySession = localStorage.getItem("marqueza_usuario_sesion");
                const parsedLegacySession = JSON.parse(legacySession || "null");
                if (
                    parsedLegacySession?.id
                    && sessionStorage.getItem("marqueza_sesion_activa") === String(parsedLegacySession.id)
                ) {
                    storedSession = legacySession;
                    sessionStorage.setItem("marqueza_usuario_sesion", legacySession);
                    localStorage.removeItem("marqueza_usuario_sesion");
                }
            }
            const session = JSON.parse(storedSession || "null");
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
        if (isPublicAccessPage() || hasActiveSession()) return;
        const path = `${window.location.pathname}${window.location.search}`;
        log({ action: "Acceso denegado", module: "Acceso", entity: "Sesión requerida", detail: `Intento de acceso sin sesión a ${path}`, outcome: "denied" });
        window.location.replace("../inicio_sesion/inicio_sesion.html");
    }

    window.MarquezaAudit = { log, read, loadAll, recordChange, guardPage, syncPending };
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