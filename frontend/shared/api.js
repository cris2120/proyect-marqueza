class MarquezaApiClient {
    constructor(baseUrl = window.MARQUEZA_API_URL || "/api") {
        this.baseUrl = baseUrl.replace(/\/$/, "");
    }

    async request(path, options = {}) {
        const headers = new Headers(options.headers || {});
        if (options.body && !headers.has("Content-Type")) {
            headers.set("Content-Type", "application/json");
        }

        const response = await fetch(`${this.baseUrl}${path}`, {
            ...options,
            headers,
            credentials: "same-origin"
        });
        const contentType = response.headers.get("content-type") || "";
        const result = contentType.includes("application/json")
            ? await response.json()
            : await response.text();

        if (!response.ok) {
            const message = typeof result === "object"
                ? result.error || result.message
                : result;
            throw new Error(message || `La API respondió ${response.status}.`);
        }

        return result;
    }

    get(path) {
        return this.request(path);
    }

    post(path, data) {
        return this.request(path, { method: "POST", body: JSON.stringify(data) });
    }

    put(path, data) {
        return this.request(path, { method: "PUT", body: JSON.stringify(data) });
    }

    delete(path) {
        return this.request(path, { method: "DELETE" });
    }
}

window.MarquezaApi = new MarquezaApiClient();

const api = window.MarquezaApi;
const asNumber = value => {
    const parsed = Number(String(value || "").replace(/\D/g, ""));
    return Number.isSafeInteger(parsed) ? parsed : 0;
};

const toPersonaPayload = record => ({
    nombre: record.nombre || record.empresa,
    seg_nombre: null,
    pri_apellido: null,
    seg_apellido: null,
    correo: record.correo,
    direccion: record.direccion || "No especificada",
    identificacion: Number(record.documento || record._identificacion),
    telefono: asNumber(record.telefono)
});

const findPersona = async identificacion => {
    const people = await api.get("/personas/");
    return people.find(person => Number(person.identificacion) === Number(identificacion));
};

const clientAdapter = {
    async list() {
        const [clients, people] = await Promise.all([api.get("/clientes/"), api.get("/personas/")]);
        const peopleById = new Map(people.map(person => [Number(person.id), person]));
        return clients.flatMap(client => {
            const person = peopleById.get(Number(client.per_id));
            if (!person) return [];
            return [{
                id: client.id,
                _personaId: person.id,
                uuid: client.uuid,
                nombre: person.nombre,
                documento: String(person.identificacion),
                telefono: String(person.telefono),
                correo: person.correo
            }];
        });
    },
    async create(record) {
        const person = await api.post("/personas/", toPersonaPayload(record));
        try {
            const clientId = await api.post("/clientes/", { persona_id: person.id });
            return { id: typeof clientId === "object" ? clientId.id : clientId, _personaId: person.id };
        } catch (error) {
            await api.delete(`/personas/${person.id}`).catch(() => {});
            throw error;
        }
    },
    async update(existing, record) {
        await api.put(`/personas/${existing._personaId}`, toPersonaPayload(record));
        await api.put(`/clientes/${existing.id}`, { persona_id: existing._personaId });
    },
    async delete(record) {
        await api.delete(`/clientes/${record.id}`);
        await api.delete(`/personas/${record._personaId}`);
    }
};

const supplierAdapter = {
    async list() {
        const [suppliers, people, contacts] = await Promise.all([
            api.get("/proveedores/"),
            api.get("/personas/"),
            api.get("/contactos/")
        ]);
        const peopleById = new Map(people.map(person => [Number(person.id), person]));
        return suppliers.flatMap(supplier => {
            const person = peopleById.get(Number(supplier.per_id));
            if (!person) return [];
            const related = contacts.filter(contact => Number(contact.proveedor_id) === Number(supplier.id));
            const byType = type => related.find(contact => String(contact.tipo_contacto).toLowerCase() === type);
            return [{
                id: supplier.id,
                _personaId: person.id,
                _contactIds: Object.fromEntries(related.map(contact => [String(contact.tipo_contacto).toLowerCase(), contact.id])),
                empresa: person.nombre,
                contacto: byType("contacto")?.contenido || "",
                telefono: byType("telefono")?.contenido || String(person.telefono || ""),
                correo: byType("correo")?.contenido || person.correo,
                direccion: person.direccion,
                documento: String(person.identificacion)
            }];
        });
    },
    async saveContacts(supplierId, record, existing = {}) {
        for (const [type, content] of [["contacto", record.contacto], ["telefono", record.telefono], ["correo", record.correo]]) {
            if (existing[type]) {
                await api.put(`/contactos/${existing[type]}`, { tipo_contacto: type, contenido: content, proveedor_id: supplierId });
            } else {
                await api.post("/contactos/", { tipo_contacto: type, contenido: content, proveedor_id: supplierId });
            }
        }
    },
    async create(record) {
        const personPayload = toPersonaPayload({ ...record, _identificacion: 1000000000 + Math.floor(Math.random() * 1000000000) });
        const person = await api.post("/personas/", personPayload);
        let supplierId;
        try {
            const result = await api.post("/proveedores/", { persona_id: person.id });
            supplierId = typeof result === "object" ? result.id : result;
            await this.saveContacts(supplierId, record);
            return { id: supplierId, _personaId: person.id };
        } catch (error) {
            if (supplierId) {
                const contacts = await api.get("/contactos/").catch(() => []);
                for (const contact of contacts.filter(item => Number(item.proveedor_id) === Number(supplierId))) {
                    await api.delete(`/contactos/${contact.id}`).catch(() => {});
                }
                await api.delete(`/proveedores/${supplierId}`).catch(() => {});
            }
            await api.delete(`/personas/${person.id}`).catch(() => {});
            throw error;
        }
    },
    async update(existing, record) {
        await api.put(`/personas/${existing._personaId}`, toPersonaPayload({ ...record, _identificacion: existing.documento }));
        await api.put(`/proveedores/${existing.id}`, { persona_id: existing._personaId });
        await this.saveContacts(existing.id, record, existing._contactIds);
    },
    async delete(record) {
        const contacts = await api.get("/contactos/");
        for (const contact of contacts.filter(item => Number(item.proveedor_id) === Number(record.id))) {
            await api.delete(`/contactos/${contact.id}`);
        }
        await api.delete(`/proveedores/${record.id}`);
        await api.delete(`/personas/${record._personaId}`);
    }
};

const salesAdapter = {
    async list() {
        const [sales, lines, products, clientRows, people] = await Promise.all([
            api.get("/ventas/"),
            api.get("/ventas-productos/"),
            api.get("/productos/"),
            api.get("/clientes/"),
            api.get("/personas/")
        ]);
        const productsById = new Map(products.map(product => [Number(product.id), product]));
        const peopleById = new Map(people.map(person => [Number(person.id), person]));
        const clientsById = new Map(clientRows.map(client => [Number(client.id), peopleById.get(Number(client.per_id))]));
        return sales.map(sale => {
            const saleLines = lines.filter(line => Number(line.vent_id) === Number(sale.id));
            const firstLine = saleLines[0];
            const firstProduct = firstLine && productsById.get(Number(firstLine.prod_id));
            return {
                id: sale.id,
                fecha: sale.fecha,
                cliente: clientsById.get(Number(sale.cli_id))?.nombre || "",
                clienteId: Number(sale.cli_id),
                producto: saleLines.map(line => productsById.get(Number(line.prod_id))?.nombre || "Producto").join(", "),
                productoId: firstLine ? Number(firstLine.prod_id) : "",
                cantidad: saleLines.reduce((sum, line) => sum + Number(line.cantidad || 0), 0),
                total: saleLines.reduce((sum, line) => sum + Number(line.precio || firstProduct?.precio || 0) * Number(line.cantidad || 0), 0),
                usuarioId: Number(sale.usua_id),
                lineIds: saleLines.map(line => line.id)
            };
        });
    },
    async create(record) {
        const [users, products] = await Promise.all([api.get("/usuarios/"), api.get("/productos/")]);
        const session = JSON.parse(localStorage.getItem("marqueza_usuario_sesion") || "null");
        const userId = session?.id || users[0]?.id;
        const product = products.find(item => Number(item.id) === Number(record.producto));
        if (!userId || !product) throw new Error("Selecciona un usuario y un producto existentes.");
        const sale = await api.post("/ventas/", { fecha: record.fecha, usua_id: userId, cli_id: Number(record.cliente) });
        try {
            await api.post("/ventas-productos/", { cantidad: Number(record.cantidad), vent_id: sale.id, prod_id: product.id, precio: Number(product.precio) });
        } catch (error) {
            await api.delete(`/ventas/${sale.id}`).catch(() => {});
            throw error;
        }
    },
    async update(existing, record) {
        const [users, products, lines] = await Promise.all([api.get("/usuarios/"), api.get("/productos/"), api.get("/ventas-productos/")]);
        const session = JSON.parse(localStorage.getItem("marqueza_usuario_sesion") || "null");
        const userId = session?.id || existing.usuarioId || users[0]?.id;
        const product = products.find(item => Number(item.id) === Number(record.producto));
        if (!userId || !product) throw new Error("Selecciona un usuario y un producto existentes.");
        await api.put(`/ventas/${existing.id}`, { fecha: record.fecha, usua_id: userId, cli_id: Number(record.cliente) });
        for (const line of lines.filter(item => Number(item.vent_id) === Number(existing.id))) {
            await api.delete(`/ventas-productos/${line.id}`);
        }
        await api.post("/ventas-productos/", { cantidad: Number(record.cantidad), vent_id: existing.id, prod_id: product.id, precio: Number(product.precio) });
    },
    async delete(record) {
        const lines = await api.get("/ventas-productos/");
        for (const line of lines.filter(item => Number(item.vent_id) === Number(record.id))) {
            await api.delete(`/ventas-productos/${line.id}`);
        }
        await api.delete(`/ventas/${record.id}`);
    }
};

window.MarquezaCrudAdapters = {
    marqueza_clientes: clientAdapter,
    marqueza_proveedores: supplierAdapter,
    marqueza_ventas: salesAdapter
};