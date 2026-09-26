/* ============================================================
   usuarios.js  —  MARQUEZA
   Maneja:
     • Toggle lateral (desktop ≥ 1025 px): Expande/colapsa la barra lateral.
     • Hamburger + menú desplegable (tablet / móvil ≤ 1024 px): Controla la barra superior responsive.
     • Drag lateral (solo desktop): Permite arrastrar la barra lateral para colapsarla.
     • Modo oscuro / claro: Cambia el tema visual de la aplicación.
    • Gestión de Usuarios: CRUD (Crear, Leer, Actualizar, Eliminar) usando la API.
   ============================================================ */

// --- Selección de elementos del DOM para la interfaz general ---
const body = document.querySelector("body");
const sidebar = body.querySelector(".barra_lateral");
const toggle = body.querySelector(".toggle");
const hamburger = document.getElementById("hamburger");
const modeSwitch = body.querySelector(".toggle_switch");
const modeText = body.querySelector(".modo_texto");

/**
 * Detecta si la ventana tiene un ancho de tablet o móvil (<= 1024px).
 * @returns {boolean} True si es vista móvil/tablet.
 */
const isTopbar = () => window.innerWidth <= 1024;

/* ─────────────────────────────────────────────────────────
   MODO OSCURO / CLARO
   ───────────────────────────────────────────────────────── */
modeSwitch.addEventListener("click", () => {
    body.classList.toggle("dark");
    modeText.innerText = body.classList.contains("dark") ? "Claro" : "Oscuro";
});

/**
 * Ajusta el espaciado del body (padding) dependiendo de si la barra lateral 
 * está expandida, colapsada o en modo superior (móvil).
 */
function updateLayout() {
    // Si estamos en modo topbar (tablet/móvil)
    if (isTopbar()) {
        body.classList.remove("sidebar-collapsed");
        body.style.paddingLeft = "0";
        // requestAnimationFrame asegura que el cálculo se haga después del renderizado del navegador
        requestAnimationFrame(() => {
            body.style.paddingTop = `${sidebar.getBoundingClientRect().height}px`;
        });
    } else {
        body.style.paddingTop = "0";
        if (sidebar.classList.contains("close")) {
            body.classList.add("sidebar-collapsed");
            body.style.paddingLeft = "88px";
        } else {
            body.classList.remove("sidebar-collapsed");
            body.style.paddingLeft = "250px";
        }
    }
}

updateLayout();

/* ─────────────────────────────────────────────────────────
   DESKTOP — toggle lateral (flecha)
   ───────────────────────────────────────────────────────── */
toggle.addEventListener("click", () => {
    if (isTopbar()) return; // Ignorar en móvil
    sidebar.classList.toggle("close");
    updateLayout();
});

/* ─────────────────────────────────────────────────────────
   TABLET / MÓVIL — hamburger → despliega/colapsa topbar
   ───────────────────────────────────────────────────────── */
/**
 * Abre o cierra el menú desplegable en dispositivos móviles.
 */
function toggleMobileMenu() {
    const isOpen = sidebar.classList.toggle("open");

    if (isOpen) {
        sidebar.classList.remove("close");
    } else {
        sidebar.classList.add("close");
    }

    updateLayout();

    setTimeout(() => {
        if (isTopbar()) {
            body.style.paddingTop = `${sidebar.getBoundingClientRect().height}px`;
        }
    }, 450);
}

hamburger.addEventListener("click", toggleMobileMenu);

hamburger.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        toggleMobileMenu();
    }
});

// Cerrar menú al seleccionar una opción (útil en móvil)
sidebar.querySelectorAll(".nav_links a").forEach(link => {
    link.addEventListener("click", () => {
        if (isTopbar() && sidebar.classList.contains("open")) {
            toggleMobileMenu();
        }
    });
});

/* ─────────────────────────────────────────────────────────
   RESIZE — sincronizar estado al cambiar tamaño de ventana
   ───────────────────────────────────────────────────────── */
let resizeTimer;
window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        if (!isTopbar()) {
            sidebar.classList.remove("open");
            // En desktop, preferimos que inicie colapsada
            if (!sidebar.classList.contains("close")) {
                sidebar.classList.add("close");
            }
            sidebar.style.left = ""; // Limpiar cualquier posición residual del drag
        }
        updateLayout();
    }, 100);
});

/* ─────────────────────────────────────────────────────────
   DESKTOP — arrastrar barra lateral con el mouse
   ───────────────────────────────────────────────────────── */
let isDragging = false;
let dragStartX = 0; 
let sidebarStartLeft = 0; 

// Inicia el arrastre si se hace clic en el header
sidebar.addEventListener("mousedown", (event) => {
    if (isTopbar()) return; 
    if (event.target.closest(".toggle")) return; 
    // Si el click es en el header de la barra lateral
    if (event.target.closest("header")) {
        isDragging = true;
        dragStartX = event.clientX;
        sidebarStartLeft = sidebar.getBoundingClientRect().left;
        sidebar.classList.add("dragging");
    }
});

// Mueve la barra mientras se arrastra el mouse
document.addEventListener("mousemove", (event) => {
    if (!isDragging) return;

    const deltaX = event.clientX - dragStartX;
    let nextLeft = sidebarStartLeft + deltaX;
    
    // Define los límites de arrastre para la barra lateral
    const sidebarWidth = sidebar.offsetWidth;
    const minLeft = -sidebarWidth + 40;
    const maxLeft = 0;

    nextLeft = Math.max(minLeft, Math.min(maxLeft, nextLeft));
    sidebar.style.left = `${nextLeft}px`;
});

// Suelta la barra y decide si colapsar o expandir
document.addEventListener("mouseup", () => {
    if (!isDragging) return;
    isDragging = false;
    sidebar.classList.remove("dragging");

    if (sidebar.getBoundingClientRect().left < -sidebar.offsetWidth / 2) {
        sidebar.classList.add("close");
    } else {
        sidebar.classList.remove("close");
    }

    sidebar.style.left = "0";
    updateLayout();
});

sidebar.addEventListener("mouseleave", () => {
    if (isDragging) {
        isDragging = false;
        sidebar.classList.remove("dragging");
        sidebar.style.left = "0";
    }
});

/* ─────────────────────────────────────────────────────────
   GESTIÓN DE USUARIOS CON LOCAL STORAGE
   ───────────────────────────────────────────────────────── */

// --- Constantes y Selectores para la gestión de usuarios ---
const STORAGE_KEY = 'marqueza_usuarios';
const tableBody = document.querySelector(".cont_tabla tbody");
const btnAgregar = document.querySelector(".agregar");
const searchInput = document.querySelector(".cont_busqueda input");
const btnBuscar = document.querySelector(".cont_busqueda button:not(.agregar)");
const modalUsuario = document.getElementById("modalUsuario"); // Modal Agregar
const formUsuario = document.getElementById("formUsuario");
const btnCerrarModal = document.getElementById("cerrarModal");
const btnCancelar = document.getElementById("btnCancelar");
const modalEditarUsuario = document.getElementById("modalEditarUsuario");
const formEditarUsuario = document.getElementById("formEditarUsuario");
const btnCerrarEditModal = document.getElementById("cerrarEditModal");
const btnCancelarEdit = document.getElementById("btnCancelarEdit");

let usuarios = [];
let roles = [];
const getUsuarios = () => usuarios;

const cargarUsuarios = async () => {
    try {
        const [rows, details] = await Promise.all([
            window.MarquezaApi.get("/usuarios/"),
            window.MarquezaApi.get("/detalles-etc/")
        ]);
        roles = details;
        const roleNames = new Map(details.map(item => [Number(item.id), item.nombre]));
        usuarios = rows.map(user => ({ ...user, rol: roleNames.get(Number(user.det_etc_id)) || "Sin rol" }));
        renderTabla(searchInput?.value || "");
    } catch (error) {
        Swal.fire({ icon: "error", title: "No se pudieron cargar los usuarios", text: error.message });
    }
};

/**
 * Limpia y vuelve a generar las filas de la tabla basadas en los usuarios almacenados.
 * Soporta filtrado por texto.
 * @param {string} filtro - Texto para buscar en nombre o correo.
 */
const renderTabla = (filtro = "") => {
    if (!tableBody) return;
    // Conservamos el índice de la respuesta para resolver el ID al operar.
    const registros = getUsuarios();
    let usuarios = registros.map((u, i) => ({ ...u, originalIndex: i }));

    // Lógica de filtrado
    if (filtro) {
        const termino = filtro.toLowerCase();
        usuarios = usuarios.filter(u =>
            String(u.nombre || "").toLowerCase().includes(termino) ||
            String(u.correo || "").toLowerCase().includes(termino)
        );
    }

    tableBody.innerHTML = ""; 

    const emptyState = document.querySelector(".empty-state");
    if (emptyState) emptyState.style.display = usuarios.length ? "none" : "block";
    updateSummary(registros, usuarios);

    usuarios.forEach((usuario) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${usuario.nombre}</td>
            <td>${usuario.correo}</td>
            <td>${usuario.rol}</td>
            <td>********</td>
            <td><button type="button" class="btn-editar" data-index="${usuario.originalIndex}" title="Editar" aria-label="Editar"><i class="bx bx-pencil" aria-hidden="true"></i></button></td>
            <td><button type="button" class="btn-eliminar" data-index="${usuario.originalIndex}" title="Eliminar" aria-label="Eliminar"><i class="bx bx-trash-alt" aria-hidden="true"></i></button></td>
        `;
        tableBody.appendChild(tr);
    });
};

const updateSummary = (registros, visibles) => {
    const setText = (id, value) => {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    };
    const administradores = registros.filter(usuario => String(usuario.rol).toLowerCase().includes("admin")).length;
    const empleados = registros.length - administradores;
    const correos = registros.filter(usuario => String(usuario.correo || "").trim()).length;
    setText("totalUsuarios", registros.length);
    setText("administradoresUsuarios", administradores);
    setText("empleadosUsuarios", empleados);
    setText("correosUsuarios", `${registros.length ? Math.round((correos / registros.length) * 100) : 0}%`);
    setText("resultadosUsuarios", `${visibles.length} ${visibles.length === 1 ? "resultado" : "resultados"}`);
};

// --- Listeners para Búsqueda ---
btnBuscar?.addEventListener("click", () => renderTabla(searchInput.value));

// Búsqueda en tiempo real mientras el usuario escribe
searchInput?.addEventListener("input", () => renderTabla(searchInput.value));

tableBody?.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-index]");
    if (!button) return;
    const index = Number(button.dataset.index);
    if (button.classList.contains("btn-editar")) editarUsuario(index);
    if (button.classList.contains("btn-eliminar")) eliminarUsuario(index);
});

// --- Control del Modal de Agregar ---
btnAgregar?.addEventListener("click", () => {
    modalUsuario.style.display = "flex";
    document.getElementById("nombre").focus();
});

// Función para cerrar el modal
const cerrarModal = () => {
    modalUsuario.style.display = "none";
    formUsuario.reset();
};

// Función para cerrar el modal de edición
const cerrarEditModal = () => {
    modalEditarUsuario.style.display = "none";
    formEditarUsuario.reset();
};

btnCerrarModal?.addEventListener("click", cerrarModal);
btnCancelar?.addEventListener("click", cerrarModal);
btnCerrarEditModal?.addEventListener("click", cerrarEditModal);
btnCancelarEdit?.addEventListener("click", cerrarEditModal);

// Cerrar modales si se hace clic en el fondo oscuro
window.addEventListener("click", (e) => {
    if (e.target === modalUsuario) {
        cerrarModal();
    } else if (e.target === modalEditarUsuario) {
        cerrarEditModal();
    }
});

// --- Lógica de Guardado (Nuevo Usuario) ---
formUsuario?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const nombre = document.getElementById("nombre").value.trim();
    const correo = document.getElementById("correo").value.trim();
    const rol = document.getElementById("rol").value;
    const contrasena = document.getElementById("contrasena").value;
    const confirmarContrasena = document.getElementById("confirmarContrasena").value;

    // Validación de coincidencia de contraseñas
    if (contrasena !== confirmarContrasena) {
        Swal.fire({
            icon: 'error',
            title: 'Error de validación',
            text: 'Las contraseñas no coinciden. Por favor, verifícalas.',
            confirmButtonColor: '#27B7F5',
            customClass: {
                container: 'swal-above-modal' // Clase personalizada para asegurar que esté encima
            }
        });
        return;
    }
    if (contrasena.length > 45) {
        Swal.fire({ icon: "warning", title: "Contraseña muy larga", text: "La base de datos actual admite hasta 45 caracteres." });
        return;
    }

    const usuarios = getUsuarios();

    // Validar longitud del nombre
    if (nombre.length < 3) {
        Swal.fire({
            icon: 'warning',
            title: 'Nombre muy corto',
            text: 'El nombre debe tener al menos 3 caracteres.',
            confirmButtonColor: '#27B7F5',
            customClass: {
                container: 'swal-above-modal'
            }
        });
        return;
    }

    // Verificar si el usuario ya existe por correo electrónico
    if (usuarios.some(u => u.correo === correo)) {
        Swal.fire({
            icon: 'error',
            title: 'Usuario ya registrado',
            text: 'El correo electrónico ingresado ya se encuentra en uso por otro usuario.',
            confirmButtonColor: '#27B7F5',
            customClass: {
                container: 'swal-above-modal'
            }
        });
        return;
    }

    const role = roles.find(item => String(item.nombre).toLowerCase() === rol.toLowerCase());
    if (!role) {
        Swal.fire({ icon: "error", title: "Rol no disponible", text: "Selecciona un rol configurado en la base de datos." });
        return;
    }
    try {
        await window.MarquezaApi.post("/usuarios/", { nombre, correo, contrasena, estado: "Activo", det_etc_id: role.id });
        window.MarquezaAudit?.recordChange("create", STORAGE_KEY, { nombre, correo, rol });
        await cargarUsuarios();
        cerrarModal();
        Swal.fire('¡Guardado!', 'El usuario se creó en la base de datos.', 'success');
    } catch (error) {
        Swal.fire({ icon: "error", title: "No se pudo guardar", text: error.message });
    }
});

// --- Lógica de Actualización (Editar Usuario) ---
formEditarUsuario?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const index = document.getElementById("editIndex").value;
    const nombre = document.getElementById("editNombre").value.trim();
    const correo = document.getElementById("editCorreo").value.trim();
    const rol = document.getElementById("editRol").value;
    const nuevaPass = document.getElementById("editContrasena").value;

    const usuarios = getUsuarios();

    // Verificar si el nuevo nombre ya existe en otro usuario
    if (usuarios.some((u, i) => u.nombre.toLowerCase() === nombre.toLowerCase() && i != index)) {
        Swal.fire({
            icon: 'error',
            title: 'Nombre en uso',
            text: 'Este nombre de usuario ya pertenece a otra persona.',
            confirmButtonColor: '#27B7F5',
            customClass: {
                container: 'swal-above-modal'
            }
        });
        return;
    }

    // Verificar si el nuevo correo ya existe en otro usuario (excluyendo al actual)
    if (usuarios.some((u, i) => u.correo === correo && i != index)) {
        Swal.fire({
            icon: 'error',
            title: 'Correo en uso',
            text: 'Este correo electrónico ya pertenece a otro usuario registrado.',
            confirmButtonColor: '#27B7F5',
            customClass: {
                container: 'swal-above-modal'
            }
        });
        return;
    }

    const usuarioActual = usuarios[index];

    const role = roles.find(item => String(item.nombre).toLowerCase() === rol.toLowerCase());
    if (!role) {
        Swal.fire({ icon: "error", title: "Rol no disponible", text: "Selecciona un rol configurado en la base de datos." });
        return;
    }
    if (nuevaPass && nuevaPass.length > 45) {
        Swal.fire({ icon: "warning", title: "Contraseña muy larga", text: "La base de datos actual admite hasta 45 caracteres." });
        return;
    }
    const payload = { nombre, correo, estado: usuarioActual.estado || "Activo", det_etc_id: role.id };
    if (nuevaPass) payload.contrasena = nuevaPass;
    try {
        await window.MarquezaApi.put(`/usuarios/${usuarioActual.id}`, payload);
        window.MarquezaAudit?.recordChange("update", STORAGE_KEY, { nombre, correo, rol });
        await cargarUsuarios();
        cerrarEditModal();
        Swal.fire('¡Actualizado!', 'Los cambios se guardaron en la base de datos.', 'success');
    } catch (error) {
        Swal.fire({ icon: "error", title: "No se pudo actualizar", text: error.message });
    }
});

// Función global para editar usuarios
window.editarUsuario = (index) => {
    const usuarios = getUsuarios();
    const usuario = usuarios[index];

    // Llenar el formulario del modal de edición
    document.getElementById("editIndex").value = index;
    document.getElementById("editNombre").value = usuario.nombre;
    document.getElementById("editCorreo").value = usuario.correo;
    document.getElementById("editRol").value = usuario.rol;
    document.getElementById("editContrasena").value = ""; 

    // Mostrar el modal
    modalEditarUsuario.style.display = "flex";
    document.getElementById("editNombre").focus();
};

// Función global para eliminar usuarios (necesaria para el atributo onclick)
window.eliminarUsuario = (index) => {
    Swal.fire({
        title: '¿Estás seguro?',
        text: "Esta acción no se puede deshacer",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e74c3c',
        cancelButtonColor: '#707070',
        confirmButtonText: 'Eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            const usuario = getUsuarios()[index];
            window.MarquezaApi.delete(`/usuarios/${usuario.id}`).then(async () => {
                window.MarquezaAudit?.recordChange("delete", STORAGE_KEY, { nombre: usuario.nombre, correo: usuario.correo });
                await cargarUsuarios();
                Swal.fire('¡Eliminado!', 'El usuario se eliminó de la base de datos.', 'success');
            }).catch(error => Swal.fire({ icon: "error", title: "No se pudo eliminar", text: error.message }));
        }
    });
};

cargarUsuarios();

// Inicializar la tabla al cargar el script
renderTabla();
window.MarquezaRealtime?.subscribe(({ key }) => {
    if (key === STORAGE_KEY) renderTabla(searchInput.value);
});