"""
Página 3: Evolución Histórica, Comparativo Presidencial y Efecto Ley de Garantías Electorales
Colombia Compra Eficiente – Observatorio de Prestación de Servicios (OPS 2018–2026)
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Evolución y Gobiernos | OPS CCE", page_icon="📅", layout="wide")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.styles import inject_css
from utils.data_loader import (
    load_entidades_data,
    load_mensual_data,
    apply_filters,
    render_sidebar_filters,
    fmt_int_co,
    fmt_dec_co,
    fmt_billones,
    fmt_cop_exacto,
    GOBIERNO_ORDER,
    GOBIERNO_COLORS,
    ORDEN_ORDER,
    ORDEN_LABELS,
    ORDEN_COLORS,
)
from utils.charts import (
    chart_serie_mensual_garantias,
    chart_transicion_secop,
    CCE_AZUL,
    CCE_ROJO,
    CCE_NARANJA,
    CCE_VERDE,
    LAYOUT_DEFAULTS,
)

inject_css()

df_raw = load_entidades_data()
df_mes_raw = load_mensual_data()
if df_raw.empty or df_mes_raw.empty:
    st.error("Ejecute primero `python dashboard_ops/build_dashboard_data.py`.")
    st.stop()

df, filtros = render_sidebar_filters(df_raw, return_state=True)
df_mes = apply_filters(
    df_mes_raw,
    anios=filtros["anios"],
    gobiernos=filtros["gobiernos"],
    ordenes=filtros["ordenes"],
    departamentos=filtros["departamentos"],
    fuentes=filtros["fuentes"],
    tipos_proveedor=filtros["tipos_proveedor"],
)

if df.empty:
    st.warning("No hay registros para los filtros seleccionados.")
    st.stop()

st.markdown("# 📅 Evolución Histórica, Periodos Presidenciales y Ley de Garantías")
st.markdown(
    "Análisis comparativo entre periodos de gobierno (fechas exactas de posesión presidencial el 7 de agosto), "
    "estacionalidad mensual y picos de contratación previa a **Ley de Garantías Electorales**."
)

# ── BLOQUE 1: TARJETAS POR PERIODO PRESIDENCIAL ──────────────────────────────
st.markdown('<div class="section-header">⚖️ Comparativo por Periodo Presidencial (2018–2026)</div>', unsafe_allow_html=True)

gob_meses = df_mes.groupby("GOBIERNO", observed=True)["ANIO_MES"].nunique().to_dict()
gob_agg = df.groupby("GOBIERNO", observed=True).agg(
    contratos=("N_CONTRATOS", "sum"),
    valor=("VALOR_TOTAL", "sum"),
    entidades=("CODIGO_ENTIDAD", "nunique"),
    dur_sum=("DURACION_SUMA", "sum"),
    dur_cnt=("DURACION_CONTEO", "sum"),
)

gobs_presentes = [g for g in GOBIERNO_ORDER if g in gob_agg.index]
cols_g = st.columns(max(len(gobs_presentes), 1))
cls_map = {
    "Santos II (cierre 2018)": "gris",
    "Duque (2018–2022)": "",
    "Petro (2022–2026)": "rojo",
    "Post 7-Ago-2026 (ago–nov)": "verde",
}
for col_ui, gob_name in zip(cols_g, gobs_presentes):
    cls_c = cls_map.get(gob_name, "")
    if gob_name in gob_agg.index:
        r = gob_agg.loc[gob_name]
        nc = int(r["contratos"])
        vv = float(r["valor"])
        ne = int(r["entidades"])
        n_meses = max(int(gob_meses.get(gob_name, 1)), 1)
        prom_mes = nc / n_meses
        val_mes = vv / n_meses
    else:
        nc, vv, ne, n_meses, prom_mes, val_mes = 0, 0.0, 0, 1, 0.0, 0.0

    with col_ui:
        st.markdown(f"""
        <div class="kpi-card {cls_c}">
            <div class="kpi-label">{gob_name}</div>
            <div class="kpi-value">{fmt_int_co(nc)}</div>
            <div class="kpi-sub"><b>{fmt_billones(vv)}</b> • {fmt_int_co(ne)} entidades ({n_meses} meses con datos)</div>
            <div class="kpi-sub">📈 Promedio mensual: <b>{fmt_int_co(prom_mes)}</b> contratos/mes • <b>{fmt_billones(val_mes, short=True)}</b>/mes</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

c_g1, c_g2 = st.columns(2)
with c_g1:
    st.markdown("**Contratos por Periodo Presidencial y Carácter Territorial**")
    gob_ord = (
        df.groupby(["GOBIERNO", "ORDEN_CPS"], observed=True)["N_CONTRATOS"]
        .sum()
        .reset_index(name="Contratos")
    )
    gob_ord["Carácter"] = gob_ord["ORDEN_CPS"].map(ORDEN_LABELS)
    fig_go = px.bar(
        gob_ord,
        x="GOBIERNO",
        y="Contratos",
        color="Carácter",
        category_orders={"GOBIERNO": GOBIERNO_ORDER, "Carácter": [ORDEN_LABELS[k] for k in ORDEN_ORDER]},
        color_discrete_map={ORDEN_LABELS[k]: v for k, v in ORDEN_COLORS.items()},
        barmode="stack",
        labels={"GOBIERNO": "Periodo Presidencial", "Contratos": "Número de Contratos"},
    )
    fig_go.update_layout(**LAYOUT_DEFAULTS, legend=dict(orientation="h", y=1.08, x=1, xanchor="right"), height=360)
    st.plotly_chart(fig_go, width="stretch", key="gob_ord_c")

with c_g2:
    st.markdown("**Intensidad Mensual Normalizada (Contratos y Billones promedio por mes)**")
    rows_norm = []
    for g in GOBIERNO_ORDER:
        if g in gob_agg.index:
            m_cnt = max(int(gob_meses.get(g, 1)), 1)
            rows_norm.append({
                "Periodo": g,
                "Contratos / Mes": gob_agg.loc[g, "contratos"] / m_cnt,
                "Billones / Mes": (gob_agg.loc[g, "valor"] / 1e12) / m_cnt,
            })
    df_norm = pd.DataFrame(rows_norm)
    if not df_norm.empty:
        fig_norm = go.Figure()
        fig_norm.add_trace(go.Bar(
            x=df_norm["Periodo"],
            y=df_norm["Contratos / Mes"],
            name="Contratos / Mes",
            marker_color=[GOBIERNO_COLORS.get(p, CCE_AZUL) for p in df_norm["Periodo"]],
            text=df_norm["Contratos / Mes"].apply(lambda v: fmt_int_co(v)),
            textposition="outside",
        ))
        fig_norm.update_layout(**LAYOUT_DEFAULTS, yaxis_title="Promedio Mensual de Contratos", height=360)
        st.plotly_chart(fig_norm, width="stretch", key="gob_norm_mes")

# ── BLOQUE 2: SERIE MENSUAL Y LEY DE GARANTÍAS ──────────────────────────────
st.markdown('<div class="section-header">🚨 Serie Mensual Interactiva y Efecto Ley de Garantías Electorales</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="info-box">📌 <b>Patrón Electoral Comprobado:</b> Las bandas sombreadas corresponden a las ventanas de restricción de contratación directa por <b>Ley de Garantías Electorales</b> (Ley 996 de 2005). En los meses de <b>enero de año electoral presidencial (2018, 2022, 2026)</b> se evidencia el fenómeno de contratación acelerada previa a la entrada en vigencia de la prohibición.</div>',
    unsafe_allow_html=True,
)

met_mes = st.radio(
    "Métrica de serie mensual:",
    options=["contratos", "valor"],
    format_func=lambda x: "📄 Contratos Firmados por Mes" if x == "contratos" else "💰 Valor Contratado por Mes ($ Billones)",
    horizontal=True,
    key="met_mes_ops",
)
st.plotly_chart(chart_serie_mensual_garantias(df_mes, met_mes), width="stretch", key="serie_mes_garantias")

# ── BLOQUE 3: ESTACIONALIDAD (MES DEL AÑO x VIGENCIA) ──────────────────────
st.markdown('<div class="section-header">📆 Estacionalidad Mensual: El Pico de Enero y Cierre de Vigencia</div>', unsafe_allow_html=True)

mes_names = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
piv_mes = (
    df_mes.groupby(["ANIO", "MES"], observed=True)["N_CONTRATOS"]
    .sum()
    .unstack(fill_value=0)
)
piv_mes.columns = [mes_names.get(int(c), str(c)) for c in piv_mes.columns]

fig_est = px.imshow(
    piv_mes,
    text_auto=True,
    aspect="auto",
    color_continuous_scale=[[0.0, "#F8FAFC"], [0.35, "#7FB3D5"], [0.7, CCE_AZUL], [1.0, CCE_ROJO]],
    labels=dict(x="Mes de Firma", y="Vigencia", color="Contratos"),
)
fig_est.update_layout(**LAYOUT_DEFAULTS, height=390)
st.plotly_chart(fig_est, width="stretch", key="heatmap_estacionalidad")

# ── BLOQUE 4: TRANSICIÓN SECOP I -> SECOP II ────────────────────────────────
st.markdown('<div class="section-header">💻 Adopción Digital: Migración de Contratos OPS de SECOP I a SECOP II</div>', unsafe_allow_html=True)
st.plotly_chart(chart_transicion_secop(df, "contratos"), width="stretch", key="trans_secop_p3")
