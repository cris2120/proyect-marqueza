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

        const button = this.formulario.querySelector("button[type='submit']");
        if (button) button.disabled = true;
        try {
            const result = await window.MarquezaApi.post("/auth/login", { usuario: username, contrasena: password });
            const user = result.usuario;
            const details = await window.MarquezaApi.get("/detalles-etc/");
            const role = details.find(item => Number(item.id) === Number(user.det_etc_id))?.nombre || "Usuario";
            localStorage.setItem("marqueza_usuario_sesion", JSON.stringify({ id: user.id, nombre: user.nombre, correo: user.correo, rol: role }));
            window.MarquezaAudit?.log({ action: "Inicio de sesión", module: "Acceso", detail: "Inicio de sesión autorizado." });
            await Swal.fire({ title: "Inicio de sesión exitoso", icon: "success", text: `Bienvenido ${user.nombre}` });
            window.location.href = "../inicio/inicio.html";
        } catch (error) {
            window.MarquezaAudit?.log({ action: "Inicio de sesión rechazado", module: "Acceso", entity: username, detail: "La API rechazó las credenciales.", outcome: "denied", actor: username });
            Swal.fire({ icon: "error", title: "No se pudo iniciar sesión", text: error.message });
        } finally {
            if (button) button.disabled = false;
        }
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
