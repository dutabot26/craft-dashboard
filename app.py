"""
Dashboard Presupuesto 2026 – Craft Logistics
Conectado a SharePoint · Se actualiza automáticamente cada 30 minutos

Ejecutar: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from sharepoint_connector import cargar_config, validar_config, obtener_datos_sharepoint

# ─────────────────────────────────────────────
#  CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Presupuesto 2026 · Craft",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .stApp { background-color: #F8FAFC; }
  #MainMenu, footer { visibility: hidden; }
  .dash-header {
    background: linear-gradient(135deg, #0F1C3F 0%, #1A3A6B 100%);
    padding: 20px 28px; border-radius: 14px; margin-bottom: 22px;
  }
  .dash-header h1 { color: #FFFFFF; font-size: 22px; margin: 0; font-weight: 700; }
  .dash-header p  { color: #94AECF; font-size: 13px; margin: 4px 0 0 0; }
  .kpi-box {
    background: #FFFFFF; border-radius: 12px; padding: 18px 20px;
    border-left: 4px solid #1A56DB;
    box-shadow: 0 1px 6px rgba(0,0,0,0.07); margin-bottom: 4px;
  }
  .kpi-label { font-size: 11px; font-weight: 600; color: #64748B;
               text-transform: uppercase; letter-spacing: .06em; }
  .kpi-value { font-size: 26px; font-weight: 700; color: #0F1C3F;
               margin: 6px 0 2px; line-height: 1; }
  .kpi-sub   { font-size: 11px; color: #94A3B8; }
  .section-label {
    font-size: 11px; font-weight: 700; color: #64748B;
    text-transform: uppercase; letter-spacing: .1em;
    margin: 24px 0 12px; border-bottom: 1px solid #E2E8F0; padding-bottom: 6px;
  }
  .sp-badge {
    background: #EEF3FF; color: #1A56DB; border: 1px solid #BFDBFE;
    border-radius: 20px; padding: 3px 12px; font-size: 11px;
    font-weight: 600; display: inline-block;
  }
  .warn-box {
    background: #FFFBEB; border: 1px solid #FCD34D; border-radius: 10px;
    padding: 10px 16px; font-size: 12px; color: #92400E; margin-bottom: 14px;
  }
</style>
""", unsafe_allow_html=True)

PALETTE = ["#1A56DB","#7C3AED","#059669","#D97706","#DC2626",
           "#0891B2","#DB2777","#65A30D","#EA580C","#0369A1"]
COLORES_AREA = {"ADM":"#1A56DB","IT":"#7C3AED","GH":"#059669","Sin clasificar":"#94A3B8"}
MESES_ORDEN  = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

# ─────────────────────────────────────────────
#  CARGAR CONFIGURACIÓN
# ─────────────────────────────────────────────
config = cargar_config()
opciones = config.get("opciones", {})
empresa  = opciones.get("nombre_empresa", "Craft Logistics")
ttl_min  = opciones.get("actualizar_cada_minutos", 30)

if not validar_config(config):
    st.info("📋 **Instrucciones:** Abre `config.toml`, pega los 4 links de SharePoint y vuelve a cargar esta página.")
    st.stop()

archivos = config["archivos"]

# ─────────────────────────────────────────────
#  DESCARGAR DATOS DESDE SHAREPOINT
# ─────────────────────────────────────────────
datos = obtener_datos_sharepoint(
    facturas_link  = archivos["facturas"],
    ppto_adm_link  = archivos["ppto_adm"],
    ppto_gh_link   = archivos["ppto_gh"],
    ppto_it_link   = archivos["ppto_it"],
)

df        = datos.get("df", pd.DataFrame())
ppto_area = datos.get("ppto_area", pd.DataFrame())
ultima    = datos.get("ultima_act", "—")
n_sin_area = datos.get("n_sin_area", 0)
n_sin_suc  = datos.get("n_sin_suc", 0)

if df.empty:
    st.error("No se pudieron cargar los datos. Revisa los links en config.toml.")
    st.stop()

# ─────────────────────────────────────────────
#  SIDEBAR – FILTROS
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎛️ Filtros")

    meses_disp = ["Todos"] + [m for m in MESES_ORDEN if m in df["Mes"].values]
    sel_mes = st.multiselect("Mes de ejecución", meses_disp, default=["Todos"])

    areas_disp = sorted(df["Área"].unique().tolist())
    sel_area = st.multiselect("Área", areas_disp, default=areas_disp)

    sucs_disp = sorted(df["Sucursal"].unique().tolist())
    sel_suc = st.multiselect("Sucursal / Sede", sucs_disp, default=sucs_disp)

    tipos_disp = sorted(df["Tipo"].unique().tolist())
    sel_tipo = st.multiselect("Fijo / Variable", tipos_disp, default=tipos_disp)

    st.divider()
    st.markdown("### 🔄 Actualización")
    st.markdown(f'<span class="sp-badge">📁 SharePoint</span>', unsafe_allow_html=True)
    st.caption(f"Última carga: **{ultima}**")
    st.caption(f"Se actualiza cada **{ttl_min} min** automáticamente.")

    if st.button("🔄 Forzar actualización ahora"):
        obtener_datos_sharepoint.clear()
        st.rerun()

    st.divider()
    st.markdown("### 🔍 Calidad de datos")
    st.metric("Sin área",     f"{n_sin_area} facturas")
    st.metric("Sin sucursal", f"{n_sin_suc} facturas")
    st.caption("Los nulos se conservan como 'Sin clasificar', no se eliminan.")

# ─────────────────────────────────────────────
#  FILTRADO
# ─────────────────────────────────────────────
filtro = df.copy()
if "Todos" not in sel_mes and sel_mes:
    filtro = filtro[filtro["Mes"].isin(sel_mes)]
if sel_area:
    filtro = filtro[filtro["Área"].isin(sel_area)]
if sel_suc:
    filtro = filtro[filtro["Sucursal"].isin(sel_suc)]
if sel_tipo:
    filtro = filtro[filtro["Tipo"].isin(sel_tipo)]

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
  <h1>📊 Dashboard Presupuesto 2026 · {empresa}</h1>
  <p>Control de Gastos Operativos · ADM · IT · GH · COP
     &nbsp;·&nbsp; 📁 Fuente: SharePoint &nbsp;·&nbsp; 🕐 {ultima}</p>
</div>
""", unsafe_allow_html=True)

if n_sin_area + n_sin_suc > 0:
    st.markdown(f"""<div class="warn-box">
    ⚠️ <strong>{n_sin_area} facturas sin área</strong> y
    <strong>{n_sin_suc} sin sucursal</strong> están incluidas como "Sin clasificar".
    Se recomienda completar estos campos en el archivo fuente de SharePoint.
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  KPIs
# ─────────────────────────────────────────────
total_ppto  = ppto_area["Ppto_Anual"].sum() if not ppto_area.empty else 0
total_gasto = filtro["Monto"].sum()
saldo       = total_ppto - total_gasto
pct_ejec    = (total_gasto / total_ppto * 100) if total_ppto > 0 else 0
n_facturas  = len(filtro)
mes_validos = filtro[filtro["Mes_num"] > 0].groupby("Mes_num")["Monto"].sum()
prom_mes    = mes_validos.mean() if len(mes_validos) > 0 else 0

def fmt(v): return f"${v/1_000_000:,.1f}M"

st.markdown('<div class="section-label">Indicadores Clave</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""<div class="kpi-box" style="border-left-color:#1A56DB">
    <div class="kpi-label">Total Gastado</div>
    <div class="kpi-value" style="color:#1A56DB">{fmt(total_gasto)}</div>
    <div class="kpi-sub">COP acumulado</div></div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="kpi-box" style="border-left-color:#7C3AED">
    <div class="kpi-label">Presupuesto Anual</div>
    <div class="kpi-value" style="color:#7C3AED">{fmt(total_ppto)}</div>
    <div class="kpi-sub">ADM + IT + GH</div></div>""", unsafe_allow_html=True)

with c3:
    ce = "#059669" if pct_ejec < 80 else "#D97706" if pct_ejec < 95 else "#DC2626"
    st.markdown(f"""<div class="kpi-box" style="border-left-color:{ce}">
    <div class="kpi-label">% Ejecución</div>
    <div class="kpi-value" style="color:{ce}">{pct_ejec:.1f}%</div>
    <div class="kpi-sub">del presupuesto anual</div></div>""", unsafe_allow_html=True)

with c4:
    cs = "#059669" if saldo > 0 else "#DC2626"
    st.markdown(f"""<div class="kpi-box" style="border-left-color:{cs}">
    <div class="kpi-label">Saldo Disponible</div>
    <div class="kpi-value" style="color:{cs}">{fmt(saldo)}</div>
    <div class="kpi-sub">{"disponible" if saldo > 0 else "⚠️ excedido"}</div></div>""",
    unsafe_allow_html=True)

with c5:
    st.markdown(f"""<div class="kpi-box" style="border-left-color:#0891B2">
    <div class="kpi-label">Facturas</div>
    <div class="kpi-value" style="color:#0891B2">{n_facturas}</div>
    <div class="kpi-sub">Prom {fmt(prom_mes)}/mes</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  GRÁFICOS FILA 1: MENSUAL + COMPARATIVO
# ─────────────────────────────────────────────
st.markdown('<div class="section-label">Evolución & Comparativo por Área</div>', unsafe_allow_html=True)
g1, g2 = st.columns([3, 2])

with g1:
    mes_df = (filtro[filtro["Mes_num"] > 0]
              .groupby(["Mes_num","Mes"])["Monto"].sum()
              .reset_index().sort_values("Mes_num"))

    fig_mes = go.Figure()
    fig_mes.add_trace(go.Bar(x=mes_df["Mes"], y=mes_df["Monto"]/1e6,
                             name="Gasto mensual", marker_color=PALETTE[0]))
    fig_mes.add_trace(go.Scatter(x=mes_df["Mes"], y=mes_df["Monto"]/1e6,
                                  name="Tendencia", mode="lines+markers",
                                  line=dict(color="#D97706", width=2.5),
                                  marker=dict(size=7, color="#D97706")))
    fig_mes.update_layout(title="Gasto Mensual (COP millones)",
                          plot_bgcolor="white", paper_bgcolor="white",
                          yaxis_title="M COP", legend=dict(orientation="h", y=-0.2),
                          margin=dict(t=45,b=10,l=10,r=10), height=320)
    st.plotly_chart(fig_mes, use_container_width=True)

with g2:
    area_g = filtro.groupby("Área")["Monto"].sum().reset_index()
    area_g.columns = ["Area","Gastado"]
    comp = ppto_area.merge(area_g, on="Area", how="left").fillna(0)
    comp["Pct"] = (comp["Gastado"] / comp["Ppto_Anual"] * 100).round(1)

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(name="Presupuesto Anual",
                               x=comp["Area"], y=comp["Ppto_Anual"]/1e6,
                               marker_color="rgba(26,86,219,0.15)",
                               marker_line=dict(color="#1A56DB", width=1.5)))
    fig_comp.add_trace(go.Bar(name="Gastado",
                               x=comp["Area"], y=comp["Gastado"]/1e6,
                               marker_color=[COLORES_AREA.get(a,"#94A3B8") for a in comp["Area"]],
                               text=[f"{p}%" for p in comp["Pct"]],
                               textposition="outside"))
    fig_comp.update_layout(title="Presupuesto vs Ejecutado",
                           barmode="group", plot_bgcolor="white", paper_bgcolor="white",
                           yaxis_title="M COP", legend=dict(orientation="h", y=-0.2),
                           margin=dict(t=45,b=10,l=10,r=10), height=320)
    st.plotly_chart(fig_comp, use_container_width=True)

# ─────────────────────────────────────────────
#  FILA 2: SUCURSALES + TIPO DE GASTO
# ─────────────────────────────────────────────
st.markdown('<div class="section-label">Por Sucursal & Tipo de Gasto</div>', unsafe_allow_html=True)
g3, g4 = st.columns([3, 2])

with g3:
    suc_df = (filtro.groupby("Sucursal")["Monto"].sum()
              .reset_index().sort_values("Monto", ascending=True))
    suc_df["Pct"] = (suc_df["Monto"] / suc_df["Monto"].sum() * 100).round(1)

    fig_suc = go.Figure(go.Bar(
        x=suc_df["Monto"]/1e6, y=suc_df["Sucursal"], orientation="h",
        marker_color=[PALETTE[i % len(PALETTE)] for i in range(len(suc_df))],
        text=[f"${v:.1f}M ({p}%)" for v, p in zip(suc_df["Monto"]/1e6, suc_df["Pct"])],
        textposition="outside"))
    fig_suc.update_layout(title="Gasto por Sucursal (COP millones)",
                          plot_bgcolor="white", paper_bgcolor="white",
                          xaxis_title="M COP",
                          margin=dict(t=45,b=10,l=10,r=10), height=360)
    st.plotly_chart(fig_suc, use_container_width=True)

with g4:
    cta_df = (filtro.groupby("Cuenta")["Monto"].sum()
              .reset_index().sort_values("Monto", ascending=False).head(8))
    fig_pie = px.pie(cta_df, values="Monto", names="Cuenta",
                     title="Distribución por Tipo de Gasto",
                     color_discrete_sequence=PALETTE, hole=0.45)
    fig_pie.update_traces(textposition="inside", textinfo="percent+label", textfont_size=10)
    fig_pie.update_layout(showlegend=False,
                          margin=dict(t=45,b=10,l=10,r=10), height=360,
                          plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig_pie, use_container_width=True)

# ─────────────────────────────────────────────
#  FILA 3: TOP PROVEEDORES + TABLA
# ─────────────────────────────────────────────
st.markdown('<div class="section-label">Top Proveedores & Detalle</div>', unsafe_allow_html=True)
g5, g6 = st.columns([2, 3])

with g5:
    prov_df = (filtro[filtro["Proveedor"] != "Sin proveedor"]
               .groupby("Proveedor")["Monto"].sum()
               .reset_index().sort_values("Monto", ascending=False).head(10))
    prov_df["Pct"] = (prov_df["Monto"] / filtro["Monto"].sum() * 100).round(1)

    fig_prov = go.Figure(go.Bar(
        x=prov_df["Monto"]/1e6, y=prov_df["Proveedor"].str[:32],
        orientation="h", marker_color=PALETTE[0],
        text=[f"{p}%" for p in prov_df["Pct"]], textposition="outside"))
    fig_prov.update_layout(title="Top 10 Proveedores",
                           plot_bgcolor="white", paper_bgcolor="white",
                           xaxis_title="M COP", yaxis=dict(autorange="reversed"),
                           margin=dict(t=45,b=10,l=10,r=10), height=380)
    st.plotly_chart(fig_prov, use_container_width=True)

with g6:
    tabla = filtro[["Proveedor","Área","Sucursal","Cuenta","Tipo","Mes","Monto"]].copy()
    tabla["Monto"] = tabla["Monto"].apply(lambda x: f"${x:,.0f}")
    st.markdown("**Detalle de facturas filtradas**")
    st.dataframe(tabla.rename(columns={"Tipo":"Fijo/Variable","Monto":"Monto COP"}),
                 use_container_width=True, height=340, hide_index=True)
    st.caption(f"{len(tabla)} facturas mostradas")

# ─────────────────────────────────────────────
#  FILA 4: ÁREA × MES
# ─────────────────────────────────────────────
st.markdown('<div class="section-label">Gasto por Área y Mes</div>', unsafe_allow_html=True)
am = (filtro[filtro["Mes_num"] > 0]
      .groupby(["Área","Mes_num","Mes"])["Monto"].sum()
      .reset_index().sort_values("Mes_num"))

fig_am = px.bar(am, x="Mes", y=am["Monto"]/1e6, color="Área",
                color_discrete_map=COLORES_AREA, barmode="group",
                title="Gasto Mensual por Área (COP millones)",
                labels={"y":"M COP"}, text_auto=".1f")
fig_am.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                     legend=dict(orientation="h", y=-0.15),
                     margin=dict(t=45,b=10,l=10,r=10), height=320)
st.plotly_chart(fig_am, use_container_width=True)

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.divider()
st.caption(
    f"📁 Fuente: SharePoint · {empresa}  "
    f"| 🕐 Última actualización: {ultima}  "
    f"| 🔄 Refresco automático cada {ttl_min} min  "
    f"| ⚠️ Nulos tratados como 'Sin clasificar' (no eliminados)"
)
