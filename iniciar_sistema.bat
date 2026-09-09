@echo off
setlocal
title Sistema de Gestion de Viaticos - UNSL (FICA / FCEJS)

echo =====================================================================
echo       SISTEMA DE GESTION DE VIATICOS - UNIVERSIDAD NACIONAL DE SAN LUIS
echo       Facultad de Ingenieria y Ciencias Agropecuarias / FCEJS
echo =====================================================================
echo.
echo Detectando entorno de Python...

set "PYTHON_BIN="

if exist "C:\Python314\python.exe" (
    set "PYTHON_BIN=C:\Python314\python.exe"
) else if exist "C:\Python312\python.exe" (
    set "PYTHON_BIN=C:\Python312\python.exe"
) else if exist "%LocalAppData%\Programs\Python\Python314\python.exe" (
    set "PYTHON_BIN=%LocalAppData%\Programs\Python\Python314\python.exe"
) else if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    set "PYTHON_BIN=%LocalAppData%\Programs\Python\Python312\python.exe"
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_BIN=py"
    ) else (
        where python >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_BIN=python"
        )
    )
)

if "%PYTHON_BIN%"=="" (
    echo [ERROR] No se encontro Python en el sistema.
    echo Por favor instale Python y agreguelo al PATH.
    pause
    exit /b 1
)

echo [OK] Utilizando: %PYTHON_BIN%
"%PYTHON_BIN%" --version
echo.

echo Iniciando servidor web en http://127.0.0.1:5000 ...
echo Abriendo navegador web automaticamente...
echo.
echo Presione CTRL + C o cierre esta ventana cuando desee detener el sistema.
echo =====================================================================
echo.

start "" "http://127.0.0.1:5000"
"%PYTHON_BIN%" app.py

pause
