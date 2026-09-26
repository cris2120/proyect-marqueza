class VentasPage extends MarquezaCrudPage {
    constructor() {
        super({
            storageKey: "marqueza_ventas",
            modalId: "modalVenta",
            formId: "formVenta",
            fields: ["fecha", "cliente", "producto", "cantidad", "total"],
            columns: ["fecha", "cliente", "producto", "cantidad", "total"]
        });
        this.clients = [];
        this.products = [];
    }

    async init() {
        try {
            const [clientRows, people, products] = await Promise.all([
                window.MarquezaApi.get("/clientes/"),
                window.MarquezaApi.get("/personas/"),
                window.MarquezaApi.get("/productos/")
            ]);
            const peopleById = new Map(people.map(person => [Number(person.id), person]));
            this.clients = clientRows.map(client => ({ ...client, nombre: peopleById.get(Number(client.per_id))?.nombre || "" }));
            this.products = products;
        } catch (error) {
            window.Swal?.fire({ icon: "error", title: "No se pudieron cargar ventas", text: error.message });
            return;
        }
        super.init();
        document.getElementById("producto")?.addEventListener("change", () => this.updateSaleTotal());
        document.getElementById("cantidad")?.addEventListener("input", () => this.updateSaleTotal());
        this.updateSummary(this.readRecords(), this.readRecords());
    }

    loadClients(selectedValue = "") {
        const select = document.getElementById("cliente");
        if (!select) return;
        select.replaceChildren(new Option("Selecciona un cliente", ""));
        this.clients.forEach(client => {
            const value = String(client.nombre || "").trim();
            if (!value) return;
            const label = client.documento ? `${value} - ${client.documento}` : value;
            select.appendChild(new Option(label, String(client.id)));
        });
        select.value = String(selectedValue || "");
    }

    loadProducts(selectedValue = "") {
        const select = document.getElementById("producto");
        if (!select) return;
        select.replaceChildren(new Option("Selecciona un producto", ""));
        this.products.forEach(product => {
            const value = String(product.id);
            if (!value) return;
            const label = product.codigo ? `${product.codigo} - ${product.nombre}` : product.nombre;
            const option = new Option(label, value);
            option.dataset.price = String(Number(product.precio || 0));
            select.appendChild(option);
        });
        select.value = selectedValue;
    }

    updateSaleTotal() {
        const product = document.getElementById("producto");
        const quantity = Number(document.getElementById("cantidad")?.value || 0);
        const price = Number(product?.selectedOptions[0]?.dataset.price || 0);
        const total = document.getElementById("total");
        if (total) total.value = price > 0 && quantity > 0 ? String(price * quantity) : "";
    }

    openModal(index = -1) {
        super.openModal(index);
        if (index >= 0) {
            const record = this.readRecords()[index];
            document.getElementById("cliente").value = String(record.clienteId);
            document.getElementById("producto").value = String(record.productoId);
        }
        this.updateSaleTotal();
    }

    render(query = "") {
        super.render(query);
        const normalizedQuery = query.trim().toLowerCase();
        const visible = this.readRecords().filter(record => !normalizedQuery || JSON.stringify(record).toLowerCase().includes(normalizedQuery));
        this.updateSummary(this.readRecords(), visible);
    }

    updateSummary(records, visibleRecords) {
        const money = value => Number(value || 0).toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
        const number = value => Number(value || 0).toLocaleString("es-CO");
        const total = records.reduce((sum, record) => sum + Number(record.total || 0), 0);
        const units = records.reduce((sum, record) => sum + Number(record.cantidad || 0), 0);
        const setText = (id, value) => { const element = document.getElementById(id); if (element) element.textContent = value; };
        setText("totalVentas", number(records.length));
        setText("ingresosVentas", money(total));
        setText("unidadesVendidas", number(units));
        setText("promedioVenta", money(records.length ? total / records.length : 0));
        setText("resultadosVentas", `${visibleRecords.length} ${visibleRecords.length === 1 ? "resultado" : "resultados"}`);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    new MarquezaAppShell().init();
    const ventasPage = new VentasPage();
    ventasPage.init();
    window.addEventListener("focus", async () => {
        try {
            await ventasPage.refresh();
        } catch (error) {
            window.Swal?.fire({ icon: "error", title: "No se pudieron actualizar ventas", text: error.message });
        }
    });
});
