(function () {
    const tables = document.querySelectorAll(".cont_tabla .table-scroll table");

    tables.forEach((table) => {
        const labelCells = () => {
            const headerRow = table.tHead && table.tHead.rows[0];
            if (!headerRow) return;

            const labels = Array.from(headerRow.cells, (cell) => cell.textContent.trim());
            Array.from(table.tBodies).forEach((body) => {
                Array.from(body.rows).forEach((row) => {
                    Array.from(row.cells).forEach((cell, index) => {
                        if (cell.colSpan !== 1 || !labels[index]) return;
                        cell.dataset.label = labels[index];
                        if (cell.querySelector("button")) cell.dataset.actions = "true";
                    });
                });
            });
        };

        table.classList.add("responsive-table");
        labelCells();

        const bodyObserver = new MutationObserver(labelCells);
        Array.from(table.tBodies).forEach((body) => {
            bodyObserver.observe(body, { childList: true, subtree: true });
        });
    });
})();
