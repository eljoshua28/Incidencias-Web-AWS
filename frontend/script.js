const API_URL = "https://mpufe9cgw5.execute-api.us-east-1.amazonaws.com";

const formulario = document.getElementById("formIncidencia");
const lista = document.getElementById("listaIncidencias");

async function cargarIncidencias() {
    try {
        const respuesta = await fetch(`${API_URL}/incidencias`);
        if (!respuesta.ok) throw new Error("No se pudieron consultar las incidencias");

        const incidencias = await respuesta.json();
        mostrarIncidencias(incidencias);
    } catch (error) {
        alert("Error al cargar las incidencias: " + error.message);
    }
}

function mostrarIncidencias(incidencias) {
    lista.innerHTML = "";

    incidencias.forEach(incidencia => {
        const fila = document.createElement("tr");

        [incidencia.id, incidencia.titulo, incidencia.descripcion, incidencia.estado]
            .forEach(dato => {
                const celda = document.createElement("td");
                celda.textContent = dato;
                fila.appendChild(celda);
            });

        const acciones = document.createElement("td");

        const botonEstado = document.createElement("button");
        botonEstado.textContent = "Cambiar estado";
        botonEstado.addEventListener("click", () => cambiarEstado(incidencia));

        const botonEliminar = document.createElement("button");
        botonEliminar.textContent = "Eliminar";
        botonEliminar.addEventListener("click", () => eliminarIncidencia(incidencia.id));

        acciones.append(botonEstado, botonEliminar);
        fila.appendChild(acciones);
        lista.appendChild(fila);
    });
}

async function registrarIncidencia(event) {
    event.preventDefault();

    const titulo = document.getElementById("titulo").value.trim();
    const descripcion = document.getElementById("descripcion").value.trim();

    try {
        const respuesta = await fetch(`${API_URL}/incidencias`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ titulo, descripcion })
        });

        if (!respuesta.ok) throw new Error("No se pudo registrar la incidencia");

        formulario.reset();
        await cargarIncidencias();
    } catch (error) {
        alert("Error al registrar: " + error.message);
    }
}

async function cambiarEstado(incidencia) {
    const estados = ["Pendiente", "En proceso", "Completada"];
    const siguiente = estados[(estados.indexOf(incidencia.estado) + 1) % estados.length];

    try {
        const respuesta = await fetch(
            `${API_URL}/incidencias/${encodeURIComponent(incidencia.id)}`,
            {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ estado: siguiente })
            }
        );

        if (!respuesta.ok) throw new Error("No se pudo actualizar el estado");

        await cargarIncidencias();
    } catch (error) {
        alert("Error al cambiar el estado: " + error.message);
    }
}

async function eliminarIncidencia(id) {
    if (!confirm("¿Deseas eliminar esta incidencia?")) return;

    try {
        const respuesta = await fetch(
            `${API_URL}/incidencias/${encodeURIComponent(id)}`,
            { method: "DELETE" }
        );

        if (!respuesta.ok) throw new Error("No se pudo eliminar la incidencia");

        await cargarIncidencias();
    } catch (error) {
        alert("Error al eliminar: " + error.message);
    }
}

formulario.addEventListener("submit", registrarIncidencia);

cargarIncidencias();
