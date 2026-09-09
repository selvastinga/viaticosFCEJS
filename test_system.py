"""
Suite de pruebas automatizadas para el Sistema de Viáticos con Autenticación.
"""
import unittest
import json
import io
import pypdf
import openpyxl

from app import app
import database


class ViaticosAuthSystemTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        database.init_db()

    def test_01_bloqueo_sin_autenticacion(self):
        """Verifica que un usuario no autenticado no puede acceder a las páginas ni APIs"""
        # Acceso a la página principal debe redirigir a /login
        res = self.client.get("/")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers.get("Location", ""))

        # Acceso a APIs sin sesión debe devolver 401 Unauthorized
        res_api = self.client.get("/api/viaticos")
        self.assertEqual(res_api.status_code, 401)
        self.assertIn("error", res_api.get_json())

        res_inicial = self.client.get("/api/inicial")
        self.assertEqual(res_inicial.status_code, 401)

        # Intento de agregar viático sin autenticación debe dar 401
        res_post = self.client.post("/api/viaticos", json={"apellido_nombre": "PRUEBA"})
        self.assertEqual(res_post.status_code, 401)

    def test_02_login_usuarios_y_logout(self):
        """Verifica login con credenciales erróneas y con ambos usuarios (admin y secretaria)"""
        # Login fallido
        res_fail = self.client.post("/login", data={
            "username": "admin",
            "password": "clave_incorrecta"
        }, follow_redirects=True)
        self.assertIn(b"incorrectos", res_fail.data)

        # Login exitoso con usuario 'admin'
        res_admin = self.client.post("/login", data={
            "username": "admin",
            "password": "admin2026"
        })
        self.assertEqual(res_admin.status_code, 302)

        # Verificar que ahora tiene acceso a la página principal y APIs
        res_home = self.client.get("/")
        self.assertEqual(res_home.status_code, 200)
        self.assertIn(b"admin", res_home.data)

        # Cerrar sesión
        res_logout = self.client.get("/logout")
        self.assertEqual(res_logout.status_code, 302)

        # Tras cerrar sesión, el acceso a "/" debe volver a bloquearse
        res_blocked = self.client.get("/")
        self.assertEqual(res_blocked.status_code, 302)

        # Login exitoso con segundo usuario 'secretaria'
        res_sec = self.client.post("/login", data={
            "username": "secretaria",
            "password": "secretaria2026"
        })
        self.assertEqual(res_sec.status_code, 302)

        res_home_sec = self.client.get("/")
        self.assertEqual(res_home_sec.status_code, 200)
        self.assertIn(b"secretaria", res_home_sec.data)

    def test_03_operaciones_completas_autenticado(self):
        """Verifica todo el flujo operativo (CRUD, PDF, Excel, Reportes) con usuario logueado"""
        # Iniciar sesión como secretaria
        self.client.post("/login", data={
            "username": "secretaria",
            "password": "secretaria2026"
        })

        # 1. Obtener datos iniciales
        res_init = self.client.get("/api/inicial")
        self.assertEqual(res_init.status_code, 200)
        init_data = res_init.get_json()
        self.assertGreaterEqual(len(init_data["cargos"]), 30)
        self.assertEqual(init_data["usuario"]["username"], "secretaria")

        # 2. Crear viático oficial
        payload = {
            "nro_viatico": "00002",
            "fecha": "2026-09-08",
            "apellido_nombre": "GUAYCOCHEA MONICA BEATRIZ",
            "cargo_codigo": "ADE",
            "cargo_denominacion": "Profesor Adjunto Exclusivo",
            "cant_dias": 3.0,
            "fecha_desde": "2026-09-10",
            "hora_desde": "07:00",
            "fecha_hasta": "2026-09-13",
            "hora_hasta": "7:00",
            "lugar": "San Luis",
            "mision": "CONGRESO FAUATS",
            "medio_transporte": "Terrestre",
            "valor_diario": 80000.0,
            "importe_total": 240000.0,
            "imputacion": "Decanato",
            "cheque": "",
            "f_cheque": "",
            "expediente": "EXP-101/2026",
            "estado": "Pendiente"
        }

        res_create = self.client.post("/api/viaticos", json=payload)
        self.assertEqual(res_create.status_code, 201)
        v_id = res_create.get_json()["id"]

        # 3. Generar PDF oficial A4
        res_pdf = self.client.get(f"/api/viaticos/{v_id}/pdf")
        self.assertEqual(res_pdf.status_code, 200)
        pdf_reader = pypdf.PdfReader(io.BytesIO(res_pdf.data))
        self.assertEqual(len(pdf_reader.pages), 1)
        text = pdf_reader.pages[0].extract_text()
        self.assertIn("GUAYCOCHEA MONICA BEATRIZ", text)
        self.assertIn("240.000,00", text)

        # 4. Cambiar estado a Pagado con Cheque
        res_est = self.client.patch(f"/api/viaticos/{v_id}/estado", json={
            "estado": "Pagado",
            "cheque": "CHQ-8899",
            "f_cheque": "2026-09-08"
        })
        self.assertEqual(res_est.status_code, 200)

        # 5. Generar reporte PDF y Excel
        res_rep_pdf = self.client.get("/api/reportes/pdf")
        self.assertEqual(res_rep_pdf.status_code, 200)

        res_rep_excel = self.client.get("/api/reportes/excel")
        self.assertEqual(res_rep_excel.status_code, 200)
        wb = openpyxl.load_workbook(io.BytesIO(res_rep_excel.data))
        self.assertIn("Reporte de Viáticos", wb.sheetnames)

        # 6. Eliminar viático
        res_del = self.client.delete(f"/api/viaticos/{v_id}")
        self.assertEqual(res_del.status_code, 200)


if __name__ == "__main__":
    unittest.main()
