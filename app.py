"""
Aplicación Principal Flask - Sistema de Gestión de Viáticos
Facultad de Ingeniería y Ciencias Agropecuarias / FCEJS - UNSL
Con autenticación de usuarios y protección de rutas.
"""
import os
from io import BytesIO
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session

import database
import pdf_generator
import excel_generator
import utils

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "viaticos-unsl-secret-key-2026-auth")

# Inicialización segura de la base de datos
try:
    database.init_db()
except Exception as e:
    print(f"[WARN] Error inicializando base de datos en startup: {e}")


@app.errorhandler(Exception)
def handle_exception(e):
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return e
    
    print(f"[ERROR NO MANEJADO] {e}")
    error_msg = str(e)
    
    # Respuesta amigable en HTML para errores de base de datos o runtime
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Aviso del Sistema - Viáticos UNSL</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex align-items-center justify-content-center" style="min-height: 100vh; padding: 20px;">
  <div class="card p-4 shadow-sm border-0" style="max-width: 580px; border-radius: 12px;">
    <h4 class="text-danger fw-bold mb-2">⚠️ Error de Conexión a la Base de Datos</h4>
    <p class="text-muted small mb-3">La aplicación no pudo comunicarse con la base de datos. Detalle técnico:</p>
    <div class="bg-dark text-white p-3 rounded mb-3" style="font-size: 0.82rem; font-family: monospace; white-space: pre-wrap; word-break: break-all;">{error_msg}</div>
    <div class="alert alert-warning small mb-3">
      <strong>Verificación recomendada en Vercel:</strong>
      <ul class="mb-0 mt-1 ps-3">
        <li>Comprueba en <em>Project Settings &gt; Environment Variables</em> que <code>DATABASE_URL</code> esté configurada.</li>
        <li>Si usas Supabase, asegúrate de utilizar la URI del <strong>Connection Pooler</strong> (puerto 6543 o 5432) y que la contraseña sea la correcta.</li>
        <li>Asegúrate de haber ejecutado el script <code>schema_supabase.sql</code> en el SQL Editor de Supabase.</li>
      </ul>
    </div>
    <a href="/" class="btn btn-primary btn-sm">Volver a intentar</a>
  </div>
</body>
</html>"""
    return html, 500


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            # Si es una petición API, devolver 401 Unauthorized
            if request.path.startswith("/api/"):
                return jsonify({"error": "No autorizado. Inicie sesión."}), 401
            # Si es petición web, redirigir a login
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# ------------------ AUTENTICACIÓN (LOGIN / LOGOUT) ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = database.verificar_credenciales(username, password)
        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["nombre_completo"] = user["nombre_completo"]
            
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("index"))
        else:
            error = "Usuario o contraseña incorrectos. Verifique sus credenciales."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------ VISTA PRINCIPAL (PROTEGIDA) ------------------
@app.route("/")
@login_required
def index():
    current_user = {
        "id": session.get("user_id"),
        "username": session.get("username"),
        "nombre_completo": session.get("nombre_completo")
    }
    return render_template("index.html", current_user=current_user)


# ------------------ API DATOS INICIALES ------------------
@app.route("/api/inicial", methods=["GET"])
@login_required
def api_inicial():
    config = database.get_configuracion()
    cargos = database.get_cargos(solo_activos=True)
    transportes = database.get_transportes()
    imputaciones = database.get_imputaciones()
    sig_nro = database.get_siguiente_nro_viatico()
    hoy_iso = date.today().isoformat()

    return jsonify({
        "configuracion": config,
        "cargos": cargos,
        "transportes": transportes,
        "imputaciones": imputaciones,
        "siguiente_nro": sig_nro,
        "fecha_hoy": hoy_iso,
        "usuario": {
            "username": session.get("username"),
            "nombre_completo": session.get("nombre_completo")
        }
    })


# ------------------ API VIÁTICOS (CRUD) ------------------
@app.route("/api/viaticos", methods=["GET"])
@login_required
def api_list_viaticos():
    fecha_desde = request.args.get("fecha_desde")
    fecha_hasta = request.args.get("fecha_hasta")
    estado = request.args.get("estado")
    imputacion = request.args.get("imputacion")
    busqueda = request.args.get("busqueda")

    viaticos = database.list_viaticos(fecha_desde, fecha_hasta, estado, imputacion, busqueda)
    return jsonify(viaticos)


@app.route("/api/viaticos/<int:viatico_id>", methods=["GET"])
@login_required
def api_get_viatico(viatico_id):
    v = database.get_viatico(viatico_id)
    if not v:
        return jsonify({"error": "Viático no encontrado"}), 404
    return jsonify(v)


@app.route("/api/viaticos", methods=["POST"])
@login_required
def api_create_viatico():
    data = request.json or {}
    
    # Validaciones y normalización
    if not data.get("apellido_nombre"):
        return jsonify({"error": "El Apellido y Nombre es obligatorio"}), 400

    # Auto cálculo si faltan días o total
    cant_dias = float(data.get("cant_dias") or 0.0)
    if cant_dias <= 0 and data.get("fecha_desde") and data.get("fecha_hasta"):
        cant_dias = utils.calcular_dias(data.get("fecha_desde"), data.get("fecha_hasta"))
        data["cant_dias"] = cant_dias

    valor_diario = float(data.get("valor_diario") or 0.0)
    importe_total = float(data.get("importe_total") or (cant_dias * valor_diario))
    data["importe_total"] = importe_total

    if not data.get("nro_viatico"):
        data["nro_viatico"] = database.get_siguiente_nro_viatico()

    if not data.get("fecha"):
        data["fecha"] = date.today().isoformat()

    viatico_id = database.create_viatico({
        "nro_viatico": str(data.get("nro_viatico")).strip(),
        "fecha": str(data.get("fecha")).strip(),
        "apellido_nombre": str(data.get("apellido_nombre")).strip().upper(),
        "cargo_codigo": str(data.get("cargo_codigo") or "").strip(),
        "cargo_denominacion": str(data.get("cargo_denominacion") or "").strip(),
        "cant_dias": cant_dias,
        "fecha_desde": str(data.get("fecha_desde") or "").strip(),
        "hora_desde": str(data.get("hora_desde") or "").strip(),
        "fecha_hasta": str(data.get("fecha_hasta") or "").strip(),
        "hora_hasta": str(data.get("hora_hasta") or "").strip(),
        "lugar": str(data.get("lugar") or "").strip(),
        "mision": str(data.get("mision") or "").strip(),
        "medio_transporte": str(data.get("medio_transporte") or "Terrestre").strip(),
        "valor_diario": valor_diario,
        "importe_total": importe_total,
        "imputacion": str(data.get("imputacion") or "").strip(),
        "cheque": str(data.get("cheque") or "").strip(),
        "f_cheque": str(data.get("f_cheque") or "").strip(),
        "expediente": str(data.get("expediente") or "").strip(),
        "estado": str(data.get("estado") or "Pendiente").strip(),
        "observaciones": str(data.get("observaciones") or "").strip(),
    })

    return jsonify({"success": True, "id": viatico_id, "nro_viatico": data["nro_viatico"]}), 201


@app.route("/api/viaticos/<int:viatico_id>", methods=["PUT"])
@login_required
def api_update_viatico(viatico_id):
    data = request.json or {}
    existing = database.get_viatico(viatico_id)
    if not existing:
        return jsonify({"error": "Viático no encontrado"}), 404

    cant_dias = float(data.get("cant_dias") or 0.0)
    if cant_dias <= 0 and data.get("fecha_desde") and data.get("fecha_hasta"):
        cant_dias = utils.calcular_dias(data.get("fecha_desde"), data.get("fecha_hasta"))
        data["cant_dias"] = cant_dias

    valor_diario = float(data.get("valor_diario") or 0.0)
    importe_total = float(data.get("importe_total") or (cant_dias * valor_diario))

    database.update_viatico(viatico_id, {
        "nro_viatico": str(data.get("nro_viatico") or existing["nro_viatico"]).strip(),
        "fecha": str(data.get("fecha") or existing["fecha"]).strip(),
        "apellido_nombre": str(data.get("apellido_nombre") or existing["apellido_nombre"]).strip().upper(),
        "cargo_codigo": str(data.get("cargo_codigo") or "").strip(),
        "cargo_denominacion": str(data.get("cargo_denominacion") or "").strip(),
        "cant_dias": cant_dias,
        "fecha_desde": str(data.get("fecha_desde") or "").strip(),
        "hora_desde": str(data.get("hora_desde") or "").strip(),
        "fecha_hasta": str(data.get("fecha_hasta") or "").strip(),
        "hora_hasta": str(data.get("hora_hasta") or "").strip(),
        "lugar": str(data.get("lugar") or "").strip(),
        "mision": str(data.get("mision") or "").strip(),
        "medio_transporte": str(data.get("medio_transporte") or "Terrestre").strip(),
        "valor_diario": valor_diario,
        "importe_total": importe_total,
        "imputacion": str(data.get("imputacion") or "").strip(),
        "cheque": str(data.get("cheque") or "").strip(),
        "f_cheque": str(data.get("f_cheque") or "").strip(),
        "expediente": str(data.get("expediente") or "").strip(),
        "estado": str(data.get("estado") or existing["estado"]).strip(),
        "observaciones": str(data.get("observaciones") or "").strip(),
    })

    return jsonify({"success": True})


@app.route("/api/viaticos/<int:viatico_id>/estado", methods=["PATCH"])
@login_required
def api_update_estado(viatico_id):
    data = request.json or {}
    estado = data.get("estado")
    if not estado:
        return jsonify({"error": "Estado requerido"}), 400

    cheque = data.get("cheque")
    f_cheque = data.get("f_cheque")
    database.update_estado_viatico(viatico_id, estado, cheque, f_cheque)
    return jsonify({"success": True})


@app.route("/api/viaticos/<int:viatico_id>", methods=["DELETE"])
@login_required
def api_delete_viatico(viatico_id):
    database.delete_viatico(viatico_id)
    return jsonify({"success": True})


# ------------------ GENERACIÓN DE PDF OFICIAL ------------------
@app.route("/api/viaticos/<int:viatico_id>/pdf", methods=["GET"])
@login_required
def api_viatico_pdf(viatico_id):
    v = database.get_viatico(viatico_id)
    if not v:
        return "Viático no encontrado", 404

    cfg = database.get_configuracion()
    buffer = BytesIO()
    pdf_generator.generar_pdf_viatico(v, cfg, buffer)
    buffer.seek(0)

    filename = f"Solicitud_Viatico_{v.get('nro_viatico', viatico_id)}.pdf"
    as_attachment = request.args.get("download", "0") == "1"
    
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=as_attachment,
        download_name=filename
    )


# ------------------ API OPCIONES (CARGOS, TRANSPORTES, IMPUTACIONES) ------------------
@app.route("/api/cargos", methods=["GET", "POST"])
@login_required
def api_cargos():
    if request.method == "POST":
        data = request.json or {}
        codigo = data.get("codigo")
        nombre = data.get("nombre")
        valor_diario = data.get("valor_diario", 0)
        cargo_id = data.get("id")

        if not codigo or not nombre:
            return jsonify({"error": "Código y Nombre son obligatorios"}), 400

        database.save_cargo(codigo, nombre, valor_diario, cargo_id)
        return jsonify({"success": True})

    cargos = database.get_cargos(solo_activos=False)
    return jsonify(cargos)


@app.route("/api/cargos/<int:cargo_id>", methods=["DELETE"])
@login_required
def api_delete_cargo(cargo_id):
    database.delete_cargo(cargo_id)
    return jsonify({"success": True})


@app.route("/api/transportes", methods=["GET", "POST"])
@login_required
def api_transportes():
    if request.method == "POST":
        data = request.json or {}
        nombre = data.get("nombre")
        if not nombre:
            return jsonify({"error": "Nombre requerido"}), 400
        database.add_transporte(nombre)
        return jsonify({"success": True})

    return jsonify(database.get_transportes())


@app.route("/api/transportes/<int:transporte_id>", methods=["DELETE"])
@login_required
def api_delete_transporte(transporte_id):
    database.delete_transporte(transporte_id)
    return jsonify({"success": True})


@app.route("/api/imputaciones", methods=["GET", "POST"])
@login_required
def api_imputaciones():
    if request.method == "POST":
        data = request.json or {}
        nombre = data.get("nombre")
        if not nombre:
            return jsonify({"error": "Nombre requerido"}), 400
        database.add_imputacion(nombre)
        return jsonify({"success": True})

    return jsonify(database.get_imputaciones())


@app.route("/api/imputaciones/<int:imputacion_id>", methods=["DELETE"])
@login_required
def api_delete_imputacion(imputacion_id):
    database.delete_imputacion(imputacion_id)
    return jsonify({"success": True})


@app.route("/api/configuracion", methods=["GET", "POST"])
@login_required
def api_configuracion():
    if request.method == "POST":
        data = request.json or {}
        database.update_configuracion(data)
        return jsonify({"success": True})

    return jsonify(database.get_configuracion())


# ------------------ REPORTES Y EXPORTACIÓN ------------------
@app.route("/api/reportes", methods=["GET"])
@login_required
def api_reportes():
    fecha_desde = request.args.get("fecha_desde")
    fecha_hasta = request.args.get("fecha_hasta")
    estado = request.args.get("estado")
    imputacion = request.args.get("imputacion")
    busqueda = request.args.get("busqueda")

    metricas = database.get_reporte_metricas(fecha_desde, fecha_hasta, estado, imputacion, busqueda)
    return jsonify(metricas)


@app.route("/api/reportes/pdf", methods=["GET"])
@login_required
def api_reportes_pdf():
    fecha_desde = request.args.get("fecha_desde")
    fecha_hasta = request.args.get("fecha_hasta")
    estado = request.args.get("estado")
    imputacion = request.args.get("imputacion")
    busqueda = request.args.get("busqueda")

    filtros = {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "estado": estado,
        "imputacion": imputacion,
        "busqueda": busqueda
    }

    cfg = database.get_configuracion()
    metricas = database.get_reporte_metricas(fecha_desde, fecha_hasta, estado, imputacion, busqueda)
    
    buffer = BytesIO()
    pdf_generator.generar_pdf_reporte(metricas, metricas["viaticos"], cfg, filtros, buffer)
    buffer.seek(0)

    filename = f"Reporte_Viaticos_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=filename)


@app.route("/api/reportes/excel", methods=["GET"])
@login_required
def api_reportes_excel():
    fecha_desde = request.args.get("fecha_desde")
    fecha_hasta = request.args.get("fecha_hasta")
    estado = request.args.get("estado")
    imputacion = request.args.get("imputacion")
    busqueda = request.args.get("busqueda")

    filtros = {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "estado": estado,
        "imputacion": imputacion,
        "busqueda": busqueda
    }

    cfg = database.get_configuracion()
    metricas = database.get_reporte_metricas(fecha_desde, fecha_hasta, estado, imputacion, busqueda)

    buffer = BytesIO()
    excel_generator.generar_excel_reporte(metricas, metricas["viaticos"], cfg, filtros, buffer)
    buffer.seek(0)

    filename = f"Reporte_Viaticos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(
        buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
