"""
Dashboard Presupuesto – Craft Logistics  v3
· Fuente: PROTOTIPO_Homologacion_CRAFT (REGISTRO + REGISTRO NO PAGAR)
· Conectado a SharePoint · Presupuesto mensual por área
Ejecutar: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sharepoint_connector import cargar_config, validar_config, obtener_datos_sharepoint

# ── PÁGINA ────────────────────────────────────────────────────────
st.set_page_config(page_title="Dashboard Presupuesto · Craft",
                   page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
  .stApp{background:#F8FAFC} #MainMenu,footer{visibility:hidden}
  .hdr{background:linear-gradient(135deg,#0F1C3F,#1A3A6B);
    padding:20px 28px;border-radius:14px;margin-bottom:22px}
  .hdr h1{color:#FFF;font-size:22px;margin:0;font-weight:700}
  .hdr p{color:#94AECF;font-size:13px;margin:4px 0 0}
  .kpi{background:#FFF;border-radius:12px;padding:18px 20px;
    box-shadow:0 1px 6px rgba(0,0,0,.07);margin-bottom:4px}
  .kl{font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.06em}
  .kv{font-size:26px;font-weight:700;margin:6px 0 2px;line-height:1}
  .ks{font-size:11px;color:#94A3B8}
  .sec{font-size:11px;font-weight:700;color:#64748B;text-transform:uppercase;
    letter-spacing:.1em;margin:24px 0 12px;border-bottom:1px solid #E2E8F0;padding-bottom:6px}
  .warn{background:#FFFBEB;border:1px solid #FCD34D;border-radius:10px;
    padding:10px 16px;font-size:12px;color:#92400E;margin-bottom:14px}
  .spb{background:#EEF3FF;color:#1A56DB;border:1px solid #BFDBFE;
    border-radius:20px;padding:3px 12px;font-size:11px;font-weight:600;display:inline-block}
</style>
""", unsafe_allow_html=True)

PAL       = ["#1A56DB","#7C3AED","#059669","#D97706","#DC2626",
             "#0891B2","#DB2777","#65A30D","#EA580C","#0369A1"]
COL_AREA  = {"ADM":"#1A56DB","IT":"#7C3AED","GH":"#059669","Sin clasificar":"#94A3B8"}
COL_FUENTE= {"REGISTRO":"#1A56DB","NO PAGAR":"#DC2626"}
MESES_ORD = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
             "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
fmt = lambda v: f"${v/1_000_000:,.1f}M"
fmt_cop = lambda v: f"${v:,.0f}"

# ── CONFIG & DATOS ────────────────────────────────────────────────
config   = cargar_config()
if not validar_config(config):
    st.info("📋 Abre config.toml, pega los links de SharePoint y recarga.")
    st.stop()

arc      = config["archivos"]
opciones = config.get("opciones", {})
empresa  = opciones.get("nombre_empresa", "Craft Logistics")
ttl_min  = opciones.get("actualizar_cada_minutos", 30)

datos = obtener_datos_sharepoint(arc["facturas"], arc["ppto_adm"],
                                  arc["ppto_gh"],  arc["ppto_it"])

df           = datos.get("df", pd.DataFrame())
ppto_mensual = datos.get("ppto_mensual", pd.DataFrame())
ppto_area    = datos.get("ppto_area", pd.DataFrame())
ultima       = datos.get("ultima_act", "—")
n_sin_area   = datos.get("n_sin_area", 0)
n_sin_suc    = datos.get("n_sin_suc", 0)

if df.empty:
    st.error("No se pudieron cargar los datos. Revisa los links en config.toml.")
    st.stop()

# Años y meses disponibles
anios_disp = sorted(df["Anio"].unique().tolist())
anios_disp = [a for a in anios_disp if a > 0]

# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎛️ Filtros")

    # Fuente
    fuentes_disp = sorted(df["Fuente"].unique().tolist())
    sel_fuente = st.multiselect("📂 Fuente", fuentes_disp, default=fuentes_disp,
                                 help="REGISTRO = facturas a pagar · NO PAGAR = rechazadas/baja")

    # Año
    if len(anios_disp) > 1:
        sel_anio = st.multiselect("📆 Año", anios_disp, default=anios_disp)
    else:
        sel_anio = anios_disp

    # Mes — opciones limpias tipo "Enero", sin el año
    meses_base = [m for m in MESES_ORD
                  if any(df["Mes"].str.startswith(m))]
    sel_mes = st.multiselect("📅 Mes de ejecución",
                              ["Todos"] + meses_base, default=["Todos"])

    # Área
    areas_disp = sorted(df["Area"].unique().tolist())
    sel_area = st.multiselect("🏢 Área", areas_disp, default=areas_disp)

    # Sucursal
    sucs_disp = sorted(df["Sucursal"].unique().tolist())
    sel_suc = st.multiselect("📍 Sucursal / Sede", sucs_disp, default=sucs_disp)

    # Fijo / Variable
    tipos_disp = sorted(df["Tipo"].unique().tolist())
    sel_tipo = st.multiselect("📌 Fijo / Variable", tipos_disp, default=tipos_disp)

    st.divider()

    # Vista presupuesto
    st.markdown("### 📋 Vista de Presupuesto")
    vista_ppto = st.radio("Mostrar presupuesto como:",
                           ["Anual (total año)", "Mensual (según filtro de meses)"],
                           index=0,
                           help="'Mensual' toma solo los meses seleccionados arriba.")

    st.divider()
    st.markdown("### 🔄 Actualización")
    st.markdown(f'<span class="spb">📁 SharePoint</span>', unsafe_allow_html=True)
    st.caption(f"Última carga: **{ultima}**")
    st.caption(f"Refresco automático cada **{ttl_min} min**")
    if st.button("🔄 Forzar actualización"):
        obtener_datos_sharepoint.clear()
        st.rerun()

    st.divider()
    st.markdown("### 🔍 Calidad de datos")
    st.metric("Sin área",     f"{n_sin_area} registros")
    st.metric("Sin sucursal", f"{n_sin_suc} registros")
    st.caption("Nulos → 'Sin clasificar', no eliminados.")

# ── FILTRADO ─────────────────────────────────────────────────────
f = df.copy()
if sel_fuente:
    f = f[f["Fuente"].isin(sel_fuente)]
if sel_anio:
    f = f[f["Anio"].isin(sel_anio)]
if "Todos" not in sel_mes and sel_mes:
    f = f[f["Mes"].apply(lambda m: any(m.startswith(s) for s in sel_mes))]
if sel_area:
    f = f[f["Area"].isin(sel_area)]
if sel_suc:
    f = f[f["Sucursal"].isin(sel_suc)]
if sel_tipo:
    f = f[f["Tipo"].isin(sel_tipo)]

meses_activos = [m for m in sel_mes if m != "Todos"]

# ── PRESUPUESTO SEGÚN VISTA ───────────────────────────────────────
if not ppto_mensual.empty:
    pm = ppto_mensual[ppto_mensual["Area"].isin(sel_area)] if sel_area else ppto_mensual.copy()
    if vista_ppto.startswith("Mensual") and meses_activos:
        pm = pm[pm["Mes"].apply(lambda m: any(m.startswith(s) for s in meses_activos))]
    ppto_calc = pm.groupby("Area")["Ppto_Mes"].sum().reset_index().rename(columns={"Ppto_Mes":"Ppto_Anual"})
else:
    ppto_calc = ppto_area[ppto_area["Area"].isin(sel_area)].copy() if sel_area else ppto_area.copy()

label_ppto = "Presupuesto " + ("Mensual" if vista_ppto.startswith("Mensual") and meses_activos else "Anual")

# ── KPIs ──────────────────────────────────────────────────────────
total_ppto  = ppto_calc["Ppto_Anual"].sum() if not ppto_calc.empty else 0
total_gasto = f["Monto"].sum()
saldo       = total_ppto - total_gasto
pct_ejec    = (total_gasto / total_ppto * 100) if total_ppto > 0 else 0
n_fact      = len(f)
mes_v       = f[f["Mes_num"] > 0].groupby("Mes_num")["Monto"].sum()
prom_mes    = mes_v.mean() if len(mes_v) > 0 else 0

# ── HEADER ────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hdr">
  <h1>📊 Dashboard Presupuesto · {empresa}</h1>
  <p>REGISTRO + NO PAGAR · ADM · IT · GH · COP · 📁 SharePoint · 🕐 {ultima}</p>
</div>""", unsafe_allow_html=True)

if n_sin_area + n_sin_suc > 0:
    st.markdown(f"""<div class="warn">
    ⚠️ <strong>{n_sin_area} registros sin área</strong> y
    <strong>{n_sin_suc} sin sucursal</strong> incluidos como "Sin clasificar".
    Se recomienda completar estos campos en el Excel de SharePoint.
    </div>""", unsafe_allow_html=True)

# ── KPI CARDS ─────────────────────────────────────────────────────
st.markdown('<div class="sec">Indicadores Clave</div>', unsafe_allow_html=True)
c1,c2,c3,c4,c5 = st.columns(5)

cards = [
    (c1,"Total Gastado",   fmt(total_gasto),    "COP acumulado",   "#1A56DB"),
    (c2, label_ppto,       fmt(total_ppto),      "ADM + IT + GH",   "#7C3AED"),
    (c3,"% Ejecución",     f"{pct_ejec:.1f}%",  "gastado vs ppto", "#059669" if pct_ejec<80 else "#D97706" if pct_ejec<95 else "#DC2626"),
    (c4,"Saldo Disponible",fmt(abs(saldo)),      "disponible ✅" if saldo>=0 else "⚠️ excedido", "#059669" if saldo>=0 else "#DC2626"),
    (c5,"Registros",       str(n_fact),          f"Prom {fmt(prom_mes)}/mes", "#0891B2"),
]
for col, lbl, val, sub, clr in cards:
    with col:
        st.markdown(f"""<div class="kpi" style="border-left:4px solid {clr}">
        <div class="kl">{lbl}</div>
        <div class="kv" style="color:{clr}">{val}</div>
        <div class="ks">{sub}</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── EJECUCIÓN MENSUAL vs PRESUPUESTO ─────────────────────────────
st.markdown('<div class="sec">Ejecución Mensual vs Presupuesto</div>', unsafe_allow_html=True)

mes_gasto = (f[f["Mes_num"]>0].groupby(["Mes_num","Mes"])["Monto"]
             .sum().reset_index().sort_values("Mes_num"))

if not ppto_mensual.empty:
    pm_vis = ppto_mensual[ppto_mensual["Area"].isin(sel_area)] if sel_area else ppto_mensual
    pm_tot = (pm_vis.groupby(["Mes_num","Mes"])["Ppto_Mes"]
              .sum().reset_index().sort_values("Mes_num"))
    merged = mes_gasto.merge(pm_tot, on=["Mes_num","Mes"], how="outer").sort_values("Mes_num").fillna(0)
else:
    merged = mes_gasto.copy(); merged["Ppto_Mes"] = 0

fig_ej = go.Figure()
fig_ej.add_trace(go.Bar(name="Presupuesto", x=merged["Mes"], y=merged["Ppto_Mes"]/1e6,
                         marker_color="rgba(26,86,219,0.18)",
                         marker_line=dict(color="#1A56DB",width=1.5)))
fig_ej.add_trace(go.Bar(name="Gastado",     x=merged["Mes"], y=merged["Monto"]/1e6,
                         marker_color="#1A56DB"))
fig_ej.add_trace(go.Scatter(name="Tendencia", x=merged["Mes"], y=merged["Monto"]/1e6,
                              mode="lines+markers",
                              line=dict(color="#D97706",width=2),
                              marker=dict(size=6,color="#D97706")))
fig_ej.update_layout(barmode="group", plot_bgcolor="white", paper_bgcolor="white",
                     yaxis_title="M COP", legend=dict(orientation="h",y=-0.18),
                     margin=dict(t=20,b=10,l=10,r=10), height=340)
st.plotly_chart(fig_ej, use_container_width=True)

# ── POR ÁREA + SUCURSAL ───────────────────────────────────────────
st.markdown('<div class="sec">Por Área & Sucursal</div>', unsafe_allow_html=True)
g1, g2 = st.columns(2)

with g1:
    ag = f.groupby("Area")["Monto"].sum().reset_index()
    ag.columns = ["Area","Gastado"]
    comp = ppto_calc.merge(ag, on="Area", how="left").fillna(0)
    comp["Pct"] = (comp["Gastado"]/comp["Ppto_Anual"]*100).round(1)
    fig_c = go.Figure()
    fig_c.add_trace(go.Bar(name=label_ppto, x=comp["Area"], y=comp["Ppto_Anual"]/1e6,
                            marker_color="rgba(26,86,219,0.15)",
                            marker_line=dict(color="#1A56DB",width=1.5)))
    fig_c.add_trace(go.Bar(name="Gastado",   x=comp["Area"], y=comp["Gastado"]/1e6,
                            marker_color=[COL_AREA.get(a,"#94A3B8") for a in comp["Area"]],
                            text=[f"{p}%" for p in comp["Pct"]], textposition="outside"))
    fig_c.update_layout(title=f"{label_ppto} vs Ejecutado", barmode="group",
                        plot_bgcolor="white", paper_bgcolor="white", yaxis_title="M COP",
                        legend=dict(orientation="h",y=-0.2),
                        margin=dict(t=45,b=10,l=10,r=10), height=340)
    st.plotly_chart(fig_c, use_container_width=True)

with g2:
    sg = (f.groupby("Sucursal")["Monto"].sum().reset_index()
          .sort_values("Monto", ascending=True))
    sg["Pct"] = (sg["Monto"]/sg["Monto"].sum()*100).round(1)
    fig_s = go.Figure(go.Bar(
        x=sg["Monto"]/1e6, y=sg["Sucursal"], orientation="h",
        marker_color=[PAL[i%len(PAL)] for i in range(len(sg))],
        text=[f"${v:.1f}M ({p}%)" for v,p in zip(sg["Monto"]/1e6, sg["Pct"])],
        textposition="outside"))
    fig_s.update_layout(title="Gasto por Sucursal", plot_bgcolor="white",
                        paper_bgcolor="white", xaxis_title="M COP",
                        margin=dict(t=45,b=10,l=10,r=10), height=340)
    st.plotly_chart(fig_s, use_container_width=True)

# ── PRESUPUESTO MENSUAL POR ÁREA ──────────────────────────────────
st.markdown('<div class="sec">Presupuesto Mensual por Área</div>', unsafe_allow_html=True)
if not ppto_mensual.empty:
    pm_v = ppto_mensual[ppto_mensual["Area"].isin(sel_area)] if sel_area else ppto_mensual
    if "Todos" not in sel_mes and meses_activos:
        pm_v = pm_v[pm_v["Mes"].apply(lambda m: any(m.startswith(s) for s in meses_activos))]
    fig_pm = px.bar(pm_v, x="Mes", y=pm_v["Ppto_Mes"]/1e6, color="Area",
                    color_discrete_map=COL_AREA, barmode="group",
                    title="Presupuesto mensual por área (COP millones)",
                    labels={"y":"M COP"}, text_auto=".0f",
                    category_orders={"Mes":MESES_ORD})
    fig_pm.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                         legend=dict(orientation="h",y=-0.15),
                         margin=dict(t=45,b=10,l=10,r=10), height=320)
    st.plotly_chart(fig_pm, use_container_width=True)

    tabla_pm = pm_v.pivot_table(index="Mes", columns="Area",
                                 values="Ppto_Mes", aggfunc="sum").reset_index()
    for col in tabla_pm.columns[1:]:
        tabla_pm[col] = tabla_pm[col].apply(lambda x: f"${x/1e6:,.1f}M" if pd.notna(x) else "—")
    st.dataframe(tabla_pm, use_container_width=True, hide_index=True)

# ── TIPO GASTO + PROVEEDORES ──────────────────────────────────────
st.markdown('<div class="sec">Tipo de Gasto & Top Proveedores</div>', unsafe_allow_html=True)
g3, g4 = st.columns(2)

with g3:
    cta = (f.groupby("Cuenta")["Monto"].sum().reset_index()
           .sort_values("Monto", ascending=False).head(8))
    cta = cta[cta["Cuenta"] != "Sin clasificar"]
    fig_pie = px.pie(cta, values="Monto", names="Cuenta",
                     title="Distribución por Tipo de Gasto",
                     color_discrete_sequence=PAL, hole=0.45)
    fig_pie.update_traces(textposition="inside", textinfo="percent+label", textfont_size=10)
    fig_pie.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
                          margin=dict(t=45,b=10,l=10,r=10), height=340)
    st.plotly_chart(fig_pie, use_container_width=True)

with g4:
    prov = (f[f["Proveedor"]!="Sin proveedor"]
            .groupby("Proveedor")["Monto"].sum().reset_index()
            .sort_values("Monto", ascending=False).head(10))
    prov["Pct"] = (prov["Monto"]/f["Monto"].sum()*100).round(1)
    fig_pv = go.Figure(go.Bar(
        x=prov["Monto"]/1e6, y=prov["Proveedor"].str[:32], orientation="h",
        marker_color=PAL[0],
        text=[f"{p}%" for p in prov["Pct"]], textposition="outside"))
    fig_pv.update_layout(title="Top 10 Proveedores", plot_bgcolor="white",
                         paper_bgcolor="white", xaxis_title="M COP",
                         yaxis=dict(autorange="reversed"),
                         margin=dict(t=45,b=10,l=10,r=10), height=340)
    st.plotly_chart(fig_pv, use_container_width=True)

# ── GASTO POR ÁREA × MES ─────────────────────────────────────────
st.markdown('<div class="sec">Gasto por Área y Mes</div>', unsafe_allow_html=True)
am = (f[f["Mes_num"]>0].groupby(["Area","Mes_num","Mes"])["Monto"]
      .sum().reset_index().sort_values("Mes_num"))
fig_am = px.bar(am, x="Mes", y=am["Monto"]/1e6, color="Area",
                color_discrete_map=COL_AREA, barmode="group",
                title="Gasto mensual por área (COP millones)",
                labels={"y":"M COP"}, text_auto=".1f")
fig_am.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                     legend=dict(orientation="h",y=-0.15),
                     margin=dict(t=45,b=10,l=10,r=10), height=320)
st.plotly_chart(fig_am, use_container_width=True)

# ── TABLA DETALLE ─────────────────────────────────────────────────
st.markdown('<div class="sec">Detalle de Registros</div>', unsafe_allow_html=True)

tabla = f[["Fuente","Proveedor","Servicio","Area","Sucursal",
           "Cuenta","Tipo","Mes","Monto","Gasto_Neto"]].copy()

# Formato COP correcto — sin decimales, con separador de miles, símbolo $
tabla["Monto"]     = tabla["Monto"].apply(lambda x: f"${x:,.0f}")
tabla["Gasto_Neto"]= tabla["Gasto_Neto"].apply(lambda x: f"${x:,.0f}")

tabla = tabla.rename(columns={
    "Fuente":"Fuente","Proveedor":"Proveedor","Servicio":"Servicio",
    "Area":"Área","Sucursal":"Sede","Cuenta":"Tipo de Gasto",
    "Tipo":"Fijo/Variable","Mes":"Mes","Monto":"Monto Factura (COP)",
    "Gasto_Neto":"Gasto Neto (COP)"
})

# Colorear fila según fuente
def color_fuente(row):
    if row["Fuente"] == "NO PAGAR":
        return ["background-color:#FFF5F5;color:#991B1B"]*len(row)
    return [""]*len(row)

st.dataframe(
    tabla.style.apply(color_fuente, axis=1),
    use_container_width=True,
    height=380,
    hide_index=True
)
st.caption(
    f"🔵 **REGISTRO** ({len(f[f['Fuente']=='REGISTRO'])} registros) · "
    f"🔴 **NO PAGAR** ({len(f[f['Fuente']=='NO PAGAR'])} registros) · "
    f"Total: {len(tabla)} · Montos en COP con separador de miles"
)

# ── FOOTER ────────────────────────────────────────────────────────
st.divider()
st.caption(f"📁 SharePoint · {empresa} · {ultima} · Refresco cada {ttl_min} min · "
           "Nulos → 'Sin clasificar' (no eliminados) · Montos en COP")
