
        let originalData = []; // Guardar el orden original de los datos
        let currentSortColumn = null; // Columna actual seleccionada para orden
        let currentSortDirection = 0; // 0 = sin ordenar, 1 = ascendente, -1 = descendente

        // Función para interpolar colores más saturados
        function getColorForValue(value) {
            const clamp = (num, min, max) => Math.min(Math.max(num, min), max);

            // Limitar valor al rango de -100 a 100
            const clampedValue = clamp(value, -100, 100);

            let r, g, b;

            if (clampedValue === 0) {
                // En el punto neutro: color naranja
                return 'rgb(235, 133, 0)';
            }

            if (clampedValue > 0) {
                // Valores positivos: de naranja (219, 235, 0) a verde puro (0, 255, 0)
                const normalized = clampedValue / 100; // Normaliza rango [0, 100] a [0, 1]
                r = Math.round(196 - (219 * normalized)); // R decrece de 219 a 0
                g = Math.round(235 + (20 * normalized)); // G incrementa de 235 a 255
                b = 0; // Azul constante
            } else {
                // Valores negativos: de naranja (235, 133, 0) a rojo puro (255, 0, 0)
                const normalized = Math.abs(clampedValue) / 100; // Normaliza rango [-100, 0] a [0, 1]
                r = Math.round(235 + (20 * normalized)); // R incrementa de 235 a 255
                g = Math.round(133 - (133 * normalized)); // G decrece de 133 a 0
                b = 0; // Azul constante
            }

            return `rgb(${r},${g},${b})`;
        }

        // Ordenar tabla por columna
        function sortTable(data, column, direction) {
            return data.sort((a, b) => {
                const aValue = parseFloat(a[column]) || 0;
                const bValue = parseFloat(b[column]) || 0;

                if (direction === 1) return aValue - bValue; // Orden ascendente
                if (direction === -1) return bValue - aValue; // Orden descendente
                return 0; // Sin ordenar
            });
        }

        // Actualizar la tabla con los datos
        function updateTable(data) {
            const table = document.getElementById('data-table');
            table.innerHTML = '';

            if (data.length > 0) {
                const headers = Object.keys(data[0]);

                // Crear encabezados de la tabla
                const headerRow = document.createElement('tr');
                headers.forEach(header => {
                    const th = document.createElement('th');
                    th.innerHTML = `${header} <span class="sort-indicator"></span>`;

                    // Añadir funcionalidad de orden al hacer clic
                    th.onclick = () => {
                        if (currentSortColumn === header) {
                            // Ciclar entre sin ordenar, ascendente, descendente
                            currentSortDirection = (currentSortDirection + 2) % 3 - 1; // 0 -> 1 -> -1 -> 0
                        } else {
                            currentSortColumn = header;
                            currentSortDirection = -1; // Empezar con descendente
                        }

                        const sortedData = currentSortDirection === 0
                            ? [...originalData] // Restaurar orden original
                            : sortTable([...data], header, currentSortDirection);

                        updateTable(sortedData);
                    };

                    // Actualizar triángulos según el estado de orden
                    if (currentSortColumn === header) {
                        const indicator = th.querySelector(".sort-indicator");
                        indicator.innerHTML = currentSortDirection === 1 ? "&#9650;" : currentSortDirection === -1 ? "&#9660;" : "";
                    }

                    headerRow.appendChild(th);
                });
                table.appendChild(headerRow);

                // Crear filas de la tabla
                data.forEach(row => {
                    const tr = document.createElement('tr');
                    headers.forEach(header => {
                        const td = document.createElement('td');

                        if (header === "Symbol") {
                            // Crear enlace para Symbol
                            const symbol = row[header];
                            td.innerHTML = `<a href="https://es.tradingview.com/symbols/${symbol}/" target="_blank" class="symbol-link">${symbol}</a>`;
                        } else if (header === "Expected Return") {
                            const expectedReturn = row[header];
                            if (expectedReturn === "ND") {
                                td.innerHTML = `<span class="tag tag-gray">ND</span>`;
                            } else {
                                const roundedValue = expectedReturn.toFixed(2);

                                // Asignar color dinámico
                                const color = getColorForValue(roundedValue);
                                td.innerHTML = `<span class="tag" style="background-color: ${color}">${roundedValue}%</span>`;
                            }
                        } else if (!isNaN(row[header])) {
                            // Mostrar número redondeado y todos los decimales al hacer hover
                            const originalValue = parseFloat(row[header]);
                            const roundedValue = originalValue.toFixed(2);
                            td.innerHTML = `<span class="decimal-hover">${roundedValue}<span>${originalValue}</span></span>`;
                        } else {
                            td.textContent = row[header] === '' ? 'ND' : row[header];
                        }
                        tr.appendChild(td);
                    });
                    table.appendChild(tr);
                });
            } else {
                const emptyRow = document.createElement('tr');
                const td = document.createElement('td');
                td.colSpan = "100%";
                td.textContent = "No data available";
                emptyRow.appendChild(td);
                table.appendChild(emptyRow);
            }
        }

        // Agregar eventos de doble clic para mostrar el modal
        function addDoubleClickEvents() {
            const table = document.getElementById('data-table');
            table.addEventListener('dblclick', async (event) => {
                const cell = event.target;
                const row = cell.parentElement;
                const symbolCell = row.querySelector('td:nth-child(1)'); // Suponemos que la primera columna es "Symbol"

                if (symbolCell) {
                    const symbol = symbolCell.textContent.trim();

                    // Mostrar modal con mensaje de carga
                    showModal(null, true);

                    try {
                        // Hacer la solicitud a la API
                        const rowData = await fetchRowData(symbol);

                        // Actualizar modal con los datos obtenidos
                        showModal(rowData, false);
                    } catch (error) {
                        console.error("Error fetching row data:", error);
                        // Mostrar modal con mensaje de error
                        showModal(null, false);
                    }
                }
            });
        }

        async function fetchRowData(symbol) {
            try {
                const response = await fetch(`/get_rows?Symbol=${symbol}`);
                if (!response.ok) {
                    throw new Error("Error fetching data");
                }
                const data = await response.json();
                return data;
            } catch (error) {
                console.error("Error fetching row data:", error);
                return null;
            }
        }

        function showModal(data = null, loading = true) {
            const modal = document.getElementById('modal');
            const modalContent = document.getElementById('modal-content');

            if (loading) {
                modalContent.innerHTML = `
            <button type="button" class="close btn" aria-label="Close">
                <i class="bi bi-x-circle"></i>
            </button>
            <h4>Loading data...</h4>
        `;
            } else if (data) {
                const symbolData = data.symbol_data?.[0] || {};
                const finvizData = data.finviz_data || [];

                // Crear la tabla para `symbol_data`
                const symbolTable = `
            <table class="table table-dark table-bordered">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Ownership Count</th>
                        <th>Current Price</th>
                        <th>Target Price</th>
                        <th>5 Year EPS Growth</th>
                        <th>Earnings Yield</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>${symbolData.Symbol || 'ND'}</td>
                        <td>${symbolData.Ownershipcount || 'ND'}</td>
                        <td>${symbolData.CurrentPrice || 'ND'}</td>
                        <td>${symbolData.TargetPrice || 'ND'}</td>
                        <td>${symbolData['5 Year EPS Growth'] || 'ND'}</td>
                        <td>${symbolData['Earnings Yield'] || 'ND'}</td>
                    </tr>
                </tbody>
            </table>
        `;

                // Crear la tabla para `finviz_data`
                const finvizTable = `
    <table class="table table-dark table-bordered">
        <thead>
            <tr>
                <th>Date</th>
                <th>Action</th>
                <th>Analyst</th>
                <th>Rating Change</th>
                <th>Price Target Change</th>
            </tr>
        </thead>
        <tbody>
            ${finvizData.length > 0
                        ? finvizData
                            .map((row) => {
                                // Determinar el estilo de la fila según la acción
                                let rowClass = '';
                                let actionClass = '';

                                if (row.Action === 'Downgrade') {
                                    rowClass = 'row-danger';
                                    actionClass = 'tag-red';
                                } else if (
                                    row.Action === 'Initiated' ||
                                    row.Action === 'Reiterated' ||
                                    row.Action === 'Resumed'
                                ) {
                                    actionClass = 'tag-black';
                                } else if (row.Action === 'Upgrade') {
                                    rowClass = 'row-success';
                                    actionClass = 'tag-green';
                                }

                                return `
                            <tr class="${rowClass}">
                                <td>${row.Date || 'ND'}</td>
                                <td><span class="tag ${actionClass}">${row.Action || 'ND'}</span></td>
                                <td>${row.Analyst || 'ND'}</td>
                                <td>${row['Rating Change'] || 'ND'}</td>
                                <td>${row['Price Target Change'] || 'ND'}</td>
                            </tr>
                        `;
                            })
                            .join('')
                        : '<tr><td colspan="5">No data available</td></tr>'}
        </tbody>
    </table>
`;



                // Montar el contenido del modal
                modalContent.innerHTML = `
            <button type="button" class="close btn" aria-label="Close">
                <i class="bi bi-x-circle"></i>
            </button>
            <h4>Symbol: ${symbolData.Symbol || 'ND'}</h4>
            ${symbolTable}
            <h4>Finviz Data</h4>
            ${finvizTable}
        `;
            } else {
                modalContent.innerHTML = `
            <button type="button" class="close btn" aria-label="Close">
                <i class="bi bi-x-circle"></i>
            </button>
            <h4>Error</h4>
            <p>The symbol information could not be loaded, it may not exist.</p>
        `;
            }

            // Mostrar el modal
            modal.style.display = 'flex';

            // Evento para cerrar el modal
            const closeButton = modalContent.querySelector('.close');
            closeButton.onclick = () => (modal.style.display = 'none');

            // Cerrar modal al hacer clic fuera de él
            modal.onclick = (e) => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            };
        }


        async function loadTable() {
            document.getElementById('loader').style.display = 'flex';
            document.getElementById('data-container').style.display = 'none';

            try {
                const response = await fetch('/get_full_dataframe/');
                const data = await response.json();

                data.forEach(row => {
                    const targetPrice = row["TargetPrice"] === '' ? "ND" : parseFloat(row["TargetPrice"]);
                    const currentPrice = parseFloat(row["CurrentPrice"]) || 0;

                    if (targetPrice === "ND" || currentPrice === 0) {
                        row["Expected Return"] = "ND";
                    } else {
                        row["Expected Return"] = ((targetPrice - currentPrice) / currentPrice) * 100;
                    }
                });

                originalData = [...data];
                updateTable(data);
                addDoubleClickEvents();
            } catch (error) {
                console.error("Error loading data:", error);
            } finally {
                document.getElementById('loader').style.display = 'none';
                document.getElementById('data-container').style.display = 'block';
            }
        }

        window.onload = loadTable;
