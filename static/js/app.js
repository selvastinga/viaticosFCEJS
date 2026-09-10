/**
 * Lógica Cliente del Sistema de Gestión de Viáticos
 * FCEJS - Universidad Nacional de San Luis
 */

// Estado Global
let state = {
  configuracion: {},
  cargos: [],
  transportes: [],
  imputaciones: [],
  viaticos: [],
  viaticoEnEdicionId: null,
  cargosDict: {}
};

// Inicialización al cargar el DOM
document.addEventListener("DOMContentLoaded", () => {
  cargarDatosIniciales();
  configurarEventosFormulario();
  configurarEventosFiltros();
  configurarEventosReportes();
  configurarEventosOpciones();
});

// ------------------ CARGA DE DATOS INICIALES ------------------
async function cargarDatosIniciales() {
  try {
    const res = await fetch("/api/inicial");
    const data = await res.json();

    state.configuracion = data.configuracion || {};
    state.cargos = data.cargos || [];
    state.transportes = data.transportes || [];
    state.imputaciones = data.imputaciones || [];

    // Mapeo rápido de cargos por código
    state.cargosDict = {};
    state.cargos.forEach(c => {
      state.cargosDict[c.codigo] = c;
    });

    // Actualizar encabezados institucionales
    actualizarEncabezadosInstitucionales();

    // Llenar selectores
    poblarSelectCargos();
    poblarSelectTransportes();
    poblarSelectImputaciones();

    // Valores por defecto del formulario
    if (!state.viaticoEnEdicionId) {
      document.getElementById("nro_viatico").value = data.siguiente_nro || "00001";
      document.getElementById("fecha").value = data.fecha_hoy || new Date().toISOString().substring(0, 10);
      document.getElementById("fecha_desde").value = data.fecha_hoy || new Date().toISOString().substring(0, 10);
      document.getElementById("fecha_hasta").value = data.fecha_hoy || new Date().toISOString().substring(0, 10);
      calcularDiasYTotal();
    }

    // Cargar listas
    cargarListadoViaticos();
    cargarReporte();
    cargarTablaCargos();
    cargarTablaTransportes();
    cargarTablaImputaciones();
    cargarFormConfiguracion();

  } catch (err) {
    console.error("Error al cargar datos iniciales:", err);
  }
}

function actualizarEncabezadosInstitucionales() {
  const univ = state.configuracion.universidad || "UNIVERSIDAD NACIONAL DE SAN LUIS";
  const fac = state.configuracion.facultad || "FACULTAD DE CIENCIAS ECONÓMICAS, JURÍDICAS Y SOCIALES";
  
  const hFac = document.getElementById("header-facultad-nombre");
  if (hFac) hFac.textContent = fac;

  const fUniv = document.getElementById("form-header-univ");
  if (fUniv) fUniv.textContent = univ;

  const fFac = document.getElementById("form-header-fac");
  if (fFac) fFac.textContent = fac;
}

function poblarSelectCargos() {
  const sel = document.getElementById("cargo_codigo");
  if (!sel) return;
  
  const currentVal = sel.value;
  sel.innerHTML = '<option value="">-- Seleccionar Cargo --</option>';
  
  state.cargos.forEach(c => {
    const opt = document.createElement("option");
    opt.value = c.codigo;
    opt.textContent = `[${c.codigo}] ${c.nombre} ($ ${formatearMoneda(c.valor_diario, false)})`;
    sel.appendChild(opt);
  });

  if (currentVal && state.cargosDict[currentVal]) {
    sel.value = currentVal;
  }
}

function poblarSelectTransportes() {
  const sel = document.getElementById("medio_transporte");
  if (!sel) return;
  const currentVal = sel.value;
  sel.innerHTML = "";

  state.transportes.forEach(t => {
    const opt = document.createElement("option");
    opt.value = t.nombre;
    opt.textContent = t.nombre;
    sel.appendChild(opt);
  });

  if (currentVal) sel.value = currentVal;
  else if (state.transportes.length > 0) sel.value = state.transportes[0].nombre;
}

function poblarSelectImputaciones() {
  const sel = document.getElementById("imputacion");
  const filtroSel = document.getElementById("filtro-imputacion");
  const repSel = document.getElementById("rep-imputacion");

  if (sel) {
    const currentVal = sel.value;
    sel.innerHTML = '<option value="">-- Seleccionar Imputación --</option>';
    state.imputaciones.forEach(imp => {
      const opt = document.createElement("option");
      opt.value = imp.nombre;
      opt.textContent = imp.nombre;
      sel.appendChild(opt);
    });
    if (currentVal) sel.value = currentVal;
  }

  // Llenar selectores de filtro
  [filtroSel, repSel].forEach(s => {
    if (s) {
      s.innerHTML = '<option value="Todas">Todas las Imputaciones</option>';
      state.imputaciones.forEach(imp => {
        const opt = document.createElement("option");
        opt.value = imp.nombre;
        opt.textContent = imp.nombre;
        s.appendChild(opt);
      });
    }
  });
}

// ------------------ EVENTOS DEL FORMULARIO Y CÁLCULOS ------------------
function configurarEventosFormulario() {
  // Cambio de cargo
  document.getElementById("cargo_codigo").addEventListener("change", (e) => {
    const cod = e.target.value;
    if (state.cargosDict[cod]) {
      const c = state.cargosDict[cod];
      document.getElementById("cargo_denominacion").value = c.nombre;
      document.getElementById("valor_diario").value = c.valor_diario;
    }
    calcularDiasYTotal();
  });

  // Cambio de fechas
  document.getElementById("fecha_desde").addEventListener("change", calcularDiasYTotal);
  document.getElementById("fecha_hasta").addEventListener("change", calcularDiasYTotal);

  // Cambio manual de días o valor diario
  document.getElementById("cant_dias").addEventListener("input", recalcularImporteTotal);
  document.getElementById("valor_diario").addEventListener("input", recalcularImporteTotal);

  // Botones de acción
  document.getElementById("btn-guardar").addEventListener("click", () => guardarViatico(false));
  document.getElementById("btn-guardar-imprimir").addEventListener("click", () => guardarViatico(true));
  document.getElementById("btn-limpiar").addEventListener("click", resetearFormulario);
  document.getElementById("btn-ir-nuevo").addEventListener("click", () => {
    resetearFormulario();
    bootstrap.Tab.getInstance(document.getElementById("tab-alta-btn")).show();
  });
}

function calcularDiasYTotal() {
  const desde = document.getElementById("fecha_desde").value;
  const hasta = document.getElementById("fecha_hasta").value;

  if (desde && hasta) {
    const d1 = new Date(desde);
    const d2 = new Date(hasta);
    const diffTime = d2 - d1;
    let diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
    
    // Si la fecha hasta es menor que desde, no dejar negativo
    if (diffDays < 0) diffDays = 0;
    
    // Si viaja el mismo día se computa 1 día, o según la resta
    const diasVal = (diffDays === 0) ? 1.0 : diffDays;
    document.getElementById("cant_dias").value = diasVal.toFixed(1);
  }

  recalcularImporteTotal();
}

function recalcularImporteTotal() {
  const dias = parseFloat(document.getElementById("cant_dias").value) || 0;
  const valDiario = parseFloat(document.getElementById("valor_diario").value) || 0;
  const total = dias * valDiario;

  document.getElementById("importe_total").value = total.toFixed(2);
  
  // Actualizar preview en palabras
  const letras = numeroALetras(total);
  document.getElementById("preview_letras").textContent = `Son: ${letras}`;
}

// ------------------ GUARDAR VIÁTICO (CREAR / EDITAR) ------------------
async function guardarViatico(imprimirDespues = false) {
  const apellido_nombre = document.getElementById("apellido_nombre").value.trim();
  if (!apellido_nombre) {
    alert("Por favor ingrese el Apellido y Nombre del beneficiario.");
    document.getElementById("apellido_nombre").focus();
    return;
  }

  const viaticoData = {
    nro_viatico: document.getElementById("nro_viatico").value.trim(),
    fecha: document.getElementById("fecha").value,
    apellido_nombre: apellido_nombre,
    cargo_codigo: document.getElementById("cargo_codigo").value,
    cargo_denominacion: document.getElementById("cargo_denominacion").value.trim(),
    cant_dias: parseFloat(document.getElementById("cant_dias").value) || 0,
    fecha_desde: document.getElementById("fecha_desde").value,
    hora_desde: document.getElementById("hora_desde").value,
    fecha_hasta: document.getElementById("fecha_hasta").value,
    hora_hasta: document.getElementById("hora_hasta").value,
    lugar: document.getElementById("lugar").value.trim(),
    mision: document.getElementById("mision").value.trim(),
    medio_transporte: document.getElementById("medio_transporte").value,
    valor_diario: parseFloat(document.getElementById("valor_diario").value) || 0,
    importe_total: parseFloat(document.getElementById("importe_total").value) || 0,
    imputacion: document.getElementById("imputacion").value,
    cheque: document.getElementById("cheque").value.trim(),
    f_cheque: document.getElementById("f_cheque").value,
    expediente: document.getElementById("expediente").value.trim(),
    estado: document.getElementById("estado").value,
  };

  try {
    let url = "/api/viaticos";
    let method = "POST";

    if (state.viaticoEnEdicionId) {
      url = `/api/viaticos/${state.viaticoEnEdicionId}`;
      method = "PUT";
    }

    const res = await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(viaticoData)
    });

    const result = await res.json();
    if (!res.ok) {
      alert("Error al guardar: " + (result.error || "Desconocido"));
      return;
    }

    const savedId = state.viaticoEnEdicionId || result.id;
    
    // Si se solicitó imprimir, abrir el PDF en el modal
    if (imprimirDespues && savedId) {
      verPDFViatico(savedId);
    } else {
      alert("¡Viático guardado con éxito!");
    }

    resetearFormulario();
    cargarListadoViaticos();
    cargarReporte();

    // Si no imprime, pasar al listado
    if (!imprimirDespues) {
      bootstrap.Tab.getInstance(document.getElementById("tab-listado-btn")).show();
    }

  } catch (err) {
    console.error("Error al guardar viático:", err);
    alert("Error de conexión al guardar el viático.");
  }
}

function resetearFormulario() {
  state.viaticoEnEdicionId = null;
  document.getElementById("viatico_id").value = "";
  document.getElementById("form-viatico").reset();
  
  // Restablecer botón
  document.getElementById("btn-guardar").innerHTML = '<i class="bi bi-check2-circle me-1"></i> Guardar Viático';

  // Obtener nuevo consecutivo
  fetch("/api/inicial")
    .then(r => r.json())
    .then(d => {
      document.getElementById("nro_viatico").value = d.siguiente_nro || "00001";
      document.getElementById("fecha").value = d.fecha_hoy;
      document.getElementById("fecha_desde").value = d.fecha_hoy;
      document.getElementById("fecha_hasta").value = d.fecha_hoy;
      document.getElementById("cant_dias").value = "1.0";
      document.getElementById("hora_desde").value = "07:00";
      document.getElementById("hora_hasta").value = "07:00";
      calcularDiasYTotal();
    });
}

// ------------------ LISTADO DE VIÁTICOS (ABM) ------------------
function configurarEventosFiltros() {
  const inputs = [
    "filtro-busqueda", "filtro-fecha-desde", "filtro-fecha-hasta",
    "filtro-estado", "filtro-imputacion"
  ];
  inputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("input", cargarListadoViaticos);
      el.addEventListener("change", cargarListadoViaticos);
    }
  });

  document.getElementById("btn-limpiar-filtros").addEventListener("click", () => {
    document.getElementById("filtro-busqueda").value = "";
    document.getElementById("filtro-fecha-desde").value = "";
    document.getElementById("filtro-fecha-hasta").value = "";
    document.getElementById("filtro-estado").value = "Todos";
    document.getElementById("filtro-imputacion").value = "Todas";
    cargarListadoViaticos();
  });
}

async function cargarListadoViaticos() {
  const busqueda = document.getElementById("filtro-busqueda").value;
  const fecha_desde = document.getElementById("filtro-fecha-desde").value;
  const fecha_hasta = document.getElementById("filtro-fecha-hasta").value;
  const estado = document.getElementById("filtro-estado").value;
  const imputacion = document.getElementById("filtro-imputacion").value;

  const params = new URLSearchParams();
  if (busqueda) params.append("busqueda", busqueda);
  if (fecha_desde) params.append("fecha_desde", fecha_desde);
  if (fecha_hasta) params.append("fecha_hasta", fecha_hasta);
  if (estado && estado !== "Todos") params.append("estado", estado);
  if (imputacion && imputacion !== "Todas") params.append("imputacion", imputacion);

  try {
    const res = await fetch(`/api/viaticos?${params.toString()}`);
    const viaticos = await res.json();
    state.viaticos = viaticos;

    const tbody = document.getElementById("tabla-viaticos-body");
    if (!tbody) return;

    if (viaticos.length === 0) {
      tbody.innerHTML = '<tr><td colspan="11" class="text-center py-4 text-muted">No se encontraron solicitudes registradas</td></tr>';
      return;
    }

    tbody.innerHTML = viaticos.map(v => {
      const badgeClass = v.estado === "Pagado" ? "badge-pagado" : (v.estado === "Rendido" ? "badge-rendido" : "badge-pendiente");
      const fechasViaje = `${formatearFecha(v.fecha_desde)} al ${formatearFecha(v.fecha_hasta)}`;
      const chequeExp = [v.cheque ? `Transf: ${v.cheque}` : null, v.expediente ? `Exp: ${v.expediente}` : null].filter(Boolean).join(" / ") || "-";

      return `
        <tr>
          <td class="fw-bold text-secondary">${v.nro_viatico}</td>
          <td>${formatearFecha(v.fecha)}</td>
          <td>
            <div class="fw-bold">${v.apellido_nombre}</div>
            <div class="small text-muted text-truncate" style="max-width: 200px;" title="${v.mision || ''}">${v.mision || ''}</div>
          </td>
          <td><span class="badge bg-light text-dark border">${v.cargo_codigo || '-'}</span></td>
          <td class="small">${fechasViaje}</td>
          <td class="text-center fw-semibold">${v.cant_dias || 0}</td>
          <td class="text-end fw-bold text-dark">$ ${formatearMoneda(v.importe_total, false)}</td>
          <td class="small">${v.imputacion || '-'}</td>
          <td class="small">${chequeExp}</td>
          <td class="text-center"><span class="${badgeClass}">${v.estado}</span></td>
          <td class="text-center">
            <div class="btn-group btn-group-sm">
              <button class="btn btn-outline-danger btn-action" onclick="verPDFViatico(${v.id})" title="Imprimir PDF Oficial (A4)">
                <i class="bi bi-printer"></i>
              </button>
              <button class="btn btn-outline-primary btn-action" onclick="editarViatico(${v.id})" title="Modificar">
                <i class="bi bi-pencil"></i>
              </button>
              <button class="btn btn-outline-success btn-action" onclick="abrirModalEstado(${v.id}, '${v.estado}', '${v.cheque || ''}', '${v.f_cheque || ''}')" title="Cambiar Estado / Cargar Pago">
                <i class="bi bi-arrow-repeat"></i>
              </button>
              <button class="btn btn-outline-secondary btn-action text-danger" onclick="eliminarViatico(${v.id}, '${v.nro_viatico}')" title="Eliminar">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join("");

  } catch (err) {
    console.error("Error al cargar viáticos:", err);
  }
}

function verPDFViatico(viaticoId) {
  const pdfUrl = `/api/viaticos/${viaticoId}/pdf`;
  const iframe = document.getElementById("modal-pdf-iframe");
  const downloadLink = document.getElementById("modal-pdf-download-link");

  iframe.src = pdfUrl;
  downloadLink.href = `${pdfUrl}?download=1`;

  const modal = new bootstrap.Modal(document.getElementById("modalPDF"));
  modal.show();
}

async function editarViatico(viaticoId) {
  try {
    const res = await fetch(`/api/viaticos/${viaticoId}`);
    if (!res.ok) throw new Error("No se pudo cargar el viático");
    const v = await res.json();

    state.viaticoEnEdicionId = v.id;
    document.getElementById("viatico_id").value = v.id;
    document.getElementById("nro_viatico").value = v.nro_viatico;
    document.getElementById("fecha").value = v.fecha;
    document.getElementById("apellido_nombre").value = v.apellido_nombre;
    document.getElementById("cargo_codigo").value = v.cargo_codigo;
    document.getElementById("cargo_denominacion").value = v.cargo_denominacion;
    document.getElementById("cant_dias").value = v.cant_dias;
    document.getElementById("fecha_desde").value = v.fecha_desde;
    document.getElementById("hora_desde").value = v.hora_desde || "07:00";
    document.getElementById("fecha_hasta").value = v.fecha_hasta;
    document.getElementById("hora_hasta").value = v.hora_hasta || "07:00";
    document.getElementById("lugar").value = v.lugar || "";
    document.getElementById("mision").value = v.mision || "";
    document.getElementById("medio_transporte").value = v.medio_transporte || "Terrestre";
    document.getElementById("valor_diario").value = v.valor_diario;
    document.getElementById("importe_total").value = v.importe_total;
    document.getElementById("imputacion").value = v.imputacion || "";
    document.getElementById("cheque").value = v.cheque || "";
    document.getElementById("f_cheque").value = v.f_cheque || "";
    document.getElementById("expediente").value = v.expediente || "";
    document.getElementById("estado").value = v.estado || "Pendiente";

    recalcularImporteTotal();

    document.getElementById("btn-guardar").innerHTML = '<i class="bi bi-check2-circle me-1"></i> Actualizar Viático';

    // Cambiar a pestaña 1
    bootstrap.Tab.getInstance(document.getElementById("tab-alta-btn")).show();
    window.scrollTo({ top: 0, behavior: "smooth" });

  } catch (err) {
    alert("Error al cargar datos del viático.");
  }
}

function abrirModalEstado(viaticoId, estadoActual, cheque, fCheque) {
  document.getElementById("modal-estado-id").value = viaticoId;
  document.getElementById("modal-estado-select").value = estadoActual;
  document.getElementById("modal-estado-cheque").value = cheque;
  document.getElementById("modal-estado-fcheque").value = fCheque;

  const modal = new bootstrap.Modal(document.getElementById("modalEstado"));
  modal.show();
}

document.getElementById("btn-guardar-modal-estado").addEventListener("click", async () => {
  const viaticoId = document.getElementById("modal-estado-id").value;
  const nuevoEstado = document.getElementById("modal-estado-select").value;
  const cheque = document.getElementById("modal-estado-cheque").value.trim();
  const fCheque = document.getElementById("modal-estado-fcheque").value;

  try {
    const res = await fetch(`/api/viaticos/${viaticoId}/estado`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        estado: nuevoEstado,
        cheque: cheque,
        f_cheque: fCheque
      })
    });

    if (res.ok) {
      bootstrap.Modal.getInstance(document.getElementById("modalEstado")).hide();
      cargarListadoViaticos();
      cargarReporte();
    } else {
      alert("Error al actualizar el estado");
    }
  } catch (err) {
    alert("Error al comunicar con el servidor.");
  }
});

async function eliminarViatico(viaticoId, nroViatico) {
  if (!confirm(`¿Está seguro de eliminar el viático N° ${nroViatico}? Esta acción no se puede deshacer.`)) {
    return;
  }

  try {
    const res = await fetch(`/api/viaticos/${viaticoId}`, { method: "DELETE" });
    if (res.ok) {
      cargarListadoViaticos();
      cargarReporte();
    } else {
      alert("Error al eliminar");
    }
  } catch (err) {
    alert("Error de conexión");
  }
}

// ------------------ REPORTES Y ESTADÍSTICAS ------------------
function configurarEventosReportes() {
  const inputs = ["rep-fecha-desde", "rep-fecha-hasta", "rep-estado", "rep-imputacion"];
  inputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("change", cargarReporte);
    }
  });

  document.getElementById("btn-exportar-pdf").addEventListener("click", () => {
    const params = getReportParams();
    window.open(`/api/reportes/pdf?${params.toString()}`, "_blank");
  });

  document.getElementById("btn-exportar-excel").addEventListener("click", () => {
    const params = getReportParams();
    window.location.href = `/api/reportes/excel?${params.toString()}`;
  });
}

function getReportParams() {
  const params = new URLSearchParams();
  const fDesde = document.getElementById("rep-fecha-desde").value;
  const fHasta = document.getElementById("rep-fecha-hasta").value;
  const estado = document.getElementById("rep-estado").value;
  const imp = document.getElementById("rep-imputacion").value;

  if (fDesde) params.append("fecha_desde", fDesde);
  if (fHasta) params.append("fecha_hasta", fHasta);
  if (estado && estado !== "Todos") params.append("estado", estado);
  if (imp && imp !== "Todas") params.append("imputacion", imp);
  return params;
}

async function cargarReporte() {
  const params = getReportParams();
  try {
    const res = await fetch(`/api/reportes?${params.toString()}`);
    const data = await res.json();

    // Actualizar KPIs
    document.getElementById("kpi-total-monto").textContent = `$ ${formatearMoneda(data.total_monto, false)}`;
    document.getElementById("kpi-total-cant").textContent = data.total_cantidad || 0;

    document.getElementById("kpi-pend-monto").textContent = `$ ${formatearMoneda(data.pendientes_monto, false)}`;
    document.getElementById("kpi-pend-cant").textContent = data.pendientes_cantidad || 0;

    document.getElementById("kpi-pag-monto").textContent = `$ ${formatearMoneda(data.pagados_monto, false)}`;
    document.getElementById("kpi-pag-cant").textContent = data.pagados_cantidad || 0;

    document.getElementById("kpi-rend-monto").textContent = `$ ${formatearMoneda(data.rendidos_monto, false)}`;
    document.getElementById("kpi-rend-cant").textContent = data.rendidos_cantidad || 0;

    // Tabla de detalle del reporte
    const tbody = document.getElementById("tabla-reporte-body");
    if (!tbody) return;

    if (!data.viaticos || data.viaticos.length === 0) {
      tbody.innerHTML = '<tr><td colspan="10" class="text-center py-4 text-muted">No existen viáticos con los filtros seleccionados</td></tr>';
      return;
    }

    tbody.innerHTML = data.viaticos.map(v => {
      const badgeClass = v.estado === "Pagado" ? "badge-pagado" : (v.estado === "Rendido" ? "badge-rendido" : "badge-pendiente");
      return `
        <tr>
          <td class="fw-bold">${v.nro_viatico}</td>
          <td>${formatearFecha(v.fecha)}</td>
          <td><b>${v.apellido_nombre}</b></td>
          <td><span class="badge bg-light text-dark border">${v.cargo_codigo || '-'}</span></td>
          <td class="small">${formatearFecha(v.fecha_desde)} al ${formatearFecha(v.fecha_hasta)}</td>
          <td class="text-center">${v.cant_dias || 0}</td>
          <td class="text-end fw-bold">$ ${formatearMoneda(v.importe_total, false)}</td>
          <td>${v.imputacion || '-'}</td>
          <td>${v.cheque || '-'}</td>
          <td class="text-center"><span class="${badgeClass}">${v.estado}</span></td>
        </tr>
      `;
    }).join("");

  } catch (err) {
    console.error("Error al cargar reporte:", err);
  }
}

// ------------------ ADMINISTRACIÓN DE OPCIONES (opciones.pdf) ------------------
function configurarEventosOpciones() {
  // Modal nuevo cargo
  document.getElementById("btn-nuevo-cargo").addEventListener("click", () => {
    document.getElementById("modal-cargo-id").value = "";
    document.getElementById("modal-cargo-codigo").value = "";
    document.getElementById("modal-cargo-codigo").readOnly = false;
    document.getElementById("modal-cargo-nombre").value = "";
    document.getElementById("modal-cargo-valor").value = "80000.00";
    document.getElementById("modalCargoTitle").textContent = "Agregar Nuevo Cargo";

    const modal = new bootstrap.Modal(document.getElementById("modalCargo"));
    modal.show();
  });

  // Guardar cargo modal
  document.getElementById("btn-guardar-modal-cargo").addEventListener("click", async () => {
    const id = document.getElementById("modal-cargo-id").value;
    const codigo = document.getElementById("modal-cargo-codigo").value.trim().toUpperCase();
    const nombre = document.getElementById("modal-cargo-nombre").value.trim();
    const valor_diario = parseFloat(document.getElementById("modal-cargo-valor").value) || 0;

    if (!codigo || !nombre) {
      alert("Código y Nombre son obligatorios");
      return;
    }

    try {
      const res = await fetch("/api/cargos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: id || null, codigo, nombre, valor_diario })
      });

      if (res.ok) {
        bootstrap.Modal.getInstance(document.getElementById("modalCargo")).hide();
        cargarDatosIniciales();
      } else {
        alert("Error al guardar el cargo");
      }
    } catch (err) {
      alert("Error de conexión");
    }
  });

  // Agregar Transporte
  document.getElementById("btn-agregar-transporte").addEventListener("click", async () => {
    const input = document.getElementById("nuevo-transporte-nombre");
    const nombre = input.value.trim();
    if (!nombre) return;

    try {
      const res = await fetch("/api/transportes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nombre })
      });
      if (res.ok) {
        input.value = "";
        cargarDatosIniciales();
      }
    } catch (e) {
      alert("Error al agregar transporte");
    }
  });

  // Agregar Imputación
  document.getElementById("btn-agregar-imputacion").addEventListener("click", async () => {
    const input = document.getElementById("nueva-imputacion-nombre");
    const nombre = input.value.trim();
    if (!nombre) return;

    try {
      const res = await fetch("/api/imputaciones", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nombre })
      });
      if (res.ok) {
        input.value = "";
        cargarDatosIniciales();
      }
    } catch (e) {
      alert("Error al agregar imputación");
    }
  });

  // Guardar Configuración Institucional
  document.getElementById("btn-guardar-config").addEventListener("click", async () => {
    const cfgData = {
      universidad: document.getElementById("cfg-universidad").value.trim(),
      facultad: document.getElementById("cfg-facultad").value.trim(),
      normativa: document.getElementById("cfg-normativa").value.trim(),
      ciudad: document.getElementById("cfg-ciudad").value.trim(),
      valor_dolar: parseFloat(document.getElementById("cfg-valor-dolar").value) || 1515,
      director_financiero: document.getElementById("cfg-director-financiero").value.trim(),
      cargo_dir_financiero: document.getElementById("cfg-cargo-dir-financiero").value.trim(),
      secretario_administrativo: document.getElementById("cfg-secretario-administrativo").value.trim(),
      cargo_sec_administrativo: document.getElementById("cfg-cargo-sec-administrativo").value.trim(),
      decano: document.getElementById("cfg-decano").value.trim(),
      cargo_decano: document.getElementById("cfg-cargo-decano").value.trim(),
      director_economico: document.getElementById("cfg-director-economico").value.trim(),
      cargo_dir_economico: document.getElementById("cfg-cargo-dir-economico").value.trim(),
    };

    try {
      const res = await fetch("/api/configuracion", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cfgData)
      });
      if (res.ok) {
        alert("¡Configuración guardada exitosamente!");
        state.configuracion = cfgData;
        actualizarEncabezadosInstitucionales();
      } else {
        alert("Error al guardar la configuración");
      }
    } catch (e) {
      alert("Error de conexión al guardar configuración");
    }
  });
}

function setFacultadPreset(nombre) {
  document.getElementById("cfg-facultad").value = nombre;
}

async function cargarTablaCargos() {
  const tbody = document.getElementById("tabla-cargos-body");
  if (!tbody) return;

  try {
    const res = await fetch("/api/cargos");
    const cargos = await res.json();
    tbody.innerHTML = cargos.map(c => `
      <tr>
        <td class="fw-bold text-primary">${c.codigo}</td>
        <td>${c.nombre}</td>
        <td class="text-end fw-bold">$ ${formatearMoneda(c.valor_diario, false)}</td>
        <td class="text-center">
          <button class="btn btn-sm btn-outline-primary py-0 px-2" onclick="editarCargo(${c.id}, '${c.codigo}', '${escapeQuotes(c.nombre)}', ${c.valor_diario})" title="Editar">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger py-0 px-2" onclick="eliminarCargo(${c.id}, '${c.codigo}')" title="Eliminar">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error al cargar cargos:", err);
  }
}

function editarCargo(id, codigo, nombre, valor) {
  document.getElementById("modal-cargo-id").value = id;
  document.getElementById("modal-cargo-codigo").value = codigo;
  document.getElementById("modal-cargo-nombre").value = nombre;
  document.getElementById("modal-cargo-valor").value = valor;
  document.getElementById("modalCargoTitle").textContent = "Modificar Cargo";

  const modal = new bootstrap.Modal(document.getElementById("modalCargo"));
  modal.show();
}

async function eliminarCargo(id, codigo) {
  if (!confirm(`¿Eliminar el cargo ${codigo}?`)) return;
  try {
    const res = await fetch(`/api/cargos/${id}`, { method: "DELETE" });
    if (res.ok) cargarDatosIniciales();
  } catch (e) {
    alert("Error al eliminar cargo");
  }
}

async function cargarTablaTransportes() {
  const tbody = document.getElementById("tabla-transportes-body");
  if (!tbody) return;
  try {
    const res = await fetch("/api/transportes");
    const list = await res.json();
    tbody.innerHTML = list.map(t => `
      <tr>
        <td><b>${t.nombre}</b></td>
        <td class="text-center">
          <button class="btn btn-sm btn-outline-danger py-0 px-2" onclick="eliminarTransporte(${t.id})">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}

async function eliminarTransporte(id) {
  if (!confirm("¿Eliminar este medio de transporte?")) return;
  try {
    const res = await fetch(`/api/transportes/${id}`, { method: "DELETE" });
    if (res.ok) cargarDatosIniciales();
  } catch (e) {
    alert("Error al eliminar");
  }
}

async function cargarTablaImputaciones() {
  const tbody = document.getElementById("tabla-imputaciones-body");
  if (!tbody) return;
  try {
    const res = await fetch("/api/imputaciones");
    const list = await res.json();
    tbody.innerHTML = list.map(imp => `
      <tr>
        <td><b>${imp.nombre}</b></td>
        <td class="text-center">
          <button class="btn btn-sm btn-outline-danger py-0 px-2" onclick="eliminarImputacion(${imp.id})">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}

async function eliminarImputacion(id) {
  if (!confirm("¿Eliminar esta imputación?")) return;
  try {
    const res = await fetch(`/api/imputaciones/${id}`, { method: "DELETE" });
    if (res.ok) cargarDatosIniciales();
  } catch (e) {
    alert("Error al eliminar");
  }
}

function cargarFormConfiguracion() {
  const c = state.configuracion || {};
  document.getElementById("cfg-universidad").value = c.universidad || "UNIVERSIDAD NACIONAL DE SAN LUIS";
  document.getElementById("cfg-facultad").value = c.facultad || "FACULTAD DE CIENCIAS ECONÓMICAS, JURÍDICAS Y SOCIALES";
  document.getElementById("cfg-normativa").value = c.normativa || "";
  document.getElementById("cfg-ciudad").value = c.ciudad || "Villa Mercedes (SL)";
  document.getElementById("cfg-valor-dolar").value = c.valor_dolar || 1515;

  document.getElementById("cfg-director-financiero").value = c.director_financiero || "";
  document.getElementById("cfg-cargo-dir-financiero").value = c.cargo_dir_financiero || "Director Financiero";
  document.getElementById("cfg-secretario-administrativo").value = c.secretario_administrativo || "";
  document.getElementById("cfg-cargo-sec-administrativo").value = c.cargo_sec_administrativo || "Secretario Administrativo";
  document.getElementById("cfg-decano").value = c.decano || "";
  document.getElementById("cfg-cargo-decano").value = c.cargo_decano || "Decano";
  document.getElementById("cfg-director-economico").value = c.director_economico || "";
  document.getElementById("cfg-cargo-dir-economico").value = c.cargo_dir_economico || "Director Económico- Fciero";
}

// ------------------ HELPERS Y CONVERSIÓN DE NÚMEROS A PALABRAS ------------------
function formatearMoneda(val, incluirSimbolo = true) {
  const n = parseFloat(val) || 0;
  const s = n.toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return incluirSimbolo ? `$ ${s}` : s;
}

function formatearFecha(fStr) {
  if (!fStr) return "-";
  if (fStr.includes("-")) {
    const parts = fStr.split("-");
    if (parts.length === 3) return `${parts[2]}/${parts[1]}/${parts[0]}`;
  }
  return fStr;
}

function escapeQuotes(str) {
  return (str || "").replace(/'/g, "\\'");
}

// Conversor a palabras cliente (idéntico a Python utils.py)
function numeroALetras(monto) {
  const unidades = [
    "", "Un", "Dos", "Tres", "Cuatro", "Cinco", "Seis", "Siete", "Ocho", "Nueve",
    "Diez", "Once", "Doce", "Trece", "Catorce", "Quince", "Dieciséis", "Diecisiete",
    "Dieciocho", "Diecinueve", "Veinte", "Veintiuno", "Veintidós", "Veintitrés",
    "Veinticuatro", "Veinticinco", "Veintiséis", "Veintisiete", "Veintiocho", "Veintinueve"
  ];
  const decenas = ["", "", "", "Treinta", "Cuarenta", "Cincuenta", "Sesenta", "Setenta", "Ochenta", "Noventa"];
  const centenas = ["", "Ciento", "Doscientos", "Trescientos", "Cuatrocientos", "Quinientos", "Seiscientos", "Setecientos", "Ochocientos", "Novecientos"];

  function centenasALetras(n) {
    if (n === 0) return "";
    if (n === 100) return "Cien";
    const c = Math.floor(n / 100);
    const resto = n % 100;
    const p = [];
    if (c > 0) p.push(centenas[c]);
    if (resto < 30) {
      if (resto > 0) p.push(unidades[resto]);
    } else {
      const d = Math.floor(resto / 10);
      const u = resto % 10;
      p.push(u === 0 ? decenas[d] : `${decenas[d]} y ${unidades[u]}`);
    }
    return p.join(" ");
  }

  function milesALetras(n) {
    if (n === 0) return "";
    const miles = Math.floor(n / 1000);
    const resto = n % 1000;
    const p = [];
    if (miles > 0) {
      p.push(miles === 1 ? "Mil" : `${centenasALetras(miles)} Mil`);
    }
    if (resto > 0) p.push(centenasALetras(resto));
    return p.join(" ");
  }

  function enteroALetras(n) {
    if (n === 0) return "Cero";
    const millones = Math.floor(n / 1000000);
    const restoMillones = n % 1000000;
    const p = [];
    if (millones > 0) {
      p.push(millones === 1 ? "Un Millón" : `${milesALetras(millones)} Millones`);
    }
    if (restoMillones > 0) p.push(milesALetras(restoMillones));
    return p.join(" ");
  }

  const num = Math.abs(parseFloat(monto) || 0);
  let entero = Math.floor(num);
  let centavos = Math.round((num - entero) * 100);
  if (centavos === 100) { entero += 1; centavos = 0; }

  const letras = enteroALetras(entero);
  let moneda = "Pesos";
  if (entero === 1) moneda = "Peso";
  else if (entero > 0 && entero % 1000000 === 0) moneda = "de Pesos";

  const centavosStr = String(centavos).padStart(2, "0");
  return `${letras} ${moneda} ${centavosStr}/100`;
}
