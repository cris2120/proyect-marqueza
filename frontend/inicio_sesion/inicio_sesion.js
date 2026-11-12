class LoginForm {
    constructor(formulario) {
        this.formulario = formulario;
        this.username = formulario.querySelector("#usuario");
        this.password = formulario.querySelector("#contraseña");
        this.passwordToggle = formulario.querySelector("#toggle-contrasena");
        this.isSubmitting = false;
    }

    init() {
        this.formulario.addEventListener("submit", (event) => this.submit(event));
        this.passwordToggle?.addEventListener("click", () => this.togglePasswordVisibility());
    }

    togglePasswordVisibility() {
        const isPasswordHidden = this.password.type === "password";
        this.password.type = isPasswordHidden ? "text" : "password";
        this.passwordToggle.setAttribute("aria-label", isPasswordHidden ? "Ocultar contraseña" : "Mostrar contraseña");
        this.passwordToggle.setAttribute("aria-pressed", String(isPasswordHidden));
        this.passwordToggle.querySelector(".password-icon-show").hidden = !isPasswordHidden;
        this.passwordToggle.querySelector(".password-icon-hide").hidden = isPasswordHidden;
    }

    async submit(event) {
        event.preventDefault();
        if (this.isSubmitting) return;

        const username = this.username?.value || "";
        const password = this.password?.value || "";

        if (!username.length || !password.length) {
            return Swal.fire({ icon: "warning", title: "Campos incompletos", text: "Por favor completa todos los campos." });
        }

        this.isSubmitting = true;
        try {
            let result;
            try {
                result = await this.login(username, password);
            } catch (error) {
                if (error.code !== "SESSION_ACTIVE") throw error;
                const approved = await this.requestSessionClosure(error.usuarioId);
                if (!approved) return;
                result = await this.login(username, password);
            }

            const user = result.usuario;
            sessionStorage.setItem("marqueza_usuario_sesion", JSON.stringify({ ...user, token: result.token }));
            localStorage.removeItem("marqueza_usuario_sesion");
            sessionStorage.setItem("marqueza_sesion_activa", String(user.id));
            window.MarquezaAudit?.log({ action: "Inicio de sesión", module: "Acceso", detail: "Inicio de sesión autorizado.", actor: user.nombre, email: user.correo, role: user.rol });
            window.location.replace("../inicio/inicio.html");
        } catch (error) {
            window.MarquezaAudit?.log({ action: "Inicio de sesión rechazado", module: "Acceso", entity: username, detail: error.message, outcome: "denied", actor: username });
            await window.MarquezaApi.notifyError(error, "No se pudo iniciar sesión");
        } finally {
            this.isSubmitting = false;
        }
    }

    login(username, password) {
        return window.MarquezaApi.request("/auth/login", {
            method: "POST",
            body: JSON.stringify({ usuario: username, contrasena: password })
        });
    }

    async requestSessionClosure(usuarioId) {
        const currentSession = JSON.parse(window.MarquezaApi.sessionData() || "null");
        if (String(currentSession?.id) === String(usuarioId)) {
            const result = await window.Swal?.fire({
                icon: "warning",
                title: "Usuario activo en esta pestaña",
                text: "Este usuario ya tiene una sesión abierta aquí. ¿Quieres cerrarla para continuar?",
                showCancelButton: true,
                confirmButtonText: "Sí, cerrar sesión",
                cancelButtonText: "No, mantener sesión"
            });
            if (!result?.isConfirmed) return false;

            await window.MarquezaApi.request("/auth/logout", { method: "POST" });
            sessionStorage.removeItem("marqueza_usuario_sesion");
            sessionStorage.removeItem("marqueza_sesion_activa");
            window.MarquezaAudit?.log({
                action: "Cierre de sesión",
                module: "Acceso",
                detail: "La sesión se cerró desde la pestaña actual para iniciar sesión nuevamente.",
                actor: currentSession.nombre,
                email: currentSession.correo,
                role: currentSession.rol
            });
            return true;
        }

        const requestId = window.crypto?.randomUUID?.()
            || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const responseKey = `marqueza_respuesta_cierre_sesion_${requestId}`;
        const response = this.waitForSessionClosure(responseKey);

        localStorage.setItem("marqueza_solicitud_cierre_sesion", JSON.stringify({
            id: requestId,
            usuarioId,
            createdAt: Date.now()
        }));

        try {
            const result = await response;
            if (result?.approved) return true;
            if (result) {
                await window.Swal?.fire({
                    icon: "info",
                    title: "Sesión conservada",
                    text: "La sesión abierta no se cerró. Puedes volver a intentarlo cuando quede libre."
                });
            } else {
                await window.Swal?.fire({
                    icon: "info",
                    title: "No se encontró una pestaña abierta",
                    text: "El servidor todavía registra una sesión reciente, pero ninguna pestaña respondió. Espera un par de minutos e intenta de nuevo."
                });
            }
            return false;
        } finally {
            const currentRequest = localStorage.getItem("marqueza_solicitud_cierre_sesion");
            try {
                if (JSON.parse(currentRequest || "null")?.id === requestId) {
                    localStorage.removeItem("marqueza_solicitud_cierre_sesion");
                }
            } catch (error) {
                console.error("No fue posible limpiar la solicitud de cierre de sesión.", error);
            }
            localStorage.removeItem(responseKey);
        }
    }

    waitForSessionClosure(responseKey) {
        return new Promise(resolve => {
            let settled = false;
            const finish = result => {
                if (settled) return;
                settled = true;
                window.removeEventListener("storage", onStorage);
                window.clearInterval(pollId);
                window.clearTimeout(timeoutId);
                resolve(result);
            };
            const readResponse = () => {
                const value = localStorage.getItem(responseKey);
                if (!value) return;
                try {
                    finish(JSON.parse(value));
                } catch (error) {
                    console.error("No fue posible leer la respuesta de cierre de sesión.", error);
                }
            };
            const onStorage = event => {
                if (event.key === responseKey) readResponse();
            };
            window.addEventListener("storage", onStorage);
            const pollId = window.setInterval(readResponse, 300);
            const timeoutId = window.setTimeout(() => finish(null), 60000);
            readResponse();
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const formulario = document.getElementById("formulario");
    if (formulario) new LoginForm(formulario).init();
    if (new URLSearchParams(window.location.search).get("motivo") === "sesion_requerida") {
        window.Swal?.fire({ icon: "warning", title: "Inicia sesión", text: "Necesitas una sesión activa para entrar a esa sección." });
        window.history.replaceState({}, "", window.location.pathname);
    } else if (new URLSearchParams(window.location.search).get("motivo") === "servidor_desconectado") {
        window.Swal?.fire({ icon: "warning", title: "Conexión perdida", text: "El servidor dejó de responder. Vuelve a iniciar sesión cuando esté disponible." });
        window.history.replaceState({}, "", window.location.pathname);
    }
});
