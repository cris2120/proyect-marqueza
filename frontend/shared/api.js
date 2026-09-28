(function () {
    const API_BASE = (window.MARQUEZA_API_BASE_URL || "/api").replace(/\/+$/, "");
    const DATA_KEYS = [
        "marqueza_clientes",
        "marqueza_proveedores",
        "marqueza_productos",
        "marqueza_insumos",
        "marqueza_ventas",
        "marqueza_cotizaciones"
    ];
    const originalSetItem = Storage.prototype.setItem;
    const pendingWrites = new Map();
    const collectionVersions = new Map();
    let syncing = false;
    let readyToSync = false;
    let syncErrorShown = false;

    const readJson = (key, fallback = null) => {
        try {
            return JSON.parse(localStorage.getItem(key) || "null") ?? fallback;
        } catch {
            return fallback;
        }
    };

    const currentSession = () => readJson("marqueza_usuario_sesion");

    async function request(path, options = {}) {
        const session = currentSession();
        const headers = new Headers(options.headers || {});
        if (options.body !== undefined) headers.set("Content-Type", "application/json");
        if (session?.token) headers.set("Authorization", `Bearer ${session.token}`);
        let response;
        try {
            response = await fetch(`${API_BASE}/${path.replace(/^\/+/, "")}`, { ...options, headers });
        } catch {
            throw new Error("No se pudo conectar con la API de MARQUEZA.");
        }
        const text = await response.text();
        let payload = null;
        if (text) {
            try {
                payload = JSON.parse(text);
            } catch {
                payload = { detail: text };
            }
        }
        if (!response.ok) {
            const error = new Error(payload?.detail || payload?.message || `Error HTTP ${response.status}`);
            error.status = response.status;
            if (response.status === 401 && session?.token) {
                localStorage.removeItem("marqueza_usuario_sesion");
                if (document.querySelector(".barra_lateral")) {
                    window.location.replace("../inicio_sesion/inicio_sesion.html?motivo=sesion_requerida");
                }
            }
            throw error;
        }
        return payload;
    }

    function notifyError(error, title = "No se pudo guardar") {
        const message = error instanceof Error ? error.message : String(error);
        if (window.Swal?.fire) return window.Swal.fire({ icon: "error", title, text: message });
        window.alert(`${title}: ${message}`);
        return Promise.resolve();
    }

    function replaceLocal(key, records) {
        syncing = true;
        try {
            localStorage.setItem(key, JSON.stringify(records));
        } finally {
            syncing = false;
        }
    }

    async function writeToServer(key, value, previousValue) {
        let records;
        try {
            records = JSON.parse(value);
        } catch {
            return;
        }
        if (!Array.isArray(records)) return;
        const prior = pendingWrites.get(key) || Promise.resolve();
        const write = prior.catch(() => {}).then(async () => {
            if (key === "marqueza_usuarios") {
                const users = await request("users/sync", { method: "PUT", body: JSON.stringify({ users: records }) });
                replaceLocal(key, users);
            } else {
                const resource = key.replace(/^marqueza_/, "");
                const result = await request(`collections/${resource}`, {
                    method: "PUT",
                    body: JSON.stringify({ records, version: collectionVersions.get(resource) ?? 0 })
                });
                collectionVersions.set(resource, result.version);
            }
        });
        pendingWrites.set(key, write);
        try {
            await write;
        } catch (error) {
            if (localStorage.getItem(key) === value) {
                syncing = true;
                try {
                    if (previousValue === null) localStorage.removeItem(key);
                    else originalSetItem.call(localStorage, key, previousValue);
                } finally {
                    syncing = false;
                }
            }
            notifyError(error);
        } finally {
            if (pendingWrites.get(key) === write) pendingWrites.delete(key);
        }
    }

    Storage.prototype.setItem = function (key, value) {
        const previousValue = this === window.localStorage ? this.getItem(String(key)) : null;
        const result = originalSetItem.call(this, key, value);
        if (this === window.localStorage && !syncing && readyToSync && currentSession()?.token) {
            const normalizedKey = String(key);
            if (DATA_KEYS.includes(normalizedKey) || normalizedKey === "marqueza_usuarios") {
                void writeToServer(normalizedKey, String(value), previousValue);
            }
        }
        return result;
    };

    async function refreshCollection(key) {
        const resource = key.replace(/^marqueza_/, "");
        const remote = await request(`collections/${resource}`);
        collectionVersions.set(resource, remote.version);
        let records = remote.records;
        const localRecords = readJson(key, []);
        if (!records.length && localRecords.length && currentSession()?.rol === "Administrador") {
            const result = await request(`collections/${resource}`, {
                method: "PUT",
                body: JSON.stringify({ records: localRecords, version: remote.version })
            });
            collectionVersions.set(resource, result.version);
            records = localRecords;
        }
        if (JSON.stringify(records) !== JSON.stringify(localRecords)) replaceLocal(key, records);
    }

    async function refreshUsers() {
        let users = await request("users");
        const localUsers = readJson("marqueza_usuarios", []);
        const legacyUsers = localUsers.filter(user => !user.protegido && String(user.nombre || "").trim().toLowerCase() !== "admin");
        if (users.length === 1 && legacyUsers.length && currentSession()?.rol === "Administrador") {
            users = await request("users/sync", { method: "PUT", body: JSON.stringify({ users: [...users, ...legacyUsers] }) });
        }
        if (JSON.stringify(users) !== JSON.stringify(localUsers)) replaceLocal("marqueza_usuarios", users);
    }

    async function synchronize() {
        if (!currentSession()?.token) return;
        try {
            const tasks = DATA_KEYS.map(refreshCollection);
            if (currentSession()?.rol === "Administrador") tasks.push(refreshUsers());
            await Promise.all(tasks);
            const events = await request("audit");
            if (JSON.stringify(events) !== JSON.stringify(readJson("marqueza_bitacora", []))) {
                replaceLocal("marqueza_bitacora", events);
                window.dispatchEvent(new CustomEvent("marqueza:audit"));
            }
            readyToSync = true;
            syncErrorShown = false;
        } catch (error) {
            if (!syncErrorShown) notifyError(error, "No se pudieron sincronizar los datos");
            syncErrorShown = true;
        }
    }

    window.MarquezaApi = {
        request,
        async login(usuario, contrasena) {
            const result = await request("auth/login", { method: "POST", body: JSON.stringify({ usuario, contrasena }) });
            const session = { ...result.usuario, token: result.access_token };
            originalSetItem.call(localStorage, "marqueza_usuario_sesion", JSON.stringify(session));
            await synchronize();
            return session;
        },
        register(data) {
            return request("auth/register", { method: "POST", body: JSON.stringify(data) });
        },
        requestPasswordReset(correo) {
            return request("auth/password-reset-requests", { method: "POST", body: JSON.stringify({ correo }) });
        },
        sendAudit(event) {
            if (currentSession()?.token) void request("audit", { method: "POST", body: JSON.stringify(event) }).catch(() => {});
        },
        notifyError,
        synchronize,
        logout() {
            readyToSync = false;
            localStorage.removeItem("marqueza_usuario_sesion");
        }
    };

    document.addEventListener("DOMContentLoaded", () => {
        void synchronize();
        window.addEventListener("focus", () => void synchronize());
        window.setInterval(() => {
            if (document.visibilityState === "visible") void synchronize();
        }, 30000);
    });
})();