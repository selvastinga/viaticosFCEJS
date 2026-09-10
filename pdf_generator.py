"""
Generador de documentos PDF para el Sistema de Viáticos.
- Planilla oficial individual de viático (A4, formato idéntico a salida.pdf)
- Reporte consolidado de viáticos por fechas y estado
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

import utils

PAGE_WIDTH, PAGE_HEIGHT = A4  # 595.276, 841.89


def draw_section_banner(c: canvas.Canvas, y: float, title: str, subtitle: str = None, height: float = 16.0):
    """
    Dibuja una barra horizontal gris con borde y texto centrado en mayúsculas negrita.
    """
    x_start = 45
    width = PAGE_WIDTH - 90
    
    # Fondo gris claro con borde fino negro
    c.setFillColor(colors.HexColor("#D8D8D8"))
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.rect(x_start, y, width, height, fill=1, stroke=1)
    
    # Texto
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(PAGE_WIDTH / 2.0, y + (height - 9) / 2.0 + 1, title)
    
    if subtitle:
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(PAGE_WIDTH / 2.0, y - 11, subtitle)


def draw_signature_block(c: canvas.Canvas, y_line: float, left_title: str, left_name: str, right_title: str, right_name: str = ""):
    """
    Dibuja dos líneas de firma enfrentadas con doble línea como en el original.
    """
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.6)
    
    # Línea izquierda (doble)
    x1_left = 60
    x2_left = 250
    c.line(x1_left, y_line, x2_left, y_line)
    c.line(x1_left, y_line - 1.5, x2_left, y_line - 1.5)
    
    # Línea derecha (doble)
    x1_right = 345
    x2_right = 535
    c.line(x1_right, y_line, x2_right, y_line)
    c.line(x1_right, y_line - 1.5, x2_right, y_line - 1.5)
    
    # Textos izquierda
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    center_left = (x1_left + x2_left) / 2.0
    c.drawCentredString(center_left, y_line - 12, left_title)
    if left_name:
        c.drawCentredString(center_left, y_line - 22, left_name)
        
    # Textos derecha
    center_right = (x1_right + x2_right) / 2.0
    c.drawCentredString(center_right, y_line - 12, right_title)
    if right_name:
        c.drawCentredString(center_right, y_line - 22, right_name)


def generar_pdf_viatico(viatico: dict, config: dict, output_target) -> None:
    """
    Genera el formulario oficial de liquidación de viáticos en hoja A4 exacta como salida.pdf.
    """
    c = canvas.Canvas(output_target, pagesize=A4)
    c.setTitle(f"Solicitud_Viatico_{viatico.get('nro_viatico', '00000')}")
    
    # ------------------ ENCABEZADO ------------------
    # Escudo UNSL
    logo_path = os.path.join(os.path.dirname(__file__), "static", "img", "unsl_logo.jpg")
    if os.path.exists(logo_path):
        try:
            # Tamaño 44 x 54 pt (el logo ya incluye las letras 'Universidad Nacional de San Luis')
            c.drawImage(logo_path, 60, 745, width=44, height=54, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
            
    # Títulos centrales
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)
    univ_nombre = config.get("universidad", "UNIVERSIDAD NACIONAL DE SAN LUIS")
    fac_nombre = config.get("facultad", "FACULTAD DE CIENCIAS ECONÓMICAS, JURÍDICAS Y SOCIALES")
    c.drawCentredString(300, 778, univ_nombre)
    c.setFont("Helvetica", 10)
    c.drawCentredString(300, 763, fac_nombre)
    
    # Recuadro Solicitud y Fecha (superior derecha)
    c.setFont("Helvetica", 9)
    c.drawString(455, 785, "Solicitud N:")
    # Cajita con número
    nro_v = str(viatico.get("nro_viatico", "1")).lstrip("0") or "1"
    c.setStrokeColor(colors.black)
    c.setLineWidth(1.2)
    c.rect(515, 781, 40, 16, fill=0, stroke=1)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(535, 785, nro_v)
    
    c.setFont("Helvetica", 9)
    c.drawString(455, 765, "Fecha:")
    fecha_solicitud = utils.formato_fecha(viatico.get("fecha"))
    c.drawRightString(555, 765, fecha_solicitud)
    
    # ------------------ SECCIÓN 1: INTERVENCIÓN SECRETARÍA ADMINISTRATIVA ------------------
    y_sec1 = 718
    draw_section_banner(c, y_sec1, "INTERVENCIÓN DE LA SECRETARÍA ADMINISTRATIVA DE LA FACULTAD")
    
    # Texto normativa en 2 líneas
    c.setFont("Helvetica", 8)
    linea1 = "Según Decreto Nacional Nro 865/93 y de acuerdo a RR 139/09, la cual en su Anexo II estipula los montos"
    linea2 = "a abonar en concepto de viatico diario, le corresponde un importe de:"
    c.drawString(45, y_sec1 - 18, linea1)
    c.drawString(45, y_sec1 - 29, linea2)
    
    val_diario_num = float(viatico.get("valor_diario") or 0.0)
    val_diario_sin_signo = f"{val_diario_num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    c.setFont("Helvetica", 8)
    c.drawRightString(PAGE_WIDTH - 45, y_sec1 - 29, val_diario_sin_signo)
    
    # Subtítulo LIQUIDACIÓN
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(45, y_sec1 - 48, "LIQUIDACIÓN")
    
    # Desglose días y monto
    cant_dias = float(viatico.get("cant_dias") or 0.0)
    if cant_dias.is_integer():
        cant_dias_str = f"{int(cant_dias):d},00"
        duracion_str = f"{int(cant_dias):d},0 días"
    else:
        cant_dias_str = f"{cant_dias:.2f}".replace(".", ",")
        duracion_str = f"{cant_dias:.1f} días".replace(".", ",")
        
    val_diario_fmt = utils.formato_moneda(val_diario_num)
    imp_total_num = float(viatico.get("importe_total") or 0.0)
    imp_total_fmt = utils.formato_moneda(imp_total_num)
    
    c.setFont("Helvetica", 8.5)
    c.drawString(100, y_sec1 - 62, f"{cant_dias_str} días a pesos")
    c.drawString(185, y_sec1 - 62, val_diario_fmt)
    c.drawString(275, y_sec1 - 62, "Son pesos")
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(330, y_sec1 - 62, imp_total_fmt)
    
    # Líquido a cobrar con línea punteada limpia sin tapar el monto
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(100, y_sec1 - 85, "LÍQUIDO A COBRAR")
    c.setDash([2, 3])
    c.setLineWidth(0.7)
    c.line(205, y_sec1 - 82, 315, y_sec1 - 82)
    c.setDash([])
    c.drawString(330, y_sec1 - 85, imp_total_fmt)
    
    # Fecha y Son en letras
    c.setFont("Helvetica", 8.5)
    c.drawString(405, y_sec1 - 98, "Fecha:")
    c.drawString(455, y_sec1 - 98, fecha_solicitud)
    
    c.drawString(100, y_sec1 - 114, f"Son: {utils.numero_a_letras(imp_total_num)}")
    
    # Firmas sección 1
    y_firmas1 = 572
    draw_signature_block(
        c, y_firmas1,
        config.get("cargo_dir_financiero", "Director Financiero"),
        config.get("director_financiero", "Tec. Carina Roxana Velazquez"),
        config.get("cargo_sec_administrativo", "Secretario Administrativo"),
        config.get("secretario_administrativo", "Esp. Joaquin Flores")
    )
    
    # ------------------ SECCIÓN 2: RESOLUCIÓN FACULTAD ------------------
    y_sec2 = 530
    draw_section_banner(c, y_sec2, "RESOLUCIÓN FACULTAD")
    
    c.setFont("Helvetica", 8)
    c.drawString(45, y_sec2 - 16, "Autorízase la presente liquidación de viáticos. Páguese por donde corresponda")
    
    ciudad_str = config.get("ciudad", "Villa Mercedes (SL)")
    c.drawString(380, y_sec2 - 25, f"{ciudad_str}, {fecha_solicitud}")
    
    y_firmas2 = 465
    draw_signature_block(
        c, y_firmas2,
        config.get("cargo_sec_administrativo", "Secretario Administrativo"),
        config.get("secretario_administrativo", "Esp. Joaquin Flores"),
        config.get("cargo_decano", "Decano"),
        config.get("decano", "Mg. Héctor Daniel FLORES")
    )
    
    # ------------------ SECCIÓN 3: DIRECCIÓN CONTABLE ------------------
    y_sec3 = 422
    draw_section_banner(c, y_sec3, "DIRECCIÓN CONTABLE")
    
    c.setFont("Helvetica", 8)
    c.drawString(45, y_sec3 - 17, f"Se procedió al pago ordenado. Son pesos")
    c.setFont("Helvetica-Bold", 8)
    c.drawString(245, y_sec3 - 17, imp_total_fmt)
    
    chq_num = viatico.get("cheque") or ""
    c.setFont("Helvetica", 8)
    c.drawString(45, y_sec3 - 30, "Efectivo:")
    c.drawString(360, y_sec3 - 30, f"Transferencia Nº   {chq_num}")
    c.drawString(380, y_sec3 - 42, f"{ciudad_str},")
    
    y_firmas3 = 352
    draw_signature_block(
        c, y_firmas3,
        "Recibí Conforme", "",
        config.get("cargo_dir_economico", "Director Económico- Fciero"),
        config.get("director_economico", "Tec. Carina Roxana Velazquez")
    )
    
    # ------------------ SECCIÓN 4: INFORME DEL DESARROLLO DE LA MISIÓN ------------------
    y_sec4 = 308
    draw_section_banner(c, y_sec4, "INFORME DEL DESARROLLO DE LA MISIÓN", "(A formularse dentro de las 48Hs de cumplida)")
    
    # Datos de la misión
    y_info = y_sec4 - 26
    c.setFont("Helvetica", 7.5)
    
    # Fila 1: Apellido y Nombre
    c.drawString(45, y_info, "Apellido y Nombre:")
    c.setFont("Helvetica-Bold", 8)
    c.drawString(130, y_info, (viatico.get("apellido_nombre") or "").upper())
    
    # Fila 2: Cargo
    y_info -= 14
    c.setFont("Helvetica", 7.5)
    c.drawString(45, y_info, "Cargo:")
    cargo_texto = viatico.get("cargo_denominacion") or viatico.get("cargo_codigo") or ""
    c.setFont("Helvetica", 8)
    c.drawString(130, y_info, cargo_texto)
    
    # Fila 3: Salida, Hora, Medio
    y_info -= 14
    c.setFont("Helvetica", 7.5)
    c.drawString(45, y_info, "Salida:")
    c.setFont("Helvetica", 8)
    c.drawString(130, y_info, utils.formato_fecha(viatico.get("fecha_desde")))
    c.setFont("Helvetica", 7.5)
    c.drawString(235, y_info, "Hora Salida:")
    c.setFont("Helvetica", 8)
    c.drawString(290, y_info, viatico.get("hora_desde") or "")
    c.setFont("Helvetica", 7.5)
    c.drawString(360, y_info, "Medio Transporte")
    c.setFont("Helvetica-Bold", 8)
    c.drawString(450, y_info, viatico.get("medio_transporte") or "Terrestre")
    
    # Fila 4: Llegada, Hora
    y_info -= 14
    c.setFont("Helvetica", 7.5)
    c.drawString(45, y_info, "Llegada:")
    c.setFont("Helvetica", 8)
    c.drawString(130, y_info, utils.formato_fecha(viatico.get("fecha_hasta")))
    c.setFont("Helvetica", 7.5)
    c.drawString(235, y_info, "Hora Llegada:")
    c.setFont("Helvetica", 8)
    c.drawString(290, y_info, viatico.get("hora_hasta") or "")
    
    # Fila 5: Misión y Lugar
    y_info -= 14
    c.setFont("Helvetica", 7.5)
    c.drawString(45, y_info, "Misión:")
    c.setFont("Helvetica", 8)
    lugar = viatico.get("lugar") or ""
    mision = viatico.get("mision") or ""
    mision_completa = f"{mision} - {lugar}" if lugar and lugar not in mision else mision
    c.drawString(130, y_info, mision_completa[:75])
    
    # Fila 6: Duración
    y_info -= 14
    c.setFont("Helvetica", 7.5)
    c.drawString(45, y_info, "Duración Misión:")
    c.setFont("Helvetica", 8)
    c.drawString(220, y_info, duracion_str)
    
    # Fila 7: Liquidación N°, Importe, Fecha
    y_info -= 14
    c.setFont("Helvetica", 7.5)
    c.drawString(45, y_info, "Liquidación Nº")
    c.setFont("Helvetica", 8)
    c.drawString(130, y_info, nro_v)
    c.setFont("Helvetica", 7.5)
    c.drawString(205, y_info, "Importe")
    c.setFont("Helvetica-Bold", 8)
    c.drawString(245, y_info, imp_total_fmt)
    c.setFont("Helvetica", 7.5)
    c.drawString(335, y_info, "Fecha")
    c.setFont("Helvetica", 8)
    c.drawString(370, y_info, fecha_solicitud)
    
    # Firmas sección 4
    y_firmas4 = 115
    draw_signature_block(
        c, y_firmas4,
        "Firma Beneficiario", "",
        "Firma Jefe Dependencia",
        config.get("decano", "Mg. Héctor Daniel FLORES")
    )
    
    c.showPage()
    c.save()


def generar_pdf_reporte(metricas: dict, viaticos: list, config: dict, filtros: dict, output_target) -> None:
    """
    Genera un reporte consolidado en PDF con formato institucional y tabla de viáticos.
    """
    doc = SimpleDocTemplate(
        output_target,
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
        topMargin=35,
        bottomMargin=35
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        alignment=1,  # Center
        textColor=colors.HexColor("#1e293b")
    )
    sub_style = ParagraphStyle(
        "ReportSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        alignment=1,
        textColor=colors.HexColor("#475569")
    )
    th_style = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        alignment=1,
        textColor=colors.white
    )
    td_style = ParagraphStyle(
        "TD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#1e293b")
    )
    td_bold = ParagraphStyle(
        "TDBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#1e293b")
    )
    
    elements = []
    
    # Encabezado institucional
    univ = config.get("universidad", "UNIVERSIDAD NACIONAL DE SAN LUIS")
    fac = config.get("facultad", "FACULTAD DE CIENCIAS ECONÓMICAS, JURÍDICAS Y SOCIALES")
    elements.append(Paragraph(univ, title_style))
    elements.append(Paragraph(fac, sub_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("<b>REPORTE OFICIAL DE VIÁTICOS</b>", title_style))
    
    # Texto con filtros aplicados
    f_desde = utils.formato_fecha(filtros.get("fecha_desde")) or "Inicio"
    f_hasta = utils.formato_fecha(filtros.get("fecha_hasta")) or "Fin"
    estado_filtro = filtros.get("estado") or "Todos"
    elements.append(Paragraph(f"Período: <b>{f_desde}</b> al <b>{f_hasta}</b> | Estado: <b>{estado_filtro}</b> | Emitido el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", sub_style))
    elements.append(Spacer(1, 10))
    
    # Tabla resumen de métricas
    resumen_data = [
        [
            Paragraph("<b>Total Solicitudes</b>", td_style),
            Paragraph("<b>Total Liquidado</b>", td_style),
            Paragraph("<b>Pendientes</b>", td_style),
            Paragraph("<b>Pagados</b>", td_style),
            Paragraph("<b>Rendidos</b>", td_style),
        ],
        [
            Paragraph(f"<b>{metricas.get('total_cantidad', 0)}</b>", td_bold),
            Paragraph(f"<b>{utils.formato_moneda(metricas.get('total_monto', 0))}</b>", td_bold),
            Paragraph(f"{metricas.get('pendientes_cantidad', 0)} ({utils.formato_moneda(metricas.get('pendientes_monto', 0))})", td_style),
            Paragraph(f"{metricas.get('pagados_cantidad', 0)} ({utils.formato_moneda(metricas.get('pagados_monto', 0))})", td_style),
            Paragraph(f"{metricas.get('rendidos_cantidad', 0)} ({utils.formato_moneda(metricas.get('rendidos_monto', 0))})", td_style),
        ]
    ]
    resumen_table = Table(resumen_data, colWidths=[90, 120, 110, 110, 105])
    resumen_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#ffffff")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(resumen_table)
    elements.append(Spacer(1, 12))
    
    # Tabla detallada de viáticos
    headers = ["N°", "Fecha", "Beneficiario", "Cargo", "Fechas Viaje", "Días", "Total", "Imputación", "Transferencia", "Estado"]
    col_widths = [32, 45, 105, 65, 75, 25, 55, 55, 55, 48]
    
    table_rows = [[Paragraph(h, th_style) for h in headers]]
    
    for v in viaticos:
        d_viaje = f"{utils.formato_fecha(v.get('fecha_desde'))}<br/>{utils.formato_fecha(v.get('fecha_hasta'))}"
        estado = v.get("estado", "Pendiente")
        table_rows.append([
            Paragraph(str(v.get("nro_viatico", "")), td_style),
            Paragraph(utils.formato_fecha(v.get("fecha")), td_style),
            Paragraph(f"<b>{(v.get('apellido_nombre') or '')[:25]}</b>", td_style),
            Paragraph(str(v.get("cargo_codigo") or "")[:15], td_style),
            Paragraph(d_viaje, td_style),
            Paragraph(str(v.get("cant_dias") or "0"), td_style),
            Paragraph(f"<b>{utils.formato_moneda(v.get('importe_total') or 0)}</b>", td_style),
            Paragraph(str(v.get("imputacion") or "")[:14], td_style),
            Paragraph(str(v.get("cheque") or "-"), td_style),
            Paragraph(f"<b>{estado}</b>", td_style),
        ])
        
    v_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
    v_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (0, 0), (1, -1), "CENTER"),
        ("ALIGN", (5, 0), (5, -1), "CENTER"),
        ("ALIGN", (6, 0), (6, -1), "RIGHT"),
        ("ALIGN", (9, 0), (9, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(v_table)
    
    doc.build(elements)
