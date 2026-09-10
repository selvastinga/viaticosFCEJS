# Sistema de Gestión de Viáticos
**Facultad de Ciencias Económicas, Jurídicas y Sociales (FCEJS)**  
*Universidad Nacional de San Luis*

Aplicación para la gestión integral de viáticos (Alta, Baja, Modificación), cálculo automático de liquidaciones diarias, generación de planilla oficial A4 idéntica al modelo institucional, administración de tablas maestras y reportes estadísticos.

---

## 🚀 Inicio Rápido (1 Clic)

En Windows, haz doble clic sobre el archivo:
```
iniciar_sistema.bat
```
El sistema iniciará automáticamente el servidor y abrirá tu navegador en:
`http://127.0.0.1:5000`

---

## 🔐 Usuarios y Acceso al Sistema

El sistema cuenta con control de acceso por usuario y contraseña. Solo los usuarios autenticados pueden ver, agregar, modificar o eliminar registros:

| Usuario | Contraseña | Privilegios |
| :--- | :--- | :--- |
| **`admin`** | `admin2026` | Acceso total administrativo (ABM, reportes, opciones) |
| **`secretaria`** | `secretaria2026` | Acceso total administrativo (ABM, reportes, opciones) |

> **Nota de Seguridad**: Si se accede a la aplicación sin iniciar sesión, el sistema redirige automáticamente a la pantalla de login (`/login`) y bloquea cualquier llamada a la API con `401 Unauthorized`. Para cerrar la sesión, haz clic en el botón **"Salir"** en la barra superior.

---

## 📋 Módulos y Funcionalidades

### 1. Cargar Viático (ABM de Solicitudes)
- **Formulario oficial** basado en la pantalla del sistema (`pantalla abm.png`).
- **Autocompletado de Cargo**: Al seleccionar el código de cargo (ej. `ADE`, `SEC`, `2SE`), se completa automáticamente la denominación oficial y el valor diario del viático estipulado en `opciones.pdf`.
- **Cálculo automático de días y total**:
  - Al ingresar la *Fecha Desde* y la *Fecha Hasta*, el sistema calcula los días transcurridos (`Fecha Hasta - Fecha Desde`).
  - Calcula en tiempo real: `Importe Total = Días × Valor Diario`.
  - Muestra en tiempo real el importe expresado en letras (ej: *"Son: Doscientos Cuarenta Mil Pesos 00/100"*).
- Botón **"Guardar Viático"** y botón **"Guardar e Imprimir (A4)"** para visualizar o descargar directamente la planilla oficial generada.

### 2. Listado de Solicitudes (ABM)
- Tabla con todas las solicitudes registradas.
- Búsqueda rápida por nombre de beneficiario, número de viático, expediente o misión.
- Filtros por fecha desde/hasta, estado (`Pendiente`, `Pagado`, `Rendido`) e imputación presupuestaria.
- Acciones por fila:
  - **Imprimir PDF Oficial (A4)**: Abre el documento idéntico a `salida.pdf`.
  - **Modificar**: Carga los datos en el formulario para editar cualquier valor.
  - **Cambiar Estado**: Permite registrar el pago (N° de cheque y fecha) o marcar como rendido.
  - **Eliminar**: Baja del viático con confirmación.

### 3. Reportes y Estadísticas
- Filtrado por rango de fechas, estado de la solicitud e imputación.
- **Tarjetas de Indicadores Financieros (KPI)**:
  - Total Liquidado ($) y cantidad de solicitudes.
  - Pendientes ($ y cantidad).
  - Pagados ($ y cantidad).
  - Rendidos ($ y cantidad).
- **Exportación en 1 clic**:
  - **Exportar a PDF**: Genera un informe oficial para elevar a autoridades o archivo.
  - **Exportar a Excel (.xlsx)**: Genera planilla con fórmulas, formatos de moneda, fechas y totales.

### 4. Opciones y Tablas Maestras (`opciones.pdf`)
- **Cargos**: Permite dar de alta nuevos cargos, modificar el nombre completo y actualizar el valor diario asignado (los 30 cargos de `opciones.pdf` ya están pre-cargados).
- **Medios de Transporte**: Terrestre, Aéreo, Vehículo Oficial, etc. (agregar o eliminar).
- **Imputaciones Presupuestarias**: Decanato, Departamentos académicos y Secretarías.
- **Configuración y Firmas**:
  - Nombre de la Facultad (FCEJS o personalizado).
  - Universidad y normativa legal aplicable.
  - Autoridades firmantes del PDF (Director Financiero, Secretario Administrativo, Decano, Director Económico).
  - Ciudad y valor de referencia del dólar.

---

## 🛠️ Estructura del Proyecto

- `app.py`: Servidor Flask y endpoints REST.
- `database.py`: Esquema SQLite (`viaticos.db`) y operaciones CRUD.
- `pdf_generator.py`: Motor ReportLab para la planilla A4 oficial (`salida.pdf`) y reportes PDF.
- `excel_generator.py`: Generador de planillas Excel (`.xlsx`) con `openpyxl`.
- `utils.py`: Algoritmos de conversión de números a letras en pesos argentinos y cálculos de fechas.
- `templates/index.html`: Interfaz web interactiva.
- `static/css/style.css`: Estilos visuales.
- `static/js/app.js`: Lógica cliente y cálculos reactivos.
- `iniciar_sistema.bat`: Lanzador automático para Windows.
- `test_system.py`: Batería de pruebas automatizadas.
