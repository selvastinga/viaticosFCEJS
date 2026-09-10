# Guía Paso a Paso: Despliegue en Supabase y Vercel
**Sistema de Gestión de Viáticos (FCEJS - UNSL)**

Esta guía explica detalladamente cómo publicar la aplicación en internet utilizando **Supabase** como base de datos PostgreSQL en la nube y **Vercel** como servidor de hosting serverless gratuito.

---

## 📌 Requisitos Previos
1. Una cuenta gratuita en [Supabase](https://supabase.com).
2. Una cuenta en [GitHub](https://github.com).
3. Una cuenta gratuita en [Vercel](https://vercel.com).

---

## 🚀 PASO 1: Configurar la Base de Datos en Supabase

1. Inicia sesión en [Supabase](https://supabase.com) y haz clic en **"New Project"**.
2. Completa los datos:
   - **Name**: `sistema-viaticos` (o el nombre que prefieras).
   - **Database Password**: Elige una contraseña segura y **anótala**, la necesitarás en el paso siguiente.
   - **Region**: Selecciona `South America (São Paulo)` para menor latencia.
   - Haz clic en **"Create new project"** y espera 1 o 2 minutos a que se aprovisione.
3. En el menú lateral izquierdo, haz clic en el ícono de **SQL Editor** (`>_`).
4. Haz clic en **"New query"**.
5. Abre el archivo [`schema_supabase.sql`](schema_supabase.sql) de este proyecto, copia todo su contenido, pégalo en el editor de Supabase y haz clic en el botón verde **"Run"**.
   > *¡Listo! Esto creará automáticamente todas las tablas (`usuarios`, `cargos`, `viaticos`, `configuracion`, etc.) y cargará los 30 cargos oficiales de `opciones.pdf` y los 2 usuarios iniciales.*
6. En el menú lateral izquierdo, haz clic en el ícono de engranaje **Project Settings** -> **Database**.
7. Desplázate hacia abajo hasta la sección **Connection string**:
   - Selecciona la pestaña **URI**.
   - Haz clic en el botón de copiar. La URL tendrá un formato similar a:
     ```
     postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxx.supabase.co:5432/postgres
     ```
   - Reemplaza `[YOUR-PASSWORD]` por la contraseña que creaste en el paso 2. **Guarda esta cadena para el Paso 3.**

---

## 📦 PASO 2: Subir el Código a GitHub

Abre una terminal (PowerShell o CMD) en la carpeta de este proyecto (`Sistema_viaticos_fcejs`) y ejecuta los siguientes comandos:

```bash
# 1. Inicializar el repositorio Git
git init

# 2. Agregar todos los archivos (el .gitignore ya protege archivos locales)
git add .

# 3. Crear el primer commit
git commit -m "Sistema de viaticos preparado para Vercel y Supabase"

# 4. Cambiar la rama principal a main
git branch -M main
```

Luego:
1. Entra en tu cuenta de [GitHub](https://github.com) y crea un nuevo repositorio (por ejemplo: `sistema-viaticos-unsl`), público o privado.
2. Copia la URL del repositorio (ejemplo: `https://github.com/tu-usuario/sistema-viaticos-unsl.git`).
3. En tu terminal ejecuta:
```bash
git remote add origin https://github.com/tu-usuario/sistema-viaticos-unsl.git
git push -u origin main
```

---

## 🌐 PASO 3: Desplegar en Vercel

1. Inicia sesión en [Vercel](https://vercel.com) (puedes ingresar con tu cuenta de GitHub).
2. En el Dashboard de Vercel, haz clic en **"Add New..."** -> **"Project"**.
3. Busca tu repositorio de GitHub recién creado (`sistema-viaticos-unsl`) y haz clic en **"Import"**.
4. En la pantalla de configuración del proyecto:
   - **Framework Preset**: Dejar en `Other`.
   - **Root Directory**: `./` (raíz).
5. Despliega la sección **"Environment Variables"** y agrega las siguientes dos variables:
   - **Nombre**: `DATABASE_URL`  
     **Valor**: Pega la URI completa de Supabase del Paso 1 (ej: `postgresql://postgres:MiClave@db.xxxx.supabase.co:5432/postgres`).
   - **Nombre**: `SECRET_KEY`  
     **Valor**: Escribe cualquier frase secreta (ej: `unsl-viaticos-produccion-2026-seguro`).
   - Haz clic en **"Add"** para cada una.
6. Haz clic en el botón azul **"Deploy"**.
7. Vercel compilará la aplicación y en aproximadamente 1 minuto te entregará la URL pública oficial (por ejemplo: `https://sistema-viaticos-unsl.vercel.app`).

---

## 🔑 PASO 4: Ingreso a la Aplicación en la Nube

Al abrir la URL proporcionada por Vercel, verás la pantalla de inicio de sesión. Ingresa con cualquiera de los 2 usuarios:

| Usuario | Contraseña | Rol |
| :--- | :--- | :--- |
| **`admin`** | `admin2026` | Administrador total |
| **`secretaria`** | `secretaria2026` | Administrador total |

---

## 💡 Ventajas de esta Configuración
- **Cero costo de servidores**: Tanto Supabase como Vercel cuentan con planes gratuitos permanentes muy generosos para este tipo de aplicaciones universitarias.
- **Base de datos segura y con respaldos**: Todos los viáticos, cargas y reportes quedan permanentemente almacenados en PostgreSQL en Supabase.
- **Acceso desde cualquier lugar**: Las secretarias y autoridades pueden consultar o autorizar viáticos desde cualquier computadora o dispositivo sin necesidad de instalar nada.
- **Modo Offline intacto**: Si alguien necesita usar el sistema de forma local en una computadora sin internet, el archivo `iniciar_sistema.bat` sigue funcionando normalmente con la base de datos local SQLite.
