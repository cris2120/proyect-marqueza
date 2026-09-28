class LoginForm {
    constructor(formulario) {
        this.formulario = formulario;
        this.username = formulario.querySelector("#usuario");
        this.password = formulario.querySelector("#contraseña");
    }

    init() {
        this.formulario.addEventListener("submit", (event) => this.submit(event));
    }

    async submit(event) {
        event.preventDefault();
        const username = this.username?.value.trim() || "";
        const password = this.password?.value || "";

        if (!username || !password) {
            return Swal.fire({ icon: "warning", title: "Campos incompletos", text: "Por favor completa todos los campos." });
        }

        let user;
        try {
            user = await window.MarquezaApi.login(username, password);
            window.MarquezaAudit?.log({ action: "Inicio de sesión", module: "Acceso", detail: "Inicio de sesión autorizado." });
        } catch (error) {
            window.MarquezaAudit?.log({ action: "Inicio de sesión rechazado", module: "Acceso", entity: username, detail: error.message, outcome: "denied", actor: username });
            return window.MarquezaApi.notifyError(error, "No se pudo iniciar sesión");
        }
        Swal.fire({
            title: "Inicio de sesión exitoso",
            icon: "success",
            text: `Bienvenido ${user.nombre}`
        }).then(() => {
            window.location.href = "../inicio/inicio.html";
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const formulario = document.getElementById("formulario");
    if (formulario) new LoginForm(formulario).init();
    if (new URLSearchParams(window.location.search).get("motivo") === "sesion_requerida") {
        window.Swal?.fire({ icon: "warning", title: "Inicia sesión", text: "Necesitas una sesión activa para entrar a esa sección." });
        window.history.replaceState({}, "", window.location.pathname);
    }
});
