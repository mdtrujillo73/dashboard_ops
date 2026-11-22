"""
Página 4: Proveedores (Persona Natural vs. Persona Jurídica), Género y Recurrencia Contractual
Colombia Compra Eficiente – Observatorio de Prestación de Servicios (OPS 2018–2026)
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Proveedores y Recurrencia | OPS CCE", page_icon="👥", layout="wide")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.styles import inject_css
from utils.data_loader import (
    load_entidades_data,
    load_recurrencia_data,
    load_consecutivos_data,
    load_top_contratistas,
    render_sidebar_filters,
    fmt_int_co,
    fmt_dec_co,
    fmt_billones,
    fmt_cop_exacto,
    ORDEN_ORDER,
    ORDEN_LABELS,
    PROVEEDOR_COLORS,
)
from utils.charts import (
    chart_proveedor_binario,
    CCE_AZUL,
    CCE_NARANJA,
    CCE_ROJO,
    CCE_MORADO,
    CCE_VERDE,
    LAYOUT_DEFAULTS,
)

inject_css()

df_raw = load_entidades_data()
if df_raw.empty:
    st.error("Ejecute primero `python dashboard_ops/build_dashboard_data.py`.")
    st.stop()

df = render_sidebar_filters(df_raw)
if df.empty:
    st.warning("No hay registros para los filtros seleccionados.")
    st.stop()

tot_c = int(df["N_CONTRATOS"].sum())
tot_v = float(df["VALOR_TOTAL"].sum())

df_pn = df[df["TIPO_PROVEEDOR_FINAL"] == "PERSONA NATURAL"]
df_pj = df[df["TIPO_PROVEEDOR_FINAL"] == "PERSONA JURIDICA"]

pn_c, pn_v = int(df_pn["N_CONTRATOS"].sum()), float(df_pn["VALOR_TOTAL"].sum())
pj_c, pj_v = int(df_pj["N_CONTRATOS"].sum()), float(df_pj["VALOR_TOTAL"].sum())

c_muj = int(df["CONTRATOS_MUJER"].sum())
c_hom = int(df["CONTRATOS_HOMBRE"].sum())
v_muj = float(df["VALOR_MUJER"].sum())
v_hom = float(df["VALOR_HOMBRE"].sum())
tot_gen = max(c_muj + c_hom, 1)

st.markdown("# 👥 Proveedores, Enfoque de Género y Recurrencia Contractual")
st.markdown(
    "Análisis bajo la taxonomía oficial depurada en **dos únicas categorías** (`PERSONA NATURAL` y `PERSONA JURIDICA`), "
    "distribución de género en contratistas naturales y recurrencia interanual."
)

# ── KPIs PRINCIPALES ────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Persona Natural</div>
        <div class="kpi-value">{fmt_int_co(pn_c)}</div>
        <div class="kpi-sub">{fmt_dec_co(pn_c / max(tot_c, 1) * 100, 1)}% contratos • {fmt_billones(pn_v, short=True)}</div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""
    <div class="kpi-card naranja">
        <div class="kpi-label">Persona Jurídica</div>
        <div class="kpi-value">{fmt_int_co(pj_c)}</div>
        <div class="kpi-sub">{fmt_dec_co(pj_c / max(tot_c, 1) * 100, 1)}% contratos • {fmt_billones(pj_v, short=True)}</div>
    </div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""
    <div class="kpi-card morado">
        <div class="kpi-label">Mujeres (Persona Natural)</div>
        <div class="kpi-value">{fmt_dec_co(c_muj / tot_gen * 100, 1)}%</div>
        <div class="kpi-sub">{fmt_int_co(c_muj)} contratos • Prom.: {fmt_cop_exacto(v_muj / max(c_muj, 1))}</div>
    </div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""
    <div class="kpi-card verde">
        <div class="kpi-label">Hombres (Persona Natural)</div>
        <div class="kpi-value">{fmt_dec_co(c_hom / tot_gen * 100, 1)}%</div>
        <div class="kpi-sub">{fmt_int_co(c_hom)} contratos • Prom.: {fmt_cop_exacto(v_hom / max(c_hom, 1))}</div>
    </div>""", unsafe_allow_html=True)

# ── SECCIÓN 1: PERSONA NATURAL VS JURÍDICA ─────────────────────────────────
st.markdown('<div class="section-header">⚖️ Persona Natural vs. Persona Jurídica: Volumen vs. Cuantía</div>', unsafe_allow_html=True)

p1, p2, p3 = st.columns([1.0, 1.0, 1.35])
with p1:
    st.markdown("**Por número de contratos**")
    st.plotly_chart(chart_proveedor_binario(df, "contratos"), width="stretch", key="p4_dona_c")
with p2:
    st.markdown("**Por valor contratado ($ Billones)**")
    st.plotly_chart(chart_proveedor_binario(df, "valor"), width="stretch", key="p4_dona_v")
with p3:
    st.markdown("**% Persona Jurídica en el Valor por Carácter Territorial**")
    ord_tp = (
        df.groupby(["ORDEN_CPS", "TIPO_PROVEEDOR_FINAL"], observed=True)
        .agg(Contratos=("N_CONTRATOS", "sum"), Valor=("VALOR_TOTAL", "sum"))
        .reset_index()
    )
    ord_tp["Carácter"] = ord_tp["ORDEN_CPS"].map(ORDEN_LABELS)
    ord_tp["Valor_B"] = ord_tp["Valor"] / 1e12
    fig_otp = px.bar(
        ord_tp,
        x="Carácter",
        y="Valor_B",
        color="TIPO_PROVEEDOR_FINAL",
        category_orders={"Carácter": [ORDEN_LABELS[k] for k in ORDEN_ORDER]},
        color_discrete_map=PROVEEDOR_COLORS,
        barmode="group",
        labels={"Valor_B": "Valor ($ Billones COP)", "TIPO_PROVEEDOR_FINAL": "Tipo Proveedor Final"},
    )
    fig_otp.update_layout(**LAYOUT_DEFAULTS, legend=dict(orientation="h", y=1.1, x=1, xanchor="right"), height=340)
    st.plotly_chart(fig_otp, width="stretch", key="p4_ord_tp")

# ── SECCIÓN 2: ENFOQUE DE GÉNERO ────────────────────────────────────────────
st.markdown('<div class="section-header">⚧️ Enfoque de Género en Contratación de Personas Naturales</div>', unsafe_allow_html=True)

gen_anual = (
    df.groupby("ANIO", observed=True)
    .agg(
        Mujer_C=("CONTRATOS_MUJER", "sum"),
        Hombre_C=("CONTRATOS_HOMBRE", "sum"),
        Mujer_V=("VALOR_MUJER", "sum"),
        Hombre_V=("VALOR_HOMBRE", "sum"),
    )
    .reset_index()
    .sort_values("ANIO")
)
gen_anual["ANIO_STR"] = gen_anual["ANIO"].astype(str)
gen_anual["Prom_Mujer_M"] = np.where(gen_anual["Mujer_C"] > 0, (gen_anual["Mujer_V"] / gen_anual["Mujer_C"]) / 1e6, 0)
gen_anual["Prom_Hombre_M"] = np.where(gen_anual["Hombre_C"] > 0, (gen_anual["Hombre_V"] / gen_anual["Hombre_C"]) / 1e6, 0)

gg1, gg2 = st.columns(2)
with gg1:
    st.markdown("**Número de contratos OPS por sexo y vigencia**")
    fig_gc = go.Figure()
    fig_gc.add_trace(go.Bar(x=gen_anual["ANIO_STR"], y=gen_anual["Mujer_C"], name="Mujeres", marker_color=CCE_MORADO))
    fig_gc.add_trace(go.Bar(x=gen_anual["ANIO_STR"], y=gen_anual["Hombre_C"], name="Hombres", marker_color=CCE_AZUL))
    fig_gc.update_layout(**LAYOUT_DEFAULTS, barmode="group", yaxis_title="Número de Contratos", legend=dict(orientation="h", y=1.08, x=1, xanchor="right"), height=350)
    st.plotly_chart(fig_gc, width="stretch", key="p4_gen_c")

with gg2:
    st.markdown("**Valor promedio por contrato ($ Millones COP): Mujeres vs. Hombres**")
    fig_gv = go.Figure()
    fig_gv.add_trace(go.Scatter(x=gen_anual["ANIO_STR"], y=gen_anual["Prom_Mujer_M"], mode="lines+markers+text", text=gen_anual["Prom_Mujer_M"].round(1), textposition="bottom center", name="Mujeres ($M)", line=dict(color=CCE_MORADO, width=3)))
    fig_gv.add_trace(go.Scatter(x=gen_anual["ANIO_STR"], y=gen_anual["Prom_Hombre_M"], mode="lines+markers+text", text=gen_anual["Prom_Hombre_M"].round(1), textposition="top center", name="Hombres ($M)", line=dict(color=CCE_AZUL, width=3)))
    fig_gv.update_layout(**LAYOUT_DEFAULTS, yaxis_title="Valor Promedio ($ Millones COP)", legend=dict(orientation="h", y=1.08, x=1, xanchor="right"), height=350)
    st.plotly_chart(fig_gv, width="stretch", key="p4_gen_v")

# ── SECCIÓN 3: RECURRENCIA Y CARRUSEL DE CONTRATOS OPS ──────────────────────
st.markdown('<div class="section-header">🔄 Recurrencia y Continuidad Contractual (Personas Naturales – Base Nacional 2018–2026)</div>', unsafe_allow_html=True)

df_rec = load_recurrencia_data()
df_cons = load_consecutivos_data()

if not df_rec.empty and not df_cons.empty:
    r1, r2 = st.columns([1.25, 1.0])
    with r1:
        nivel_rec = st.selectbox(
            "Ámbito de análisis de multiplicidad anual:",
            options=["TOTAL NACIONAL (CONSOLIDADO)", "NACIONAL", "DEPARTAMENTAL", "MUNICIPAL"],
            key="nivel_rec_ops",
        )
        sub_rec = df_rec[df_rec["ORDEN_CPS"] == nivel_rec].sort_values("ANIO")
        sub_rec["ANIO_STR"] = sub_rec["ANIO"].astype(str)

        fig_rec = go.Figure()
        fig_rec.add_trace(go.Bar(x=sub_rec["ANIO_STR"], y=sub_rec["CON_1_CONTRATO"], name="1 contrato/año", marker_color=CCE_AZUL))
        fig_rec.add_trace(go.Bar(x=sub_rec["ANIO_STR"], y=sub_rec["CON_2_CONTRATOS"], name="2 contratos/año", marker_color=CCE_NARANJA))
        fig_rec.add_trace(go.Bar(x=sub_rec["ANIO_STR"], y=sub_rec["CON_3_CONTRATOS"], name="3 contratos/año", marker_color=CCE_MORADO))
        fig_rec.add_trace(go.Bar(x=sub_rec["ANIO_STR"], y=sub_rec["CON_4_O_MAS"], name="4+ contratos/año", marker_color=CCE_ROJO))
        fig_rec.update_layout(
            **LAYOUT_DEFAULTS,
            barmode="stack",
            yaxis_title="Personas Naturales Únicas",
            title="Distribución de Personas Naturales según número de contratos OPS firmados en el mismo año",
            legend=dict(orientation="h", y=1.08, x=1, xanchor="right"),
            height=380,
        )
        st.plotly_chart(fig_rec, width="stretch", key="p4_rec_bar")

    with r2:
        st.markdown("**Años consecutivos contratando con la MISMA entidad (2018–2026)**")
        st.caption("Indicador de recurrencia estructural / posible alerta de contrato realidad.")
        df_cons_s = df_cons.sort_values("ORDEN", ascending=False)
        fig_cons = go.Figure(go.Bar(
            x=df_cons_s["CONTRATISTAS"],
            y=df_cons_s["RANGO_ANIOS_CONSECUTIVOS"],
            orientation="h",
            marker_color=[CCE_ROJO, "#9E2044", CCE_MORADO, CCE_NARANJA, "#2E86C1", CCE_AZUL],
            text=df_cons_s.apply(lambda r: f"{fmt_int_co(r['CONTRATISTAS'])} ({fmt_dec_co(r['PCT'], 1)}%)", axis=1),
            textposition="outside",
        ))
        fig_cons.update_layout(**LAYOUT_DEFAULTS, xaxis_title="Personas Naturales Únicas", yaxis_title="", height=380)
        st.plotly_chart(fig_cons, width="stretch", key="p4_cons_bar")

# ── SECCIÓN 4: TOP PROVEEDORES ──────────────────────────────────────────────
df_top = load_top_contratistas()
if not df_top.empty:
    with st.expander("🏆 Ver perfiles con mayor volumen de contratos o cuantía (Top Proveedores 2018–2026)", expanded=False):
        t_pn, t_pj = st.tabs(["🏢 Top Personas Jurídicas", "👤 Top Personas Naturales (por frecuencia)"])
        with t_pj:
            sub_pj = df_top[df_top["TIPO_PROVEEDOR_FINAL"] == "PERSONA JURIDICA"].sort_values("VALOR_TOTAL", ascending=False).head(50).copy()
            sub_pj["Valor Total"] = sub_pj["VALOR_TOTAL"].apply(fmt_cop_exacto)
            sub_pj["Valor Promedio"] = sub_pj["VALOR_PROMEDIO"].apply(fmt_cop_exacto)
            st.dataframe(
                sub_pj[["NOMBRE_PROVEEDOR", "IDENTIFICACION", "N_CONTRATOS", "VIGENCIAS_ACTIVAS", "Valor Total", "Valor Promedio"]].rename(columns={
                    "NOMBRE_PROVEEDOR": "Proveedor", "IDENTIFICACION": "NIT / ID", "N_CONTRATOS": "Contratos", "VIGENCIAS_ACTIVAS": "Vigencias"
                }),
                width="stretch", hide_index=True, height=360,
            )
        with t_pn:
            sub_pn = df_top[df_top["TIPO_PROVEEDOR_FINAL"] == "PERSONA NATURAL"].sort_values("N_CONTRATOS", ascending=False).head(50).copy()
            sub_pn["Valor Total"] = sub_pn["VALOR_TOTAL"].apply(fmt_cop_exacto)
            sub_pn["Valor Promedio"] = sub_pn["VALOR_PROMEDIO"].apply(fmt_cop_exacto)
            st.dataframe(
                sub_pn[["NOMBRE_PROVEEDOR", "IDENTIFICACION", "N_CONTRATOS", "VIGENCIAS_ACTIVAS", "Valor Total", "Valor Promedio"]].rename(columns={
                    "NOMBRE_PROVEEDOR": "Proveedor", "IDENTIFICACION": "Identificación", "N_CONTRATOS": "Contratos", "VIGENCIAS_ACTIVAS": "Vigencias"
                }),
                width="stretch", hide_index=True, height=360,
            )
