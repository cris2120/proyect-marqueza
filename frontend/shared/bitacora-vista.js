(function () {
    const rootSelector = "[data-audit-view]";
    const columns = ["timestamp", "actor", "email", "role", "action", "module", "entity", "detail", "outcome"];
    const fieldLabels = ["Fecha y hora", "Persona", "Correo", "Rol", "Evento", "Módulo", "Registro", "Detalle", "Resultado"];
    const pad = (value) => String(value).padStart(2, "0");

    function localDateKey(value) {
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return "";
        return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
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

    function monthLabel(date) {
        return new Intl.DateTimeFormat("es-CO", { month: "long", year: "numeric" }).format(date);
    }

    function displayDate(value) {
        const date = new Date(value);
        return Number.isNaN(date.getTime())
            ? "Fecha no disponible"
            : new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" }).format(date);
    }

    function mount(root) {
        const showTitle = root.dataset.showTitle === "true";
        const loginOnly = root.dataset.auditMode === "logins";
        root.innerHTML = `
            ${showTitle ? `
                <header class="audit-heading">
                    <div>
                        <span class="audit-eyebrow">Seguridad y seguimiento</span>
                        <h1>Registro de actividad</h1>
                        <p>Consulta los eventos de todos los módulos por fecha.</p>
                    </div>
                </header>
            ` : loginOnly ? `
                <header class="audit-heading audit-heading-compact">
                    <div>
                        <span class="audit-eyebrow">Acceso al sistema</span>
                        <h2>Inicios de sesión</h2>
                        <p>Accesos exitosos registrados para los usuarios.</p>
                    </div>
                </header>
            ` : ""}
            ${loginOnly ? "" : `
            <section class="audit-range" aria-label="Filtrar actividades por rango y módulo">
                <div class="audit-range-heading">
                    <div><span class="audit-eyebrow">Periodo de consulta</span><h2>Filtrar registro</h2></div>
                    <button type="button" class="audit-range-refresh" data-audit-refresh><i class="bx bx-refresh"></i> Actualizar</button>
                </div>
                <div class="audit-range-controls">
                    <label>Fecha inicial<input type="date" data-audit-start></label>
                    <label>Fecha final<input type="date" data-audit-end></label>
                    <label>Módulo
                        <select data-audit-module>
                            <option value="all">Todos los módulos</option>
                        </select>
                    </label>
                    <button type="button" class="audit-range-clear" data-audit-clear><i class="bx bx-x"></i> Limpiar</button>
                </div>
            </section>
            <section class="audit-toolbar" aria-label="Buscar y exportar actividades">
                <label class="audit-search"><i class="bx bx-search" aria-hidden="true"></i><input type="search" data-audit-search placeholder="Buscar en todos los módulos..." aria-label="Buscar en todos los módulos"></label>
                <span class="audit-results" data-audit-results aria-live="polite">0 eventos</span>
                <div class="audit-export-actions" aria-label="Exportar actividades">
                    <button type="button" data-audit-export="csv"><i class="bx bx-spreadsheet"></i> CSV</button>
                    <button type="button" data-audit-export="json"><i class="bx bx-code-alt"></i> JSON</button>
                    <button type="button" data-audit-export="pdf"><i class="bx bxs-file-pdf"></i> PDF</button>
                </div>
            </section>
            <section class="audit-chart-card" aria-label="Actividad por módulo">
                <div class="audit-chart-heading">
                    <div><span class="audit-eyebrow">Línea de tiempo mensual</span><h2>Cambios realizados por módulo</h2></div>
                    <span data-audit-chart-total>0 actividades</span>
                </div>
                <div class="audit-chart" data-audit-chart></div>
                <p class="audit-empty" data-audit-chart-empty hidden>No hay actividad en el rango seleccionado.</p>
            </section>
            `}
            ${loginOnly ? `
            <section class="audit-toolbar" aria-label="Buscar y exportar actividades">
                <label class="audit-search"><i class="bx bx-search" aria-hidden="true"></i><input type="search" data-audit-search placeholder="${loginOnly ? "Buscar usuario, correo o rol..." : "Buscar en todos los módulos..."}" aria-label="${loginOnly ? "Buscar inicios de sesión" : "Buscar en todos los módulos"}"></label>
                <span class="audit-results" data-audit-results aria-live="polite">0 eventos</span>
                <div class="audit-export-actions" aria-label="Exportar actividades">
                    <button type="button" data-audit-export="csv"><i class="bx bx-spreadsheet"></i> CSV</button>
                    <button type="button" data-audit-export="json"><i class="bx bx-code-alt"></i> JSON</button>
                    <button type="button" data-audit-export="pdf"><i class="bx bxs-file-pdf"></i> PDF</button>
                </div>
            </section>
            ` : ""}
            <section class="audit-table-section" aria-label="Actividades de la fecha seleccionada">
                <div class="audit-table-scroll">
                    <table class="audit-table">
                        <thead><tr>${loginOnly
                            ? "<th scope=\"col\">Fecha y hora</th><th scope=\"col\">Usuario</th><th scope=\"col\">Correo</th><th scope=\"col\">Rol</th>"
                            : "<th scope=\"col\">Fecha y hora</th><th scope=\"col\">Persona</th><th scope=\"col\">Evento</th><th scope=\"col\">Módulo</th><th scope=\"col\">Detalle</th>"}</tr></thead>
                        <tbody data-audit-rows></tbody>
                    </table>
                </div>
                <p class="audit-empty" data-audit-empty hidden>No hay actividades para esta fecha.</p>
                <nav class="audit-pagination" aria-label="Paginación del registro" data-audit-pagination hidden>
                    <button type="button" data-audit-page-previous aria-label="Página anterior"><i class="bx bx-chevron-left"></i><span>Anterior</span></button>
                    <span data-audit-page-label aria-live="polite"></span>
                    <button type="button" data-audit-page-next aria-label="Página siguiente"><span>Siguiente</span><i class="bx bx-chevron-right"></i></button>
                </nav>
            </section>
            <p class="audit-note" data-audit-status role="status"><i class="bx bx-info-circle" aria-hidden="true"></i><span>Cargando bitácora...</span></p>
        `;

        const elements = {
            total: root.querySelector("[data-audit-total]"),
            changes: root.querySelector("[data-audit-changes]"),
            denied: root.querySelector("[data-audit-denied]"),
            errors: root.querySelector("[data-audit-errors]"),
            start: root.querySelector("[data-audit-start]"),
            end: root.querySelector("[data-audit-end]"),
            module: root.querySelector("[data-audit-module]"),
            chart: root.querySelector("[data-audit-chart]"),
            chartEmpty: root.querySelector("[data-audit-chart-empty]"),
            chartTotal: root.querySelector("[data-audit-chart-total]"),
            rows: root.querySelector("[data-audit-rows]"),
            empty: root.querySelector("[data-audit-empty]"),
            pagination: root.querySelector("[data-audit-pagination]"),
            previousPage: root.querySelector("[data-audit-page-previous]"),
            nextPage: root.querySelector("[data-audit-page-next]"),
            pageLabel: root.querySelector("[data-audit-page-label]"),
            results: root.querySelector("[data-audit-results]"),
            search: root.querySelector("[data-audit-search]"),
            filter: root.querySelector("[data-audit-filter]"),
            status: root.querySelector("[data-audit-status] span")
        };

        let events = window.MarquezaAudit.read().map(normalizeEvent);
        let currentPage = 1;
        const pageSize = 20;
        const today = new Date();
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
        let selectedStart = localDateKey(firstDay);
        let selectedEnd = localDateKey(today);

        const isChange = (event) => String(event.action).startsWith("Registro ");
        const isAccess = (event) => String(event.module).toLowerCase() === "acceso" || event.outcome === "denied";
        const isError = (event) => event.outcome === "error";
        const isLogin = (event) => String(event.action)
            .trim()
            .toLocaleLowerCase("es")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "") === "inicio de sesion";

        function dayEvents() {
            const query = elements.search.value.trim().toLocaleLowerCase("es");
            const filter = elements.filter?.value || "all";
            const selectedModule = elements.module?.value || "all";
            return events.filter((event) => {
                if (loginOnly) {
                    if (!isLogin(event)) return false;
                } else {
                    const eventDate = localDateKey(event.timestamp);
                    if (!eventDate || eventDate < selectedStart || eventDate > selectedEnd) return false;
                    if (!query && selectedModule !== "all" && event.module !== selectedModule) return false;
                }
                const matchesType = filter === "all" ||
                    (filter === "changes" && isChange(event)) ||
                    (filter === "access" && isAccess(event)) ||
                    (filter === "errors" && isError(event));
                const text = [event.actor, event.email, event.action, event.module, event.entity, event.detail].join(" ").toLocaleLowerCase("es");
                return matchesType && (!query || text.includes(query));
            });
        }

        function renderModuleOptions() {
            if (!elements.module) return;
            const current = elements.module.value || "all";
            const knownModules = [
                "Acceso", "Sistema", "Aplicación", "Inicio", "Insumos", "Productos",
                "Pedidos", "Ventas", "Cotizaciones", "Clientes", "Proveedores", "Usuarios"
            ];
            const modules = [...new Set([
                ...knownModules,
                ...events.map((event) => event.module || "Sistema")
            ])].sort((a, b) => a.localeCompare(b, "es"));
            elements.module.replaceChildren();
            const allOption = document.createElement("option");
            allOption.value = "all";
            allOption.textContent = "Todos los módulos";
            elements.module.appendChild(allOption);
            modules.forEach((module) => {
                const option = document.createElement("option");
                option.value = module;
                option.textContent = module;
                elements.module.appendChild(option);
            });
            elements.module.value = modules.includes(current) ? current : "all";
        }

        function renderChart(filtered) {
            if (!elements.chart) return;
            elements.chart.replaceChildren();
            elements.chart.classList.add("audit-timeline");

            const start = new Date(`${selectedStart}T12:00:00`);
            const end = new Date(`${selectedEnd}T12:00:00`);
            if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
                elements.chartEmpty.hidden = false;
                elements.chartTotal.textContent = "0 actividades";
                return;
            }

            const monthKeys = [];
            const cursor = new Date(start.getFullYear(), start.getMonth(), 1);
            const lastMonth = new Date(end.getFullYear(), end.getMonth(), 1);
            while (cursor <= lastMonth) {
                monthKeys.push(`${cursor.getFullYear()}-${pad(cursor.getMonth() + 1)}`);
                cursor.setMonth(cursor.getMonth() + 1);
            }

            const selectedModule = elements.module?.value || "all";
            const searchActive = Boolean(elements.search?.value.trim());
            const moduleNames = searchActive || selectedModule === "all"
                ? [...new Set(filtered.map((event) => event.module || "Sistema"))].sort((a, b) => a.localeCompare(b, "es"))
                : [selectedModule];

            elements.chartEmpty.hidden = filtered.length > 0;
            elements.chartTotal.textContent = `${filtered.length} ${filtered.length === 1 ? "actividad" : "actividades"}`;
            if (!filtered.length || !moduleNames.length) return;

            const colors = ["#176b86", "#695cff", "#ef8b32", "#16a085", "#d95b78", "#7a6ea8", "#3e8e49"];
            const monthData = new Map(moduleNames.map((module) => [module, monthKeys.map(() => 0)]));
            filtered.forEach((event) => {
                const date = new Date(event.timestamp);
                if (Number.isNaN(date.getTime())) return;
                const key = `${date.getFullYear()}-${pad(date.getMonth() + 1)}`;
                const index = monthKeys.indexOf(key);
                if (index >= 0 && monthData.has(event.module || "Sistema")) {
                    const values = monthData.get(event.module || "Sistema");
                    values[index] += 1;
                }
            });

            const rawMax = Math.max(1, ...[...monthData.values()].flat());
            const roughStep = rawMax / 4;
            const magnitude = 10 ** Math.floor(Math.log10(Math.max(roughStep, 1)));
            const normalizedStep = roughStep / magnitude;
            const niceNormalized = normalizedStep <= 1 ? 1 : normalizedStep <= 2 ? 2 : normalizedStep <= 5 ? 5 : 10;
            const tickStep = Math.max(1, niceNormalized * magnitude);
            const maxValue = tickStep * 4;
            const width = 940;
            const height = 340;
            const margin = { top: 24, right: 24, bottom: 58, left: 64 };
            const plotWidth = width - margin.left - margin.right;
            const plotHeight = height - margin.top - margin.bottom;
            const x = (index) => margin.left + (monthKeys.length === 1 ? plotWidth / 2 : index * plotWidth / (monthKeys.length - 1));
            const y = (value) => margin.top + plotHeight - (value / maxValue) * plotHeight;
            const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
            svg.setAttribute("role", "img");
            svg.setAttribute("aria-label", "Línea de tiempo mensual de actividades por módulo");
            svg.classList.add("audit-timeline-svg");

            const ns = "http://www.w3.org/2000/svg";
            for (let step = 0; step <= 4; step += 1) {
                const value = tickStep * step;
                const lineY = y(value);
                const grid = document.createElementNS(ns, "line");
                grid.setAttribute("x1", margin.left);
                grid.setAttribute("x2", width - margin.right);
                grid.setAttribute("y1", lineY);
                grid.setAttribute("y2", lineY);
                grid.classList.add("audit-timeline-grid");
                svg.appendChild(grid);
                const label = document.createElementNS(ns, "text");
                label.setAttribute("x", margin.left - 10);
                label.setAttribute("y", lineY + 4);
                label.setAttribute("text-anchor", "end");
                label.classList.add("audit-timeline-axis");
                label.textContent = value.toLocaleString("es-CO");
                svg.appendChild(label);
            }

            monthKeys.forEach((key, index) => {
                const [year, month] = key.split("-").map(Number);
                const date = new Date(year, month - 1, 1);
                const verticalGrid = document.createElementNS(ns, "line");
                verticalGrid.setAttribute("x1", x(index));
                verticalGrid.setAttribute("x2", x(index));
                verticalGrid.setAttribute("y1", margin.top);
                verticalGrid.setAttribute("y2", height - margin.bottom);
                verticalGrid.classList.add("audit-timeline-grid", "audit-timeline-grid-vertical");
                svg.insertBefore(verticalGrid, svg.firstChild);
                const label = document.createElementNS(ns, "text");
                label.setAttribute("x", x(index));
                label.setAttribute("y", height - 17);
                label.setAttribute("text-anchor", "middle");
                label.classList.add("audit-timeline-axis");
                label.textContent = new Intl.DateTimeFormat("es-CO", { month: "short", year: "2-digit" }).format(date);
                svg.appendChild(label);
            });

            const yTitle = document.createElementNS(ns, "text");
            yTitle.setAttribute("x", 14);
            yTitle.setAttribute("y", margin.top + plotHeight / 2);
            yTitle.setAttribute("text-anchor", "middle");
            yTitle.setAttribute("transform", `rotate(-90 14 ${margin.top + plotHeight / 2})`);
            yTitle.classList.add("audit-timeline-axis-title");
            yTitle.textContent = "Cantidad de actividades";
            svg.appendChild(yTitle);

            moduleNames.forEach((module, moduleIndex) => {
                const values = monthData.get(module);
                const color = colors[moduleIndex % colors.length];
                let pathData = `M ${x(0)} ${y(values[0] || 0)}`;
                for (let index = 1; index < values.length; index += 1) {
                    const controlX = (x(index - 1) + x(index)) / 2;
                    pathData += ` C ${controlX} ${y(values[index - 1] || 0)}, ${controlX} ${y(values[index] || 0)}, ${x(index)} ${y(values[index] || 0)}`;
                }
                const path = document.createElementNS(ns, "path");
                path.setAttribute("d", pathData);
                path.setAttribute("fill", "none");
                path.setAttribute("stroke", color);
                path.setAttribute("stroke-width", "3.5");
                path.setAttribute("stroke-linecap", "round");
                path.setAttribute("stroke-linejoin", "round");
                path.classList.add("audit-timeline-line");
                const title = document.createElementNS(ns, "title");
                const detail = values.map((value, index) => `${monthKeys[index]}: ${value}`).join("\n");
                title.textContent = `${module}\n${detail}`;
                path.appendChild(title);
                svg.appendChild(path);
            });

            elements.chart.appendChild(svg);

            const legend = document.createElement("div");
            legend.className = "audit-timeline-legend";
            moduleNames.forEach((module, index) => {
                const button = document.createElement("button");
                button.type = "button";
                button.innerHTML = `<span style="background:${colors[index % colors.length]}"></span>${module}`;
                button.addEventListener("click", () => {
                    elements.module.value = module;
                    currentPage = 1;
                    render();
                });
                legend.appendChild(button);
            });
            elements.chart.appendChild(legend);
        }

        function renderRows(filtered) {
            elements.rows.replaceChildren();
            elements.empty.hidden = filtered.length > 0;
            const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
            currentPage = Math.min(currentPage, pageCount);
            const start = (currentPage - 1) * pageSize;
            filtered.slice(start, start + pageSize).forEach((event) => {
                const row = document.createElement("tr");
                const dateCell = document.createElement("td");
                dateCell.className = "audit-date";
                dateCell.textContent = displayDate(event.timestamp);
                const actorCell = document.createElement("td");
                actorCell.className = "audit-actor";
                actorCell.textContent = event.actor || "Sin identificar";
                if (loginOnly) {
                    const emailCell = document.createElement("td");
                    emailCell.textContent = event.email || "Sin correo";
                    const roleCell = document.createElement("td");
                    roleCell.textContent = event.role || "Sin rol";
                    row.append(dateCell, actorCell, emailCell, roleCell);
                    elements.rows.appendChild(row);
                    return;
                }
                if (event.role) {
                    const role = document.createElement("small");
                    role.textContent = event.role;
                    actorCell.appendChild(role);
                }
                const eventCell = document.createElement("td");
                const badge = document.createElement("span");
                badge.className = `audit-badge audit-badge-${event.outcome}`;
                badge.textContent = event.action;
                eventCell.appendChild(badge);
                const moduleCell = document.createElement("td");
                moduleCell.textContent = event.module;
                const detailCell = document.createElement("td");
                detailCell.textContent = event.detail || event.entity || "Sin detalle";
                row.append(dateCell, actorCell, eventCell, moduleCell, detailCell);
                elements.rows.appendChild(row);
            });
            elements.pagination.hidden = filtered.length <= pageSize;
            elements.previousPage.disabled = currentPage === 1;
            elements.nextPage.disabled = currentPage === pageCount;
            elements.pageLabel.textContent = `Página ${currentPage} de ${pageCount} · ${filtered.length} ${filtered.length === 1 ? "registro" : "registros"}`;
        }

        function render() {
            if (!loginOnly) {
                renderModuleOptions();
                if (elements.start && elements.start.value !== selectedStart) elements.start.value = selectedStart;
                if (elements.end && elements.end.value !== selectedEnd) elements.end.value = selectedEnd;
            }
            const filtered = dayEvents();
            currentPage = Math.min(currentPage, Math.max(1, Math.ceil(filtered.length / pageSize)));
            const countLabel = loginOnly
                ? (filtered.length === 1 ? "inicio de sesión" : "inicios de sesión")
                : (filtered.length === 1 ? "actividad" : "actividades");
            elements.results.textContent = `${filtered.length} ${countLabel}`;
            if (!loginOnly) renderChart(filtered);
            renderRows(filtered);
        }

        function download(content, type, extension) {
            const url = URL.createObjectURL(new Blob([content], { type }));
            const link = document.createElement("a");
            link.href = url;
            link.download = `bitacora-marqueza-${selectedStart}-a-${selectedEnd}.${extension}`;
            link.click();
            setTimeout(() => URL.revokeObjectURL(url), 1000);
        }

        function exportEvents(format) {
            const filtered = dayEvents();
            if (!filtered.length) {
                elements.status.textContent = "No hay actividades para exportar en el rango seleccionado.";
                return;
            }
            if (format === "pdf") {
                window.print();
                return;
            }
            if (format === "json") {
                download(JSON.stringify(filtered, null, 2), "application/json;charset=utf-8", "json");
                return;
            }
            const rows = [
                fieldLabels.map((label) => `"${label}"`).join(","),
                ...filtered.map((event) => columns.map((column) => {
                    let value = String(event[column] ?? "").replaceAll('"', '""');
                    if (/^[=+\-@]/.test(value)) value = `'${value}`;
                    return `"${value}"`;
                }).join(","))
            ];
            download(`\ufeff${rows.join("\r\n")}`, "text/csv;charset=utf-8", "csv");
        }

        async function refresh() {
            elements.status.textContent = "Actualizando bitácora central...";
            try {
                events = (await window.MarquezaAudit.loadAll()).map(normalizeEvent);
                elements.status.textContent = "Bitácora central actualizada.";
            } catch (error) {
                console.error("No se pudo actualizar la bitácora central.", error);
                events = window.MarquezaAudit.read().map(normalizeEvent);
                elements.status.textContent = `No se pudo consultar la bitácora central: ${error.message}. Se muestran los registros locales.`;
            }
            render();
        }

        root.querySelector("[data-audit-refresh]")?.addEventListener("click", refresh);
        elements.start?.addEventListener("change", () => {
            selectedStart = elements.start.value || selectedStart;
            if (selectedStart > selectedEnd) selectedEnd = selectedStart;
            currentPage = 1;
            render();
        });
        elements.end?.addEventListener("change", () => {
            selectedEnd = elements.end.value || selectedEnd;
            if (selectedEnd < selectedStart) selectedStart = selectedEnd;
            currentPage = 1;
            render();
        });
        elements.module?.addEventListener("change", () => {
            currentPage = 1;
            render();
        });
        root.querySelector("[data-audit-clear]")?.addEventListener("click", () => {
            selectedStart = localDateKey(firstDay);
            selectedEnd = localDateKey(today);
            elements.module.value = "all";
            elements.search.value = "";
            if (elements.filter) elements.filter.value = "all";
            currentPage = 1;
            render();
        });
        elements.search.addEventListener("input", () => {
            currentPage = 1;
            render();
        });
        elements.filter?.addEventListener("change", () => {
            currentPage = 1;
            render();
        });
        elements.previousPage.addEventListener("click", () => {
            currentPage = Math.max(1, currentPage - 1);
            render();
        });
        elements.nextPage.addEventListener("click", () => {
            currentPage += 1;
            render();
        });
        root.querySelectorAll("[data-audit-export]").forEach((button) => {
            button.addEventListener("click", () => exportEvents(button.dataset.auditExport));
        });
        window.addEventListener("marqueza:audit", (event) => {
            if (event.detail) events = [normalizeEvent(event.detail), ...events.filter((item) => item.id !== event.detail.id)];
            render();
        });
        window.addEventListener("storage", (event) => {
            if (event.key === "marqueza_bitacora") {
                events = window.MarquezaAudit.read().map(normalizeEvent);
                render();
            }
        });
        render();
        void refresh();
    }

    document.querySelectorAll(rootSelector).forEach(mount);
})();
