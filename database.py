"""
Capa de base de datos dual: PostgreSQL (Supabase) / SQLite (Local)
Para el Sistema de Gestión de Viáticos (FICA / FCEJS - UNSL).
"""
import os
import re
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Configuración de base de datos
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_POSTGRES = bool(DATABASE_URL)

if IS_POSTGRES:
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        IS_POSTGRES = False

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viaticos.db")


def get_connection():
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn


def adapt_sql(sql: str) -> str:
    if not IS_POSTGRES:
        return sql
    # Convertir ? a %s para PostgreSQL
    sql = sql.replace("?", "%s")
    # Convertir :param a %(param)s para PostgreSQL evitando ::cast
    sql = re.sub(r'(?<!:):([a-zA-Z0-9_]+)', r'%(\1)s', sql)
    return sql


def execute_query(sql: str, params=None, fetch="all"):
    """
    Ejecuta una consulta SQL en PostgreSQL o SQLite de forma transparente.
    fetch: 'all', 'one', 'none', 'insert_id'
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        adapted = adapt_sql(sql)
        
        if fetch == "insert_id":
            if IS_POSTGRES:
                if "RETURNING id" not in adapted.upper():
                    adapted += " RETURNING id"
                cursor.execute(adapted, params or ())
                row = cursor.fetchone()
                conn.commit()
                return row["id"] if row else None
            else:
                # SQLite
                clean_sql = re.sub(r'\s+RETURNING\s+id\s*$', '', sql, flags=re.IGNORECASE)
                cursor.execute(clean_sql, params or ())
                insert_id = cursor.lastrowid
                conn.commit()
                return insert_id

        cursor.execute(adapted, params or ())
        
        if fetch == "all":
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        elif fetch == "one":
            row = cursor.fetchone()
            return dict(row) if row else None
        else:
            conn.commit()
            return None
    finally:
        conn.close()


def init_db():
    """
    Inicializa la base de datos (tablas y semillas iniciales).
    Si es PostgreSQL en Supabase, ejecuta el script schema_supabase.sql si está vacía.
    Si es SQLite, crea el esquema local correspondiente.
    """
    if IS_POSTGRES:
        # En Supabase, verificar si existen las tablas
        check_user = execute_query(
            "SELECT to_regclass('public.usuarios') as tbl",
            fetch="one"
        )
        if not check_user or not check_user.get("tbl"):
            schema_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema_supabase.sql")
            if os.path.exists(schema_file):
                with open(schema_file, "r", encoding="utf-8") as f:
                    sql_content = f.read()
                conn = get_connection()
                try:
                    cur = conn.cursor()
                    cur.execute(sql_content)
                    conn.commit()
                finally:
                    conn.close()
        return

    # Modo SQLite Local
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nombre_completo TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracion (
                id INTEGER PRIMARY KEY,
                universidad TEXT NOT NULL DEFAULT 'UNIVERSIDAD NACIONAL DE SAN LUIS',
                facultad TEXT NOT NULL DEFAULT 'FACULTAD DE INGENIERÍA Y CIENCIAS AGROPECUARIAS',
                normativa TEXT NOT NULL DEFAULT 'Según Decreto Nacional Nro 865/93 y de acuerdo a RR 139/09, la cual en su Anexo II estipula los montos a abonar en concepto de viatico diario, le corresponde un importe de:',
                director_financiero TEXT NOT NULL DEFAULT 'Tec. Carina Roxana Velazquez',
                cargo_dir_financiero TEXT NOT NULL DEFAULT 'Director Financiero',
                secretario_administrativo TEXT NOT NULL DEFAULT 'Esp. Joaquin Flores',
                cargo_sec_administrativo TEXT NOT NULL DEFAULT 'Secretario Administrativo',
                decano TEXT NOT NULL DEFAULT 'Mg. Héctor Daniel FLORES',
                cargo_decano TEXT NOT NULL DEFAULT 'Decano',
                director_economico TEXT NOT NULL DEFAULT 'Tec. Carina Roxana Velazquez',
                cargo_dir_economico TEXT NOT NULL DEFAULT 'Director Económico- Fciero',
                ciudad TEXT NOT NULL DEFAULT 'Villa Mercedes (SL)',
                valor_dolar REAL NOT NULL DEFAULT 1515.0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cargos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                valor_diario REAL NOT NULL DEFAULT 0.0,
                activo INTEGER NOT NULL DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transportes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS imputaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS viaticos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nro_viatico TEXT NOT NULL,
                fecha TEXT NOT NULL,
                apellido_nombre TEXT NOT NULL,
                cargo_codigo TEXT,
                cargo_denominacion TEXT,
                cant_dias REAL DEFAULT 1.0,
                fecha_desde TEXT,
                hora_desde TEXT,
                fecha_hasta TEXT,
                hora_hasta TEXT,
                lugar TEXT,
                mision TEXT,
                medio_transporte TEXT,
                valor_diario REAL DEFAULT 0.0,
                importe_total REAL DEFAULT 0.0,
                imputacion TEXT,
                cheque TEXT,
                f_cheque TEXT,
                expediente TEXT,
                estado TEXT DEFAULT 'Pendiente',
                observaciones TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Usuarios iniciales
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, nombre_completo)
                VALUES (?, ?, ?)
            """, ("admin", generate_password_hash("admin2026"), "Administrador"))
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, nombre_completo)
                VALUES (?, ?, ?)
            """, ("secretaria", generate_password_hash("secretaria2026"), "Secretaría Administrativa"))

        # Configuración inicial
        cursor.execute("SELECT COUNT(*) FROM configuracion")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO configuracion (
                    id, universidad, facultad, normativa,
                    director_financiero, cargo_dir_financiero,
                    secretario_administrativo, cargo_sec_administrativo,
                    decano, cargo_decano,
                    director_economico, cargo_dir_economico,
                    ciudad, valor_dolar
                ) VALUES (
                    1,
                    'UNIVERSIDAD NACIONAL DE SAN LUIS',
                    'FACULTAD DE INGENIERÍA Y CIENCIAS AGROPECUARIAS',
                    'Según Decreto Nacional Nro 865/93 y de acuerdo a RR 139/09, la cual en su Anexo II estipula los montos a abonar en concepto de viatico diario, le corresponde un importe de:',
                    'Tec. Carina Roxana Velazquez', 'Director Financiero',
                    'Esp. Joaquin Flores', 'Secretario Administrativo',
                    'Mg. Héctor Daniel FLORES', 'Decano',
                    'Tec. Carina Roxana Velazquez', 'Director Económico- Fciero',
                    'Villa Mercedes (SL)', 1515.0
                )
            """)

        # Cargos iniciales
        cursor.execute("SELECT COUNT(*) FROM cargos")
        if cursor.fetchone()[0] == 0:
            cargos_iniciales = [
                ("2SE", "Auxiliar de 2º Semi Exclusivo", 80000.0),
                ("2SI", "Auxiliar de 2º Simple", 80000.0),
                ("1EX", "Auxiliar de Primera Exclusivo", 80000.0),
                ("1SE", "Auxiliar de Primera Semi Exclusivo", 80000.0),
                ("1SI", "Auxiliar de Primera Simple", 80000.0),
                ("1TC", "Auxiliar de Primera Tiempo Completo", 80000.0),
                ("JEX", "Jefe de Trabajos Prácticos Exclusivo", 80000.0),
                ("JSE", "Jefe de Trabajos Prácticos Semi Exclusivo", 80000.0),
                ("JSI", "Jefe de Trabajos Prácticos Simple", 80000.0),
                ("JTC", "Jefe de Trabajos Prácticos Tiempo Completo", 80000.0),
                ("ADE", "Profesor Adjunto Exclusivo", 80000.0),
                ("ADS", "Profesor Adjunto Semi Exclusivo", 80000.0),
                ("ADI", "Profesor Adjunto Simple", 80000.0),
                ("ADT", "Profesor Adjunto Tiempo Completo", 80000.0),
                ("ASE", "Profesor Asociado Exclusivo", 80000.0),
                ("ASS", "Profesor Asociado Semi Exclusivo", 80000.0),
                ("ASI", "Profesor Asociado Simple", 80000.0),
                ("AST", "Profesor Asociado Tiempo Completo", 80000.0),
                ("TEX", "Profesor Titular Exclusivo", 80000.0),
                ("TSE", "Profesor Titular Semi Exclusivo", 80000.0),
                ("TSI", "Profesor Titular Simple", 80000.0),
                ("TTC", "Profesor Titular Tiempo Completo", 80000.0),
                ("PAD", "Personal de Apoyo a la Docencia", 80000.0),
                ("CON", "Personal Contratado", 80000.0),
                ("CHO", "Choferes Movilidad", 100000.0),
                ("PV", "Profesor Visitante", 80000.0),
                ("SEC", "Secretario", 100000.0),
                ("VDE", "Vicedecano", 100000.0),
                ("DEC", "Decano", 100000.0),
                ("SECINT", "Secretario Viaje Internacional Zona 1", 100000.0),
            ]
            cursor.executemany("INSERT INTO cargos (codigo, nombre, valor_diario, activo) VALUES (?, ?, ?, 1)", cargos_iniciales)

        # Transportes iniciales
        cursor.execute("SELECT COUNT(*) FROM transportes")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO transportes (nombre) VALUES (?)", [("Terrestre",), ("Aéreo",), ("Vehículo Oficial",), ("Vehículo Propio",)])

        # Imputaciones iniciales
        cursor.execute("SELECT COUNT(*) FROM imputaciones")
        if cursor.fetchone()[0] == 0:
            imputaciones_iniciales = [
                ("Decanato",), ("Dpto Cs Economicas",), ("Dpto Cs Sociales",),
                ("Dpto Cs Juridico Politicas",), ("Dpto de Ingeniería",),
                ("Dpto de Ciencias Agropecuarias",), ("Secretaría Administrativa",),
                ("Secretaría Académica",), ("Secretaría de Ciencia y Técnica",)
            ]
            cursor.executemany("INSERT INTO imputaciones (nombre) VALUES (?)", imputaciones_iniciales)

        conn.commit()
    finally:
        conn.close()


# --- USUARIOS Y AUTENTICACIÓN ---
def get_usuario_by_username(username: str):
    if not username:
        return None
    return execute_query("SELECT * FROM usuarios WHERE username = ?", (username.strip().lower(),), fetch="one")


def get_usuario_by_id(user_id: int):
    return execute_query("SELECT * FROM usuarios WHERE id = ?", (user_id,), fetch="one")


def get_usuarios():
    return execute_query("SELECT id, username, nombre_completo, created_at FROM usuarios ORDER BY id ASC", fetch="all")


def verificar_credenciales(username: str, password: str):
    user = get_usuario_by_username(username)
    if not user:
        return None
    if check_password_hash(user["password_hash"], password):
        return {
            "id": user["id"],
            "username": user["username"],
            "nombre_completo": user["nombre_completo"]
        }
    return None


# --- CONFIGURACIÓN ---
def get_configuracion():
    row = execute_query("SELECT * FROM configuracion WHERE id = 1", fetch="one")
    return row or {}


def update_configuracion(data: dict):
    sql = """
        UPDATE configuracion SET
            universidad = :universidad,
            facultad = :facultad,
            normativa = :normativa,
            director_financiero = :director_financiero,
            cargo_dir_financiero = :cargo_dir_financiero,
            secretario_administrativo = :secretario_administrativo,
            cargo_sec_administrativo = :cargo_sec_administrativo,
            decano = :decano,
            cargo_decano = :cargo_decano,
            director_economico = :director_economico,
            cargo_dir_economico = :cargo_dir_economico,
            ciudad = :ciudad,
            valor_dolar = :valor_dolar
        WHERE id = 1
    """
    execute_query(sql, data, fetch="none")


def get_siguiente_nro_viatico() -> str:
    row = execute_query("SELECT id FROM viaticos ORDER BY id DESC LIMIT 1", fetch="one")
    next_num = (row["id"] + 1) if row else 1
    return f"{next_num:05d}"


# --- CARGOS ---
def get_cargos(solo_activos=True):
    if solo_activos:
        return execute_query("SELECT * FROM cargos WHERE activo = 1 ORDER BY nombre ASC", fetch="all")
    return execute_query("SELECT * FROM cargos ORDER BY nombre ASC", fetch="all")


def get_cargo_by_id(cargo_id: int):
    return execute_query("SELECT * FROM cargos WHERE id = ?", (cargo_id,), fetch="one")


def get_cargo_by_codigo(codigo: str):
    return execute_query("SELECT * FROM cargos WHERE codigo = ?", (codigo.strip(),), fetch="one")


def save_cargo(codigo: str, nombre: str, valor_diario: float, cargo_id: int = None):
    if cargo_id:
        sql = "UPDATE cargos SET codigo = ?, nombre = ?, valor_diario = ? WHERE id = ?"
        execute_query(sql, (codigo.strip().upper(), nombre.strip(), float(valor_diario), cargo_id), fetch="none")
    else:
        sql = "INSERT INTO cargos (codigo, nombre, valor_diario, activo) VALUES (?, ?, ?, 1)"
        execute_query(sql, (codigo.strip().upper(), nombre.strip(), float(valor_diario)), fetch="none")


def delete_cargo(cargo_id: int):
    execute_query("DELETE FROM cargos WHERE id = ?", (cargo_id,), fetch="none")


# --- TRANSPORTES ---
def get_transportes():
    return execute_query("SELECT * FROM transportes ORDER BY nombre ASC", fetch="all")


def add_transporte(nombre: str):
    if IS_POSTGRES:
        execute_query("INSERT INTO transportes (nombre) VALUES (?) ON CONFLICT DO NOTHING", (nombre.strip(),), fetch="none")
    else:
        execute_query("INSERT OR IGNORE INTO transportes (nombre) VALUES (?)", (nombre.strip(),), fetch="none")


def delete_transporte(transporte_id: int):
    execute_query("DELETE FROM transportes WHERE id = ?", (transporte_id,), fetch="none")


# --- IMPUTACIONES ---
def get_imputaciones():
    return execute_query("SELECT * FROM imputaciones ORDER BY nombre ASC", fetch="all")


def add_imputacion(nombre: str):
    if IS_POSTGRES:
        execute_query("INSERT INTO imputaciones (nombre) VALUES (?) ON CONFLICT DO NOTHING", (nombre.strip(),), fetch="none")
    else:
        execute_query("INSERT OR IGNORE INTO imputaciones (nombre) VALUES (?)", (nombre.strip(),), fetch="none")


def delete_imputacion(imputacion_id: int):
    execute_query("DELETE FROM imputaciones WHERE id = ?", (imputacion_id,), fetch="none")


# --- VIATICOS ---
def create_viatico(data: dict) -> int:
    sql = """
        INSERT INTO viaticos (
            nro_viatico, fecha, apellido_nombre,
            cargo_codigo, cargo_denominacion,
            cant_dias, fecha_desde, hora_desde,
            fecha_hasta, hora_hasta, lugar, mision,
            medio_transporte, valor_diario, importe_total,
            imputacion, cheque, f_cheque, expediente,
            estado, observaciones, updated_at
        ) VALUES (
            :nro_viatico, :fecha, :apellido_nombre,
            :cargo_codigo, :cargo_denominacion,
            :cant_dias, :fecha_desde, :hora_desde,
            :fecha_hasta, :hora_hasta, :lugar, :mision,
            :medio_transporte, :valor_diario, :importe_total,
            :imputacion, :cheque, :f_cheque, :expediente,
            :estado, :observaciones, CURRENT_TIMESTAMP
        )
    """
    return execute_query(sql, data, fetch="insert_id")


def update_viatico(viatico_id: int, data: dict):
    data["id"] = viatico_id
    sql = """
        UPDATE viaticos SET
            nro_viatico = :nro_viatico,
            fecha = :fecha,
            apellido_nombre = :apellido_nombre,
            cargo_codigo = :cargo_codigo,
            cargo_denominacion = :cargo_denominacion,
            cant_dias = :cant_dias,
            fecha_desde = :fecha_desde,
            hora_desde = :hora_desde,
            fecha_hasta = :fecha_hasta,
            hora_hasta = :hora_hasta,
            lugar = :lugar,
            mision = :mision,
            medio_transporte = :medio_transporte,
            valor_diario = :valor_diario,
            importe_total = :importe_total,
            imputacion = :imputacion,
            cheque = :cheque,
            f_cheque = :f_cheque,
            expediente = :expediente,
            estado = :estado,
            observaciones = :observaciones,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = :id
    """
    execute_query(sql, data, fetch="none")


def update_estado_viatico(viatico_id: int, estado: str, cheque: str = None, f_cheque: str = None):
    if cheque is not None or f_cheque is not None:
        sql = """
            UPDATE viaticos SET
                estado = ?,
                cheque = COALESCE(?, cheque),
                f_cheque = COALESCE(?, f_cheque),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        execute_query(sql, (estado, cheque, f_cheque, viatico_id), fetch="none")
    else:
        sql = "UPDATE viaticos SET estado = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        execute_query(sql, (estado, viatico_id), fetch="none")


def delete_viatico(viatico_id: int):
    execute_query("DELETE FROM viaticos WHERE id = ?", (viatico_id,), fetch="none")


def get_viatico(viatico_id: int):
    return execute_query("SELECT * FROM viaticos WHERE id = ?", (viatico_id,), fetch="one")


def list_viaticos(fecha_desde=None, fecha_hasta=None, estado=None, imputacion=None, busqueda=None):
    query_str = "SELECT * FROM viaticos WHERE 1=1"
    params = []

    if fecha_desde:
        query_str += " AND fecha >= ?"
        params.append(fecha_desde)
    if fecha_hasta:
        query_str += " AND fecha <= ?"
        params.append(fecha_hasta)
    if estado and estado != "Todos":
        query_str += " AND estado = ?"
        params.append(estado)
    if imputacion and imputacion != "Todas":
        query_str += " AND imputacion = ?"
        params.append(imputacion)
    if busqueda:
        term = f"%{busqueda.strip()}%"
        query_str += " AND (apellido_nombre LIKE ? OR nro_viatico LIKE ? OR lugar LIKE ? OR mision LIKE ? OR expediente LIKE ?)"
        params.extend([term, term, term, term, term])

    query_str += " ORDER BY id DESC"
    return execute_query(query_str, params, fetch="all")


def get_reporte_metricas(fecha_desde=None, fecha_hasta=None, estado=None, imputacion=None, busqueda=None):
    viaticos = list_viaticos(fecha_desde, fecha_hasta, estado, imputacion, busqueda)
    total_cant = len(viaticos)
    total_monto = sum(float(v.get("importe_total") or 0) for v in viaticos)

    pendientes = [v for v in viaticos if v.get("estado") == "Pendiente"]
    pagados = [v for v in viaticos if v.get("estado") == "Pagado"]
    rendidos = [v for v in viaticos if v.get("estado") == "Rendido"]

    return {
        "total_cantidad": total_cant,
        "total_monto": total_monto,
        "pendientes_cantidad": len(pendientes),
        "pendientes_monto": sum(float(v.get("importe_total") or 0) for v in pendientes),
        "pagados_cantidad": len(pagados),
        "pagados_monto": sum(float(v.get("importe_total") or 0) for v in pagados),
        "rendidos_cantidad": len(rendidos),
        "rendidos_monto": sum(float(v.get("importe_total") or 0) for v in rendidos),
        "viaticos": viaticos
    }
