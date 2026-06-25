"""
sharepoint_connector.py  v4
· Lee REGISTRO + REGISTRO NO PAGAR del archivo homologado
· Presupuestos con fallback robusto si el archivo no se puede leer
· Compatible con Python 3.14 / Streamlit Cloud
"""

import requests, io, toml
import pandas as pd
import streamlit as st
from datetime import datetime

MESES_MAP = {
    'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,'junio':6,
    'julio':7,'agosto':8,'septiembre':9,'octubre':10,'noviembre':11,'diciembre':12
}
MESES_NOM = {v: k.capitalize() for k, v in MESES_MAP.items()}

# Presupuestos anuales conocidos (fallback si no se puede leer el Excel)
PPTO_FALLBACK = {
    "ADM": 5_020_600_000.0,
    "IT":  473_000_000.0,
    "GH":  314_225_957.73,
}

def _link_descarga(link):
    if not link or str(link).startswith("PEGA_AQUI"):
        return None
    sep = "&" if "?" in link else "?"
    return f"{link}{sep}download=1"

def descargar_excel(link, nombre):
    """Descarga un Excel desde SharePoint. Retorna bytes o None."""
    url = _link_descarga(link)
    if not url:
        return None
    try:
        r = requests.get(url,
                         headers={"User-Agent": "CraftDashboard/4.0"},
                         timeout=45,
                         allow_redirects=True)
        r.raise_for_status()
        # Verificar magic bytes ZIP (xlsx = zip internamente)
        if r.content[:4] == b'PK\x03\x04':
            return r.content
        st.warning(f"⚠️ **{nombre}**: el link no apunta a un archivo .xlsx. "
                   "Verifica que sea un archivo individual, no una carpeta.")
        return None
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        if code == 403:
            st.error(f"🔒 **{nombre}**: sin permiso. "
                     "El link debe ser 'Cualquier persona con el vínculo'.")
        elif code == 404:
            st.error(f"❌ **{nombre}**: no encontrado. Verifica el link en config.toml.")
        else:
            st.error(f"Error HTTP {code} descargando **{nombre}**.")
        return None
    except requests.exceptions.Timeout:
        st.warning(f"⏱️ **{nombre}**: tiempo de espera agotado. Reintentando...")
        return None
    except Exception as e:
        st.error(f"Error descargando **{nombre}**: {e}")
        return None

def cargar_config():
    try:
        return toml.load("config.toml")
    except FileNotFoundError:
        st.error("❌ No se encontró config.toml. "
                 "Asegúrate de estar en la carpeta correcta.")
        st.stop()
    except Exception as e:
        st.error(f"Error leyendo config.toml: {e}")
        st.stop()

def validar_config(config):
    faltantes = [k for k, v in config.get("archivos", {}).items()
                 if str(v).startswith("PEGA_AQUI")]
    if faltantes:
        st.error(f"⚙️ Faltan links en config.toml: **{', '.join(faltantes)}**\n\n"
                 "Sigue las instrucciones del README para obtenerlos.")
        return False
    return True

# ── PARSEO DE MES ─────────────────────────────────────────────────
def _parsear_mes(texto):
    """'enero 2025' → (1, 2025, 'Enero 2025')"""
    if pd.isna(texto):
        return 0, 0, "Sin mes"
    partes = str(texto).lower().strip().split()
    num  = MESES_MAP.get(partes[0], 0)
    anio = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else 0
    nombre = f"{partes[0].capitalize()} {anio}" if anio else partes[0].capitalize()
    return num, anio, nombre

# ── LECTURA DE GASTOS ─────────────────────────────────────────────
def _limpiar_registro(b):
    """Hoja REGISTRO del archivo homologado."""
    raw = pd.read_excel(io.BytesIO(b), sheet_name='REGISTRO', header=1)
    raw.columns = raw.iloc[0].tolist()
    data = raw.iloc[1:].copy().reset_index(drop=True)

    data['Monto']      = pd.to_numeric(data.get('MONTO FACTURA', 0), errors='coerce')
    data['Gasto_Neto'] = pd.to_numeric(data.get('GASTO NETO', data['Monto']), errors='coerce')
    data = data[data['Monto'] > 0].copy()

    data['Fuente']    = 'REGISTRO'
    data['Proveedor'] = data['PROVEEDOR'].fillna('Sin proveedor')
    data['Area']      = data['ÁREA'].fillna('Sin clasificar')
    data['Sucursal']  = data['SUCURSAL'].fillna('Sin clasificar')
    data['Cuenta']    = data['CUENTA CONTABLE'].fillna('Sin clasificar')
    data['Tipo']      = data['TIPO'].fillna('Sin clasificar')
    data['Servicio']  = data['SERVICIO'].fillna('Sin clasificar')
    data['Detalle']   = data['DETALLE DEL GASTO'].fillna('')

    parsed = data['MES EJECUCIÓN'].apply(_parsear_mes)
    data['Mes_num'] = parsed.apply(lambda x: x[0])
    data['Anio']    = parsed.apply(lambda x: x[1])
    data['Mes']     = parsed.apply(lambda x: x[2])

    return data[['Fuente','Proveedor','Area','Sucursal','Cuenta','Tipo',
                 'Servicio','Detalle','Monto','Gasto_Neto','Mes_num','Anio','Mes']]

def _limpiar_no_pagar(b):
    """Hoja REGISTRO NO PAGAR del archivo homologado."""
    raw = pd.read_excel(io.BytesIO(b), sheet_name='REGISTRO NO PAGAR', header=1)
    raw.columns = raw.iloc[0].tolist()
    data = raw.iloc[1:].copy().reset_index(drop=True)

    data['Monto']      = pd.to_numeric(data.get('MONTO', 0), errors='coerce')
    data['Gasto_Neto'] = data['Monto'].copy()
    data = data[data['Monto'] > 0].copy()

    data['Fuente']    = 'NO PAGAR'
    data['Proveedor'] = data['PROVEEDOR'].fillna('Sin proveedor')
    data['Area']      = data['ÁREA'].fillna('Sin clasificar')
    data['Sucursal']  = data['SUCURSAL'].fillna('Sin clasificar')
    data['Cuenta']    = data['CUENTA CONTABLE'].fillna('Sin clasificar')
    data['Tipo']      = data['TIPO'].fillna('Sin clasificar')
    data['Servicio']  = data['SERVICIO'].fillna('Sin clasificar')
    data['Detalle']   = data['DETALLE DEL GASTO'].fillna('')

    parsed = data['MES EJECUCIÓN'].apply(_parsear_mes)
    data['Mes_num'] = parsed.apply(lambda x: x[0])
    data['Anio']    = parsed.apply(lambda x: x[1])
    data['Mes']     = parsed.apply(lambda x: x[2])

    return data[['Fuente','Proveedor','Area','Sucursal','Cuenta','Tipo',
                 'Servicio','Detalle','Monto','Gasto_Neto','Mes_num','Anio','Mes']]

# ── LECTURA DE PRESUPUESTOS ───────────────────────────────────────
MESES_12 = {1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
             7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",
             11:"Noviembre",12:"Diciembre"}

def _ppto_adm(b):
    """Presupuesto ADM: valor mensual fijo × 12 meses."""
    rows = []
    try:
        # Intentar con nombre exacto primero
        xl  = pd.ExcelFile(io.BytesIO(b))
        # Buscar la hoja correcta aunque el nombre tenga espacios raros
        hoja = next((s for s in xl.sheet_names
                     if 'mensual' in s.lower() and 'adm' in s.lower()), None)
        if hoja is None:
            hoja = next((s for s in xl.sheet_names
                         if 'presupuesto' in s.lower()), None)
        if hoja is None:
            raise ValueError(f"No se encontró hoja ADM. Hojas disponibles: {xl.sheet_names}")

        adm = pd.read_excel(io.BytesIO(b), sheet_name=hoja, header=1)
        adm.columns = ["skip", "Item", "Ppto_Mes", "USD_Mes"]
        adm["Ppto_Mes"] = pd.to_numeric(adm["Ppto_Mes"], errors="coerce")
        adm = adm[adm["Ppto_Mes"] > 0].dropna(subset=["Ppto_Mes"])

        for _, r in adm.iterrows():
            for mn, mn_n in MESES_12.items():
                rows.append({"Area":"ADM","Item":r["Item"],
                             "Mes_num":mn,"Mes":mn_n,"Ppto_Mes":r["Ppto_Mes"]})
        return rows, None

    except Exception as e:
        return rows, str(e)

def _ppto_it(b):
    """Presupuesto IT: desglose mensual real."""
    rows = []
    try:
        xl   = pd.ExcelFile(io.BytesIO(b))
        hoja = next((s for s in xl.sheet_names if 'it' in s.lower()), xl.sheet_names[0])
        it   = pd.read_excel(io.BytesIO(b), sheet_name=hoja, header=None)

        for _, r in it.iloc[3:, :].iterrows():
            item = str(r.iloc[0]).strip()
            if not item or item in ["nan","None"] or "TOTAL" in item.upper():
                continue
            for col_idx, (mn, mn_n) in enumerate(MESES_12.items(), start=1):
                try:
                    val = pd.to_numeric(r.iloc[col_idx], errors="coerce")
                    if pd.notna(val) and val > 0:
                        rows.append({"Area":"IT","Item":item,
                                     "Mes_num":mn,"Mes":mn_n,"Ppto_Mes":val})
                except IndexError:
                    pass
        return rows, None

    except Exception as e:
        return rows, str(e)

def _ppto_gh(b):
    """Presupuesto GH: total mensual por actividad."""
    rows = []
    try:
        xl   = pd.ExcelFile(io.BytesIO(b))
        hoja = next((s for s in xl.sheet_names if 'hr' in s.lower() or 'gh' in s.lower()),
                    xl.sheet_names[0])
        gh   = pd.read_excel(io.BytesIO(b), sheet_name=hoja, header=0)

        n_cols = len(gh.columns)
        base_cols = ["skip","Proceso","Actividad","Cantidad","Costo_ind",
                     "Total_Año","Total_mes","Frecuencia","Frecuencia2","IPC"]
        gh.columns = base_cols[:n_cols] + [f"c{i}" for i in range(max(0, n_cols-10))]

        gh["Total_mes"] = pd.to_numeric(gh["Total_mes"], errors="coerce")
        gh_clean = gh[gh["Total_mes"] > 0].dropna(subset=["Total_mes"])

        for _, r in gh_clean.iterrows():
            for mn, mn_n in MESES_12.items():
                rows.append({"Area":"GH","Item":str(r["Actividad"]),
                             "Mes_num":mn,"Mes":mn_n,"Ppto_Mes":r["Total_mes"]})
        return rows, None

    except Exception as e:
        return rows, str(e)

def _construir_ppto(rows_adm, rows_it, rows_gh,
                    err_adm, err_it, err_gh):
    """Une presupuestos. Si alguno falló, usa fallback proporcional."""
    avisos = []

    # ADM
    if not rows_adm:
        val = PPTO_FALLBACK["ADM"] / 12
        for mn, mn_n in MESES_12.items():
            rows_adm.append({"Area":"ADM","Item":"Presupuesto ADM",
                             "Mes_num":mn,"Mes":mn_n,"Ppto_Mes":val})
        avisos.append(f"ADM ({err_adm})")

    # IT
    if not rows_it:
        val = PPTO_FALLBACK["IT"] / 12
        for mn, mn_n in MESES_12.items():
            rows_it.append({"Area":"IT","Item":"Presupuesto IT",
                            "Mes_num":mn,"Mes":mn_n,"Ppto_Mes":val})
        avisos.append(f"IT ({err_it})")

    # GH
    if not rows_gh:
        val = PPTO_FALLBACK["GH"] / 12
        for mn, mn_n in MESES_12.items():
            rows_gh.append({"Area":"GH","Item":"Presupuesto GH",
                            "Mes_num":mn,"Mes":mn_n,"Ppto_Mes":val})
        avisos.append(f"GH ({err_gh})")

    if avisos:
        st.info(f"ℹ️ Presupuesto de **{', '.join(avisos)}** cargado desde valores de referencia "
                f"porque el archivo no pudo leerse. Los totales son aproximados.")

    df = pd.concat([pd.DataFrame(rows_adm),
                    pd.DataFrame(rows_it),
                    pd.DataFrame(rows_gh)], ignore_index=True)

    ppto_mensual = (df.groupby(["Area","Mes_num","Mes"])["Ppto_Mes"]
                    .sum().reset_index().sort_values("Mes_num"))
    ppto_area    = (df.groupby("Area")["Ppto_Mes"]
                    .sum().reset_index()
                    .rename(columns={"Ppto_Mes":"Ppto_Anual"}))
    return ppto_mensual, ppto_area

# ── FUNCIÓN PRINCIPAL ─────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def obtener_datos_sharepoint(facturas_link, ppto_adm_link,
                              ppto_gh_link, ppto_it_link):
    out = {}

    # ── Descargas paralelas con spinners ──────────────────────────
    with st.spinner("📥 Descargando facturas desde SharePoint..."):
        b_fact = descargar_excel(facturas_link, "Facturas")
    with st.spinner("📥 Descargando presupuesto ADM..."):
        b_adm  = descargar_excel(ppto_adm_link,  "Presupuesto ADM")
    with st.spinner("📥 Descargando presupuesto IT..."):
        b_it   = descargar_excel(ppto_it_link,   "Presupuesto IT")
    with st.spinner("📥 Descargando presupuesto GH..."):
        b_gh   = descargar_excel(ppto_gh_link,   "Presupuesto GH")

    # ── Gastos reales ─────────────────────────────────────────────
    if b_fact:
        try:
            df_reg = _limpiar_registro(b_fact)
        except Exception as e:
            st.error(f"Error leyendo hoja REGISTRO: {e}")
            df_reg = pd.DataFrame()

        try:
            df_np = _limpiar_no_pagar(b_fact)
        except Exception as e:
            st.error(f"Error leyendo hoja REGISTRO NO PAGAR: {e}")
            df_np = pd.DataFrame()

        df = pd.concat([df_reg, df_np], ignore_index=True) if not df_reg.empty else df_np
        out["df"]         = df
        out["n_sin_area"] = int((df["Area"] == "Sin clasificar").sum())
        out["n_sin_suc"]  = int((df["Sucursal"] == "Sin clasificar").sum())
    else:
        out["df"]         = pd.DataFrame()
        out["n_sin_area"] = 0
        out["n_sin_suc"]  = 0

    # ── Presupuestos (con fallback individual por área) ───────────
    rows_adm, err_adm = _ppto_adm(b_adm) if b_adm else ([], "archivo no descargado")
    rows_it,  err_it  = _ppto_it(b_it)   if b_it  else ([], "archivo no descargado")
    rows_gh,  err_gh  = _ppto_gh(b_gh)   if b_gh  else ([], "archivo no descargado")

    ppto_mensual, ppto_area = _construir_ppto(
        rows_adm, rows_it, rows_gh, err_adm, err_it, err_gh
    )
    out["ppto_mensual"] = ppto_mensual
    out["ppto_area"]    = ppto_area
    out["ultima_act"]   = datetime.now().strftime("%d/%m/%Y %H:%M")
    return out
