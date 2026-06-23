"""
sharepoint_connector.py
Descarga los archivos Excel desde SharePoint usando links de descarga directa.
No requiere Azure, ni OneDrive instalado, ni credenciales de API.
"""

import requests
import io
import toml
import pandas as pd
import streamlit as st
from datetime import datetime


def _link_a_descarga(link: str) -> str:
    """
    Convierte un link de SharePoint compartido en un link de descarga directa.

    SharePoint genera links como:
      https://craftms-my.sharepoint.com/:x:/g/personal/.../Archivo?e=TOKEN

    Para forzar descarga directa se reemplaza el prefijo del tipo de archivo
    (:x: para Excel, :f: para carpeta) por el endpoint de descarga.
    """
    if not link or link.startswith("PEGA_AQUI"):
        return None

    # Eliminar parámetros extras si los hay
    base = link.split("?")[0]
    token = link.split("?e=")[-1] if "?e=" in link else ""

    # SharePoint acepta &download=1 para forzar descarga
    url_descarga = link.rstrip("/")
    if "?" in url_descarga:
        url_descarga += "&download=1"
    else:
        url_descarga += "?download=1"

    return url_descarga


def descargar_excel(link: str, nombre: str) -> bytes | None:
    """
    Descarga un archivo Excel desde un link de SharePoint compartido.
    Retorna los bytes del archivo o None si falla.
    """
    url = _link_a_descarga(link)
    if not url:
        return None

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; CraftDashboard/1.0)",
        }
        resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        resp.raise_for_status()

        # Verificar que sea un Excel válido (magic bytes)
        content = resp.content
        if content[:4] == b'PK\x03\x04':  # ZIP signature (xlsx es un ZIP)
            return content
        else:
            st.warning(f"⚠️ El archivo **{nombre}** no parece ser un Excel válido. "
                       f"Verifica que el link sea de un archivo .xlsx, no de una carpeta.")
            return None

    except requests.exceptions.Timeout:
        st.error(f"⏱️ Tiempo de espera agotado al descargar **{nombre}**. "
                 f"Verifica tu conexión a internet.")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            st.error(f"🔒 Sin permiso para descargar **{nombre}**. "
                     f"Asegúrate de que el link sea 'Cualquier persona con el vínculo'.")
        elif e.response.status_code == 404:
            st.error(f"❌ Archivo **{nombre}** no encontrado. Verifica que el link sea correcto.")
        else:
            st.error(f"Error HTTP {e.response.status_code} al descargar **{nombre}**.")
        return None
    except Exception as e:
        st.error(f"Error inesperado al descargar **{nombre}**: {str(e)}")
        return None


def cargar_config() -> dict:
    """Lee el archivo config.toml y retorna la configuración."""
    try:
        return toml.load("config.toml")
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo **config.toml**. "
                 "Asegúrate de que esté en la misma carpeta que app.py.")
        st.stop()
    except Exception as e:
        st.error(f"Error al leer config.toml: {e}")
        st.stop()


def validar_config(config: dict) -> bool:
    """Verifica que todos los links estén configurados."""
    archivos = config.get("archivos", {})
    faltantes = [k for k, v in archivos.items() if v.startswith("PEGA_AQUI")]

    if faltantes:
        st.error(
            "⚙️ **Configuración incompleta.** Abre el archivo `config.toml` "
            f"y reemplaza los links de: **{', '.join(faltantes)}**\n\n"
            "Sigue las instrucciones dentro del archivo para saber cómo obtener los links."
        )
        return False
    return True


@st.cache_data(ttl=1800, show_spinner=False)  # cache 30 minutos
def obtener_datos_sharepoint(facturas_link, ppto_adm_link,
                              ppto_gh_link, ppto_it_link):
    """
    Descarga y procesa todos los archivos desde SharePoint.
    Se actualiza automáticamente cada 30 minutos (ttl=1800 segundos).
    """
    MESES = {0:"Sin mes", 1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril",
             5:"Mayo",    6:"Junio", 7:"Julio",   8:"Agosto",
             9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}

    resultados = {}

    # ── 1. GASTOS REALES ────────────────────────────────────────────
    with st.spinner("📥 Descargando facturas desde SharePoint..."):
        bytes_facturas = descargar_excel(facturas_link, "Cuadro Seguimiento Facturas")

    if bytes_facturas:
        raw = pd.read_excel(io.BytesIO(bytes_facturas), sheet_name="ADMINISTRATIVO")
        raw["Monto"] = pd.to_numeric(raw["Monto "], errors="coerce")

        # Solo filas con monto real (resto son filas vacías de formato Excel)
        df = raw[raw["Monto"] > 0].copy()

        # Nulos en clasificadores → etiqueta (NO se elimina la fila)
        df["Sucursal"]  = df["Sucursal"].fillna("Sin clasificar")
        df["Área"]      = df["Área"].fillna("Sin clasificar")
        df["Cuenta"]    = df["Cuenta"].fillna("Sin clasificar")
        df["Tipo"]      = df["Fijo / Variable"].fillna("Sin clasificar")
        df["Proveedor"] = df["Proveedor"].fillna("Sin proveedor")
        df["Mes_num"]   = pd.to_numeric(df["Mes Ejecución"], errors="coerce").fillna(0).astype(int)
        df["Mes"]       = df["Mes_num"].map(MESES)
        df["Fecha"]     = pd.to_datetime(df["fecha realización eventos"], errors="coerce")

        resultados["df"]           = df
        resultados["ultima_act"]   = datetime.now().strftime("%d/%m/%Y %H:%M")
        resultados["n_sin_area"]   = (df["Área"] == "Sin clasificar").sum()
        resultados["n_sin_suc"]    = (df["Sucursal"] == "Sin clasificar").sum()
    else:
        resultados["df"] = pd.DataFrame()

    # ── 2. PRESUPUESTO ADM ──────────────────────────────────────────
    with st.spinner("📥 Descargando presupuesto ADM..."):
        bytes_adm = descargar_excel(ppto_adm_link, "Presupuesto ADM")

    if bytes_adm:
        adm_raw = pd.read_excel(io.BytesIO(bytes_adm),
                                sheet_name="Presupuesto mensual ADM General",
                                header=1)
        adm_raw.columns = ["skip", "Item", "Ppto_Mes", "USD_Mes"]
        adm = adm_raw[["Item", "Ppto_Mes"]].copy()
        adm["Ppto_Mes"]   = pd.to_numeric(adm["Ppto_Mes"], errors="coerce")
        adm = adm.dropna(subset=["Ppto_Mes"])
        adm = adm[adm["Ppto_Mes"] > 0]
        adm["Ppto_Anual"] = adm["Ppto_Mes"] * 12
        adm["Area"]        = "ADM"
        resultados["ppto_adm"] = adm
    else:
        resultados["ppto_adm"] = pd.DataFrame()

    # ── 3. PRESUPUESTO IT ───────────────────────────────────────────
    with st.spinner("📥 Descargando presupuesto IT..."):
        bytes_it = descargar_excel(ppto_it_link, "Presupuesto IT")

    if bytes_it:
        it_xl = pd.read_excel(io.BytesIO(bytes_it),
                              sheet_name="PPTO mensual IT", header=None)
        total_row = it_xl[it_xl[0] == "TOTALCOP"]
        if not total_row.empty:
            it_total = pd.to_numeric(total_row.iloc[0, 14], errors="coerce")
        else:
            it_total = 473_000_000.0  # fallback al valor conocido
        resultados["it_total"] = it_total
    else:
        resultados["it_total"] = 473_000_000.0

    # ── 4. PRESUPUESTO GH ───────────────────────────────────────────
    with st.spinner("📥 Descargando presupuesto GH..."):
        bytes_gh = descargar_excel(ppto_gh_link, "Presupuesto GH")

    if bytes_gh:
        gh_xl = pd.read_excel(io.BytesIO(bytes_gh), sheet_name="BD HR", header=None)
        # Filas de totales por proceso
        totales = gh_xl[gh_xl[1].astype(str).str.startswith("Total")]
        if not totales.empty:
            gh_total = pd.to_numeric(totales[23], errors="coerce").sum()
        else:
            gh_total = 314_225_957.73  # fallback
        resultados["gh_total"] = gh_total
    else:
        resultados["gh_total"] = 314_225_957.73

    # ── PRESUPUESTO CONSOLIDADO ──────────────────────────────────────
    ppto_adm_total = resultados.get("ppto_adm", pd.DataFrame())
    adm_anual = ppto_adm_total["Ppto_Anual"].sum() if not ppto_adm_total.empty else 5_020_000_000.0
    it_anual  = resultados.get("it_total",  473_000_000.0)
    gh_anual  = resultados.get("gh_total",  314_225_957.73)

    ppto_area = pd.DataFrame([
        {"Area": "ADM", "Ppto_Anual": adm_anual},
        {"Area": "IT",  "Ppto_Anual": it_anual},
        {"Area": "GH",  "Ppto_Anual": gh_anual},
    ])
    resultados["ppto_area"] = ppto_area

    return resultados
