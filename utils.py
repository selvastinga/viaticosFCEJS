"""
Utilidades para el Sistema de Viáticos
- Conversión de números a palabras en español (formato bancario / oficial)
- Formato de moneda y fechas
- Cálculo de días
"""
from datetime import datetime, date

UNIDADES = (
    "", "Un", "Dos", "Tres", "Cuatro", "Cinco", "Seis", "Siete", "Ocho", "Nueve",
    "Diez", "Once", "Doce", "Trece", "Catorce", "Quince", "Dieciséis", "Diecisiete",
    "Dieciocho", "Diecinueve", "Veinte", "Veintiuno", "Veintidós", "Veintitrés",
    "Veinticuatro", "Veinticinco", "Veintiséis", "Veintisiete", "Veintiocho", "Veintinueve"
)

DECENAS = (
    "", "", "", "Treinta", "Cuarenta", "Cincuenta", "Sesenta", "Setenta", "Ochenta", "Noventa"
)

CENTENAS = (
    "", "Ciento", "Doscientos", "Trescientos", "Cuatrocientos", "Quinientos",
    "Seiscientos", "Setecientos", "Ochocientos", "Novecientos"
)


def _centenas_a_letras(n: int) -> str:
    if n == 0:
        return ""
    if n == 100:
        return "Cien"
    
    c = n // 100
    resto = n % 100
    
    partes = []
    if c > 0:
        partes.append(CENTENAS[c])
    
    if resto < 30:
        if resto > 0:
            partes.append(UNIDADES[resto])
    else:
        d = resto // 10
        u = resto % 10
        if u == 0:
            partes.append(DECENAS[d])
        else:
            partes.append(f"{DECENAS[d]} y {UNIDADES[u]}")
            
    return " ".join(p for p in partes if p)


def _miles_a_letras(n: int) -> str:
    if n == 0:
        return ""
    
    miles = n // 1000
    resto = n % 1000
    
    partes = []
    if miles > 0:
        if miles == 1:
            partes.append("Mil")
        else:
            partes.append(f"{_centenas_a_letras(miles)} Mil")
            
    if resto > 0:
        partes.append(_centenas_a_letras(resto))
        
    return " ".join(partes)


def _entero_a_letras(n: int) -> str:
    if n == 0:
        return "Cero"
        
    millones = n // 1_000_000
    resto_millones = n % 1_000_000
    
    partes = []
    if millones > 0:
        if millones == 1:
            partes.append("Un Millón")
        else:
            partes.append(f"{_miles_a_letras(millones)} Millones")
            
    if resto_millones > 0:
        partes.append(_miles_a_letras(resto_millones))
        
    return " ".join(partes)


def numero_a_letras(monto: float) -> str:
    """
    Convierte un número a letras en formato oficial bancario / cheque.
    Ejemplo: 240000.0 -> "Doscientos Cuarenta Mil Pesos 00/100"
    """
    try:
        monto_float = float(monto)
    except (ValueError, TypeError):
        return ""
        
    entero = int(abs(monto_float))
    centavos = int(round((abs(monto_float) - entero) * 100))
    
    if centavos == 100:
        entero += 1
        centavos = 0
        
    letras = _entero_a_letras(entero)
    
    if entero == 1:
        moneda = "Peso"
    elif entero > 0 and entero % 1_000_000 == 0:
        moneda = "de Pesos"
    else:
        moneda = "Pesos"
        
    return f"{letras} {moneda} {centavos:02d}/100"


def formato_moneda(valor: float, incluir_simbolo: bool = True) -> str:
    """
    Formatea un número decimal a formato de moneda argentino (separador de miles con punto y decimales con coma).
    Ejemplo: 240000.0 -> "$ 240.000,00"
    """
    try:
        v = float(valor)
    except (ValueError, TypeError):
        v = 0.0
        
    # Formato con coma decimal y punto de miles
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if incluir_simbolo:
        return f"$ {s}"
    return s


def formato_fecha(fecha_val) -> str:
    """
    Convierte fechas (date, datetime, str YYYY-MM-DD) a formato DD/MM/YYYY.
    """
    if not fecha_val:
        return ""
    if isinstance(fecha_val, (datetime, date)):
        return fecha_val.strftime("%d/%m/%Y")
    
    s = str(fecha_val).strip()
    if not s:
        return ""
    # Si ya viene en formato DD/MM/YYYY
    if len(s) == 10 and s[2] == "/" and s[5] == "/":
        return s
    try:
        dt = datetime.strptime(s[:10], "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return s


def fecha_a_iso(fecha_val) -> str:
    """
    Convierte fecha DD/MM/YYYY a formato YYYY-MM-DD para inputs tipo date.
    """
    if not fecha_val:
        return ""
    s = str(fecha_val).strip()
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s
    try:
        dt = datetime.strptime(s, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return s


def calcular_dias(desde_str: str, hasta_str: str) -> float:
    """
    Calcula la cantidad de días entre dos fechas (Hasta - Desde).
    Acepta formato YYYY-MM-DD o DD/MM/YYYY.
    """
    if not desde_str or not hasta_str:
        return 0.0
    
    def _parse(val):
        v = str(val).strip()
        if "/" in v:
            return datetime.strptime(v, "%d/%m/%Y").date()
        return datetime.strptime(v[:10], "%Y-%m-%d").date()

    try:
        d1 = _parse(desde_str)
        d2 = _parse(hasta_str)
        diff = (d2 - d1).days
        return float(max(0, diff))
    except Exception:
        return 0.0
