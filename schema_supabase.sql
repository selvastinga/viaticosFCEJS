-- ============================================================================
-- SCRIPT DE MIGRACIÓN PARA SUPABASE (POSTGRESQL)
-- Sistema de Gestión de Viáticos - Universidad Nacional de San Luis
-- Facultad de Ciencias Ecnomicas Juridicas y Sociales/ FCEJS
-- ============================================================================
-- Instrucciones: Copiar todo este contenido y pegarlo en el "SQL Editor" de
-- su panel de proyecto en Supabase, luego hacer clic en "Run".
-- ============================================================================

-- 1. TABLA DE USUARIOS
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nombre_completo VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABLA DE CONFIGURACIÓN INSTITUCIONAL
CREATE TABLE IF NOT EXISTS configuracion (
    id INT PRIMARY KEY,
    universidad VARCHAR(255) NOT NULL DEFAULT 'UNIVERSIDAD NACIONAL DE SAN LUIS',
    facultad VARCHAR(255) NOT NULL DEFAULT 'FACULTAD DE CIENCIAS ECONÓMICAS, JURÍDICAS Y SOCIALES',
    normativa TEXT NOT NULL DEFAULT 'Según Decreto Nacional Nro 865/93 y de acuerdo a RR 139/09, la cual en su Anexo II estipula los montos a abonar en concepto de viatico diario, le corresponde un importe de:',
    director_financiero VARCHAR(255) NOT NULL DEFAULT 'Tec. Carina Roxana Velazquez',
    cargo_dir_financiero VARCHAR(255) NOT NULL DEFAULT 'Director Financiero',
    secretario_administrativo VARCHAR(255) NOT NULL DEFAULT 'Esp. Joaquin Flores',
    cargo_sec_administrativo VARCHAR(255) NOT NULL DEFAULT 'Secretario Administrativo',
    decano VARCHAR(255) NOT NULL DEFAULT 'Mg. Héctor Daniel FLORES',
    cargo_decano VARCHAR(255) NOT NULL DEFAULT 'Decano',
    director_economico VARCHAR(255) NOT NULL DEFAULT 'Tec. Carina Roxana Velazquez',
    cargo_dir_economico VARCHAR(255) NOT NULL DEFAULT 'Director Económico- Fciero',
    ciudad VARCHAR(100) NOT NULL DEFAULT 'Villa Mercedes (SL)',
    valor_dolar NUMERIC(12, 2) NOT NULL DEFAULT 1515.0
);

-- 3. TABLA DE CARGOS Y VALORES DIARIOS (opciones.pdf)
CREATE TABLE IF NOT EXISTS cargos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    valor_diario NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
    activo INT NOT NULL DEFAULT 1
);

-- 4. TABLA DE MEDIOS DE TRANSPORTE
CREATE TABLE IF NOT EXISTS transportes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL
);

-- 5. TABLA DE IMPUTACIONES PRESUPUESTARIAS
CREATE TABLE IF NOT EXISTS imputaciones (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) UNIQUE NOT NULL
);

-- 6. TABLA PRINCIPAL DE VIÁTICOS
CREATE TABLE IF NOT EXISTS viaticos (
    id SERIAL PRIMARY KEY,
    nro_viatico VARCHAR(50) NOT NULL,
    fecha VARCHAR(20) NOT NULL,
    apellido_nombre VARCHAR(255) NOT NULL,
    cargo_codigo VARCHAR(50),
    cargo_denominacion VARCHAR(255),
    cant_dias NUMERIC(6, 2) DEFAULT 1.0,
    fecha_desde VARCHAR(20),
    hora_desde VARCHAR(20),
    fecha_hasta VARCHAR(20),
    hora_hasta VARCHAR(20),
    lugar VARCHAR(255),
    mision TEXT,
    medio_transporte VARCHAR(100),
    valor_diario NUMERIC(12, 2) DEFAULT 0.0,
    importe_total NUMERIC(12, 2) DEFAULT 0.0,
    imputacion VARCHAR(255),
    cheque VARCHAR(100),
    f_cheque VARCHAR(20),
    expediente VARCHAR(100),
    estado VARCHAR(50) DEFAULT 'Pendiente',
    observaciones TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DATOS INICIALES Y SEMILLAS
-- ============================================================================

-- A. Usuarios administradores iniciales
INSERT INTO usuarios (username, password_hash, nombre_completo)
VALUES 
    ('admin', 'scrypt:32768:8:1$Zr13W7WyiNgIaE63$ac3749f4ddf4952c6c4686236b9323ce1f9096b151d9e3e9973c63f32d809f33918333b4b539e341b825ddea797032d44119cb7b0198d84a0dec75412f7b09e3', 'Administrador'),
    ('secretaria', 'scrypt:32768:8:1$2TNp22qKWqSEW5K3$b27164b4f9398491c3282592e94718c6eccb2d58d74cfbe17418a7e3215d936d40feaf871b22c802d78560244486b5de6174f58d4dc67191f2fc9b44d5926a59', 'Secretaría Administrativa')
ON CONFLICT (username) DO NOTHING;

-- B. Configuración institucional inicial
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
    'FACULTAD DE CIENCIAS ECONÓMICAS, JURÍDICAS Y SOCIALES',
    'Según Decreto Nacional Nro 865/93 y de acuerdo a RR 139/09, la cual en su Anexo II estipula los montos a abonar en concepto de viatico diario, le corresponde un importe de:',
    'Tec. Carina Roxana Velazquez', 'Director Financiero',
    'Esp. Joaquin Flores', 'Secretario Administrativo',
    'Mg. Héctor Daniel FLORES', 'Decano',
    'Tec. Carina Roxana Velazquez', 'Director Económico- Fciero',
    'Villa Mercedes (SL)', 1515.0
) ON CONFLICT (id) DO NOTHING;

-- Asegurar actualización en bases ya creadas
UPDATE configuracion SET facultad = 'FACULTAD DE CIENCIAS ECONÓMICAS, JURÍDICAS Y SOCIALES' WHERE facultad LIKE '%INGENIER%';

-- C. 30 Cargos oficiales de opciones.pdf
INSERT INTO cargos (codigo, nombre, valor_diario, activo) VALUES
    ('2SE', 'Auxiliar de 2º Semi Exclusivo', 80000.0, 1),
    ('2SI', 'Auxiliar de 2º Simple', 80000.0, 1),
    ('1EX', 'Auxiliar de Primera Exclusivo', 80000.0, 1),
    ('1SE', 'Auxiliar de Primera Semi Exclusivo', 80000.0, 1),
    ('1SI', 'Auxiliar de Primera Simple', 80000.0, 1),
    ('1TC', 'Auxiliar de Primera Tiempo Completo', 80000.0, 1),
    ('JEX', 'Jefe de Trabajos Prácticos Exclusivo', 80000.0, 1),
    ('JSE', 'Jefe de Trabajos Prácticos Semi Exclusivo', 80000.0, 1),
    ('JSI', 'Jefe de Trabajos Prácticos Simple', 80000.0, 1),
    ('JTC', 'Jefe de Trabajos Prácticos Tiempo Completo', 80000.0, 1),
    ('ADE', 'Profesor Adjunto Exclusivo', 80000.0, 1),
    ('ADS', 'Profesor Adjunto Semi Exclusivo', 80000.0, 1),
    ('ADI', 'Profesor Adjunto Simple', 80000.0, 1),
    ('ADT', 'Profesor Adjunto Tiempo Completo', 80000.0, 1),
    ('ASE', 'Profesor Asociado Exclusivo', 80000.0, 1),
    ('ASS', 'Profesor Asociado Semi Exclusivo', 80000.0, 1),
    ('ASI', 'Profesor Asociado Simple', 80000.0, 1),
    ('AST', 'Profesor Asociado Tiempo Completo', 80000.0, 1),
    ('TEX', 'Profesor Titular Exclusivo', 80000.0, 1),
    ('TSE', 'Profesor Titular Semi Exclusivo', 80000.0, 1),
    ('TSI', 'Profesor Titular Simple', 80000.0, 1),
    ('TTC', 'Profesor Titular Tiempo Completo', 80000.0, 1),
    ('PAD', 'Personal de Apoyo a la Docencia', 80000.0, 1),
    ('CON', 'Personal Contratado', 80000.0, 1),
    ('CHO', 'Choferes Movilidad', 100000.0, 1),
    ('PV', 'Profesor Visitante', 80000.0, 1),
    ('SEC', 'Secretario', 100000.0, 1),
    ('VDE', 'Vicedecano', 100000.0, 1),
    ('DEC', 'Decano', 100000.0, 1),
    ('SECINT', 'Secretario Viaje Internacional Zona 1', 100000.0, 1)
ON CONFLICT (codigo) DO NOTHING;

-- D. Medios de transporte iniciales
INSERT INTO transportes (nombre) VALUES
    ('Terrestre'),
    ('Aéreo'),
    ('Vehículo Oficial'),
    ('Vehículo Propio')
ON CONFLICT (nombre) DO NOTHING;

-- E. Imputaciones presupuestarias iniciales
INSERT INTO imputaciones (nombre) VALUES
    ('Decanato'),
    ('Dpto Cs Economicas'),
    ('Dpto Cs Sociales'),
    ('Dpto Cs Juridico Politicas'),
    ('Secretaría Administrativa'),
    ('Secretaría Académica'),
    ('Secretaría de Ciencia y Técnica'),
    ('Secretaría de Extensión'),
    ('Secretaría de Posgrado')
ON CONFLICT (nombre) DO NOTHING;

-- Limpiar imputaciones de otra facultad si existen
DELETE FROM imputaciones WHERE nombre IN ('Dpto de Ingeniería', 'Dpto de Ciencias Agropecuarias');
