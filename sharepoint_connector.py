"""
sharepoint_connector.py  v3
Lee REGISTRO + REGISTRO NO PAGAR del nuevo archivo homologado.
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

def _link_descarga(link):
    if not link or str(link).startswith("PEGA_AQUI"):
        return None
    return link + ("&download=1" if "?" in link else "?download=1")

def descargar_excel(link, nombre):
    url = _link_descarga(link)
    if not url:
        return None
    try:
        r = requests.get(url, headers={"User-Agent":"CraftDashboard/3.0"},
                         timeout=30, allow_redirects=True)
        r.raise_for_status()
        if r.content[:4] == b'PK\x03\x04':
            return r.content
        st.warning(f"⚠️ {nombre}: el link no apunta a un .xlsx. Verifica que sea un archivo individual.")
        return None
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        msgs = {403:"🔒 Sin permiso. El link debe ser 'Cualquier persona con el vínculo'.",
                404:"❌ Archivo no encontrado. Verifica el link en config.toml."}
        st.error(f"{nombre}: {msgs.get(code, f'Error HTTP {code}')}")
        return None
    except Exception as e:
        st.error(f"Error descargando {nombre}: {e}")
        return None

def cargar_config():
    try:
        return toml.load("config.toml")
    except FileNotFoundError:
        st.error("❌ No se encontró config.toml.")
        st.stop()

def validar_config(config):
    faltantes = [k for k,v in config.get("archivos",{}).items()
                 if str(v).startswith("PEGA_AQUI")]
    if faltantes:
        st.error(f"⚙️ Faltan links en config.toml: **{', '.join(faltantes)}**")
        return False
    return True

def _parsear_mes(texto):
    """'enero 2025' → (1, 2025, 'Enero 2025')"""
    if pd.isna(texto):
        return 0, 0, "Sin mes"
    partes = str(texto).lower().strip().split()
    num = MESES_MAP.get(partes[0], 0)
    anio = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else 0
    nombre = f"{partes[0].capitalize()} {anio}" if anio else partes[0].capitalize()
    return num, anio, nombre

def _limpiar_registro(bytes_excel):
    """Lee hoja REGISTRO del archivo homologado."""
    raw = pd.read_excel(io.BytesIO(bytes_excel), sheet_name='REGISTRO', header=1)
    raw.columns = raw.iloc[0].tolist()          # fila 0 = encabezados reales
    data = raw.iloc[1:].copy().reset_index(drop=True)

    data['Monto']     = pd.to_numeric(data.get('MONTO FACTURA', 0), errors='coerce')
    data['Gasto_Neto']= pd.to_numeric(data.get('GASTO NETO', data['Monto']), errors='coerce')
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
    data['Mes_num']   = parsed.apply(lambda x: x[0])
    data['Anio']      = parsed.apply(lambda x: x[1])
    data['Mes']       = parsed.apply(lambda x: x[2])

    return data[['Fuente','Proveedor','Area','Sucursal','Cuenta','Tipo',
                 'Servicio','Detalle','Monto','Gasto_Neto','Mes_num','Anio','Mes']]

def _limpiar_no_pagar(bytes_excel):
    """Lee hoja REGISTRO NO PAGAR del archivo homologado."""
    raw = pd.read_excel(io.BytesIO(bytes_excel), sheet_name='REGISTRO NO PAGAR', header=1)
    raw.columns = raw.iloc[0].tolist()
    data = raw.iloc[1:].copy().reset_index(drop=True)

    data['Monto']     = pd.to_numeric(data.get('MONTO', 0), errors='coerce')
    data['Gasto_Neto']= data['Monto'].copy()
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
    data['Mes_num']   = parsed.apply(lambda x: x[0])
    data['Anio']      = parsed.apply(lambda x: x[1])
    data['Mes']       = parsed.apply(lambda x: x[2])

    return data[['Fuente','Proveedor','Area','Sucursal','Cuenta','Tipo',
                 'Servicio','Detalle','Monto','Gasto_Neto','Mes_num','Anio','Mes']]

def _presupuesto_mensual(bytes_adm, bytes_it, bytes_gh):
    """Extrae presupuesto mensual real de los 3 archivos."""
    MESES = {1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
             7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"}
    rows = []

    # ADM – valor mensual fijo
    if bytes_adm:
        adm = pd.read_excel(io.BytesIO(bytes_adm),
                            sheet_name="Presupuesto mensual ADM General", header=1)
        adm.columns = ["skip","Item","Ppto_Mes","USD_Mes"]
        adm["Ppto_Mes"] = pd.to_numeric(adm["Ppto_Mes"], errors="coerce")
        adm = adm[adm["Ppto_Mes"] > 0].dropna(subset=["Ppto_Mes"])
        for _, r in adm.iterrows():
            for mn, mn_n in MESES.items():
                rows.append({"Area":"ADM","Item":r["Item"],"Mes_num":mn,"Mes":mn_n,"Ppto_Mes":r["Ppto_Mes"]})

    # IT – desglose mensual real
    if bytes_it:
        it = pd.read_excel(io.BytesIO(bytes_it), sheet_name="PPTO mensual IT", header=None)
        for _, r in it.iloc[3:, :].iterrows():
            item = str(r[0]).strip()
            if not item or item in ["nan","None"] or "TOTAL" in item.upper():
                continue
            for col_idx, (mn, mn_n) in enumerate(MESES.items(), start=1):
                val = pd.to_numeric(r[col_idx], errors="coerce")
                if pd.notna(val) and val > 0:
                    rows.append({"Area":"IT","Item":item,"Mes_num":mn,"Mes":mn_n,"Ppto_Mes":val})

    # GH – total mensual por actividad
    if bytes_gh:
        gh = pd.read_excel(io.BytesIO(bytes_gh), sheet_name="BD HR", header=0)
        cols = (["skip","Proceso","Actividad","Cantidad","Costo_ind",
                 "Total_Año","Total_mes","Frecuencia","Frecuencia2","IPC"]
                + [f"c{i}" for i in range(max(0,len(gh.columns)-10))])
        gh.columns = cols
        gh["Total_mes"] = pd.to_numeric(gh["Total_mes"], errors="coerce")
        gh_clean = gh[gh["Total_mes"] > 0].dropna(subset=["Total_mes"])
        for _, r in gh_clean.iterrows():
            for mn, mn_n in MESES.items():
                rows.append({"Area":"GH","Item":str(r["Actividad"]),"Mes_num":mn,"Mes":mn_n,"Ppto_Mes":r["Total_mes"]})

    if rows:
        df = pd.DataFrame(rows)
        ppto_mensual = df.groupby(["Area","Mes_num","Mes"])["Ppto_Mes"].sum().reset_index().sort_values("Mes_num")
        ppto_area    = df.groupby("Area")["Ppto_Mes"].sum().reset_index().rename(columns={"Ppto_Mes":"Ppto_Anual"})
        return ppto_mensual, ppto_area

    # Fallback con valores conocidos
    ppto_area = pd.DataFrame([
        {"Area":"ADM","Ppto_Anual":5_020_000_000},
        {"Area":"IT", "Ppto_Anual":473_000_000},
        {"Area":"GH", "Ppto_Anual":314_225_957},
    ])
    return pd.DataFrame(), ppto_area

@st.cache_data(ttl=1800, show_spinner=False)
def obtener_datos_sharepoint(facturas_link, ppto_adm_link, ppto_gh_link, ppto_it_link):
    out = {}

    with st.spinner("📥 Descargando facturas desde SharePoint..."):
        b_fact = descargar_excel(facturas_link, "Facturas")
    with st.spinner("📥 Descargando presupuesto ADM..."):
        b_adm  = descargar_excel(ppto_adm_link,  "Presupuesto ADM")
    with st.spinner("📥 Descargando presupuesto IT..."):
        b_it   = descargar_excel(ppto_it_link,   "Presupuesto IT")
    with st.spinner("📥 Descargando presupuesto GH..."):
        b_gh   = descargar_excel(ppto_gh_link,   "Presupuesto GH")

    if b_fact:
        df_reg = _limpiar_registro(b_fact)
        df_np  = _limpiar_no_pagar(b_fact)
        df     = pd.concat([df_reg, df_np], ignore_index=True)
        out["df"]         = df
        out["n_sin_area"] = (df["Area"] == "Sin clasificar").sum()
        out["n_sin_suc"]  = (df["Sucursal"] == "Sin clasificar").sum()
    else:
        out["df"] = pd.DataFrame()
        out["n_sin_area"] = out["n_sin_suc"] = 0

    ppto_mensual, ppto_area = _presupuesto_mensual(b_adm, b_it, b_gh)
    out["ppto_mensual"] = ppto_mensual
    out["ppto_area"]    = ppto_area
    out["ultima_act"]   = datetime.now().strftime("%d/%m/%Y %H:%M")
    return out
